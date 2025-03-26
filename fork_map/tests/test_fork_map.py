import os
import time
from multiprocessing import Queue

import pytest

from fork_map import fork_map


def test_fork_map():
    def testf(x):
        # time.sleep(300)
        return x * 2

    result = fork_map.fork_map(testf, range(5), maxworkers=2)
    assert result == [x * 2 for x in range(5)]


def test_has_finished():
    q = Queue()

    def wait(exit_q):
        exit_q.get()
        os._exit(0)

    pid = os.fork()
    if pid:
        # parent
        for i in range(10):
            assert not fork_map._has_finished(pid)
            time.sleep(0.01)
        q.put(1)
        time.sleep(0.01)
        assert fork_map._has_finished(pid)
    else:
        # child
        wait(q)


def test_exceptions():
    def fail(x):
        if not x:
            1 / 0
        return x - 1

    with pytest.raises(ZeroDivisionError):
        fork_map.fork_map(fail, reversed(range(5)))


def test_unpicklable_return():
    # fork_map can't handle functions that return unpicklable objects. Raise a descriptive
    # exception
    def f(x):
        return lambda: None

    with pytest.raises(AttributeError) as e:
        fork_map.fork_map(f, [1, 2])
    assert "test_unpicklable_return.<locals>.f.<locals>.<lambda>" in e.value.args[0]


def test_unpicklable_exception():
    # Don't let child processes crash, even if they do weird things like raise unpickleable
    # exceptions
    def f(x):
        class BadException(Exception):
            pass

        raise BadException()

    with pytest.raises(AttributeError) as e:
        fork_map.fork_map(f, [1, 2])
    msg = str(e.value)
    assert msg.startswith("<function test_unpicklable_exception.<locals>.f at")

    assert msg.endswith('raised unpicklable exception "BadException()"')
