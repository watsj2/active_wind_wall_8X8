"""German 6x6-derived operator GUI for the Coaxial 8x8x2 windwall."""

from __future__ import annotations

import json
import sys
import time
from collections import deque
from statistics import mean

from PyQt6.QtCore import QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QKeySequence, QPainter, QPen, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config import (
    COMMAND_RATE_HZ,
    CONTROLLER_COUNT,
    DEFAULT_HARDWARE_MODE,
    GRID_COLS,
    GRID_ROWS,
    GUI_PRESETS_PATH,
    LAYER_LABELS,
    NUM_MOTORS,
    PWM_IDLE,
    PWM_MAX,
    PWM_RANGE_PRESETS,
    PWM_UI_MAX,
)
from coaxial_windwall.control.signals import (
    SIGNAL_CONSTANT,
    SIGNAL_CUSTOM,
    SIGNAL_SQUARE,
    SIGNAL_TYPES,
    GroupSignal,
    Harmonic,
    SignalGroup,
    build_group_frame,
    preview_signal,
)
from coaxial_windwall.hardware import HardwareInterface
from coaxial_windwall.model import CoaxialAddress


GROUP_COLORS = (
    "#14b8a6",
    "#3b82f6",
    "#ef4444",
    "#f59e0b",
    "#a78bfa",
    "#06b6d4",
    "#84cc16",
    "#ec4899",
)

ASSIGN_BOTH = "Both layers"
ASSIGN_FRONT = "Front only"
ASSIGN_BACK = "Back only"


APP_STYLESHEET = """
QMainWindow, QWidget#AppRoot { background: #0a0f17; color: #dbe4ef; }
QFrame#TopBar, QFrame#BottomBar {
    background: #111925; border: 1px solid #293548; border-radius: 6px;
}
QFrame#Section { background: #101721; border: 1px solid #293548; border-radius: 6px; }
QFrame#Subsection { background: transparent; border-top: 1px solid #293548; }
QLabel#Title { color: #f8fafc; font-size: 21px; font-weight: 800; }
QLabel#Subtitle { color: #8fa0b5; font-size: 11px; }
QLabel#SectionTitle { color: #f8fafc; font-size: 13px; font-weight: 800; }
QLabel#Caption { color: #8fa0b5; font-size: 10px; font-weight: 700; }
QLabel#Value { color: #f8fafc; font-size: 13px; font-weight: 800; }
QLabel#Status {
    background: #132033; color: #9fb0c5; border: 1px solid #34445b;
    border-radius: 5px; padding: 7px 11px; font-weight: 800;
}
QLabel#Status[state="armed"] { background: #3b2b0c; color: #fcd34d; border-color: #a16207; }
QLabel#Status[state="running"] { background: #0f3328; color: #6ee7b7; border-color: #15745b; }
QPushButton {
    background: #1a2638; color: #e5edf7; border: 1px solid #3a4a61;
    border-radius: 5px; padding: 7px 10px; font-weight: 700;
}
QPushButton:hover { background: #22334c; border-color: #59708f; }
QPushButton:disabled { background: #121a26; color: #59687b; border-color: #273345; }
QPushButton#Primary { background: #2563eb; border-color: #3b82f6; color: white; }
QPushButton#Primary:disabled { background: #121a26; color: #59687b; border-color: #273345; }
QPushButton#Arm { background: #b45309; border-color: #d97706; color: white; }
QPushButton#Arm[armed="true"] { background: #7f1d1d; border-color: #dc2626; }
QPushButton#Stop { background: #b91c1c; border-color: #dc2626; color: white; }
QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {
    background: #0c131e; color: #e5edf7; border: 1px solid #3a4a61;
    border-radius: 5px; padding: 5px 7px; min-height: 24px;
}
QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus { border-color: #3b82f6; }
QComboBox QAbstractItemView, QListWidget, QTableWidget {
    background: #0c131e; color: #e5edf7; border: 1px solid #3a4a61;
    selection-background-color: #1d4ed8; selection-color: white;
}
QListWidget::item { padding: 6px; }
QHeaderView::section { background: #1a2638; color: #aebed1; border: 0; padding: 5px; }
QCheckBox { color: #cbd5e1; spacing: 7px; }
QScrollArea { border: 0; background: transparent; }
QWidget#ScrollContent, QScrollArea QWidget#qt_scrollarea_viewport { background: #101721; }
"""


class PairCell(QWidget):
    """One wind pixel with independently colored front and back assignments."""

    clicked = pyqtSignal(int, int)

    def __init__(self, row: int, col: int) -> None:
        super().__init__()
        self.row = row
        self.col = col
        self.front_color: str | None = None
        self.back_color: str | None = None
        self.front_pwm = PWM_IDLE
        self.back_pwm = PWM_IDLE
        self.selected = False
        self.controller_focus = False
        self.setMinimumSize(74, 66)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        address = CoaxialAddress(row, col, 0)
        self.setToolTip(f"{address.pair_label} / R{row + 1}C{col + 1}")

    def set_state(
        self,
        front_color: str | None,
        back_color: str | None,
        front_pwm: int,
        back_pwm: int,
        selected: bool,
        controller_focus: bool,
    ) -> None:
        state = (front_color, back_color, front_pwm, back_pwm, selected, controller_focus)
        current = (
            self.front_color,
            self.back_color,
            self.front_pwm,
            self.back_pwm,
            self.selected,
            self.controller_focus,
        )
        if state != current:
            (
                self.front_color,
                self.back_color,
                self.front_pwm,
                self.back_pwm,
                self.selected,
                self.controller_focus,
            ) = state
            self.update()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.row, self.col)
        super().mousePressEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)
        border = "#3b82f6" if self.selected else "#34445b"
        if self.controller_focus and not self.selected:
            border = "#a78bfa"
        painter.setPen(QPen(QColor(border), 2 if self.selected else 1))
        painter.setBrush(QColor("#0c131e"))
        painter.drawRoundedRect(QRectF(rect), 5, 5)

        address = CoaxialAddress(self.row, self.col, 0)
        font = QFont(self.font())
        font.setPointSize(8)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor("#f8fafc"))
        painter.drawText(6, 15, address.pair_label)
        painter.setPen(QColor("#8292a8"))
        painter.drawText(rect.width() - 34, 15, f"R{self.row + 1}C{self.col + 1}")

        self._draw_layer(painter, 6, 23, rect.width() - 10, 16, "F", self.front_color, self.front_pwm)
        self._draw_layer(painter, 6, 43, rect.width() - 10, 16, "B", self.back_color, self.back_pwm)

    def _draw_layer(
        self,
        painter: QPainter,
        x: int,
        y: int,
        width: int,
        height: int,
        label: str,
        color: str | None,
        pwm: int,
    ) -> None:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(color or "#253246"))
        painter.drawRoundedRect(QRectF(x, y, width, height), 3, 3)
        font = QFont(self.font())
        font.setPointSize(7)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor("#ffffff" if color else "#91a0b5"))
        painter.drawText(x + 4, y + 12, label)
        painter.drawText(x + width - 31, y + 12, str(pwm))


class SignalPlot(QWidget):
    """Small dependency-free oscilloscope used for preview and live PWM."""

    def __init__(self) -> None:
        super().__init__()
        self.points: list[tuple[float, int]] = []
        self.output_max = PWM_UI_MAX
        self.setMinimumHeight(150)

    def set_points(self, points: list[tuple[float, int]], output_max: int) -> None:
        self.points = points
        self.output_max = max(PWM_IDLE + 1, output_max)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(48, 12, -15, -28)
        painter.fillRect(self.rect(), QColor("#0c131e"))
        painter.setPen(QPen(QColor("#26354a"), 1))
        for index in range(5):
            y = rect.top() + index * rect.height() / 4
            painter.drawLine(rect.left(), int(y), rect.right(), int(y))
        painter.setPen(QColor("#8292a8"))
        painter.drawText(5, rect.top() + 5, str(self.output_max))
        painter.drawText(5, rect.bottom(), str(PWM_IDLE))
        if len(self.points) < 2:
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "No signal data")
            return
        t_min = self.points[0][0]
        t_max = max(t_min + 0.001, self.points[-1][0])
        path_points = []
        for sample_time, pwm in self.points:
            x = rect.left() + (sample_time - t_min) / (t_max - t_min) * rect.width()
            ratio = (pwm - PWM_IDLE) / (self.output_max - PWM_IDLE)
            y = rect.bottom() - max(0.0, min(1.0, ratio)) * rect.height()
            path_points.append((int(x), int(y)))
        painter.setPen(QPen(QColor("#22d3ee"), 2))
        for first, second in zip(path_points, path_points[1:]):
            painter.drawLine(first[0], first[1], second[0], second[1])
        painter.setPen(QColor("#8292a8"))
        painter.drawText(rect.left(), self.height() - 8, f"{t_min:.1f} s")
        painter.drawText(rect.right() - 38, self.height() - 8, f"{t_max:.1f} s")


class CoaxialWindwallWindow(QMainWindow):
    """8x8x2 extrapolation of the original German group/signal GUI."""

    def __init__(self, *, use_mock: bool | None = None) -> None:
        super().__init__()
        self.setWindowTitle("Coaxial 8x8x2 Windwall - German Control Model")
        self.resize(1480, 920)

        if use_mock is None:
            use_mock = DEFAULT_HARDWARE_MODE != "real"
        self.hardware = HardwareInterface(use_mock=use_mock)
        self.groups: list[SignalGroup] = []
        self.motor_owner: list[int | None] = [None] * NUM_MOTORS
        self.current_pwm = [PWM_IDLE] * NUM_MOTORS
        self.selected_row = 0
        self.selected_col = 0
        self.is_armed = False
        self.experiment_running = False
        self.experiment_started_s: float | None = None
        self.last_elapsed_s = 0.0
        self.monitor_samples: deque[tuple[float, int]] = deque(maxlen=300)
        self.cells: dict[tuple[int, int], PairCell] = {}
        self.loading_controls = False

        self.command_timer = QTimer(self)
        self.command_timer.setInterval(max(1, int(1000 / COMMAND_RATE_HZ)))
        self.command_timer.timeout.connect(self.command_tick)
        self.ui_timer = QTimer(self)
        self.ui_timer.setInterval(100)
        self.ui_timer.timeout.connect(self.refresh_runtime)
        self.ui_timer.start()

        self.setStyleSheet(APP_STYLESHEET)
        self.setCentralWidget(self.build_ui())
        self.stop_shortcut = QShortcut(QKeySequence("Escape"), self)
        self.stop_shortcut.activated.connect(self.emergency_stop)

        if not self.load_session():
            self.add_group("Group 1")
        self.refresh_group_list()
        self.group_list.setCurrentRow(0)
        self.load_selected_group()
        self.refresh_all()

    @property
    def selected_group_index(self) -> int:
        return self.group_list.currentRow() if hasattr(self, "group_list") else -1

    def selected_group(self) -> SignalGroup | None:
        index = self.selected_group_index
        return self.groups[index] if 0 <= index < len(self.groups) else None

    def build_ui(self) -> QWidget:
        root = QWidget()
        root.setObjectName("AppRoot")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        layout.addWidget(self.build_top_bar())

        body = QHBoxLayout()
        body.setSpacing(10)
        body.addWidget(self.build_group_signal_panel())
        body.addWidget(self.build_wall_panel(), 1)
        body.addWidget(self.build_experiment_panel())
        layout.addLayout(body, 1)
        layout.addWidget(self.build_monitor_panel())
        return root

    def build_top_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("TopBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 9, 14, 9)
        titles = QVBoxLayout()
        title = QLabel("Coaxial 8x8x2 Windwall")
        title.setObjectName("Title")
        subtitle = QLabel("German 6x6 control model / 64 wind pixels / 128 motors")
        subtitle.setObjectName("Subtitle")
        titles.addWidget(title)
        titles.addWidget(subtitle)
        layout.addLayout(titles)
        layout.addStretch(1)
        self.status_label = QLabel(f"DISARMED / {self.hardware.mode_name}")
        self.status_label.setObjectName("Status")
        layout.addWidget(self.status_label)
        self.timer_label = QLabel("00:00.0")
        self.timer_label.setObjectName("Value")
        self.timer_label.setMinimumWidth(86)
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.timer_label)
        stop = QPushButton("EMERGENCY STOP")
        stop.setObjectName("Stop")
        stop.setToolTip("Stop, send idle, and disarm (Esc)")
        stop.clicked.connect(self.emergency_stop)
        layout.addWidget(stop)
        return bar

    def build_group_signal_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("Section")
        panel.setFixedWidth(320)
        outer = QVBoxLayout(panel)
        outer.setContentsMargins(11, 11, 11, 11)
        title = QLabel("Motor Groups & Signals")
        title.setObjectName("SectionTitle")
        outer.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content.setObjectName("ScrollContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 4, 4, 0)
        layout.setSpacing(8)

        self.group_list = QListWidget()
        self.group_list.setMaximumHeight(126)
        self.group_list.currentRowChanged.connect(self.load_selected_group)
        layout.addWidget(self.labeled("Groups", self.group_list))
        group_buttons = QHBoxLayout()
        add_button = QPushButton("Add")
        add_button.clicked.connect(self.add_group)
        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(self.delete_group)
        group_buttons.addWidget(add_button)
        group_buttons.addWidget(delete_button)
        layout.addLayout(group_buttons)

        self.group_name = QLineEdit()
        self.group_name.editingFinished.connect(self.rename_group)
        layout.addWidget(self.labeled("Group name", self.group_name))

        self.signal_type = QComboBox()
        self.signal_type.addItems(SIGNAL_TYPES)
        self.signal_type.currentTextChanged.connect(self.signal_controls_changed)
        layout.addWidget(self.labeled("Signal type", self.signal_type))

        amplitudes = QHBoxLayout()
        self.minimum = self.fraction_spin(0.25)
        self.maximum = self.fraction_spin(0.75)
        amplitudes.addWidget(self.labeled("Minimum", self.minimum))
        amplitudes.addWidget(self.labeled("Maximum", self.maximum))
        layout.addLayout(amplitudes)

        self.constant = self.fraction_spin(0.50)
        layout.addWidget(self.labeled("Constant value", self.constant))

        timing = QHBoxLayout()
        self.period = QDoubleSpinBox()
        self.period.setRange(0.1, 120.0)
        self.period.setDecimals(2)
        self.period.setValue(2.0)
        self.period.setSuffix(" s")
        self.period.valueChanged.connect(self.signal_controls_changed)
        self.phase = QDoubleSpinBox()
        self.phase.setRange(-120.0, 120.0)
        self.phase.setDecimals(2)
        self.phase.setSuffix(" s")
        self.phase.valueChanged.connect(self.signal_controls_changed)
        timing.addWidget(self.labeled("Period", self.period))
        timing.addWidget(self.labeled("Phase offset", self.phase))
        layout.addLayout(timing)

        self.duty = self.fraction_spin(0.50)
        layout.addWidget(self.labeled("Duty cycle", self.duty))

        self.harmonics = QTableWidget(0, 3)
        self.harmonics.setHorizontalHeaderLabels(["Harmonic", "Amplitude", "Phase deg"])
        self.harmonics.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.harmonics.setMaximumHeight(130)
        self.harmonics.itemChanged.connect(self.signal_controls_changed)
        layout.addWidget(self.labeled("Custom harmonics", self.harmonics))
        harmonic_buttons = QHBoxLayout()
        add_harmonic = QPushButton("Add harmonic")
        add_harmonic.clicked.connect(self.add_harmonic)
        remove_harmonic = QPushButton("Remove")
        remove_harmonic.clicked.connect(self.remove_harmonic)
        harmonic_buttons.addWidget(add_harmonic)
        harmonic_buttons.addWidget(remove_harmonic)
        layout.addLayout(harmonic_buttons)

        preset_buttons = QHBoxLayout()
        save_button = QPushButton("Save preset")
        save_button.clicked.connect(self.save_preset_as)
        load_button = QPushButton("Load preset")
        load_button.clicked.connect(self.load_preset_file)
        preset_buttons.addWidget(save_button)
        preset_buttons.addWidget(load_button)
        layout.addLayout(preset_buttons)
        layout.addStretch(1)
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)
        return panel

    def build_wall_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("Section")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(11, 11, 11, 11)
        header = QHBoxLayout()
        title = QLabel("Motor Grid 8x8x2")
        title.setObjectName("SectionTitle")
        header.addWidget(title)
        header.addStretch(1)
        self.assignment_scope = QComboBox()
        self.assignment_scope.addItems([ASSIGN_BOTH, ASSIGN_FRONT, ASSIGN_BACK])
        self.assignment_scope.setToolTip("Choose which layer a grid click assigns")
        header.addWidget(self.assignment_scope)
        self.controller_filter = QComboBox()
        self.controller_filter.addItem("All controllers", None)
        for index in range(CONTROLLER_COUNT):
            self.controller_filter.addItem(f"C{index + 1:02d}", index)
        self.controller_filter.currentIndexChanged.connect(self.refresh_wall)
        header.addWidget(self.controller_filter)
        layout.addLayout(header)

        caption = QLabel("Select a group, choose a layer scope, then click pixels to assign or remove motors")
        caption.setObjectName("Caption")
        caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(caption)

        grid = QGridLayout()
        grid.setSpacing(5)
        for row in range(GRID_ROWS):
            grid.setRowStretch(row, 1)
            for col in range(GRID_COLS):
                cell = PairCell(row, col)
                cell.clicked.connect(self.assign_pixel)
                self.cells[(row, col)] = cell
                grid.addWidget(cell, row, col)
        for col in range(GRID_COLS):
            grid.setColumnStretch(col, 1)
        layout.addLayout(grid, 1)

        buttons = QHBoxLayout()
        select_all = QPushButton("Assign all")
        select_all.clicked.connect(self.assign_all)
        clear_group = QPushButton("Clear selected group")
        clear_group.clicked.connect(self.clear_selected_group)
        clear_wall = QPushButton("Clear wall")
        clear_wall.clicked.connect(self.clear_wall)
        buttons.addWidget(select_all)
        buttons.addWidget(clear_group)
        buttons.addWidget(clear_wall)
        layout.addLayout(buttons)
        return panel

    def build_experiment_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("Section")
        panel.setFixedWidth(275)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(11, 11, 11, 11)
        title = QLabel("Experiment Control")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        self.duration = QSpinBox()
        self.duration.setRange(1, 3600)
        self.duration.setValue(10)
        self.duration.setSuffix(" s")
        layout.addWidget(self.labeled("Duration", self.duration))
        self.output_range = QComboBox()
        for label, minimum, maximum in PWM_RANGE_PRESETS:
            self.output_range.addItem(label, (minimum, maximum))
        self.output_range.setCurrentIndex(1)
        self.output_range.currentIndexChanged.connect(self.preview_selected_signal)
        layout.addWidget(self.labeled("Output ceiling", self.output_range))

        self.auto_disarm = QCheckBox("Auto-disarm after experiment")
        self.auto_disarm.setChecked(True)
        layout.addWidget(self.auto_disarm)

        self.arm_button = QPushButton("ARM MOTORS")
        self.arm_button.setObjectName("Arm")
        self.arm_button.clicked.connect(self.toggle_arm)
        layout.addWidget(self.arm_button)
        self.start_button = QPushButton("START EXPERIMENT")
        self.start_button.setObjectName("Primary")
        self.start_button.clicked.connect(self.start_experiment)
        layout.addWidget(self.start_button)
        self.stop_button = QPushButton("STOP EXPERIMENT")
        self.stop_button.clicked.connect(self.stop_experiment)
        layout.addWidget(self.stop_button)

        summary = QFrame()
        summary.setObjectName("Subsection")
        summary_layout = QGridLayout(summary)
        summary_layout.setContentsMargins(0, 10, 0, 0)
        self.active_total = self.summary_row(summary_layout, 0, "Assigned", "0 / 128")
        self.active_front = self.summary_row(summary_layout, 1, "Front", "0 / 64")
        self.active_back = self.summary_row(summary_layout, 2, "Back", "0 / 64")
        self.frame_count = self.summary_row(summary_layout, 3, "Frames sent", "0")
        self.average_pwm = self.summary_row(summary_layout, 4, "Average PWM", "1000 us")
        layout.addWidget(summary)

        selected = QFrame()
        selected.setObjectName("Subsection")
        selected_layout = QVBoxLayout(selected)
        selected_layout.setContentsMargins(0, 10, 0, 0)
        selected_title = QLabel("Selected Pair")
        selected_title.setObjectName("SectionTitle")
        selected_layout.addWidget(selected_title)
        self.selected_pair = QLabel()
        self.selected_pair.setObjectName("Value")
        self.selected_pair.setWordWrap(True)
        self.selected_pair.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        selected_layout.addWidget(self.selected_pair)
        layout.addWidget(selected)
        layout.addStretch(1)
        return panel

    def build_monitor_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("BottomBar")
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(11, 9, 11, 9)
        controls = QVBoxLayout()
        title = QLabel("Live Monitor")
        title.setObjectName("SectionTitle")
        controls.addWidget(title)
        self.monitor_mode = QComboBox()
        self.monitor_mode.addItems(["Selected front", "Selected back", "Selected group average", "Wall average"])
        self.monitor_mode.currentIndexChanged.connect(self.preview_selected_signal)
        controls.addWidget(self.labeled("Trace", self.monitor_mode))
        self.monitor_value = QLabel("1000 us")
        self.monitor_value.setObjectName("Value")
        controls.addWidget(self.monitor_value)
        controls.addStretch(1)
        layout.addLayout(controls)
        self.plot = SignalPlot()
        layout.addWidget(self.plot, 1)
        return panel

    def labeled(self, text: str, widget: QWidget) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        label = QLabel(text)
        label.setObjectName("Caption")
        layout.addWidget(label)
        layout.addWidget(widget)
        return container

    def summary_row(self, layout: QGridLayout, row: int, label_text: str, value_text: str) -> QLabel:
        label = QLabel(label_text)
        label.setObjectName("Caption")
        value = QLabel(value_text)
        value.setObjectName("Value")
        layout.addWidget(label, row, 0)
        layout.addWidget(value, row, 1, Qt.AlignmentFlag.AlignRight)
        return value

    def fraction_spin(self, value: float) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(0.0, 1.0)
        spin.setSingleStep(0.05)
        spin.setDecimals(2)
        spin.setValue(value)
        spin.valueChanged.connect(self.signal_controls_changed)
        return spin

    def add_group(self, name: str | None = None) -> None:
        if len(self.groups) >= len(GROUP_COLORS):
            QMessageBox.warning(self, "Group limit", f"A maximum of {len(GROUP_COLORS)} groups is supported.")
            return
        group_name = name or f"Group {len(self.groups) + 1}"
        self.groups.append(SignalGroup(group_name, GROUP_COLORS[len(self.groups)]))
        self.refresh_group_list()
        self.group_list.setCurrentRow(len(self.groups) - 1)
        self.save_session()

    def delete_group(self) -> None:
        index = self.selected_group_index
        if not 0 <= index < len(self.groups):
            return
        if len(self.groups) == 1:
            QMessageBox.warning(self, "Cannot delete", "At least one motor group must remain.")
            return
        self.groups.pop(index)
        for motor_index, owner in enumerate(self.motor_owner):
            if owner == index:
                self.motor_owner[motor_index] = None
            elif owner is not None and owner > index:
                self.motor_owner[motor_index] = owner - 1
        self.rebuild_group_members()
        self.refresh_group_list()
        self.group_list.setCurrentRow(min(index, len(self.groups) - 1))
        self.save_session()
        self.refresh_all()

    def refresh_group_list(self) -> None:
        if not hasattr(self, "group_list"):
            return
        current = self.group_list.currentRow()
        self.group_list.blockSignals(True)
        self.group_list.clear()
        for group in self.groups:
            item = QListWidgetItem(f"{group.name}   {len(group.motors)} motors")
            item.setForeground(QColor(group.color))
            self.group_list.addItem(item)
        self.group_list.blockSignals(False)
        if self.groups:
            self.group_list.setCurrentRow(max(0, min(current, len(self.groups) - 1)))

    def rename_group(self) -> None:
        group = self.selected_group()
        if group is None:
            return
        name = self.group_name.text().strip()
        if name:
            group.name = name
            self.refresh_group_list()
            self.save_session()

    def load_selected_group(self) -> None:
        group = self.selected_group()
        if group is None:
            return
        signal = group.signal.normalized()
        self.loading_controls = True
        self.group_name.setText(group.name)
        self.signal_type.setCurrentText(signal.signal_type)
        self.minimum.setValue(signal.minimum)
        self.maximum.setValue(signal.maximum)
        self.constant.setValue(signal.constant)
        self.period.setValue(signal.period_s)
        self.phase.setValue(signal.phase_s)
        self.duty.setValue(signal.duty_cycle)
        self.harmonics.setRowCount(0)
        for harmonic in signal.harmonics:
            self.append_harmonic_row(harmonic)
        self.loading_controls = False
        self.update_signal_control_visibility()
        self.preview_selected_signal()

    def signal_controls_changed(self) -> None:
        if self.loading_controls:
            return
        group = self.selected_group()
        if group is None:
            return
        minimum = self.minimum.value()
        maximum = self.maximum.value()
        if minimum > maximum:
            source = self.sender()
            if source is self.minimum:
                self.maximum.setValue(minimum)
            else:
                self.minimum.setValue(maximum)
            minimum = self.minimum.value()
            maximum = self.maximum.value()
        group.signal = GroupSignal(
            signal_type=self.signal_type.currentText(),
            minimum=minimum,
            maximum=maximum,
            constant=self.constant.value(),
            period_s=self.period.value(),
            phase_s=self.phase.value(),
            duty_cycle=self.duty.value(),
            harmonics=self.read_harmonics(),
        ).normalized()
        self.update_signal_control_visibility()
        self.preview_selected_signal()
        self.save_session()

    def update_signal_control_visibility(self) -> None:
        signal_type = self.signal_type.currentText()
        self.constant.parentWidget().setVisible(signal_type in (SIGNAL_CONSTANT, SIGNAL_CUSTOM))
        self.duty.parentWidget().setVisible(signal_type == SIGNAL_SQUARE)
        self.harmonics.parentWidget().setVisible(signal_type == SIGNAL_CUSTOM)

    def append_harmonic_row(self, harmonic: Harmonic) -> None:
        row = self.harmonics.rowCount()
        self.harmonics.insertRow(row)
        for col, value in enumerate((harmonic.number, harmonic.amplitude, harmonic.phase_deg)):
            self.harmonics.setItem(row, col, QTableWidgetItem(str(value)))

    def add_harmonic(self) -> None:
        self.loading_controls = True
        self.append_harmonic_row(Harmonic(number=self.harmonics.rowCount() + 1))
        self.loading_controls = False
        self.signal_controls_changed()

    def remove_harmonic(self) -> None:
        row = self.harmonics.currentRow()
        if row >= 0:
            self.harmonics.removeRow(row)
            self.signal_controls_changed()

    def read_harmonics(self) -> list[Harmonic]:
        harmonics = []
        for row in range(self.harmonics.rowCount()):
            try:
                number = int(float(self.harmonics.item(row, 0).text()))
                amplitude = float(self.harmonics.item(row, 1).text())
                phase = float(self.harmonics.item(row, 2).text())
            except (AttributeError, ValueError):
                continue
            harmonics.append(Harmonic(max(1, number), amplitude, phase))
        return harmonics

    def target_motor_indices(self, row: int, col: int) -> tuple[int, ...]:
        scope = self.assignment_scope.currentText()
        front = CoaxialAddress(row, col, 0).motor_index
        back = CoaxialAddress(row, col, 1).motor_index
        if scope == ASSIGN_FRONT:
            return (front,)
        if scope == ASSIGN_BACK:
            return (back,)
        return front, back

    def assign_pixel(self, row: int, col: int) -> None:
        if self.experiment_running:
            return
        group_index = self.selected_group_index
        if not 0 <= group_index < len(self.groups):
            return
        self.selected_row, self.selected_col = row, col
        targets = self.target_motor_indices(row, col)
        remove = all(self.motor_owner[index] == group_index for index in targets)
        for motor_index in targets:
            self.motor_owner[motor_index] = None if remove else group_index
        self.rebuild_group_members()
        self.refresh_group_list()
        self.group_list.setCurrentRow(group_index)
        self.save_session()
        self.refresh_all()

    def assign_all(self) -> None:
        group_index = self.selected_group_index
        if not 0 <= group_index < len(self.groups):
            return
        scope = self.assignment_scope.currentText()
        if scope in (ASSIGN_BOTH, ASSIGN_FRONT):
            for index in range(64):
                self.motor_owner[index] = group_index
        if scope in (ASSIGN_BOTH, ASSIGN_BACK):
            for index in range(64, 128):
                self.motor_owner[index] = group_index
        self.rebuild_group_members()
        self.refresh_group_list()
        self.group_list.setCurrentRow(group_index)
        self.save_session()
        self.refresh_all()

    def clear_selected_group(self) -> None:
        group_index = self.selected_group_index
        if group_index < 0:
            return
        self.motor_owner = [None if owner == group_index else owner for owner in self.motor_owner]
        self.rebuild_group_members()
        self.refresh_group_list()
        self.group_list.setCurrentRow(group_index)
        self.save_session()
        self.refresh_all()

    def clear_wall(self) -> None:
        if self.experiment_running:
            return
        self.motor_owner = [None] * NUM_MOTORS
        self.rebuild_group_members()
        self.refresh_group_list()
        self.save_session()
        self.refresh_all()

    def rebuild_group_members(self) -> None:
        for group in self.groups:
            group.motors.clear()
        for motor_index, owner in enumerate(self.motor_owner):
            if owner is not None and 0 <= owner < len(self.groups):
                self.groups[owner].motors.add(motor_index)

    def output_maximum(self) -> int:
        data = self.output_range.currentData()
        return int(data[1]) if data else PWM_UI_MAX

    def toggle_arm(self) -> None:
        if self.is_armed:
            self.disarm()
        else:
            self.arm()

    def arm(self) -> None:
        self.is_armed = True
        self.current_pwm = [PWM_IDLE] * NUM_MOTORS
        self.hardware.send_pwm_frame(self.current_pwm, output_armed=True)
        self.refresh_all()

    def disarm(self) -> None:
        if self.experiment_running:
            self.command_timer.stop()
            self.experiment_running = False
        self.is_armed = False
        self.current_pwm = [PWM_IDLE] * NUM_MOTORS
        self.hardware.send_pwm_frame(self.current_pwm, output_armed=False)
        self.refresh_all()

    def start_experiment(self) -> None:
        if not self.is_armed or self.experiment_running:
            return
        if not any(owner is not None for owner in self.motor_owner):
            QMessageBox.warning(self, "No motors assigned", "Assign at least one motor to a group before starting.")
            return
        self.experiment_running = True
        self.experiment_started_s = time.monotonic()
        self.last_elapsed_s = 0.0
        self.monitor_samples.clear()
        self.command_timer.start()
        self.command_tick()
        self.refresh_all()

    def stop_experiment(self) -> None:
        if self.experiment_running and self.experiment_started_s is not None:
            self.last_elapsed_s = time.monotonic() - self.experiment_started_s
        self.command_timer.stop()
        self.experiment_running = False
        self.current_pwm = [PWM_IDLE] * NUM_MOTORS
        if self.auto_disarm.isChecked():
            self.is_armed = False
        self.hardware.send_pwm_frame(self.current_pwm, output_armed=self.is_armed)
        self.refresh_all()

    def emergency_stop(self) -> None:
        if self.experiment_running and self.experiment_started_s is not None:
            self.last_elapsed_s = time.monotonic() - self.experiment_started_s
        self.command_timer.stop()
        self.experiment_running = False
        self.is_armed = False
        self.current_pwm = [PWM_IDLE] * NUM_MOTORS
        self.hardware.send_pwm_frame(self.current_pwm, output_armed=False)
        self.refresh_all()

    def elapsed_s(self) -> float:
        if self.experiment_running and self.experiment_started_s is not None:
            return time.monotonic() - self.experiment_started_s
        return self.last_elapsed_s

    def command_tick(self) -> None:
        if not self.experiment_running or not self.is_armed:
            return
        elapsed = self.elapsed_s()
        if elapsed >= self.duration.value():
            self.stop_experiment()
            return
        self.current_pwm = build_group_frame(self.groups, elapsed, self.output_maximum())
        self.hardware.send_pwm_frame(self.current_pwm, output_armed=True)
        self.capture_monitor(elapsed)
        self.refresh_wall()

    def monitored_pwm(self) -> int:
        mode = self.monitor_mode.currentText()
        if mode == "Selected front":
            index = CoaxialAddress(self.selected_row, self.selected_col, 0).motor_index
            return self.current_pwm[index]
        if mode == "Selected back":
            index = CoaxialAddress(self.selected_row, self.selected_col, 1).motor_index
            return self.current_pwm[index]
        if mode == "Selected group average":
            group = self.selected_group()
            if group and group.motors:
                return int(round(mean(self.current_pwm[index] for index in group.motors)))
            return PWM_IDLE
        return int(round(mean(self.current_pwm)))

    def capture_monitor(self, elapsed: float) -> None:
        self.monitor_samples.append((elapsed, self.monitored_pwm()))

    def preview_selected_signal(self) -> None:
        if not hasattr(self, "plot") or self.experiment_running:
            return
        group = self.selected_group()
        if group is None:
            self.plot.set_points([], self.output_maximum())
            return
        duration = max(group.signal.period_s * 2.0, 2.0)
        self.plot.set_points(preview_signal(group.signal, duration, 160, self.output_maximum()), self.output_maximum())

    def refresh_runtime(self) -> None:
        elapsed = self.elapsed_s()
        minutes, seconds = divmod(elapsed, 60)
        self.timer_label.setText(f"{int(minutes):02d}:{seconds:04.1f}")
        if self.experiment_running:
            self.plot.set_points(list(self.monitor_samples), self.output_maximum())
        self.monitor_value.setText(f"{self.monitored_pwm()} us")
        self.refresh_summary()

    def refresh_all(self) -> None:
        self.refresh_status()
        self.refresh_wall()
        self.refresh_summary()
        self.preview_selected_signal()

    def refresh_status(self) -> None:
        if self.experiment_running:
            text = f"RUNNING / {self.hardware.mode_name}"
            status_style = "background:#0f3328;color:#6ee7b7;border:1px solid #15745b;"
        elif self.is_armed:
            text = f"ARMED / {self.hardware.mode_name}"
            status_style = "background:#3b2b0c;color:#fcd34d;border:1px solid #a16207;"
        else:
            text = f"DISARMED / {self.hardware.mode_name}"
            status_style = "background:#132033;color:#9fb0c5;border:1px solid #34445b;"
        self.status_label.setText(text)
        self.status_label.setStyleSheet(
            status_style + "border-radius:5px;padding:7px 11px;font-weight:800;"
        )
        self.arm_button.setText("DISARM" if self.is_armed else "ARM MOTORS")
        self.arm_button.setStyleSheet(
            "background:#991b1b;border:1px solid #dc2626;color:white;"
            if self.is_armed
            else "background:#b45309;border:1px solid #d97706;color:white;"
        )
        self.arm_button.setEnabled(not self.experiment_running)
        self.start_button.setEnabled(self.is_armed and not self.experiment_running)
        self.stop_button.setEnabled(self.experiment_running)

    def refresh_wall(self) -> None:
        focused = self.controller_filter.currentData() if hasattr(self, "controller_filter") else None
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                front = CoaxialAddress(row, col, 0)
                back = CoaxialAddress(row, col, 1)
                front_owner = self.motor_owner[front.motor_index]
                back_owner = self.motor_owner[back.motor_index]
                front_color = self.groups[front_owner].color if front_owner is not None else None
                back_color = self.groups[back_owner].color if back_owner is not None else None
                controller_focus = focused is not None and (
                    front.controller_index == focused or back.controller_index == focused
                )
                self.cells[(row, col)].set_state(
                    front_color,
                    back_color,
                    self.current_pwm[front.motor_index],
                    self.current_pwm[back.motor_index],
                    row == self.selected_row and col == self.selected_col,
                    controller_focus,
                )
        front = CoaxialAddress(self.selected_row, self.selected_col, 0)
        back = CoaxialAddress(self.selected_row, self.selected_col, 1)
        self.selected_pair.setText(
            f"{front.pair_label} / R{front.row + 1}C{front.col + 1}\n"
            f"{front.label}: {front.controller_label} {front.controller_channel_label} / {self.current_pwm[front.motor_index]} us\n"
            f"{back.label}: {back.controller_label} {back.controller_channel_label} / {self.current_pwm[back.motor_index]} us"
        )

    def refresh_summary(self) -> None:
        if not hasattr(self, "active_total"):
            return
        assigned_front = sum(owner is not None for owner in self.motor_owner[:64])
        assigned_back = sum(owner is not None for owner in self.motor_owner[64:])
        self.active_total.setText(f"{assigned_front + assigned_back} / 128")
        self.active_front.setText(f"{assigned_front} / 64")
        self.active_back.setText(f"{assigned_back} / 64")
        self.frame_count.setText(str(self.hardware.frame_count))
        self.average_pwm.setText(f"{mean(self.current_pwm):.0f} us")

    def session_data(self) -> dict:
        return {
            "schema": 3,
            "foundation": "german-6x6-group-signal-model",
            "groups": [group.to_dict() for group in self.groups],
            "motor_owner": self.motor_owner,
        }

    def apply_session_data(self, data: dict) -> bool:
        schema = data.get("schema")
        if schema not in (2, 3) or not isinstance(data.get("groups"), list):
            return False
        groups = [
            SignalGroup.from_dict(item, GROUP_COLORS[index % len(GROUP_COLORS)])
            for index, item in enumerate(data["groups"][: len(GROUP_COLORS)])
            if isinstance(item, dict)
        ]
        if not groups:
            return False
        owners = data.get("motor_owner", [])
        if schema == 2 and len(owners) == NUM_MOTORS:
            migrated: list[int | None] = [None] * NUM_MOTORS
            for row in range(GRID_ROWS):
                for col in range(GRID_COLS):
                    old_pixel_index = row * GRID_COLS + col
                    new_pixel_index = CoaxialAddress(row, col, 0).pixel_index
                    for layer in range(2):
                        migrated[layer * 64 + new_pixel_index] = owners[
                            layer * 64 + old_pixel_index
                        ]
            owners = migrated
        if len(owners) != NUM_MOTORS:
            owners = [None] * NUM_MOTORS
            for group_index, group in enumerate(groups):
                for motor_index in group.motors:
                    owners[motor_index] = group_index
        self.groups = groups
        self.motor_owner = [
            int(owner) if owner is not None and 0 <= int(owner) < len(groups) else None
            for owner in owners
        ]
        self.rebuild_group_members()
        return True

    def load_session(self) -> bool:
        if not GUI_PRESETS_PATH.exists():
            return False
        try:
            data = json.loads(GUI_PRESETS_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False
        return self.apply_session_data(data)

    def save_session(self) -> None:
        if not self.groups:
            return
        try:
            GUI_PRESETS_PATH.parent.mkdir(parents=True, exist_ok=True)
            temporary = GUI_PRESETS_PATH.with_suffix(".tmp")
            temporary.write_text(json.dumps(self.session_data(), indent=2), encoding="utf-8")
            temporary.replace(GUI_PRESETS_PATH)
        except OSError as exc:
            print(f"Could not save GUI session: {exc}", file=sys.stderr)

    def save_preset_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save windwall preset", "", "JSON preset (*.json)")
        if not path:
            return
        if not path.lower().endswith(".json"):
            path += ".json"
        try:
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(self.session_data(), handle, indent=2)
        except OSError as exc:
            QMessageBox.critical(self, "Save failed", str(exc))

    def load_preset_file(self) -> None:
        if self.experiment_running:
            return
        path, _ = QFileDialog.getOpenFileName(self, "Load windwall preset", "", "JSON preset (*.json)")
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            QMessageBox.critical(self, "Load failed", str(exc))
            return
        if not self.apply_session_data(data):
            QMessageBox.warning(self, "Unsupported preset", "This is not a German-derived coaxial preset.")
            return
        self.refresh_group_list()
        self.group_list.setCurrentRow(0)
        self.load_selected_group()
        self.save_session()
        self.refresh_all()

    def closeEvent(self, event) -> None:  # noqa: N802
        self.command_timer.stop()
        self.ui_timer.stop()
        self.save_session()
        self.is_armed = False
        self.hardware.shutdown()
        event.accept()


def run_app(smoke_test_ms: int = 0, *, use_mock: bool | None = None) -> int:
    app = QApplication(sys.argv[:1])
    app.setFont(QFont("Arial", 9))
    window = CoaxialWindwallWindow(use_mock=use_mock)
    window.show()
    if smoke_test_ms:
        QTimer.singleShot(smoke_test_ms, app.quit)
    return app.exec()
