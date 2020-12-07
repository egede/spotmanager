import unittest

from instance import Instance

class InstanceTestCase(unittest.TestCase):

    def test_start(self):
        i = instance()
        i.start()

    def test_stop(self):
        i = instance()
        i.stop()

