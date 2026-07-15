"""PyQt6 GUI for the clean Coaxial 8x8x2 baseline."""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass, field
from statistics import mean

from PyQt6.QtCore import QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QKeySequence, QPainter, QPen, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from config import (
    COMMAND_RATE_HZ,
    GUI_REFRESH_HZ,
    GUI_PRESETS_PATH,
    GRID_COLS,
    GRID_ROWS,
    LAYER_LABELS,
    LAYER_NAMES,
    NUM_MOTORS,
    PWM_DEFAULT,
    PWM_IDLE,
    PWM_MIN,
    PWM_PRESETS,
    PWM_RANGE_PRESETS,
    PWM_UI_MAX,
)
from coaxial_windwall.control.profiles import (
    checkerboard_frame,
    idle_frame,
    layer_split_frame,
    single_pixel_frame,
    uniform_pair_frame,
)
from coaxial_windwall.hardware import HardwareInterface
from coaxial_windwall.model import CoaxialAddress, clamp_pwm


APP_STYLESHEET = """
QMainWindow {
    background: #0b1017;
}
QWidget {
    color: #d7dee9;
}
QFrame#TopBar {
    background: #141b26;
    border: 1px solid #2a3443;
    border-radius: 6px;
}
QLabel#Title {
    color: #f8fafc;
    font-size: 22px;
    font-weight: 800;
}
QLabel#Status {
    background: #0f2f2b;
    color: #7dd3c7;
    border: 1px solid #176b62;
    border-radius: 6px;
    padding: 7px 10px;
    font-weight: 800;
}
QLabel#Status[running="true"] {
    background: #12351f;
    color: #86efac;
    border-color: #238249;
}
QLabel#Status[armed="true"] {
    background: #3b2b0c;
    color: #fcd34d;
    border-color: #a16207;
}
QLabel#Timer {
    background: #101722;
    color: #f8fafc;
    border: 1px solid #2f3b4c;
    border-radius: 6px;
    padding: 7px 10px;
    font-size: 15px;
    font-weight: 900;
}
QFrame#Panel {
    background: #111823;
    border: 1px solid #2a3443;
    border-radius: 6px;
}
QFrame#SelectedInspector {
    background: #0d1420;
    border-top: 1px solid #2a3443;
}
QLabel#PanelTitle {
    color: #f8fafc;
    font-size: 14px;
    font-weight: 800;
}
QLabel#MetricLabel {
    color: #91a0b5;
    font-size: 11px;
    font-weight: 700;
}
QLabel#MetricValue {
    color: #f8fafc;
    font-size: 18px;
    font-weight: 900;
}
QPushButton {
    background: #182233;
    color: #e5edf7;
    border: 1px solid #3a4658;
    border-radius: 6px;
    padding: 8px 12px;
    font-weight: 700;
}
QPushButton:hover {
    background: #223047;
}
QPushButton#PrimaryButton {
    background: #2563eb;
    border-color: #2563eb;
    color: #ffffff;
}
QPushButton#StopButton {
    background: #b91c1c;
    border-color: #b91c1c;
    color: #ffffff;
}
QPushButton#StopButton:hover {
    background: #dc2626;
}
QCheckBox {
    color: #d7dee9;
    spacing: 8px;
    font-weight: 700;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    background: #0d1420;
    border: 1px solid #475569;
    border-radius: 4px;
}
QCheckBox::indicator:checked {
    background: #d97706;
    border-color: #f59e0b;
}
QLabel#InspectorValue {
    color: #e5edf7;
    font-size: 12px;
    font-weight: 800;
}
QComboBox, QSpinBox {
    background: #0d1420;
    color: #e5edf7;
    border: 1px solid #3a4658;
    border-radius: 5px;
    padding: 6px;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}
QComboBox:disabled, QSpinBox:disabled {
    background: #111827;
    color: #64748b;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid #3a4658;
    background: #182233;
    border-top-right-radius: 5px;
    border-bottom-right-radius: 5px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #cbd5e1;
    width: 0;
    height: 0;
}
QComboBox QAbstractItemView {
    background: #0d1420;
    color: #e5edf7;
    border: 1px solid #3a4658;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
    outline: 0;
}
QComboBox QAbstractItemView::item {
    background: #0d1420;
    color: #e5edf7;
    min-height: 24px;
    padding: 6px;
}
QComboBox QAbstractItemView::item:hover,
QComboBox QAbstractItemView::item:selected {
    background: #2563eb;
    color: #ffffff;
}
QSpinBox::up-button, QSpinBox::down-button {
    background: #182233;
    border-left: 1px solid #3a4658;
    width: 18px;
}
QSpinBox::up-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 5px solid #cbd5e1;
    width: 0;
    height: 0;
}
QSpinBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #cbd5e1;
    width: 0;
    height: 0;
}
QLineEdit {
    background: #0d1420;
    color: #e5edf7;
    border: 1px solid #3a4658;
    border-radius: 5px;
    padding: 7px;
}
QListWidget {
    background: #0d1420;
    color: #e5edf7;
    border: 1px solid #3a4658;
    border-radius: 5px;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}
QListWidget::item {
    color: #e5edf7;
    padding: 5px;
}
QListWidget::item:selected {
    background: #2563eb;
    color: #ffffff;
}
QTabWidget::pane {
    border: 0;
}
QTabBar::tab {
    background: #182233;
    color: #aeb9c9;
    border: 1px solid #3a4658;
    border-bottom: 0;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    padding: 7px 10px;
    font-weight: 700;
}
QTabBar::tab:selected {
    background: #111823;
    color: #f8fafc;
}
QSlider::groove:horizontal {
    background: #2a3443;
    border-radius: 3px;
    height: 6px;
}
QSlider::handle:horizontal {
    background: #8fb3ff;
    border: 1px solid #c9d8ff;
    border-radius: 8px;
    margin: -5px 0;
    width: 16px;
}
"""


GROUP_SCOPE_BOTH = "Both"
GROUP_SCOPE_FRONT = "Front"
GROUP_SCOPE_BACK = "Back"
GROUP_SCOPES = (GROUP_SCOPE_BOTH, GROUP_SCOPE_FRONT, GROUP_SCOPE_BACK)

BUILT_IN_TESTS = (
    "Uniform Current PWM",
    "All Idle",
    "Front Current PWM",
    "Back Current PWM",
    "Selected Pair Current PWM",
    "Checkerboard Current PWM",
    "Active Group Current PWM",
)


@dataclass
class MotorGroup:
    name: str
    pixels: set[tuple[int, int]] = field(default_factory=set)
    layer_scope: str = GROUP_SCOPE_BOTH

    def sorted_pixels(self) -> list[tuple[int, int]]:
        return sorted(self.pixels)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "pixels": [list(pixel) for pixel in self.sorted_pixels()],
            "layer_scope": self.layer_scope,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MotorGroup":
        name = str(data.get("name") or "Group")
        layer_scope = str(data.get("layer_scope") or GROUP_SCOPE_BOTH)
        if layer_scope not in GROUP_SCOPES:
            layer_scope = GROUP_SCOPE_BOTH
        pixels: set[tuple[int, int]] = set()
        for item in data.get("pixels", []):
            if not isinstance(item, (list, tuple)) or len(item) != 2:
                continue
            row, col = int(item[0]), int(item[1])
            if 0 <= row < GRID_ROWS and 0 <= col < GRID_COLS:
                pixels.add((row, col))
        return cls(name=name, pixels=pixels, layer_scope=layer_scope)


@dataclass
class PresetTest:
    name: str
    frame: list[int]

    def to_dict(self) -> dict:
        return {"name": self.name, "frame": list(self.frame)}

    @classmethod
    def from_dict(cls, data: dict) -> "PresetTest":
        name = str(data.get("name") or "Preset")
        frame = [int(value) for value in data.get("frame", [])]
        return cls(name=name, frame=frame)


class PixelCell(QFrame):
    clicked = pyqtSignal(int, int)

    def __init__(self, row: int, col: int) -> None:
        super().__init__()
        self.row = row
        self.col = col
        self.pair_label = CoaxialAddress(row, col, 0).pair_label
        self.location_label = f"R{row + 1}C{col + 1}"
        self.selected = False
        self.in_group = False
        self.controller_focus = False
        self.layer_a_pwm = PWM_IDLE
        self.layer_b_pwm = PWM_IDLE
        self.minimum_pwm = PWM_MIN
        self.maximum_pwm = PWM_UI_MAX
        self.setMinimumSize(82, 72)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setToolTip(f"{self.pair_label}  {self.location_label}")

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.row, self.col)
        super().mousePressEvent(event)

    def set_selected(self, selected: bool) -> None:
        if self.selected != selected:
            self.selected = selected
            self.update()

    def set_in_group(self, in_group: bool) -> None:
        if self.in_group != in_group:
            self.in_group = in_group
            self.update()

    def set_controller_focus(self, focused: bool) -> None:
        if self.controller_focus != focused:
            self.controller_focus = focused
            self.update()

    def set_pwm(self, layer_a: int, layer_b: int) -> None:
        layer_a = clamp_pwm(layer_a)
        layer_b = clamp_pwm(layer_b)
        if self.layer_a_pwm != layer_a or self.layer_b_pwm != layer_b:
            self.layer_a_pwm = layer_a
            self.layer_b_pwm = layer_b
            self.update()

    def set_pwm_range(self, minimum: int, maximum: int) -> None:
        self.minimum_pwm = minimum
        self.maximum_pwm = max(maximum, minimum + 1)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = self.rect().adjusted(1, 1, -1, -1)
        fill = QColor("#132033" if self.in_group else "#0f1724")
        border = QColor("#3b82f6" if self.selected else "#2c3848")
        if self.in_group and not self.selected:
            border = QColor("#14b8a6")
        if self.controller_focus and not self.selected:
            border = QColor("#a78bfa")
        painter.setPen(QPen(border, 2 if self.selected else 1))
        painter.setBrush(fill)
        painter.drawRoundedRect(QRectF(rect), 5, 5)

        title_font = QFont(self.font())
        title_font.setPointSize(9)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(QColor("#f8fafc"))
        painter.drawText(7, 16, self.pair_label)

        small_font = QFont(self.font())
        small_font.setPointSize(8)
        painter.setFont(small_font)
        painter.setPen(QColor("#94a3b8"))
        painter.drawText(rect.width() - 41, 16, self.location_label)

        self.draw_pwm_bar(painter, 7, 27, rect.width() - 12, 13, self.layer_a_pwm, "#14b8a6", "F")
        self.draw_pwm_bar(painter, 7, 47, rect.width() - 12, 13, self.layer_b_pwm, "#d97706", "B")

    def draw_pwm_bar(
        self,
        painter: QPainter,
        x: int,
        y: int,
        width: int,
        height: int,
        pwm: int,
        color: str,
        label: str,
    ) -> None:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#202b3a"))
        painter.drawRoundedRect(QRectF(x, y, width, height), 3, 3)

        span = max(1, self.maximum_pwm - self.minimum_pwm)
        ratio = max(0.0, min(1.0, (pwm - self.minimum_pwm) / span))
        fill_width = max(2, int(width * ratio)) if pwm > self.minimum_pwm else 0
        if fill_width:
            painter.setBrush(QColor(color))
            painter.drawRoundedRect(QRectF(x, y, fill_width, height), 3, 3)

        label_font = QFont(self.font())
        label_font.setPointSize(7)
        label_font.setBold(True)
        painter.setFont(label_font)
        painter.setPen(QColor("#e5edf7"))
        painter.drawText(x + 4, y + 10, label)
        painter.setPen(QColor("#cbd5e1"))
        painter.drawText(x + width - 33, y + 10, str(pwm))


class CoaxialWindwallWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Coaxial 8x8x2 Windwall System")
        self.resize(1220, 780)

        self.hardware = HardwareInterface(use_mock=True)
        self.current_pwm = idle_frame()
        self.running = False
        self.output_armed = False
        self.selected_row = 0
        self.selected_col = 0
        self.cells: dict[tuple[int, int], PixelCell] = {}
        self.groups: dict[str, MotorGroup] = {}
        self.preset_tests: dict[str, PresetTest] = {}
        self.view_dirty = True
        self.run_started_s: float | None = None
        self.last_run_elapsed_s = 0.0
        self.timed_test_duration_s: int | None = None
        self.timed_test_end_s: float | None = None
        self.load_user_presets()
        if not self.groups:
            self.groups["Group 1"] = MotorGroup(name="Group 1")

        self.command_timer = QTimer(self)
        self.command_timer.setInterval(max(1, int(1000 / COMMAND_RATE_HZ)))
        self.command_timer.timeout.connect(self.send_current_frame)

        self.visual_timer = QTimer(self)
        self.visual_timer.setInterval(max(1, int(1000 / GUI_REFRESH_HZ)))
        self.visual_timer.timeout.connect(self.refresh_view_if_dirty)
        self.visual_timer.start()

        self.elapsed_timer = QTimer(self)
        self.elapsed_timer.setInterval(250)
        self.elapsed_timer.timeout.connect(self.update_run_timer)
        self.elapsed_timer.start()

        self.setStyleSheet(APP_STYLESHEET)
        self.setCentralWidget(self.build_ui())
        self.emergency_shortcut = QShortcut(QKeySequence("Escape"), self)
        self.emergency_shortcut.activated.connect(self.emergency_stop)
        self.apply_profile()
        self.mark_view_dirty()

    def build_ui(self) -> QWidget:
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(14, 14, 14, 14)
        root_layout.setSpacing(12)

        root_layout.addWidget(self.build_top_bar())

        content = QHBoxLayout()
        content.setSpacing(12)
        content.addWidget(self.build_wall_panel(), stretch=1)
        content.addWidget(self.build_control_panel())
        root_layout.addLayout(content, stretch=1)

        root_layout.addWidget(self.build_metric_panel())
        return root

    def build_top_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("TopBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)

        title = QLabel("Coaxial 8x8x2 Windwall")
        title.setObjectName("Title")
        layout.addWidget(title)
        layout.addStretch(1)

        self.status_label = QLabel("IDLE / MOCK")
        self.status_label.setObjectName("Status")
        layout.addWidget(self.status_label)

        self.timer_label = QLabel("00:00")
        self.timer_label.setObjectName("Timer")
        self.timer_label.setMinimumWidth(205)
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.timer_label)

        self.arm_checkbox = QCheckBox("Arm output")
        self.arm_checkbox.setToolTip("Required before commands can be started or sent")
        self.arm_checkbox.toggled.connect(self.set_output_armed)
        layout.addWidget(self.arm_checkbox)

        self.start_button = QPushButton("Start")
        self.start_button.setObjectName("PrimaryButton")
        self.start_button.clicked.connect(self.start_commands)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton("EMERGENCY STOP")
        self.stop_button.setObjectName("StopButton")
        self.stop_button.setToolTip("Immediately idle all outputs (Esc)")
        self.stop_button.clicked.connect(self.emergency_stop)
        layout.addWidget(self.stop_button)

        self.idle_button = QPushButton("Idle")
        self.idle_button.clicked.connect(self.set_idle)
        layout.addWidget(self.idle_button)

        return bar

    def build_wall_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("Panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("Wind Pixel Wall")
        title.setObjectName("PanelTitle")
        header.addWidget(title)
        header.addStretch(1)

        legend_a = QLabel(f"{LAYER_NAMES[0]} / {LAYER_LABELS[0]} teal")
        legend_a.setObjectName("MetricLabel")
        header.addWidget(legend_a)
        legend_b = QLabel(f"{LAYER_NAMES[1]} / {LAYER_LABELS[1]} amber")
        legend_b.setObjectName("MetricLabel")
        header.addWidget(legend_b)
        self.controller_focus_combo = QComboBox()
        self.controller_focus_combo.addItem("All controllers", None)
        for controller in range(1, 17):
            self.controller_focus_combo.addItem(f"C{controller:02d}", controller - 1)
        self.controller_focus_combo.setToolTip("Highlight pixels wired to one controller")
        self.controller_focus_combo.currentIndexChanged.connect(self.mark_view_dirty)
        header.addWidget(self.controller_focus_combo)
        layout.addLayout(header)

        grid = QGridLayout()
        grid.setSpacing(6)
        for index in range(GRID_ROWS):
            grid.setRowStretch(index, 1)
        for index in range(GRID_COLS):
            grid.setColumnStretch(index, 1)
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                cell = PixelCell(row, col)
                cell.clicked.connect(self.select_cell)
                self.cells[(row, col)] = cell
                grid.addWidget(cell, row, col)
        layout.addLayout(grid)
        layout.addStretch(1)
        return panel

    def build_control_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("Panel")
        panel.setFixedWidth(360)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        title = QLabel("Command Builder")
        title.setObjectName("PanelTitle")
        layout.addWidget(title)

        tabs = QTabWidget()
        tabs.addTab(self.build_command_tab(), "Command")
        tabs.addTab(self.build_groups_tab(), "Groups")
        tabs.addTab(self.build_tests_tab(), "Tests")
        layout.addWidget(tabs, stretch=1)
        layout.addWidget(self.build_selected_inspector())
        return panel

    def build_selected_inspector(self) -> QFrame:
        inspector = QFrame()
        inspector.setObjectName("SelectedInspector")
        layout = QGridLayout(inspector)
        layout.setContentsMargins(10, 9, 10, 9)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(4)
        title = QLabel("Selected Pair")
        title.setObjectName("PanelTitle")
        layout.addWidget(title, 0, 0, 1, 2)
        self.inspector_pair = self.add_inspector_row(layout, 1, "Pixel", "P01 / R1C1")
        self.inspector_front = self.add_inspector_row(layout, 2, "Front", "F01  C01 CH1")
        self.inspector_back = self.add_inspector_row(layout, 3, "Back", "B01  C01 CH2")
        return inspector

    def add_inspector_row(
        self, layout: QGridLayout, row: int, label_text: str, value_text: str
    ) -> QLabel:
        label = QLabel(label_text)
        label.setObjectName("MetricLabel")
        value = QLabel(value_text)
        value.setObjectName("InspectorValue")
        value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(label, row, 0)
        layout.addWidget(value, row, 1)
        return value

    def build_command_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(12)

        self.profile_combo = QComboBox()
        self.profile_combo.addItems(
            ["Uniform Pair", "Layer Split", "Checkerboard", "Single Pixel"]
        )
        self.profile_combo.currentIndexChanged.connect(self.apply_profile)
        layout.addWidget(self.labeled_widget("Profile", self.profile_combo))

        self.pwm_range_combo = QComboBox()
        for label, minimum, maximum in PWM_RANGE_PRESETS:
            self.pwm_range_combo.addItem(label, (minimum, maximum))
        self.pwm_range_combo.setCurrentIndex(1)
        self.pwm_range_combo.currentIndexChanged.connect(self.apply_pwm_range)
        layout.addWidget(self.labeled_widget("PWM Range", self.pwm_range_combo))

        self.pwm_preset_combo = QComboBox()
        self.pwm_preset_combo.addItem("Custom", None)
        for label, pwm in PWM_PRESETS:
            self.pwm_preset_combo.addItem(f"{label} - {pwm}", pwm)
        self.pwm_preset_combo.setCurrentIndex(3)
        self.pwm_preset_combo.currentIndexChanged.connect(self.apply_pwm_preset)
        layout.addWidget(self.labeled_widget("PWM Preset", self.pwm_preset_combo))

        self.base_slider = self.slider(PWM_MIN, PWM_UI_MAX, PWM_DEFAULT)
        self.base_slider.valueChanged.connect(self.apply_profile)
        self.base_value = QLabel(str(PWM_DEFAULT))
        layout.addWidget(self.labeled_slider("Base PWM", self.base_slider, self.base_value))

        self.diff_slider = self.slider(-300, 300, 0)
        self.diff_slider.valueChanged.connect(self.apply_profile)
        self.diff_value = QLabel("0")
        layout.addWidget(self.labeled_slider("Layer Diff", self.diff_slider, self.diff_value))

        self.row_spin = QSpinBox()
        self.row_spin.setRange(1, GRID_ROWS)
        self.row_spin.valueChanged.connect(self.spin_selected_cell)
        layout.addWidget(self.labeled_widget("Row", self.row_spin))

        self.col_spin = QSpinBox()
        self.col_spin.setRange(1, GRID_COLS)
        self.col_spin.valueChanged.connect(self.spin_selected_cell)
        layout.addWidget(self.labeled_widget("Column", self.col_spin))

        self.layer_combo = QComboBox()
        self.layer_combo.addItems(
            ["Both", f"{LAYER_NAMES[0]} ({LAYER_LABELS[0]})", f"{LAYER_NAMES[1]} ({LAYER_LABELS[1]})"]
        )
        self.layer_combo.currentIndexChanged.connect(self.apply_profile)
        layout.addWidget(self.labeled_widget("Layer", self.layer_combo))

        self.send_once_button = QPushButton("Send Once")
        self.send_once_button.clicked.connect(self.send_current_frame)
        layout.addWidget(self.send_once_button)

        layout.addStretch(1)
        return tab

    def build_groups_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(10)

        self.group_combo = QComboBox()
        self.group_combo.currentIndexChanged.connect(self.select_group_from_combo)
        layout.addWidget(self.labeled_widget("Active Group", self.group_combo))

        self.group_name_input = QLineEdit()
        self.group_name_input.setPlaceholderText("Group name")
        layout.addWidget(self.labeled_widget("Group Name", self.group_name_input))

        self.group_scope_combo = QComboBox()
        self.add_scope_items(self.group_scope_combo)
        self.group_scope_combo.currentIndexChanged.connect(self.update_active_group_scope)
        layout.addWidget(self.labeled_widget("Layer Scope", self.group_scope_combo))

        button_row = QHBoxLayout()
        new_group_button = QPushButton("New")
        new_group_button.clicked.connect(self.create_group)
        button_row.addWidget(new_group_button)
        delete_group_button = QPushButton("Delete")
        delete_group_button.clicked.connect(self.delete_active_group)
        button_row.addWidget(delete_group_button)
        layout.addLayout(button_row)

        add_selected_button = QPushButton("Add Selected Pixel")
        add_selected_button.clicked.connect(self.add_selected_pixel_to_group)
        layout.addWidget(add_selected_button)

        remove_selected_button = QPushButton("Remove Selected")
        remove_selected_button.clicked.connect(self.remove_selected_pixels_from_group)
        layout.addWidget(remove_selected_button)

        clear_group_button = QPushButton("Clear Group")
        clear_group_button.clicked.connect(self.clear_active_group)
        layout.addWidget(clear_group_button)

        apply_group_button = QPushButton("Apply Group PWM")
        apply_group_button.setObjectName("PrimaryButton")
        apply_group_button.clicked.connect(self.apply_active_group)
        layout.addWidget(apply_group_button)

        self.group_members_list = QListWidget()
        layout.addWidget(self.labeled_widget("Pixels", self.group_members_list), stretch=1)

        self.refresh_group_combo()
        return tab

    def build_tests_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(10)

        self.test_combo = QComboBox()
        layout.addWidget(self.labeled_widget("Preset Test", self.test_combo))

        self.test_speed_spin = QSpinBox()
        self.test_speed_spin.setRange(PWM_MIN, PWM_UI_MAX)
        self.test_speed_spin.setValue(PWM_DEFAULT)
        self.test_speed_spin.setSingleStep(25)
        layout.addWidget(self.labeled_widget("Test Speed PWM", self.test_speed_spin))

        self.test_duration_spin = QSpinBox()
        self.test_duration_spin.setRange(1, 3600)
        self.test_duration_spin.setValue(10)
        self.test_duration_spin.setSuffix(" s")
        layout.addWidget(self.labeled_widget("Duration", self.test_duration_spin))

        run_timed_button = QPushButton("Run Timed Test")
        run_timed_button.setObjectName("PrimaryButton")
        run_timed_button.clicked.connect(self.run_timed_test)
        layout.addWidget(run_timed_button)

        self.test_name_input = QLineEdit()
        self.test_name_input.setPlaceholderText("New test name")
        layout.addWidget(self.labeled_widget("Save Current As", self.test_name_input))

        apply_test_button = QPushButton("Apply Test")
        apply_test_button.setObjectName("PrimaryButton")
        apply_test_button.clicked.connect(self.apply_selected_test)
        layout.addWidget(apply_test_button)

        save_test_button = QPushButton("Save Current Frame")
        save_test_button.clicked.connect(self.save_current_test)
        layout.addWidget(save_test_button)

        delete_test_button = QPushButton("Delete Saved Test")
        delete_test_button.clicked.connect(self.delete_selected_test)
        layout.addWidget(delete_test_button)

        layout.addStretch(1)
        self.refresh_test_combo()
        return tab

    def build_metric_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("Panel")
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(24)

        self.metric_active = self.add_metric(layout, "Active Motors", "0")
        self.metric_front = self.add_metric(layout, "Front Active", "0 / 64")
        self.metric_back = self.add_metric(layout, "Back Active", "0 / 64")
        self.metric_average = self.add_metric(layout, "Average PWM", "1000")
        self.metric_peak = self.add_metric(layout, "Peak PWM", "1000")
        self.metric_frames = self.add_metric(layout, "Frames Sent", "0")
        self.metric_runtime = self.add_metric(layout, "Run Time", "00:00")
        self.metric_selected = self.add_metric(layout, "Selected Pixel", "P01")
        layout.addStretch(1)
        return panel

    def add_metric(self, layout: QHBoxLayout, label_text: str, value_text: str) -> QLabel:
        box = QVBoxLayout()
        label = QLabel(label_text)
        label.setObjectName("MetricLabel")
        value = QLabel(value_text)
        value.setObjectName("MetricValue")
        box.addWidget(label)
        box.addWidget(value)
        layout.addLayout(box)
        return value

    def labeled_widget(self, label_text: str, widget: QWidget) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        label = QLabel(label_text)
        label.setObjectName("MetricLabel")
        layout.addWidget(label)
        layout.addWidget(widget)
        return container

    def labeled_slider(self, label_text: str, slider: QSlider, value_label: QLabel) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        header = QHBoxLayout()
        label = QLabel(label_text)
        label.setObjectName("MetricLabel")
        value_label.setObjectName("MetricLabel")
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        header.addWidget(label)
        header.addStretch(1)
        header.addWidget(value_label)
        layout.addLayout(header)
        layout.addWidget(slider)
        return container

    def slider(self, minimum: int, maximum: int, value: int) -> QSlider:
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(minimum, maximum)
        slider.setValue(value)
        return slider

    def set_current_pwm(self, frame: list[int]) -> None:
        if len(frame) != NUM_MOTORS:
            raise ValueError(f"expected {NUM_MOTORS} PWM values, got {len(frame)}")
        self.current_pwm = [clamp_pwm(value) for value in frame]
        self.mark_view_dirty()

    def mark_view_dirty(self) -> None:
        self.view_dirty = True
        self.refresh_metrics()
        self.refresh_status()

    def refresh_view_if_dirty(self) -> None:
        if self.view_dirty:
            self.refresh_view()

    def format_duration(self, seconds: float | int) -> str:
        seconds = max(0, int(seconds))
        minutes, secs = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours:d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    def elapsed_run_seconds(self) -> float:
        if self.running and self.run_started_s is not None:
            return time.monotonic() - self.run_started_s
        return self.last_run_elapsed_s

    def update_run_timer(self) -> None:
        if not hasattr(self, "timer_label"):
            return
        now = time.monotonic()
        if self.running and self.timed_test_end_s is not None and now >= self.timed_test_end_s:
            self.finish_timed_test()
            return

        elapsed = self.elapsed_run_seconds()
        if self.running and self.timed_test_duration_s is not None:
            total = self.timed_test_duration_s
            remaining = max(0, total - int(elapsed))
            self.timer_label.setText(
                f"{self.format_duration(elapsed)} / {self.format_duration(total)}  left {self.format_duration(remaining)}"
            )
        else:
            self.timer_label.setText(self.format_duration(elapsed))
        if hasattr(self, "metric_runtime"):
            self.metric_runtime.setText(self.format_duration(elapsed))

    def load_user_presets(self) -> None:
        if not GUI_PRESETS_PATH.exists():
            return
        try:
            data = json.loads(GUI_PRESETS_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return

        for group_data in data.get("groups", []):
            group = MotorGroup.from_dict(group_data)
            if group.name:
                self.groups[group.name] = group

        for test_data in data.get("tests", []):
            test = PresetTest.from_dict(test_data)
            if test.name and len(test.frame) == NUM_MOTORS:
                test.frame = [clamp_pwm(value) for value in test.frame]
                self.preset_tests[test.name] = test

    def save_user_presets(self) -> None:
        data = {
            "groups": [group.to_dict() for group in self.groups.values()],
            "tests": [test.to_dict() for test in self.preset_tests.values()],
        }
        try:
            GUI_PRESETS_PATH.parent.mkdir(parents=True, exist_ok=True)
            temp_path = GUI_PRESETS_PATH.with_suffix(".tmp")
            temp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            temp_path.replace(GUI_PRESETS_PATH)
        except OSError as exc:
            print(f"Could not save GUI presets: {exc}", file=sys.stderr)

    def add_scope_items(self, combo: QComboBox) -> None:
        combo.addItem("Both Layers", GROUP_SCOPE_BOTH)
        combo.addItem(f"{LAYER_NAMES[0]} ({LAYER_LABELS[0]})", GROUP_SCOPE_FRONT)
        combo.addItem(f"{LAYER_NAMES[1]} ({LAYER_LABELS[1]})", GROUP_SCOPE_BACK)

    def current_group_scope(self) -> str:
        if not hasattr(self, "group_scope_combo"):
            return GROUP_SCOPE_BOTH
        scope = self.group_scope_combo.currentData()
        return scope if scope in GROUP_SCOPES else GROUP_SCOPE_BOTH

    def set_scope_combo_value(self, combo: QComboBox, scope: str) -> None:
        index = combo.findData(scope)
        combo.setCurrentIndex(index if index >= 0 else 0)

    def make_unique_name(self, existing: dict[str, object], prefix: str) -> str:
        index = 1
        while f"{prefix} {index}" in existing:
            index += 1
        return f"{prefix} {index}"

    def active_group(self) -> MotorGroup | None:
        if not hasattr(self, "group_combo"):
            return None
        name = self.group_combo.currentData()
        if name is None:
            return None
        return self.groups.get(str(name))

    def refresh_group_combo(self) -> None:
        if not hasattr(self, "group_combo"):
            return
        current_name = self.group_combo.currentData()
        if current_name not in self.groups:
            current_name = next(iter(sorted(self.groups)), None)

        self.group_combo.blockSignals(True)
        self.group_combo.clear()
        for name in sorted(self.groups):
            self.group_combo.addItem(name, name)
        if current_name is not None:
            index = self.group_combo.findData(current_name)
            self.group_combo.setCurrentIndex(index if index >= 0 else 0)
        self.group_combo.blockSignals(False)
        self.select_group_from_combo()

    def select_group_from_combo(self) -> None:
        group = self.active_group()
        if group is None:
            return
        self.group_name_input.setText(group.name)
        self.group_scope_combo.blockSignals(True)
        self.set_scope_combo_value(self.group_scope_combo, group.layer_scope)
        self.group_scope_combo.blockSignals(False)
        self.refresh_group_members()
        self.mark_view_dirty()

    def refresh_group_members(self) -> None:
        if not hasattr(self, "group_members_list"):
            return
        self.group_members_list.clear()
        group = self.active_group()
        if group is None:
            return
        for row, col in group.sorted_pixels():
            address = CoaxialAddress(row, col, 0)
            item = QListWidgetItem(f"{address.pair_label}  R{row + 1} C{col + 1}")
            item.setData(Qt.ItemDataRole.UserRole, (row, col))
            self.group_members_list.addItem(item)

    def create_group(self) -> None:
        raw_name = self.group_name_input.text().strip()
        name = raw_name or self.make_unique_name(self.groups, "Group")
        if name in self.groups:
            name = self.make_unique_name(self.groups, name)
        self.groups[name] = MotorGroup(
            name=name,
            pixels={(self.selected_row, self.selected_col)},
            layer_scope=self.current_group_scope(),
        )
        self.save_user_presets()
        self.refresh_group_combo()
        index = self.group_combo.findData(name)
        if index >= 0:
            self.group_combo.setCurrentIndex(index)

    def delete_active_group(self) -> None:
        group = self.active_group()
        if group is None:
            return
        self.groups.pop(group.name, None)
        if not self.groups:
            self.groups["Group 1"] = MotorGroup(name="Group 1")
        self.save_user_presets()
        self.refresh_group_combo()

    def update_active_group_scope(self) -> None:
        group = self.active_group()
        if group is None:
            return
        group.layer_scope = self.current_group_scope()
        self.save_user_presets()
        self.refresh_group_members()
        self.mark_view_dirty()

    def add_selected_pixel_to_group(self) -> None:
        group = self.active_group()
        if group is None:
            return
        group.pixels.add((self.selected_row, self.selected_col))
        self.save_user_presets()
        self.refresh_group_members()
        self.mark_view_dirty()

    def remove_selected_pixels_from_group(self) -> None:
        group = self.active_group()
        if group is None:
            return
        selected_items = self.group_members_list.selectedItems()
        if selected_items:
            for item in selected_items:
                row, col = item.data(Qt.ItemDataRole.UserRole)
                group.pixels.discard((row, col))
        else:
            group.pixels.discard((self.selected_row, self.selected_col))
        self.save_user_presets()
        self.refresh_group_members()
        self.mark_view_dirty()

    def clear_active_group(self) -> None:
        group = self.active_group()
        if group is None:
            return
        group.pixels.clear()
        self.save_user_presets()
        self.refresh_group_members()
        self.mark_view_dirty()

    def frame_for_pixels(
        self,
        pixels: set[tuple[int, int]] | list[tuple[int, int]],
        layer_scope: str,
        value: int,
    ) -> list[int]:
        frame = idle_frame()
        pwm = clamp_pwm(value)
        for row, col in pixels:
            if layer_scope in (GROUP_SCOPE_BOTH, GROUP_SCOPE_FRONT):
                frame[CoaxialAddress(row, col, 0).motor_index] = pwm
            if layer_scope in (GROUP_SCOPE_BOTH, GROUP_SCOPE_BACK):
                frame[CoaxialAddress(row, col, 1).motor_index] = pwm
        return frame

    def apply_active_group(self) -> None:
        group = self.active_group()
        if group is None:
            return
        self.set_current_pwm(
            self.frame_for_pixels(
                group.pixels,
                group.layer_scope,
                self.base_slider.value(),
            )
        )

    def refresh_test_combo(self) -> None:
        if not hasattr(self, "test_combo"):
            return
        current = self.test_combo.currentData()
        self.test_combo.blockSignals(True)
        self.test_combo.clear()
        for name in BUILT_IN_TESTS:
            self.test_combo.addItem(name, ("builtin", name))
        if self.preset_tests:
            self.test_combo.insertSeparator(self.test_combo.count())
        for name in sorted(self.preset_tests):
            self.test_combo.addItem(name, ("saved", name))
        if current is not None:
            for index in range(self.test_combo.count()):
                if self.test_combo.itemData(index) == current:
                    self.test_combo.setCurrentIndex(index)
                    break
        self.test_combo.blockSignals(False)

    def save_current_test(self) -> None:
        name = self.test_name_input.text().strip()
        if not name:
            name = self.make_unique_name(self.preset_tests, "Test")
        self.preset_tests[name] = PresetTest(name=name, frame=list(self.current_pwm))
        self.test_name_input.clear()
        self.save_user_presets()
        self.refresh_test_combo()
        index = self.test_combo.findData(("saved", name))
        if index >= 0:
            self.test_combo.setCurrentIndex(index)

    def delete_selected_test(self) -> None:
        data = self.test_combo.currentData()
        if not data or data[0] != "saved":
            return
        self.preset_tests.pop(data[1], None)
        self.save_user_presets()
        self.refresh_test_combo()

    def selected_test_frame(self) -> list[int]:
        data = self.test_combo.currentData()
        if not data:
            return idle_frame()
        kind, name = data
        if kind == "saved":
            test = self.preset_tests.get(name)
            if test is None:
                return idle_frame()
            return [clamp_pwm(value) for value in test.frame]
        return self.built_in_test_frame(name)

    def apply_selected_test(self) -> None:
        self.set_current_pwm(self.selected_test_frame())

    def run_timed_test(self) -> None:
        if not self.output_armed:
            self.status_label.setText("ARM OUTPUT TO RUN TEST")
            return
        pwm = self.test_speed_spin.value()
        duration_s = self.test_duration_spin.value()
        self.base_slider.setValue(pwm)
        self.set_current_pwm(self.selected_test_frame())

        self.running = True
        self.run_started_s = time.monotonic()
        self.last_run_elapsed_s = 0.0
        self.timed_test_duration_s = duration_s
        self.timed_test_end_s = self.run_started_s + duration_s
        self.command_timer.start()
        self.send_current_frame()
        self.update_run_timer()

    def finish_timed_test(self) -> None:
        self.last_run_elapsed_s = float(self.timed_test_duration_s or 0)
        self.running = False
        self.command_timer.stop()
        self.timed_test_duration_s = None
        self.timed_test_end_s = None
        self.hardware.shutdown()
        self.set_current_pwm(idle_frame())
        self.update_run_timer()

    def built_in_test_frame(self, name: str) -> list[int]:
        base = self.base_slider.value()
        diff = abs(self.diff_slider.value())
        if name == "All Idle":
            return idle_frame()
        if name == "Uniform Current PWM":
            return uniform_pair_frame(base)
        if name == "Front Current PWM":
            pixels = [(row, col) for row in range(GRID_ROWS) for col in range(GRID_COLS)]
            return self.frame_for_pixels(pixels, GROUP_SCOPE_FRONT, base)
        if name == "Back Current PWM":
            pixels = [(row, col) for row in range(GRID_ROWS) for col in range(GRID_COLS)]
            return self.frame_for_pixels(pixels, GROUP_SCOPE_BACK, base)
        if name == "Selected Pair Current PWM":
            return self.frame_for_pixels(
                [(self.selected_row, self.selected_col)],
                GROUP_SCOPE_BOTH,
                base,
            )
        if name == "Checkerboard Current PWM":
            return checkerboard_frame(base, diff or 100)
        if name == "Active Group Current PWM":
            group = self.active_group()
            if group is None:
                return idle_frame()
            return self.frame_for_pixels(group.pixels, group.layer_scope, base)
        return idle_frame()

    def active_pwm_range(self) -> tuple[int, int]:
        data = self.pwm_range_combo.currentData()
        if data is None:
            return PWM_MIN, PWM_UI_MAX
        minimum, maximum = data
        return int(minimum), int(maximum)

    def apply_pwm_range(self) -> None:
        minimum, maximum = self.active_pwm_range()
        current = max(minimum, min(maximum, self.base_slider.value()))
        self.base_slider.blockSignals(True)
        self.base_slider.setRange(minimum, maximum)
        self.base_slider.setValue(current)
        self.base_slider.blockSignals(False)
        if hasattr(self, "test_speed_spin"):
            test_pwm = max(minimum, min(maximum, self.test_speed_spin.value()))
            self.test_speed_spin.blockSignals(True)
            self.test_speed_spin.setRange(minimum, maximum)
            self.test_speed_spin.setValue(test_pwm)
            self.test_speed_spin.blockSignals(False)
        for cell in self.cells.values():
            cell.set_pwm_range(minimum, maximum)
        self.apply_profile()

    def apply_pwm_preset(self) -> None:
        preset = self.pwm_preset_combo.currentData()
        if preset is None:
            return
        minimum, maximum = self.active_pwm_range()
        pwm = max(minimum, min(maximum, int(preset)))
        self.base_slider.setValue(pwm)
        self.apply_profile()

    def select_cell(self, row: int, col: int) -> None:
        self.selected_row = row
        self.selected_col = col
        self.row_spin.blockSignals(True)
        self.col_spin.blockSignals(True)
        self.row_spin.setValue(row + 1)
        self.col_spin.setValue(col + 1)
        self.row_spin.blockSignals(False)
        self.col_spin.blockSignals(False)
        self.apply_profile()

    def spin_selected_cell(self) -> None:
        self.selected_row = self.row_spin.value() - 1
        self.selected_col = self.col_spin.value() - 1
        self.apply_profile()

    def apply_profile(self) -> None:
        base = self.base_slider.value()
        diff = self.diff_slider.value()
        self.base_value.setText(str(base))
        self.diff_value.setText(str(diff))
        matching_preset = next(
            (
                index
                for index in range(1, self.pwm_preset_combo.count())
                if self.pwm_preset_combo.itemData(index) == base
            ),
            0,
        )
        if self.pwm_preset_combo.currentIndex() != matching_preset:
            self.pwm_preset_combo.blockSignals(True)
            self.pwm_preset_combo.setCurrentIndex(matching_preset)
            self.pwm_preset_combo.blockSignals(False)

        profile = self.profile_combo.currentText()
        if profile == "Uniform Pair":
            frame = uniform_pair_frame(base)
        elif profile == "Layer Split":
            frame = layer_split_frame(base, diff)
        elif profile == "Checkerboard":
            frame = checkerboard_frame(base, abs(diff))
        else:
            layer_index = self.layer_combo.currentIndex()
            layer = None if layer_index == 0 else layer_index - 1
            frame = single_pixel_frame(
                self.selected_row,
                self.selected_col,
                layer,
                base,
                background=PWM_IDLE,
            )
        self.set_current_pwm(frame)

    def set_idle(self) -> None:
        self.set_current_pwm(idle_frame())
        self.send_current_frame()

    def set_output_armed(self, armed: bool) -> None:
        self.output_armed = bool(armed)
        if not self.output_armed and self.running:
            self.stop_commands()
        self.refresh_status()

    def can_send_active_frame(self) -> bool:
        return self.output_armed or all(value == PWM_IDLE for value in self.current_pwm)

    def start_commands(self) -> None:
        if not self.output_armed:
            self.status_label.setText("ARM OUTPUT TO START")
            return
        self.running = True
        self.run_started_s = time.monotonic()
        self.last_run_elapsed_s = 0.0
        self.timed_test_duration_s = None
        self.timed_test_end_s = None
        self.command_timer.start()
        self.send_current_frame()
        self.update_run_timer()
        self.refresh_status()

    def stop_commands(self) -> None:
        if self.running and self.run_started_s is not None:
            self.last_run_elapsed_s = time.monotonic() - self.run_started_s
        self.running = False
        self.timed_test_duration_s = None
        self.timed_test_end_s = None
        self.command_timer.stop()
        self.hardware.shutdown()
        self.set_current_pwm(idle_frame())
        self.update_run_timer()
        self.refresh_status()

    def emergency_stop(self) -> None:
        self.stop_commands()
        self.output_armed = False
        if hasattr(self, "arm_checkbox"):
            self.arm_checkbox.blockSignals(True)
            self.arm_checkbox.setChecked(False)
            self.arm_checkbox.blockSignals(False)
        self.refresh_status()

    def send_current_frame(self) -> None:
        if not self.can_send_active_frame():
            self.status_label.setText("ARM OUTPUT TO SEND")
            return
        self.hardware.send_pwm_frame(self.current_pwm)
        self.refresh_metrics()

    def refresh_view(self) -> None:
        group = self.active_group()
        group_pixels = group.pixels if group is not None else set()
        focused_controller = self.controller_focus_combo.currentData()
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                idx_a = CoaxialAddress(row, col, 0).motor_index
                idx_b = CoaxialAddress(row, col, 1).motor_index
                cell = self.cells[(row, col)]
                cell.set_pwm(self.current_pwm[idx_a], self.current_pwm[idx_b])
                cell.set_in_group((row, col) in group_pixels)
                controller_match = focused_controller is not None and (
                    CoaxialAddress(row, col, 0).controller_index == focused_controller
                    or CoaxialAddress(row, col, 1).controller_index == focused_controller
                )
                cell.set_controller_focus(controller_match)
                cell.set_selected(row == self.selected_row and col == self.selected_col)
        self.view_dirty = False
        self.refresh_metrics()
        self.refresh_status()

    def refresh_metrics(self) -> None:
        if not hasattr(self, "metric_active"):
            return
        active = sum(1 for value in self.current_pwm if value > PWM_IDLE)
        front_active = sum(1 for value in self.current_pwm[:64] if value > PWM_IDLE)
        back_active = sum(1 for value in self.current_pwm[64:] if value > PWM_IDLE)
        self.metric_active.setText(f"{active} / {NUM_MOTORS}")
        self.metric_front.setText(f"{front_active} / 64")
        self.metric_back.setText(f"{back_active} / 64")
        self.metric_average.setText(f"{mean(self.current_pwm):.0f}")
        self.metric_peak.setText(str(max(self.current_pwm)))
        self.metric_frames.setText(str(self.hardware.frame_count))
        self.metric_runtime.setText(self.format_duration(self.elapsed_run_seconds()))
        address = CoaxialAddress(self.selected_row, self.selected_col, 0)
        self.metric_selected.setText(address.pair_label)
        front = address
        back = CoaxialAddress(self.selected_row, self.selected_col, 1)
        self.inspector_pair.setText(f"{front.pair_label} / R{front.row + 1}C{front.col + 1}")
        self.inspector_front.setText(
            f"{front.label}  {front.controller_label} {front.controller_channel_label}  {self.current_pwm[front.motor_index]} us"
        )
        self.inspector_back.setText(
            f"{back.label}  {back.controller_label} {back.controller_channel_label}  {self.current_pwm[back.motor_index]} us"
        )

    def refresh_status(self) -> None:
        mode = "RUNNING" if self.running else "IDLE"
        armed = self.output_armed and not self.running
        self.status_label.setProperty("running", self.running)
        self.status_label.setProperty("armed", armed)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        state = mode if self.running else ("ARMED" if armed else "IDLE")
        self.status_label.setText(f"{state} / {self.hardware.mode_name}")
        self.start_button.setEnabled(self.output_armed and not self.running)
        self.send_once_button.setEnabled(self.output_armed)

    def closeEvent(self, event) -> None:  # noqa: N802
        self.command_timer.stop()
        self.visual_timer.stop()
        self.elapsed_timer.stop()
        self.hardware.shutdown()
        event.accept()


def run_app(smoke_test_ms: int = 0) -> int:
    app = QApplication(sys.argv[:1])
    app.setFont(QFont("Arial", 10))
    window = CoaxialWindwallWindow()
    window.show()
    if smoke_test_ms:
        QTimer.singleShot(smoke_test_ms, app.quit)
    return app.exec()
