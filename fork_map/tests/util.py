"""
Testing tools
"""

import os
import random
import sys
import tempfile
import unittest


class BaseTestCase(unittest.TestCase):
    def __init__(self, methodName="runTest"):
        super().__init__(methodName)
        self._tempdir = None
        self.seed = random.randrange(sys.maxsize)

    @property
    def self_destructing_directory(self):
        """Return a temporary directory that exists for the duration of the test and is automatically removed after teardown."""
        if not (self._tempdir and os.path.exists(self._tempdir.name)):
            self._tempdir = tempfile.TemporaryDirectory(
                prefix=f"{self._testMethodName}_"
            )
            self.addCleanup(self.cleanup_self_destructing_directory)
            self._tempdir.__enter__()
        return self._tempdir.name

    def cleanup_self_destructing_directory(self):
        # Only try to exit the temporaryDirectory context manager if the directory still exists
        if os.path.exists(self._tempdir.name):
            self._tempdir.__exit__(None, None, None)

    def _formatMessage(self, msg, standardMsg):
        msg = msg or ""
        return super()._formatMessage(
            msg=f"{msg} (seed: {self.seed})", standardMsg=standardMsg
        )
