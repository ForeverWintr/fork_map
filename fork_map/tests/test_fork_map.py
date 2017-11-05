
from fork_map.tests import util
from fork_map.fork_map import fork_map


class TestForkMap(util.BaseTestCase):

    def test_fork_map(self):
        def testf(x):
            return x * 2


        result = fork_map(testf, range(5), nworkers=2)
        self.fail()
