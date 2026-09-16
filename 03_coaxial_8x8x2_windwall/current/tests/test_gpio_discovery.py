"""Verify GPIO selection without opening hardware or requesting output lines."""

from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from coaxial_windwall.hardware.interface import RealSync


class GPIODiscoveryTests(unittest.TestCase):
    def test_selects_header_chip_by_label_for_both_gpiod_apis(self):
        for api in (1, 2):
            with self.subTest(api=api):
                closed = []

                def chip(path):
                    label = "pinctrl-rp1" if path.endswith("15") else "other-chip"
                    methods = {"close": lambda: closed.append(path)}
                    if api == 1:
                        methods["label"] = lambda: label
                    else:
                        methods["get_info"] = lambda: SimpleNamespace(label=label)
                    return SimpleNamespace(**methods)

                paths = [Path("/dev/gpiochip11"), Path("/dev/gpiochip15")]
                with patch.object(Path, "glob", return_value=paths):
                    result = RealSync._find_chip_path(SimpleNamespace(Chip=chip), "pinctrl-rp1")
                self.assertEqual(result, "/dev/gpiochip15")
                self.assertEqual(closed, [str(path) for path in paths])

    def test_missing_header_chip_fails_without_selecting_another_chip(self):
        chip = SimpleNamespace(label=lambda: "other-chip", close=Mock())
        with patch.object(Path, "glob", return_value=[Path("/dev/gpiochip11")]):
            with self.assertRaisesRegex(FileNotFoundError, "pinctrl-rp1"):
                RealSync._find_chip_path(SimpleNamespace(Chip=lambda _: chip), "pinctrl-rp1")
        chip.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
