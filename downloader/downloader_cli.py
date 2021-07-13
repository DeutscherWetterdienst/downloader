#!/usr/bin/env python
""" downloader.py

 Script to download and extract NWP files in GRIB2 format from DWD's open data file server https://opendata.dwd.de

 Author:
    Eduard Rosert
 Version history:
    0.1, 2020-06-26, initial version
    0.2, 2021-07-13, added optional --time-step-interval parameter
"""

import bz2
import click
import json
import math
import os
import urllib.request
from datetime import datetime, timedelta, timezone

from . import logger as log
# custom stringFormatter with uppercase/lowercase functionality
from .formatter import ExtendedFormatter
from .version import __version__

try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 `importlib_resources`.
    import importlib_resources as pkg_resources

from . import models as models

log.setLevel(level="INFO")
available = {
    "models" : {},
    "grids" : {}
}

def parseAvailable(models:dict):
    available_opts = {
        "models" : {},
        "grids" : {}
    }
    for model in models:
        available_opts["models"][model["model"]] = model
        if "grids" in model:
            for grid in model["grids"]:
                available_opts["grids"][grid] = grid
    return available_opts

jsonobj = pkg_resources.open_text(package=models, resource= "models.json")

with jsonobj as jsonfile:
    models = json.load(jsonfile)
    available = parseAvailable(models)

CONTEXT_SETTINGS = dict(
    help_option_names=["-h", "--help"],
    info_name = "downloader",
    token_normalize_func=lambda x: x.lower(),
    no_args_is_help = True
)
@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version=__version__)
def cli(): 
    pass

stringFormatter = ExtendedFormatter()

def loadAvailable(filename:str="models.json"):
    with open(filename,"r") as jsonfile:
        models = json.load(jsonfile)
        available = parseAvailable(models)



def configureHttpProxyForUrllib( proxySettings = {'http': 'proxyserver:8080'} ):
    proxy = urllib.request.ProxyHandler(proxySettings)
    opener = urllib.request.build_opener(proxy)
    urllib.request.install_opener(opener)


def getMostRecentTimestamp(waitTimeMinutes:int=360, modelIntervalHours:int=3):
    # model data becomes available approx 1.5 hours (90minutes) after a model run
    # cosmo-d2 model and icon-eu run every 3 hours
    now = datetime.utcnow() - timedelta(minutes=waitTimeMinutes)
    latestAvailableUTCRun = int(math.floor(now.hour/modelIntervalHours) * modelIntervalHours)
    modelTimestamp = datetime( now.year, now.month, now.day, latestAvailableUTCRun)
    return modelTimestamp

# @click.command(help="Display the latest available timestamp for the given model.")
# @click.option("--model", 
#     help="the NWP model name", 
#     type=click.Choice(availableModels.keys(), case_sensitive=False),
#     required=True )
def getMostRecentModelTimestamp(model:str):
    selectedModel = available["models"][model]
    openDataDeliveryOffsetMinutes = selectedModel["openDataDeliveryOffsetMinutes"]
    modelIntervalHours = selectedModel["intervalHours"]
    return getMostRecentTimestamp(
        waitTimeMinutes=openDataDeliveryOffsetMinutes, 
        modelIntervalHours=modelIntervalHours)

def downloadAndExtractBz2FileFromUrl( url , destFilePath=None, destFileName=None):
    log.info("downloading file: '{0}'".format(url))

    if destFileName == "" or destFileName == None:
        # strip the filename from the url and remove the bz2 extension
        destFileName = url.split('/')[-1].split('.bz2')[0]

    if destFilePath == "" or destFilePath == None:
        destFilePath = os.getcwd()

    resource = urllib.request.urlopen(url)
    compressedData = resource.read()
    binaryData = bz2.decompress(compressedData)
    fullFilePath = os.path.join(destFilePath, destFileName)
    log.info("saving file as: '{0}'".format(fullFilePath))
    with open(fullFilePath, 'wb') as outfile:
        outfile.write(binaryData)
    log.info("Done.")

def getGribFileUrl(model="icon-eu", grid=None, param="t_2m", timestep=0, timestamp=getMostRecentTimestamp(waitTimeMinutes=180, modelIntervalHours=12)):
    cfg = available["models"][model]
    levtype = "single-level"
    if grid is None:
        log.warn("No grid specified. Trying to use default.")
        grid = cfg["grids"][0]
        log.warn("Grid type '{}' selected".format(grid))
    elif grid not in cfg["grids"]:
        log.warn("Unknown grid type '{}' for model '{}'.".format(grid,model))
    url = cfg["pattern"]["single-level"]
    # pattern is something like this:
    #  "https://opendata.dwd.de/weather/nwp/{model!l}/grib/{modelrun:>02d}/{param!l}/{model!l}_{scope}_{grid}_{levtype}_{timestamp:%Y%m%d}{modelrun:>02d}_{step:>03d}_{param!u}.grib2.bz2"
    # e.g. https://opendata.dwd.de/weather/nwp/icon/grib/09/t_2m/icon_global_icosahedral_single-level_2020062609_000_T_2M.grib2.bz2
    return stringFormatter.format( url,
        model = cfg["model"],
        param = param,
        grid = grid,
        modelrun = timestamp.hour,
        scope = cfg["scope"],
        levtype = levtype,
        timestamp = timestamp,
        step = timestep)

def downloadGribData( model="icon-eu", grid=None, param="t_2m", timestep=0, timestamp=getMostRecentTimestamp(), destFilePath=None, destFileName=None ):
    dataUrl=getGribFileUrl(model=model, grid=grid, param=param, timestep=timestep, timestamp=timestamp)#

    downloadAndExtractBz2FileFromUrl(dataUrl, destFilePath=destFilePath, destFileName=destFileName)


def downloadGribDataSequence(model:str, grid:str=None, param:str="t_2m", minTimeStep:int=0, maxTimeStep:int=12, timeStepInterval:int=1, timestamp:datetime=None, destFilePath=None ):
    fields = [p.strip() for p in param.split(',')]
    #get latest timestamp if necessary
    if timestamp is None: 
        timestamp = getMostRecentModelTimestamp( model=model )
    #download data from open data server for the next x steps
    for timestep in range(minTimeStep, maxTimeStep+1, timeStepInterval):
        for field in fields:
            downloadGribData(model=model, grid=grid, param=field, timestep=timestep, timestamp=timestamp, destFilePath=destFilePath)

def formatDateIso8601(date):
    return date.replace(microsecond=0,tzinfo=timezone.utc).isoformat()

def getTimestampString(date):
    modelrun = "{0:02d}".format(date.hour)
    return date.strftime("%Y%m%d"+ modelrun )


@click.command(help="Downloads NWP model data in GRIB2 format from DWD's Open Data file server https://opendata.dwd.de using HTTPS.")
@click.option("--model", 
    help="the NWP model name", 
    type=click.Choice(available["models"].keys(), case_sensitive=False),
    required=False,
    default=None )
@click.option("--grid",
    type=click.Choice(available["grids"].keys(), case_sensitive=False),
    help="the model grid",
    required=False, 
    default=None )
@click.option("--single-level-fields",
    type=click.STRING,
    help="one or more single-level model fields that should be donwloaded, e.g. t_2m,tmax_2m,clch,pmsl, ...",
    required=True, 
    default="t_2m" )
@click.option("--min-time-step",
    type=click.INT,
    help="the minimum forecast time step to download (default=0)",
    required=False, 
    default=0 )
@click.option("--max-time-step",
    type=click.INT,
    help="the maximung forecast time step to download, e.g. 12 will download time steps from min-time-step - 12 (default=0)",
    required=False, 
    default=0 )
@click.option("--time-step-interval",
    type=click.INT,
    help="the interval (in hours) between forecast time steps to download. (Default=1)",
    required=False,
    default=1 )
@click.option("--timestamp",
    type=click.DateTime(),
    help="the time stamp of the dataset, e.g. '2020-06-26 18:00'. Uses latest available if no timestamp is specified.",
    required=False, 
    default=None )
@click.option("--directory",
    type=click.Path(writable=True,exists=True,file_okay=False,dir_okay=True),
    help="the download directory, defaults to working directory",
    required=False, 
    default=os.getcwd() )
# @click.option("--model-file",
#     type=click.Path(readable=True,exists=True,file_okay=True,dir_okay=False),
#     help="""the path to model definition file in json format: [{
#         "model": "icon",
#         "scope": "global",
#         "intervalHours": 6,
#         "grids": ["icosahedral"],
#         "pattern": {"single-level": "https://opendata.dwd.de/weather/nwp/{model!L}/grib/{modelrun:>02d}/{param!L}/{model!L}_{scope}_{grid}_{levtype}_{timestamp:%Y%m%d}{modelrun:>02d}_{step:>03d}_{param!U}.grib2.bz2" },
#         "openDataDeliveryOffsetMinutes": 240
#     }, ...]""",
#     required=False,
#     default=None)
def download(model:str, grid:str, single_level_fields:str, min_time_step:int, max_time_step:int, time_step_interval:int, timestamp:datetime, directory:str, model_file:str=None):
    if model_file is not None:
        print("loading model file from {}".format(model_file))
        loadAvailable(filename=model_file)
    if model is None:
        # pick any available model
        model = next(iter(available["models"]))
    if grid is None:
        # pick any available grid for model
        grid = available["models"][model]["grids"][0]
    if timestamp is None:
        timestamp = getMostRecentModelTimestamp(model)
    log.info("""
---------------
Model: {model}
Grid: {grid}
Fields: {param}
Minimum time step: {minTimeStep}
Maximum time step: {maxTimeStep}
Time step interval: {timeStepInterval}
Timestamp: {timestamp:%Y-%m-%d}
Model run: {modelrun:>02d}
Destination: {destFilePath}
---------------
""".format(
        model=model, 
        grid=grid, 
        param=single_level_fields, 
        minTimeStep=min_time_step, 
        maxTimeStep=max_time_step,
        timeStepInterval=time_step_interval,
        timestamp=timestamp,
        modelrun=timestamp.hour, 
        destFilePath=directory ))
    downloadGribDataSequence(
        model=model, 
        grid=grid, 
        param=single_level_fields, 
        minTimeStep=min_time_step, 
        maxTimeStep=max_time_step,
        timeStepInterval=time_step_interval,
        timestamp=timestamp, 
        destFilePath=directory )

if __name__ == "__main__":
    download()
