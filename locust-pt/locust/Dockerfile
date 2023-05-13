# syntax=docker/dockerfile:1

FROM locustio/locust as locust


WORKDIR /build

COPY locust/requirements.txt requirements.txt
RUN python3 -m pip install --upgrade pip

RUN pip3 install -r requirements.txt


COPY . .
# EXPOSE 6565

# CMD ["./start_lb.sh"]