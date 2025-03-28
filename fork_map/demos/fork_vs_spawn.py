"""The below fails unless start method is fork"""

import os
import multiprocessing
from concurrent.futures import ProcessPoolExecutor


def get_letter(idx: int) -> str:
    pid = os.getpid()
    return f"{pid=} got letter {LETTERS[idx]}"


if __name__ == "__main__":
    multiprocessing.set_start_method("spawn")
    LETTERS = "abcde"

    with ProcessPoolExecutor() as e:
        for r in e.map(get_letter, [0, 1, 3]):
            print(r)
