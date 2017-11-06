import time
from multiprocessing import Queue
import os

from fork_map.tests import util
from fork_map import fork_map


class TestForkMap(util.BaseTestCase):

    def test_fork_map(self):
        def testf(x):
            time.sleep(300)
            return x * 2


        result = fork_map.fork_map(testf, range(5), maxworkers=2)
        self.fail()

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
                time.sleep(0.1)
            q.put(1)
            time.sleep(0.1)
            self.assertTrue(fork_map._has_finished(pid))
        else:
            #child
            wait(q)
