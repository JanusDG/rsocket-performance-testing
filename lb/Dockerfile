# syntax=docker/dockerfile:1

FROM python:3.8.10-slim-buster as lb

WORKDIR /build

COPY lb/requirements.txt requirements.txt
RUN python3 -m pip install --upgrade pip

RUN pip3 install -r requirements.txt


COPY . .
EXPOSE 6565