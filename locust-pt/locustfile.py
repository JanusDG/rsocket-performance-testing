import logging
import gevent
import gevent.monkey
import asyncio

from locust import events, task, between,  run_single_user
from rsocket.frame_helpers import safe_len

from rsocket_user import RsocketUser

gevent.monkey.patch_all()
from rsocket.load_balancer.load_balancer_rsocket import LoadBalancerRSocket

from rsocket_user import ConnectionServerWrapper
def asyncio_if_event_loop(call, *args):
    try:
        loop = asyncio.get_event_loop()
        future_response = asyncio.run_coroutine_threadsafe(call(*args), loop)

        logging.info(f"---{call.__name__}--- is running in event loop")

    except RuntimeError:
        future_response = asyncio.run(call(*args))
        logging.info(f"---{call.__name__}--- not running in event loop")
    return future_response


class ResponseRsocketUser(RsocketUser):
    wait_time = between(1,5)
    def __init__(self, environment):
        super().__init__(environment)
    @task
    def getResponse(self):
        logging.info("RequestResponse task started")
        call = self.request_response
        future_response = asyncio_if_event_loop(call, 6565)

        # locust does not support async tasks
        try:
            while not future_response.done():
                gevent.sleep(0.1)
            response_time=future_response.result()[1]
            response_length=safe_len(future_response.result()[0].data)
        except AttributeError:
            response_time=future_response[1]
            response_length=safe_len(future_response[0].data)
            
        # call event hook that sends data to locust 
        self.environment.events.request.fire(
            request_type="tcp",
            name="name",
            response_time=response_time,
            response_length=response_length,
        ) 

if __name__ == "__main__":
    # run_rsocket_server()
    run_single_user(ResponseRsocketUser)