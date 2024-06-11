import os
import time
from multiprocessing import Queue

from fork_map import fork_map
from fork_map.tests import util


class TestForkMap(util.BaseTestCase):

    def test_fork_map(self):
        def testf(x):
            #time.sleep(300)
            return x * 2

        result = fork_map.fork_map(testf, range(5), maxworkers=2)
        self.assertListEqual(result, [x * 2 for x in range(5)])

    def test_has_finished(self):
        q = Queue()
        def wait(exit_q):
            exit_q.get()
            os._exit(0)

        pid = os.fork()
        if pid:
            #parent
            for i in range(10):
                self.assertFalse(fork_map._has_finished(pid))
                time.sleep(0.01)
            q.put(1)
            time.sleep(0.01)
            self.assertTrue(fork_map._has_finished(pid))
        else:
            #child
            wait(q)

    def test_exceptions(self):
        def fail(x):
            if not x:
                1 / 0
            return x - 1

        with self.assertRaises(ZeroDivisionError) as e:
            fork_map.fork_map(fail, reversed(range(5)))

    def test_unpicklable_return(self):
        # fork_map can't handle functions that return unpicklable objects. Raise a descriptive
        # exception
        def f(x):
            return lambda:None
        with self.assertRaises(AttributeError) as e:
            fork_map.fork_map(f, [1, 2])
        self.assertEqual(str(e.exception),
                "Can't pickle local object "
                "'TestForkMap.test_unpicklable_return.<locals>.f.<locals>.<lambda>'")

    def test_unpicklable_exception(self):
        # Don't let child processes crash, even if they do weird things like raise unpickleable
        # exceptions
        def f(x):
            class BadException(Exception):
                pass
            raise BadException()

        with self.assertRaises(AttributeError) as e:
            fork_map.fork_map(f, [1, 2])
        msg = str(e.exception)
        self.assertTrue(msg.startswith('<function TestForkMap.test_unpicklable_exception.<locals>.f at'))
        self.assertTrue(msg.endswith('raised unpicklable exception "BadException()"'))
