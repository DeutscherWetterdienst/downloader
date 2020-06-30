ARG PYTHON_VERSION=3.7
FROM python:${PYTHON_VERSION}-alpine as build

# copy the script
COPY . /src/

RUN set -ex \
    && cd /src \
    && pip install .

# display help
CMD downloader --help

# METADATA
# Build-time metadata as defined at http://label-schema.org
# --build-arg BUILD_DATE=`date -u +"%Y-%m-%dT%H:%M:%SZ"`
ARG BUILD_DATE
# --build-arg VCS_REF=`git rev-parse --short HEAD`, e.g. 'c30d602'
ARG VCS_REF
# --build-arg VCS_URL=`git config --get remote.origin.url`, e.g. 'https://github.com/deutscherwetterdienst/python-eccodes'
ARG VCS_URL
# --build-arg VERSION=`git tag`, e.g. '0.2.1'
ARG VERSION
LABEL org.label-schema.build-date=$BUILD_DATE \
        org.label-schema.name="DWD Downloader" \
        org.label-schema.description="A simple python module and command line tool to download NWP GRIB2 data from DWD's Open Data File Server https://opendata.dwd.de." \
        org.label-schema.url="https://www.dwd.de/opendatahelp" \
        org.label-schema.vcs-ref=$VCS_REF \
        org.label-schema.vcs-url=$VCS_URL \
        org.label-schema.vendor="DWD - Deutscher Wetterdienst" \
        org.label-schema.version=$VERSION \
        org.label-schema.schema-version="1.0"