WORKERS_DEFAULT = 3

lb-up:
	sudo docker-compose -f docker-compose-lb.yaml up

lb-build:
	sudo docker-compose -f docker-compose-lb.yaml build

lb-all: lb-build lb-up

ifdef WORKERS
	WORKERS_DEFAULT = $(WORKERS)
endif

locust-up:
	sudo docker-compose -f docker-compose-locust.yaml up --scale worker=$(WORKERS_DEFAULT)

locust-build:
	sudo docker-compose -f docker-compose-lb.yaml build

locust-all: locust-build locust-up