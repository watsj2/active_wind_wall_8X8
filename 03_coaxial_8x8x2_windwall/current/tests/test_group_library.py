from __future__ import annotations

import unittest

from coaxial_windwall.gui.group_library import template_motors, template_pixels
from coaxial_windwall.model import controller_host_indices


class PremadeMappingTests(unittest.TestCase):
    def test_halves_partition_both_layers_by_physical_pair(self):
        left = template_motors("left", (0, 1))
        right = template_motors("right", (0, 1))
        self.assertEqual(left, set(range(32)) | set(range(64, 96)))
        self.assertEqual(right, set(range(32, 64)) | set(range(96, 128)))
        self.assertFalse(left & right)
        self.assertEqual(left | right, template_motors("whole", (0, 1)))

    def test_all_pico_templates_match_firmware_channel_tables(self):
        all_motors = set()
        for number in range(1, 17):
            motors = template_motors(f"pico:{number}", (0, 1))
            self.assertEqual(motors, set(controller_host_indices(number - 1)))
            self.assertFalse(all_motors & motors)
            all_motors |= motors
            self.assertEqual(len(template_pixels(f"pico:{number}")), 4)
        self.assertEqual(all_motors, set(range(128)))

    def test_square_positions_and_planes(self):
        for size in range(2, 8):
            for row in range(9 - size):
                for col in range(9 - size):
                    pixels = template_pixels(f"square:{size}", row, col)
                    self.assertEqual(len(pixels), size * size)
                    self.assertEqual(pixels[0], (row, col))
                    self.assertEqual(pixels[-1], (row + size - 1, col + size - 1))
                    front = template_motors(f"square:{size}", (0,), row, col)
                    back = template_motors(f"square:{size}", (1,), row, col)
                    self.assertEqual(back, {motor + 64 for motor in front})
        with self.assertRaises(ValueError):
            template_pixels("square:3", 6, 0)

