from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

import coaxial_windwall.gui.app as app_module
from config import PWM_IDLE
from coaxial_windwall.gui.app import ASSIGN_FRONT, CoaxialWindwallWindow
from coaxial_windwall.model import CoaxialAddress
from coaxial_windwall.protocol import decode_pwm_us_frame


class GermanDerivedGuiWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_presets_path = app_module.GUI_PRESETS_PATH
        app_module.GUI_PRESETS_PATH = Path(self.temp_dir.name) / "session.json"
        self.window = CoaxialWindwallWindow()

    def tearDown(self) -> None:
        self.window.close()
        app_module.GUI_PRESETS_PATH = self.original_presets_path
        self.temp_dir.cleanup()

    def test_pair_assignment_uses_front_and_back_host_indices(self) -> None:
        self.window.assign_pixel(0, 0)
        self.assertEqual(self.window.motor_owner[0], 0)
        self.assertEqual(self.window.motor_owner[64], 0)
        self.assertEqual(self.window.groups[0].motors, {0, 64})

        self.window.assign_pixel(0, 0)
        self.assertIsNone(self.window.motor_owner[0])
        self.assertIsNone(self.window.motor_owner[64])

    def test_front_only_assignment_does_not_change_back(self) -> None:
        self.window.assignment_scope.setCurrentText(ASSIGN_FRONT)
        self.window.assign_pixel(0, 0)
        self.assertEqual(self.window.motor_owner[0], 0)
        self.assertIsNone(self.window.motor_owner[64])

    def test_arm_start_and_emergency_stop_protocol_flags(self) -> None:
        self.assertFalse(self.window.start_button.isEnabled())
        self.window.assign_pixel(0, 0)
        self.window.arm()
        armed_idle = decode_pwm_us_frame(self.window.hardware.last_protocol_frame)
        self.assertTrue(armed_idle.output_armed)
        self.assertTrue(self.window.start_button.isEnabled())

        self.window.start_experiment()
        self.assertTrue(self.window.experiment_running)
        running = decode_pwm_us_frame(self.window.hardware.last_protocol_frame)
        self.assertTrue(running.output_armed)
        self.assertGreater(running.pwm_us[0], PWM_IDLE)
        self.assertGreater(running.pwm_us[64], PWM_IDLE)

        self.window.emergency_stop()
        stopped = decode_pwm_us_frame(self.window.hardware.last_protocol_frame)
        self.assertFalse(stopped.output_armed)
        self.assertFalse(self.window.is_armed)
        self.assertTrue(all(value == PWM_IDLE for value in stopped.pwm_us))

    def test_selected_pair_uses_frozen_controller_map(self) -> None:
        front = CoaxialAddress(0, 0, 0)
        back = CoaxialAddress(0, 0, 1)
        self.assertEqual((front.controller_label, front.controller_channel_label), ("C01", "CH1"))
        self.assertEqual((back.controller_label, back.controller_channel_label), ("C01", "CH2"))


if __name__ == "__main__":
    unittest.main()
