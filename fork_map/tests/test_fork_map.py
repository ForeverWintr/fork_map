
from fork_map.tests import util
from fork_map.fork_map import fork_map


class TestForkMap(util.BaseTestCase):

    def test_fork_map(self):
        def testf(x):
            return x * 2

        args = [(n,) for n in range(5)]

        result = fork_map(testf, args, nworkers=2)
        self.fail()
