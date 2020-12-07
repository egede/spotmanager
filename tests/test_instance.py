import unittest

from instance import instance

class FroniusTestCase(unittest.TestCase):

    def test_start():
        i = instance()
        i.start()

    def test_stop():
        i = instance()
        i.stop()

