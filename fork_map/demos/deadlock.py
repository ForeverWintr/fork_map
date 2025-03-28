"""The below code causes a deadlock on python <3.14"""

import os
import time
from concurrent.futures import ProcessPoolExecutor
import threading

lock = threading.Lock()


def process_items(name):
    print(f"{name}: acquiring lock")
    with lock:
        print(f"{name}: has lock")
        time.sleep(0.1)
    print(f"{name}: released lock")


t = threading.Thread(target=process_items, args=("Thread",))
t.start()

with ProcessPoolExecutor() as e:
    e.submit(process_items, "Process")
