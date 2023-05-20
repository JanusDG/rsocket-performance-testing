# syntax=docker/dockerfile:1

FROM python:3.8.10-slim-buster as server
# FROM ubuntu:20.04 as server

WORKDIR /build

COPY lb/servers/requirements.txt requirements.txt

RUN apt-get update
# RUN apt-get install -y python3.8
# RUN apt-get install -y net-tools
# RUN apt-get install -y dnsutils
# RUN apt-get install -y pip
RUN python3 -m pip install --upgrade pip

RUN pip3 install -r requirements.txt


COPY . .
EXPOSE 6566