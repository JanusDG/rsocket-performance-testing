from locust import User
from locust.exception import LocustError


class RsocketUser(User):
    abstract = True

    def __init__(self, environment):
        super().__init__(environment)
        host = "http://127.0.0.1:6565/"