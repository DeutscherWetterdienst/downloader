FROM python:3.7-alpine as build

# copy the script
COPY . /src/

RUN set -ex \
    && cd /src \
    && pip install .

# display help
CMD downloader --help