import random
import time


def fetch(url, retries=3):
    for attempt in range(retries):
        if random.random() > 0.3:
            return "ok"
        time.sleep(0.01 * attempt)
    raise TimeoutError(url)
