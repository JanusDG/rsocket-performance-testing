import random
import time
import math
import json
import string

def work_sleep(work_size:int, variation_scale:int):
    """
    min_time, max_time - seconds
    """
    work_size = random.randint(work_size*(1 - variation_scale/100),
                               work_size*(1 + variation_scale/100))
    min_time = 1
    max_time = int(work_size)
    diff = 1000
    time.sleep(random.randint(min_time*diff,max_time*diff)/diff)

def generate_random_data(work_size:int):
    num_chars = work_size // 4

    data = {}
    for _ in range(num_chars // 10):
        key = ''.join(random.choices(string.ascii_letters, k=5))
        value = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
        data[key] = value

    return data

def work_json(work_size:int, variation_scale:int):
    work_size = random.randint(work_size*(1 - variation_scale/100),
                               work_size*(1 + variation_scale/100))
    data = generate_random_data(int(work_size))
    json_data = json.dumps(data)
    data = json.loads(json_data)
    return data

def work_factorization(work_size:int, variation_scale:int):
    work_size = random.randint(work_size*(1 - variation_scale/100),
                               work_size*(1 + variation_scale/100))
    number = int(work_size)
    def x (num):
        if num == 1:
            return num
        return num*x(num-1)
    return x(number)
