#!/usr/bin/env python

import io
import os

import setuptools

# get __version__ from version.py
exec(open('./downloader/version.py').read()) 

def read(fname):
    file_path = os.path.join(os.path.dirname(__file__), fname)
    return io.open(file_path, encoding='utf-8').read()

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='downloader',
    version=__version__,
    description="Downloads NWP model data in GRIB2 format from DWD's Open Data file server https://opendata.dwd.de using HTTPS.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Deutscher Wetterdienst (DWD)',
    author_email='opendata@dwd.de',
    license='Apache License Version 2.0',
    url='https://github.com/deutscherwetterdienst/opendata-downloader',
    packages=setuptools.find_packages(),
    #package_data={'downloader.models': ['downloader/models/*.json']},
    include_package_data=True,
    install_requires=[
        'click==7.1.2',
    ],
    entry_points={
        'console_scripts': [
            'downloader = downloader.downloader_cli:download'
        ],
    },
    zip_safe=True,
    keywords='deutscher wetterdienst DWD GRIB2 meteorology open data',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Operating System :: OS Independent',
    ],
)
