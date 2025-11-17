FROM python:3.13-slim

WORKDIR /tmp

COPY ./src/requirements.txt .
RUN apt-get update && apt-get  install gcc git libsecp256k1-dev libpq-dev automake libtool make -y
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /tmp/requirements.txt

