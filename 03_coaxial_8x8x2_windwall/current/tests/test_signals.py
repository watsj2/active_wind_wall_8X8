from __future__ import annotations

import unittest

from config import NUM_MOTORS, PWM_IDLE
from coaxial_windwall.control.signals import (
    SIGNAL_CONSTANT,
    SIGNAL_SQUARE,
    GroupSignal,
    SignalGroup,
    build_group_frame,
    fraction_to_pwm,
    signal_fraction,
)
from coaxial_windwall.model import CoaxialAddress, address_from_motor_index, controller_host_indices


class SignalGenerationTests(unittest.TestCase):
    def test_sine_uses_configured_minimum_and_maximum(self) -> None:
        signal = GroupSignal(minimum=0.2, maximum=0.8, period_s=4.0)
        self.assertAlmostEqual(signal_fraction(signal, 0.0), 0.5)
        self.assertAlmostEqual(signal_fraction(signal, 1.0), 0.8)
        self.assertAlmostEqual(signal_fraction(signal, 3.0), 0.2)

    def test_square_respects_duty_cycle(self) -> None:
        signal = GroupSignal(
            signal_type=SIGNAL_SQUARE,
            minimum=0.1,
            maximum=0.9,
            period_s=2.0,
            duty_cycle=0.25,
        )
        self.assertEqual(signal_fraction(signal, 0.1), 0.9)
        self.assertEqual(signal_fraction(signal, 0.75), 0.1)

    def test_group_frame_keeps_layer_first_motor_indices(self) -> None:
        group = SignalGroup(
            "Pair 1",
            "#ffffff",
            motors={0, 64},
            signal=GroupSignal(signal_type=SIGNAL_CONSTANT, constant=0.5),
        )
        frame = build_group_frame([group], 0.0, output_max=1800)
        self.assertEqual(len(frame), NUM_MOTORS)
        self.assertEqual(frame[0], 1400)
        self.assertEqual(frame[64], 1400)
        self.assertTrue(all(value == PWM_IDLE for value in frame[1:64]))
        self.assertTrue(all(value == PWM_IDLE for value in frame[65:]))

    def test_zero_fraction_is_idle(self) -> None:
        self.assertEqual(fraction_to_pwm(0.0, 1800), PWM_IDLE)

    def test_excel_grid_and_inverse_address_lookup(self) -> None:
        expected_top_row = (1, 2, 3, 4, 33, 34, 35, 36)
        self.assertEqual(
            tuple(CoaxialAddress(0, col, 0).pixel_number for col in range(8)),
            expected_top_row,
        )
        address = address_from_motor_index(32)
        self.assertEqual((address.row, address.col, address.label), (0, 4, "F33"))

    def test_controller_positions_stay_fixed_with_new_host_indices(self) -> None:
        self.assertEqual(
            controller_host_indices(0),
            (0, 64, 3, 67, 4, 68, 7, 71),
        )
        self.assertEqual(
            controller_host_indices(4),
            (32, 96, 35, 99, 36, 100, 39, 103),
        )


if __name__ == "__main__":
    unittest.main()
