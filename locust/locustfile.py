import logging
import gevent
import gevent.monkey
import asyncio

from locust import events, task, between,  run_single_user
from rsocket.frame_helpers import safe_len

from rsocket_user import RsocketUser

gevent.monkey.patch_all()
from rsocket.load_balancer.load_balancer_rsocket import LoadBalancerRSocket
from gevent.pool import Pool
from gevent.pool import Group
from rsocket_user import ConnectionServerWrapper
import asyncio
import os
# from apscheduler.schedulers.asyncio import AsyncIOScheduler
def asyncio_if_event_loop(call, *args):
    try:
        try:
            loop = asyncio.get_event_loop()
            future_response = asyncio.run_coroutine_threadsafe(call(*args), loop)
            if future_response is None:
                return None
        except asyncio.exceptions.InvalidStateError:
            return None

    except RuntimeError:
        try:
            future_response = asyncio.run(call(*args))
            if future_response is None:
                return None
        except asyncio.exceptions.InvalidStateError:
            return None
        
    return future_response


class ResponseRsocketUser(RsocketUser):
    wait_time = between(1,5)
    def __init__(self, environment):
        super().__init__(environment)
        logging.basicConfig(level=logging.INFO)

    def fire(self,time, length, error=None):
        # call event hook that sends data to locust 
        self.environment.events.request.fire(
            request_type="tcp",
            name="name",
            response_time=time,
            response_length=length,
            exception=error
        ) 
    @task
    def getResponse(self):
        # def x():
        call = self.request_response
        lb_address=os.environ["LB_ADDRESS"]
        future_response = asyncio_if_event_loop(call,lb_address, 6565)
        if future_response is None:
            logging.info("Request failed")
            self.fire(0, 0, NotImplementedError)
            return
        try:
            try:
                # locust does not support async tasks
                while not future_response.done():
                    gevent.sleep(0.01)
                response_time=future_response.result()[1]
                response_length=safe_len(future_response.result()[0].data)
            except AttributeError:
                response_time=future_response[1]
                response_length=safe_len(future_response[0].data)
        except:
            logging.info("Request failed")
            self.fire(0, 0, NotImplementedError)
            return
        self.fire(response_time, response_length)


if __name__ == "__main__":
    run_single_user(ResponseRsocketUser)