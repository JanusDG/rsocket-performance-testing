import logging
import gevent
import gevent.monkey
import asyncio

from locust import events, task, between
from rsocket.frame_helpers import safe_len

from chat_server import run_server
from rsocket_user import RsocketUser

gevent.monkey.patch_all()


# let locust run the server 
@events.init.add_listener
def run_rsocket_server(environment, **_kwargs):
    def async_run_server():
        asyncio.run(run_server()) 
    gevent.spawn(async_run_server)
    logging.info(f"server started")


class ResponseRsocketUser(RsocketUser):
    wait_time = between(1,5)

    @task
    def getResponse(self):
        logging.info("getResponse task started")
        loop =  asyncio.get_event_loop()
        future_response = asyncio.run_coroutine_threadsafe(self.request_response(), loop)

        # locust does not support async tasks
        while not future_response.done():
            gevent.sleep(0.1)
        
        response_time=future_response.result()[1]
        response_length=safe_len(future_response.result()[0].data)
        
        # call event hook that sends data to locust 
        self.environment.events.request.fire(
            request_type="tcp",
            name="name",
            response_time=response_time,
            response_length=response_length,
        ) 
