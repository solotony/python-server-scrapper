import unittest
from demo import Converter

class TestMyTest(unittest.TestCase):

    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        pass

    def test_001_all_ok(self):
        self.assertTrue(True)

    def test_002_fetch(self):
        Converter.fetch_rate()
        self.assertTrue(Converter.get_rate() is not None)
        self.assertTrue(Converter.get_rate() > 0)

    def test_003_convert(self):
        Converter.fetch_rate()
        x = 1
        y = Converter.convert(x)
        self.assertTrue(x is not None)
        self.assertTrue(x > 0)

