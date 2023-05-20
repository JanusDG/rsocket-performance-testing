import random
import time
import math
import json
import string

def work_sleep(message):
    """
    min_time, max_time - seconds
    """
    min_time = 1
    max_time = int(message)
    diff = 1000
    time.sleep(random.randint(min_time*diff,max_time*diff)/diff)

def generate_random_data(message):
    num_chars = message // 4

    data = {}
    for _ in range(num_chars // 10):
        key = ''.join(random.choices(string.ascii_letters, k=5))
        value = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
        data[key] = value

    return data

def work_json(message):
    data = generate_random_data(int(message))
    json_data = json.dumps(data)
    data = json.loads(json_data)
    return data

def work_factorization(message):
    number = int(message)
    def x (num):
        if num == 1:
            return num
        return num*x(num-1)
    return x(number)
