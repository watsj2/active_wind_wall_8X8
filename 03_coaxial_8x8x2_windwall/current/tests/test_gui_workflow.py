from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QLabel

import coaxial_windwall.gui.app as app_module
from config import GUI_REFRESH_HZ, PWM_IDLE, PWM_MAX
from coaxial_windwall.control.signals import SIGNAL_CONSTANT
from coaxial_windwall.gui.app import (
    ASSIGN_BACK,
    ASSIGN_BOTH,
    ASSIGN_FRONT,
    MONITOR_DOWNSTREAM,
    MONITOR_UPSTREAM,
    CoaxialWindwallWindow,
)
from coaxial_windwall.hardware.interface import HardwareInterface
from coaxial_windwall.model import CoaxialAddress
from coaxial_windwall.protocol import decode_pwm_us_frame


class NoOutputSPI:
    def write_frame(self, frame: bytes) -> None:
        pass

    def close(self) -> None:
        pass


class NoOutputSync:
    def pulse(self) -> None:
        pass

    def close(self) -> None:
        pass


class GermanDerivedGuiWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_presets_path = app_module.GUI_PRESETS_PATH
        app_module.GUI_PRESETS_PATH = Path(self.temp_dir.name) / "session.json"
        hardware = HardwareInterface(spi=NoOutputSPI(), sync=NoOutputSync())
        self.window = CoaxialWindwallWindow(hardware=hardware)

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
        self.window.assign_pixel(0, 0, ASSIGN_FRONT)
        self.assertEqual(self.window.motor_owner[0], 0)
        self.assertIsNone(self.window.motor_owner[64])

    def test_cell_zones_directly_select_upstream_pair_or_downstream(self) -> None:
        cell = self.window.cells[(0, 0)]
        cell.resize(72, 72)

        QTest.mouseClick(
            cell,
            Qt.MouseButton.LeftButton,
            pos=QPoint(cell.width() // 2, 5),
        )
        self.assertEqual(self.window.motor_owner[0], 0)
        self.assertIsNone(self.window.motor_owner[64])

        QTest.mouseClick(
            cell,
            Qt.MouseButton.LeftButton,
            pos=QPoint(cell.width() // 2, cell.height() // 2),
        )
        self.assertEqual(self.window.motor_owner[0], 0)
        self.assertEqual(self.window.motor_owner[64], 0)

        QTest.mouseClick(
            cell,
            Qt.MouseButton.LeftButton,
            pos=QPoint(cell.width() // 2, cell.height() - 5),
        )
        self.assertEqual(self.window.motor_owner[0], 0)
        self.assertIsNone(self.window.motor_owner[64])

    def test_arm_start_and_emergency_stop_protocol_flags(self) -> None:
        self.assertFalse(self.window.start_button.isEnabled())
        self.window.assign_pixel(0, 0)
        self.window.arm()
        armed_idle = decode_pwm_us_frame(self.window.hardware.last_protocol_frame)
        self.assertTrue(armed_idle.output_armed)
        self.assertTrue(self.window.start_button.isEnabled())
        self.assertEqual(self.window.arm_button.parentWidget().objectName(), "TopBar")
        self.assertEqual(self.window.arm_button.property("state"), "armed")

        self.window.start_experiment()
        self.assertTrue(self.window.experiment_running)
        self.assertEqual(self.window.start_button.text(), "STOP EXPERIMENT")
        self.assertEqual(self.window.arm_button.property("state"), "running")
        running = decode_pwm_us_frame(self.window.hardware.last_protocol_frame)
        self.assertTrue(running.output_armed)
        self.assertGreater(running.pwm_us[0], PWM_IDLE)
        self.assertGreater(running.pwm_us[64], PWM_IDLE)

        self.window.emergency_stop()
        stopped = decode_pwm_us_frame(self.window.hardware.last_protocol_frame)
        self.assertFalse(stopped.output_armed)
        self.assertFalse(self.window.is_armed)
        self.assertTrue(all(value == PWM_IDLE for value in stopped.pwm_us))

    def test_top_bar_stacks_emergency_stop_above_arm(self) -> None:
        self.assertIs(
            self.window.safety_controls.itemAt(0).widget(),
            self.window.emergency_stop_button,
        )
        self.assertIs(
            self.window.safety_controls.itemAt(1).widget(),
            self.window.arm_button,
        )
        self.assertEqual(self.window.arm_button.property("state"), "safe")
        self.assertEqual(self.window.arm_button.text(), "ARM SYSTEM")

        self.window.arm()
        self.assertEqual(self.window.arm_button.text(), "DISARM SYSTEM")
        self.window.assign_pixel(0, 0)
        self.window.start_experiment()
        self.assertEqual(self.window.arm_button.text(), "SYSTEM RUNNING")

    def test_operator_uses_upstream_downstream_plane_terminology(self) -> None:
        self.assertFalse(hasattr(self.window, "assignment_scope"))
        cell = self.window.cells[(0, 0)]
        self.assertIn("box drag on UP for Upstream", cell.toolTip())
        self.assertIn("DN for Downstream", cell.toolTip())
        monitor_modes = [
            self.window.monitor_mode.itemText(index)
            for index in range(self.window.monitor_mode.count())
        ]
        self.assertIn(MONITOR_UPSTREAM, monitor_modes)
        self.assertIn(MONITOR_DOWNSTREAM, monitor_modes)
        self.assertIn("Upstream F01", self.window.selected_pair.text())
        self.assertIn("Downstream B01", self.window.selected_pair.text())

    def test_controller_filter_is_removed_from_motor_grid(self) -> None:
        self.assertFalse(hasattr(self.window, "controller_filter"))
        visible_text = " ".join(
            label.text() for label in self.window.findChildren(QLabel)
        )
        self.assertNotIn("All controllers", visible_text)

    def test_pico_grid_overlay_shows_fixed_controller_pattern(self) -> None:
        expected = {
            (0, 0): "C01",
            (0, 1): "C09",
            (0, 4): "C05",
            (4, 0): "C03",
            (4, 1): "C11",
            (7, 7): "C08",
        }
        self.assertFalse(self.window.show_pico_grid.isChecked())
        self.assertTrue(
            all(not cell.controller_overlay for cell in self.window.cells.values())
        )

        self.window.show_pico_grid.click()

        self.assertTrue(
            all(cell.controller_overlay for cell in self.window.cells.values())
        )
        for location, controller_label in expected.items():
            cell = self.window.cells[location]
            self.assertEqual(cell.controller_label, controller_label)
            self.assertIn(f"Pico {controller_label}", cell.toolTip())

        self.window.cells[(0, 1)].clicked.emit(0, 1, ASSIGN_FRONT)
        self.assertEqual(self.window.motor_owner[1], 0)
        self.assertIsNone(self.window.motor_owner[65])

        self.window.show_pico_grid.click()
        self.assertTrue(
            all(not cell.controller_overlay for cell in self.window.cells.values())
        )

    def test_grid_uses_prominent_left_right_physical_numbers(self) -> None:
        for row in range(8):
            for col in range(8):
                expected = row * 4 + col % 4 + 1 + (32 if col >= 4 else 0)
                cell = self.window.cells[(row, col)]
                self.assertEqual(cell.display_number, expected)
                self.assertEqual(cell.display_label, f"{expected:02d}")
                self.assertNotIn("P", cell.toolTip().split(" / ", 1)[0])
        self.assertGreaterEqual(self.window.cells[(0, 0)].DISPLAY_LABEL_POINT_SIZE, 12)

        self.window.resize(1480, 920)
        self.window.show()
        self.app.processEvents()
        for cell in self.window.cells.values():
            self.assertGreaterEqual(cell.width(), cell.MINIMUM_SIDE)
            self.assertGreaterEqual(cell.height(), cell.MINIMUM_SIDE)

        self.window.selected_row = 0
        self.window.selected_col = 4
        self.window.refresh_wall()
        self.assertTrue(self.window.selected_pair.text().startswith("33 / R1C5\n"))
        self.assertNotIn("P33", self.window.selected_pair.text())
        self.assertIn("Upstream F33", self.window.selected_pair.text())

    def test_large_experiment_button_toggles_start_and_stop(self) -> None:
        self.assertEqual(self.window.start_button.objectName(), "ExperimentToggle")
        self.assertGreaterEqual(self.window.start_button.minimumHeight(), 64)
        self.assertFalse(hasattr(self.window, "stop_button"))

        self.window.assign_pixel(0, 0)
        self.window.arm()
        self.window.start_button.click()
        self.assertTrue(self.window.experiment_running)
        self.assertEqual(self.window.start_button.text(), "STOP EXPERIMENT")

        self.window.start_button.click()
        self.assertFalse(self.window.experiment_running)
        self.assertEqual(self.window.start_button.text(), "START EXPERIMENT")
        self.assertTrue(all(value == PWM_IDLE for value in self.window.current_pwm))

    def test_rival_lab_branding_replaces_development_header(self) -> None:
        self.assertEqual(self.window.windowTitle(), "Windwall")
        self.assertEqual(self.window.brand_title.text(), "Windwall")
        self.assertIsNotNone(self.window.brand_logo.pixmap())
        self.assertFalse(self.window.brand_logo.pixmap().isNull())
        visible_text = " ".join(
            label.text() for label in self.window.findChildren(QLabel)
        ).lower()
        self.assertNotIn("coaxial 8x8x2 windwall", visible_text)
        self.assertNotIn("german 6x6", visible_text)

    def test_direct_constant_pwm_reaches_assigned_pair_exactly(self) -> None:
        self.window.signal_type.setCurrentText(SIGNAL_CONSTANT)
        self.window.constant_pwm.setValue(1150)
        self.window.assign_pixel(0, 0)
        self.window.arm()
        self.window.start_experiment()

        running = decode_pwm_us_frame(self.window.hardware.last_protocol_frame)
        self.assertEqual(running.pwm_us[0], 1150)
        self.assertEqual(running.pwm_us[64], 1150)
        self.assertTrue(all(value == PWM_IDLE for value in running.pwm_us[1:64]))
        self.assertTrue(all(value == PWM_IDLE for value in running.pwm_us[65:]))

    def test_full_output_range_is_always_available_after_start(self) -> None:
        self.assertFalse(hasattr(self.window, "output_range"))
        self.assertEqual(self.window.output_maximum(), PWM_MAX)
        self.window.signal_type.setCurrentText(SIGNAL_CONSTANT)
        self.window.constant_pwm.setValue(PWM_MAX)
        self.window.assign_pixel(0, 0)

        self.window.arm()
        armed_idle = decode_pwm_us_frame(self.window.hardware.last_protocol_frame)
        self.assertTrue(all(value == PWM_IDLE for value in armed_idle.pwm_us))

        self.window.start_experiment()
        running = decode_pwm_us_frame(self.window.hardware.last_protocol_frame)
        self.assertEqual(running.pwm_us[0], PWM_MAX)
        self.assertEqual(running.pwm_us[64], PWM_MAX)

    def test_selected_pair_uses_frozen_controller_map(self) -> None:
        front = CoaxialAddress(0, 0, 0)
        back = CoaxialAddress(0, 0, 1)
        self.assertEqual((front.controller_label, front.controller_channel_label), ("C01", "CH1"))
        self.assertEqual((back.controller_label, back.controller_channel_label), ("C01", "CH2"))

    def test_excel_numbering_is_used_by_grid_assignments(self) -> None:
        front = CoaxialAddress(0, 4, 0)
        back = CoaxialAddress(0, 4, 1)
        self.assertEqual((front.pair_label, front.motor_index), ("P33", 32))
        self.assertEqual((back.label, back.motor_index), ("B33", 96))
        self.assertEqual((front.controller_label, front.controller_channel_label), ("C05", "CH1"))

        self.window.assign_pixel(0, 4)
        self.assertEqual(self.window.motor_owner[32], 0)
        self.assertEqual(self.window.motor_owner[96], 0)

    def test_assign_all_keeps_explicit_plane_targets_without_dropdown(self) -> None:
        self.window.assign_all(ASSIGN_FRONT)
        self.assertTrue(all(owner == 0 for owner in self.window.motor_owner[:64]))
        self.assertTrue(all(owner is None for owner in self.window.motor_owner[64:]))

        self.window.clear_wall()
        self.window.assign_all(ASSIGN_BACK)
        self.assertTrue(all(owner is None for owner in self.window.motor_owner[:64]))
        self.assertTrue(all(owner == 0 for owner in self.window.motor_owner[64:]))

        self.window.clear_wall()
        self.window.assign_all(ASSIGN_BOTH)
        self.assertTrue(all(owner == 0 for owner in self.window.motor_owner))

    def test_rubber_band_assigns_every_pixel_inside_the_box(self) -> None:
        self.window.resize(1600, 1000)
        self.window.show()
        self.app.processEvents()
        grid = self.window.cell_grid
        first = self.window.cells[(0, 0)]
        last = self.window.cells[(1, 2)]
        end = last.mapTo(grid, last.rect().center())
        end_on_first = first.mapFrom(grid, end)

        QTest.mousePress(
            first,
            Qt.MouseButton.LeftButton,
            pos=first.rect().center(),
        )
        QTest.mouseMove(first, pos=end_on_first)
        self.assertTrue(grid.dragging)
        self.assertTrue(grid.rubber_band.isVisible())
        QTest.mouseRelease(
            first,
            Qt.MouseButton.LeftButton,
            pos=end_on_first,
        )

        expected_pixels = {
            (row, col)
            for row in range(2)
            for col in range(3)
        }
        expected_motors = {
            CoaxialAddress(row, col, layer).motor_index
            for row, col in expected_pixels
            for layer in range(2)
        }
        self.assertEqual(self.window.groups[0].motors, expected_motors)
        self.assertFalse(grid.rubber_band.isVisible())

    def test_rubber_band_uses_the_plane_where_the_drag_started(self) -> None:
        self.window.resize(1600, 1000)
        self.window.show()
        self.app.processEvents()
        grid = self.window.cell_grid
        first = self.window.cells[(2, 1)]
        last = self.window.cells[(3, 2)]
        start = first.mapTo(grid, QPoint(first.width() // 2, 5))
        end = last.mapTo(grid, last.rect().center())

        grid._begin_drag(start, first.assignment_scope_at(5))
        grid._update_drag(end)
        grid._finish_drag(end)

        expected_pixels = {
            (row, col)
            for row in range(2, 4)
            for col in range(1, 3)
        }
        expected_upstream = {
            CoaxialAddress(row, col, 0).motor_index
            for row, col in expected_pixels
        }
        self.assertEqual(self.window.groups[0].motors, expected_upstream)
        self.assertTrue(
            all(owner is None for owner in self.window.motor_owner[64:])
        )

    def test_mouse_drag_preserves_upstream_and_downstream_start_zones(self) -> None:
        self.window.resize(1600, 1000)
        self.window.show()
        self.app.processEvents()
        grid = self.window.cell_grid
        first = self.window.cells[(2, 1)]
        last = self.window.cells[(3, 2)]
        expected_pixels = {
            (row, col)
            for row in range(2, 4)
            for col in range(1, 3)
        }
        end = last.mapTo(grid, last.rect().center())
        end_on_first = first.mapFrom(grid, end)

        QTest.mousePress(
            first,
            Qt.MouseButton.LeftButton,
            pos=QPoint(first.width() // 2, 5),
        )
        QTest.mouseMove(first, pos=end_on_first)
        QTest.mouseRelease(
            first,
            Qt.MouseButton.LeftButton,
            pos=end_on_first,
        )
        expected_upstream = {
            CoaxialAddress(row, col, 0).motor_index
            for row, col in expected_pixels
        }
        self.assertEqual(self.window.groups[0].motors, expected_upstream)
        self.assertTrue(
            all(owner is None for owner in self.window.motor_owner[64:])
        )

        self.window.clear_wall()
        QTest.mousePress(
            first,
            Qt.MouseButton.LeftButton,
            pos=QPoint(first.width() // 2, first.height() - 5),
        )
        QTest.mouseMove(first, pos=end_on_first)
        QTest.mouseRelease(
            first,
            Qt.MouseButton.LeftButton,
            pos=end_on_first,
        )
        expected_downstream = {
            CoaxialAddress(row, col, 1).motor_index
            for row, col in expected_pixels
        }
        self.assertEqual(self.window.groups[0].motors, expected_downstream)
        self.assertTrue(
            all(owner is None for owner in self.window.motor_owner[:64])
        )

    def test_wall_repaint_is_throttled_to_the_gui_timer(self) -> None:
        self.assertEqual(
            self.window.ui_timer.interval(),
            max(1, int(1000 / GUI_REFRESH_HZ)),
        )
        self.window.experiment_running = True
        self.window.is_armed = True
        self.window.experiment_started_s = app_module.time.monotonic()
        refresh_wall = Mock(wraps=self.window.refresh_wall)
        self.window.refresh_wall = refresh_wall

        self.window.command_tick()
        self.assertEqual(refresh_wall.call_count, 0)

        self.window.refresh_runtime()
        self.assertEqual(refresh_wall.call_count, 1)

    def test_live_plot_is_compact_by_default_and_can_be_expanded(self) -> None:
        self.assertTrue(self.window.plot.isHidden())
        self.assertEqual(self.window.monitor_plot_button.text(), "Show plot")

        self.window.monitor_plot_button.click()
        self.assertFalse(self.window.plot.isHidden())
        self.assertEqual(self.window.monitor_plot_button.text(), "Hide plot")

    def test_premade_groups_move_only_selected_motors_and_start_at_idle(self) -> None:
        from coaxial_windwall.gui.group_library import template_motors
        self.window.assign_all()
        before_frames = self.window.hardware.frame_count
        right = template_motors("right", (0, 1))
        self.window.add_template_group("Right half", right)
        self.assertEqual(self.window.groups[1].motors, right)
        self.assertEqual(self.window.groups[0].motors, set(range(128)) - right)
        self.assertEqual(self.window.groups[1].signal.signal_type, SIGNAL_CONSTANT)
        self.assertEqual(self.window.groups[1].signal.constant_pwm_us, PWM_IDLE)
        self.assertEqual(self.window.hardware.frame_count, before_frames)
        self.assertEqual(self.window.selected_group_index, 1)

    def test_all_sixteen_pico_groups_survive_session_reload(self) -> None:
        from coaxial_windwall.gui.group_library import template_motors
        for number in range(1, 17):
            self.window.add_template_group(f"Pico {number:02d}", template_motors(f"pico:{number}", (0, 1)))
        data = self.window.session_data()
        self.assertTrue(self.window.apply_session_data(data))
        self.assertEqual(len(self.window.groups), 17)
        for number in range(1, 17):
            self.assertEqual(self.window.groups[number].motors, template_motors(f"pico:{number}", (0, 1)))

    def test_premade_group_is_blocked_during_experiment(self) -> None:
        before = self.window.session_data()
        self.window.experiment_running = True
        self.window.add_template_group("Whole wall", set(range(128)))
        self.assertEqual(self.window.session_data(), before)
        self.window.experiment_running = False

    def test_group_library_preview_tracks_position_layers_and_overlap(self) -> None:
        from coaxial_windwall.gui.group_library import GroupLibraryDialog
        self.window.assign_all()
        dialog = GroupLibraryDialog(self.window)
        dialog.template.setCurrentIndex(dialog.template.findData("square:3"))
        dialog.row.setValue(2)
        dialog.col.setValue(5)
        dialog.layers.setCurrentIndex(2)
        self.assertEqual(len(dialog.selected_motors()), 9)
        self.assertTrue(all(motor >= 64 for motor in dialog.selected_motors()))
        self.assertIn("9 motors will move", dialog.summary.text())
        self.assertIn("R2 C5", dialog.group_name())
        self.assertEqual(min(dialog.preview.pixels), (1, 4))
        dialog.reject()

    def test_redesigned_layout_fits_1366_by_900(self) -> None:
        self.window.resize(1366, 900)
        self.window.show()
        self.app.processEvents()
        self.assertEqual((self.window.width(), self.window.height()), (1366, 900))
        self.assertGreater(
            self.window.cells[(0, 4)].x() - self.window.cells[(0, 3)].geometry().right(),
            self.window.cells[(0, 3)].x() - self.window.cells[(0, 2)].geometry().right(),
        )

    def test_square_grid_uses_largest_fitting_cells_after_resize(self) -> None:
        for width, height in ((1600, 1000), (1920, 1080), (1366, 900)):
            self.window.resize(width, height)
            self.window.show()
            self.app.processEvents()
            grid = self.window.cell_grid
            first = self.window.cells[(0, 0)].geometry()
            last = self.window.cells[(7, 7)].geometry()
            for cell in self.window.cells.values():
                self.assertEqual(cell.width(), cell.height())
            horizontal_margin = grid.width() - (last.right() - first.left() + 1)
            vertical_margin = grid.height() - (last.bottom() - first.top() + 1)
            self.assertLessEqual(min(horizontal_margin, vertical_margin), 8)

    def test_first_paint_uses_final_grid_geometry_without_fixed_cell_sizes(self) -> None:
        from PyQt6.QtCore import QEvent, QObject
        from PyQt6.QtWidgets import QSizePolicy

        first_paints = {}

        class PaintRecorder(QObject):
            def eventFilter(self, watched, event):
                if event.type() == QEvent.Type.Paint:
                    first_paints.setdefault((watched.row, watched.col), watched.geometry())
                return False

        recorder = PaintRecorder(self.window)
        for cell in self.window.cells.values():
            cell.installEventFilter(recorder)
            self.assertEqual(cell.sizePolicy().horizontalPolicy(), QSizePolicy.Policy.Expanding)
            self.assertGreater(cell.maximumWidth(), 1920)
        self.window.resize(1600, 1000)
        self.window.show()
        self.app.processEvents()
        self.app.processEvents()
        self.assertEqual(len(first_paints), 64)
        for position, geometry in first_paints.items():
            self.assertEqual(geometry, self.window.cells[position].geometry())

    def test_side_shortcuts_assign_selected_group_without_toggling_or_changing_signal(self) -> None:
        frames = self.window.hardware.frame_count
        signal = self.window.groups[0].signal.to_dict()
        self.window.quick_buttons["right:Downstream"].click()
        self.window.quick_buttons["right:Downstream"].click()
        self.assertEqual(self.window.groups[0].motors, set(range(96, 128)))
        self.assertEqual(len(self.window.groups), 1)
        self.assertEqual(self.window.groups[0].signal.to_dict(), signal)
        self.assertEqual(self.window.hardware.frame_count, frames)
        self.window.experiment_running = True
        self.window.assign_quick_shape("left", (0, 1))
        self.assertEqual(self.window.groups[0].motors, set(range(96, 128)))
        self.window.experiment_running = False

    def test_direct_pico_and_patch_buttons_use_selected_layers(self) -> None:
        from coaxial_windwall.gui.group_library import template_motors
        self.window.quick_scope.setCurrentIndex(1)
        for number in range(1, 17):
            self.window.clear_wall()
            self.window.quick_buttons[f"pico:{number}"].click()
            self.assertEqual(self.window.groups[0].motors, template_motors(f"pico:{number}", (0,)))
        self.window.clear_wall()
        self.window.quick_buttons["square:3"].click()
        self.assertEqual(self.window.groups[0].motors, template_motors("square:3", (0,), 2, 2))

    def test_signal_controls_are_right_of_grid(self) -> None:
        self.window.resize(1600, 1000)
        self.window.show()
        self.app.processEvents()
        grid_right = self.window.cell_grid.mapTo(self.window, QPoint(self.window.cell_grid.width(), 0)).x()
        self.assertGreater(self.window.signal_type.mapTo(self.window, QPoint(0, 0)).x(), grid_right)


if __name__ == "__main__":
    unittest.main()
