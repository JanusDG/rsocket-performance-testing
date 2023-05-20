-include .env
WORKERS_DEFAULT = 3
SERVERS_DEFAULT = 3

ifdef NUM_WORKERS
	WORKERS_DEFAULT = $(NUM_WORKERS)
endif

ifdef NUM_SERVERS
	SERVERS_DEFAULT = $(NUM_SERVERS)
endif

lb-up:
	docker-compose -f docker-compose-lb.yaml up

lb-build:
	docker-compose -f docker-compose-lb.yaml build

lb-all: lb-build lb-up



locust-up:
	docker-compose -f docker-compose-locust.yaml up --scale worker=$(WORKERS_DEFAULT)

locust-build:
	docker-compose -f docker-compose-locust.yaml build

locust-all: locust-build locust-up

dhub-tag-lb:
	docker tag lb dbilusyak/rsocket-performance-test:lb
dhub-push-lb:
	docker push dbilusyak/rsocket-performance-test:lb
dhub-tag-locust:
	docker tag locust dbilusyak/rsocket-performance-test:locust
dhub-push-locust:
	docker push dbilusyak/rsocket-performance-test:locust

dhub-all-lb: dhub-tag-lb dhub-push-lb
dhub-all-locust: dhub-tag-locust dhub-push-locust
dhub-all: dhub-all-lb dhub-all-locust