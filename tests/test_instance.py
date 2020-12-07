import unittest

from spotmanager.instance import Instance

class InstanceTestCase(unittest.TestCase):

    def test_start(self):
        i = Instance()
        i.start()

    def test_stop(self):
        i = Instance()
        i.stop()

