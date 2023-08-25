from dessia_common.forms import MovingStandaloneObject
import unittest
from parameterized import parameterized


class TestMovindObject(unittest.TestCase):
    def setUp(self) -> None:
        self.mso = MovingStandaloneObject(origin=0, name="Moving Test")
        self.displays = self.mso._displays()

    def test_viability(self):
        self.mso._check_platform()

    def test_length(self):
        self.assertEqual(len(self.displays), 2)

    @parameterized.expand([
        (0, "markdown"),
        (1, "babylon_data"),
    ])
    def test_decorators(self, index, expected_type):
        display = self.displays[index]
        self.assertEqual(display[index]["type"], expected_type)
