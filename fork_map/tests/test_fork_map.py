import os
import pickle
import time
import typing as tp
from multiprocessing import Queue

import pytest

from fork_map import fork_map


def test_fork_map() -> None:
    def testf(x):
        # time.sleep(300)
        return x * 2

    result = fork_map.fork_map(testf, range(5), maxworkers=2)
    assert result == [x * 2 for x in range(5)]


def test_has_finished() -> None:
    q: Queue[int] = Queue()

    def wait(exit_q: Queue[int]) -> tp.NoReturn:
        exit_q.get()
        os._exit(0)

    pid = os.fork()
    if pid:
        # parent
        for _ in range(10):
            assert not fork_map._has_finished(pid)
            time.sleep(0.01)
        q.put(1)
        time.sleep(0.01)
        assert fork_map._has_finished(pid)
    else:
        # child
        wait(q)


def test_exceptions() -> None:
    def fail(x: int) -> int:
        if not x:
            raise ZeroDivisionError
        return x - 1

    with pytest.raises(ZeroDivisionError):
        fork_map.fork_map(fail, reversed(range(5)))


def test_unpicklable_return() -> None:
    # fork_map can't handle functions that return unpicklable objects. Raise a
    # descriptive exception
    def f(x: tp.Any) -> tp.Any:
        return lambda: None

    # The exception type pickle raises here varies by Python version
    with pytest.raises((AttributeError, pickle.PicklingError)) as e:
        fork_map.fork_map(f, [1, 2])
    assert "test_unpicklable_return.<locals>.f.<locals>.<lambda>" in e.value.args[0]


def test_unpicklable_exception() -> None:
    # Don't let child processes crash, even if they do weird things like raise
    # unpickleable exceptions
    def f(x: tp.Any) -> None:
        class BadException(Exception):
            pass

        raise BadException()

    with pytest.raises(AttributeError) as e:
        fork_map.fork_map(f, [1, 2])
    msg = str(e.value)
    assert msg.startswith("<function test_unpicklable_exception.<locals>.f at")

    assert msg.endswith('raised unpicklable exception "BadException()"')
