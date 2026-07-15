#!/usr/bin/env python3
"""
Enhanced GUI Interface for Active Wind Wall Control System.
Features: Multiple groups, live monitoring, custom Fourier signals.
"""

import sys
import math
import os
import platform
import threading
import time
from pathlib import Path
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
    QGridLayout, QGroupBox, QMessageBox, QListWidget, QSplitter,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QSizePolicy,
    QCheckBox, QTabWidget, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor
import pyqtgraph as pg
import multiprocessing
from collections import deque

from config import (
    BASE_FREQUENCY,
    NUM_MOTORS,
    PWM_MIN,
    PWM_MAX,
    GRID_ROWS,
    GRID_COLS,
    UPDATE_RATE_HZ,
    WALL_MOTOR_GRID,
    PWM_SPEED_PRESETS,
    PWM_TEST_PRESETS,
    ANEMOMETER_CALIBRATION_PRESETS,
    ANEMOMETER_CALIBRATION_DIR,
    TACH_ENABLED,
    TACH_POLL_HZ,
    TACH_PULSES_PER_REV,
)
from src.physics.signal_designer import generate_sine_wave, generate_square_pulse, generate_uniform
from src.core import MotorStateBuffer
from src.core.anemometer_calibration import (
    AnemometerSample,
    create_testo_correlation_result,
    filter_grid_by_row_col,
    summarize_anemometer_samples,
    write_calibration_workbook,
    write_testo_correlation_csv_bundle,
    write_testo_correlation_workbook,
)
from src.hardware import HardwareInterface


# Color palette for groups
GROUP_COLORS = [
    ("#14B8A6", "#0F766E"),  # Teal
    ("#3B82F6", "#1D4ED8"),  # Blue
    ("#EF4444", "#B91C1C"),  # Red
    ("#F59E0B", "#B45309"),  # Amber
    ("#8B5CF6", "#6D28D9"),  # Violet
    ("#06B6D4", "#0E7490"),  # Cyan
]

MAX_GUI_DURATION_S = 3600
DEFAULT_CONSTANT_PWM_US = 1600


APP_STYLESHEET = """
QMainWindow {
    background: #090f1a;
}
QWidget#AppRoot {
    background: #090f1a;
}
QFrame#TopBar {
    background: #111827;
    border: 1px solid #263244;
    border-radius: 8px;
}
QFrame#MetricCard {
    background: #0f172a;
    border: 1px solid #263244;
    border-radius: 8px;
}
QLabel#AppTitle {
    color: #f8fafc;
    font-size: 24px;
    font-weight: 800;
}
QLabel#AppSubtitle {
    color: #94a3b8;
    font-size: 12px;
}
QLabel#HeaderStatus {
    background: #0f2f2b;
    color: #5eead4;
    border: 1px solid #115e59;
    border-radius: 8px;
    padding: 8px 12px;
    font-weight: 800;
    letter-spacing: 1px;
}
QLabel#MetricLabel {
    color: #94a3b8;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1px;
}
QLabel#MetricValue {
    color: #e2e8f0;
    font-size: 16px;
    font-weight: 900;
}
QSplitter::handle {
    background: #1e293b;
    width: 2px;
    height: 2px;
}
QGroupBox {
    background: #111827;
    border: 1px solid #263244;
    border-radius: 8px;
    margin-top: 18px;
    padding: 14px 12px 12px 12px;
    font-weight: 800;
    color: #e2e8f0;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    color: #cbd5e1;
    background: #111827;
}
QLabel {
    color: #cbd5e1;
}
QLabel[role="caption"] {
    color: #94a3b8;
    font-size: 11px;
}
QCheckBox {
    color: #cbd5e1;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #334155;
    background: #0f172a;
}
QCheckBox::indicator:checked {
    background: #14b8a6;
    border: 1px solid #2dd4bf;
}
QComboBox, QSpinBox, QDoubleSpinBox {
    background: #0f172a;
    color: #e2e8f0;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 5px 8px;
    min-height: 28px;
}
QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover {
    border-color: #14b8a6;
}
QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #2dd4bf;
}
QComboBox QAbstractItemView {
    background: #0f172a;
    color: #e2e8f0;
    selection-background-color: #134e4a;
    selection-color: #ffffff;
    border: 1px solid #334155;
}
QPushButton {
    background: #1e293b;
    color: #e2e8f0;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px 12px;
    font-weight: 700;
}
QPushButton:hover {
    background: #273449;
    border-color: #475569;
}
QPushButton:pressed {
    background: #334155;
}
QPushButton:disabled {
    background: #111827;
    color: #64748b;
    border-color: #263244;
}
QPushButton#PrimaryButton {
    background: #14b8a6;
    color: #ffffff;
    border: 1px solid #0f9488;
    font-size: 15px;
}
QPushButton#PrimaryButton:hover {
    background: #0f9f91;
}
QPushButton#DangerButton {
    background: #ef4444;
    color: #ffffff;
    border: 1px solid #dc2626;
    font-size: 15px;
}
QPushButton#DangerButton:hover {
    background: #dc2626;
}
QTabWidget::pane {
    background: #111827;
    border: 1px solid #263244;
    border-radius: 8px;
    top: -1px;
}
QTabBar::tab {
    background: #0f172a;
    color: #94a3b8;
    border: 1px solid #263244;
    border-bottom: 0;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 7px 10px;
    font-weight: 800;
}
QTabBar::tab:selected {
    background: #111827;
    color: #5eead4;
}
QListWidget, QTableWidget {
    background: #0f172a;
    border: 1px solid #263244;
    border-radius: 6px;
    color: #e2e8f0;
    selection-background-color: #134e4a;
    selection-color: #ffffff;
}
QListWidget::item {
    border-radius: 6px;
    padding: 7px 8px;
    margin: 2px;
}
QListWidget::item:hover {
    background: #1e293b;
}
QHeaderView::section {
    background: #1e293b;
    color: #cbd5e1;
    border: 0;
    padding: 6px;
    font-weight: 700;
}
QFrame#LegendPanel {
    background: #0f172a;
    border: 1px solid #263244;
    border-radius: 8px;
}
QLabel#LegendTitle {
    color: #cbd5e1;
    font-weight: 800;
}
QScrollBar:vertical {
    background: #0f172a;
    width: 10px;
    margin: 0;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #334155;
    border-radius: 5px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""


STATUS_STYLES = {
    "ready": """
        QLabel {
            background-color: #0f172a;
            color: #93c5fd;
            border: 1px solid #1e3a8a;
            padding: 10px;
            border-radius: 8px;
            font-weight: 800;
        }
    """,
    "running": """
        QLabel {
            background-color: #0f2f2b;
            color: #5eead4;
            border: 1px solid #115e59;
            padding: 10px;
            border-radius: 8px;
            font-weight: 800;
        }
    """,
    "stopping": """
        QLabel {
            background-color: #342409;
            color: #fbbf24;
            border: 1px solid #92400e;
            padding: 10px;
            border-radius: 8px;
            font-weight: 800;
        }
    """,
    "error": """
        QLabel {
            background-color: #3f1218;
            color: #fca5a5;
            border: 1px solid #991b1b;
            padding: 10px;
            border-radius: 8px;
            font-weight: 800;
        }
    """,
}


def interpolate_color(start_hex, end_hex, fraction):
    """Interpolate between two hex colors."""
    fraction = max(0.0, min(1.0, float(fraction)))
    start = tuple(int(start_hex[i:i + 2], 16) for i in (1, 3, 5))
    end = tuple(int(end_hex[i:i + 2], 16) for i in (1, 3, 5))
    rgb = tuple(round(s + (e - s) * fraction) for s, e in zip(start, end))
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def pwm_to_color(pwm_value):
    """Return a WindControl-style heat color for a PWM value."""
    if not np.isfinite(pwm_value) or pwm_value <= 1050:
        return "#e5edf5", "#cbd5e1", "#475569"
    ratio = max(0.0, min(1.0, (float(pwm_value) - PWM_MIN) / (PWM_MAX - PWM_MIN)))
    if ratio < 0.45:
        color = interpolate_color("#ccfbf1", "#38bdf8", ratio / 0.45)
        return color, "#0ea5e9", "#083344"
    if ratio < 0.75:
        color = interpolate_color("#38bdf8", "#fbbf24", (ratio - 0.45) / 0.30)
        return color, "#d97706", "#1f2937"
    color = interpolate_color("#fbbf24", "#ef4444", (ratio - 0.75) / 0.25)
    return color, "#b91c1c", "#ffffff"


def telemetry_to_color(value, max_value, hot_color="#3b82f6"):
    """Return a color for tach telemetry values."""
    if not np.isfinite(value) or max_value <= 0:
        return "#e5edf5", "#cbd5e1", "#475569"
    ratio = max(0.0, min(1.0, float(value) / float(max_value)))
    if ratio < 0.5:
        color = interpolate_color("#dbeafe", hot_color, ratio / 0.5)
        return color, "#2563eb", "#082f49"
    color = interpolate_color(hot_color, "#f59e0b", (ratio - 0.5) / 0.5)
    return color, "#b45309", "#111827"


def add_soft_shadow(widget, blur=22, y_offset=8, alpha=30):
    """No-op on the Pi desktop; Qt shadow effects were too expensive."""
    return


def format_timer_seconds(seconds):
    """Format seconds as mm:ss or h:mm:ss for the run timer."""
    total_seconds = int(max(0, round(float(seconds))))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


class MotorGroup:
    """Represents a group of motors with shared signal configuration."""
    
    def __init__(self, name, color_index=0):
        self.name = name
        self.color_index = color_index
        self.motors = set()  # Set of motor IDs
        
        # Signal configuration
        self.signal_type = "Sine Wave"
        self.amp_min = 0.25
        self.amp_max = 0.75
        self.dc_value = 0.5  # For Constant DC mode
        self.constant_pwm_us = DEFAULT_CONSTANT_PWM_US
        self.period = 2.0
        self.phase_offset = 0.0  # Phase shift in seconds (for time-shifted on/off)
        self.fourier_terms = 7
        
        # Custom Fourier harmonics: [(harmonic_num, amplitude, phase_deg), ...]
        self.custom_harmonics = []
    
    def get_color(self):
        """Get the color tuple for this group."""
        return GROUP_COLORS[self.color_index % len(GROUP_COLORS)]


class MotorButton(QPushButton):
    """Custom button for motor selection with group support."""
    
    def __init__(self, motor_id, parent_gui):
        super().__init__(str(motor_id + 1))
        self.motor_id = motor_id
        self.parent_gui = parent_gui
        self.assigned_group = None
        self.setFixedSize(50, 50)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(f"Motor {motor_id + 1}")
        self.update_style()
        self.clicked.connect(self.on_click)
    
    def on_click(self):
        """Handle motor button click - assign to selected group."""
        selected_group = self.parent_gui.get_selected_group()
        if selected_group:
            if self.assigned_group == selected_group:
                # Unassign if already in this group
                selected_group.motors.discard(self.motor_id)
                self.assigned_group = None
            else:
                # Remove from old group if assigned
                if self.assigned_group:
                    self.assigned_group.motors.discard(self.motor_id)
                # Assign to new group
                selected_group.motors.add(self.motor_id)
                self.assigned_group = selected_group
            self.update_style()
            self.parent_gui.update_group_list_labels()
            self.parent_gui.refresh_header_metrics()
    
    def update_style(self):
        """Update button appearance based on group assignment."""
        self.setText(str(self.motor_id + 1))
        if self.assigned_group:
            bg_color, border_color = self.assigned_group.get_color()
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg_color};
                    color: white;
                    border: 2px solid {border_color};
                    border-radius: 8px;
                    font-weight: 800;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    border: 2px solid #111827;
                }}
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #0f172a;
                    color: #64748b;
                    border: 1px solid #263244;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background-color: #1e293b;
                    border: 1px solid #475569;
                }
            """)

    def set_live_value(self, value, mode, max_value=None):
        """Render this motor as a live wind-pixel heat cell."""
        if mode == "PWM":
            fill, border, text_color = pwm_to_color(value)
            label = f"{self.motor_id + 1}\n{int(value) if np.isfinite(value) else '--'}"
            tip = f"Motor {self.motor_id + 1}: {int(value) if np.isfinite(value) else '--'} us"
        else:
            fill, border, text_color = telemetry_to_color(value, max_value or 0.0)
            label = f"{self.motor_id + 1}\n{value:.0f}" if np.isfinite(value) else f"{self.motor_id + 1}\n--"
            unit = "Hz" if mode == "Tach Hz" else "RPM"
            tip = f"Motor {self.motor_id + 1}: {value:.1f} {unit}" if np.isfinite(value) else f"Motor {self.motor_id + 1}: no tach"

        self.setText(label)
        self.setToolTip(tip)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {fill};
                color: {text_color};
                border: 2px solid {border};
                border-radius: 8px;
                font-size: 11px;
                font-weight: 900;
                line-height: 1.0;
            }}
            QPushButton:hover {{
                border: 2px solid #111827;
            }}
        """)

    def set_scalar_value(self, value, unit, max_value=None):
        """Render this motor with an imported scalar heatmap value."""
        fill, border, text_color = telemetry_to_color(value, max_value or 0.0, hot_color="#14b8a6")
        label = f"{self.motor_id + 1}\n{value:.1f}" if np.isfinite(value) else f"{self.motor_id + 1}\n--"
        tip = f"Motor {self.motor_id + 1}: {value:.2f} {unit}" if np.isfinite(value) else f"Motor {self.motor_id + 1}: no imported value"
        self.setText(label)
        self.setToolTip(tip)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {fill};
                color: {text_color};
                border: 2px solid {border};
                border-radius: 8px;
                font-size: 11px;
                font-weight: 900;
                line-height: 1.0;
            }}
            QPushButton:hover {{
                border: 2px solid #111827;
            }}
        """)


class CsvDropLabel(QLabel):
    """Drop target for Testo CSV imports."""

    def __init__(self, parent_gui):
        super().__init__("Drop R#C#.csv files")
        self.parent_gui = parent_gui
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(58)
        self.setStyleSheet("""
            QLabel {
                background: #0f172a;
                border: 1px dashed #475569;
                border-radius: 8px;
                padding: 12px;
                color: #cbd5e1;
                font-weight: 800;
            }
        """)

    def dragEnterEvent(self, event):
        if any(url.toLocalFile().lower().endswith(".csv") for url in event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if url.toLocalFile().lower().endswith(".csv")
        ]
        if paths:
            self.parent_gui.import_testo_files(paths)
            event.acceptProposedAction()


class WindWallGUI(QMainWindow):
    """Main GUI window for Active Wind Wall control."""

    bench_status_signal = pyqtSignal(str, str)
    bench_test_finished_signal = pyqtSignal(str, bool)
    calibration_status_signal = pyqtSignal(str, str)
    calibration_finished_signal = pyqtSignal(str, bool, object)
    
    def __init__(self):
        super().__init__()
        self.groups = []
        self.selected_group_index = -1
        self.motor_buttons = [None] * NUM_MOTORS
        self.experiment_running = False
        self.flight_process = None
        self.stop_event = None
        self.shared_buffer = None
        
        # Live monitoring - oscilloscope style
        self.monitor_data_time = deque(maxlen=200)  # 5 seconds at 40Hz
        self.monitor_data_value = deque(maxlen=200)
        self.monitor_timer = None
        self.run_timer = None
        self.run_timer_started_at = None
        self.run_timer_duration_s = 0.0
        self.live_wall_rendering = False
        self.grid_rows = GRID_ROWS
        self.grid_cols = GRID_COLS
        self.bench_test_running = False
        self.bench_test_thread = None
        self.bench_stop_event = None
        self.calibration_running = False
        self.calibration_thread = None
        self.calibration_stop_event = None
        self.last_calibration_result = None
        self.last_calibration_workbook = None
        self.flow_compensation_offsets = np.zeros(NUM_MOTORS, dtype=np.float64)
        self.testo_import_paths = []
        self.testo_result = None
        self.testo_workbook_path = None
        if self.grid_rows * self.grid_cols != NUM_MOTORS:
            # Fallback to a square/near-square grid if config values drift.
            self.grid_cols = max(1, int(math.sqrt(NUM_MOTORS)))
            self.grid_rows = math.ceil(NUM_MOTORS / self.grid_cols)
        self.experiment_start_time = None  # Set when experiment starts - never resets
        self.bench_status_signal.connect(self.set_bench_status)
        self.bench_test_finished_signal.connect(self.on_bench_test_finished)
        self.calibration_status_signal.connect(self.set_calibration_status)
        self.calibration_finished_signal.connect(self.on_anemometer_calibration_finished)
        self._loading_output_pwm_preset = False
        self._loading_bench_pwm_preset = False
        self._loading_constant_pwm_preset = False
        
        self.init_ui()
        
        # Create default group after UI is initialized
        self.add_group("Group 1")
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Active Wind Wall")
        self.setGeometry(35, 35, 1400, 900)
        self.setStyleSheet(APP_STYLESHEET)
        
        # Central widget with splitter
        central_widget = QWidget()
        central_widget.setObjectName("AppRoot")
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        header = self.create_header()
        main_layout.addWidget(header)
        
        # Top section - Configuration and Grid
        top_splitter = QSplitter(Qt.Orientation.Horizontal)
        top_splitter.setChildrenCollapsible(False)
        
        # Left panel - Groups and signal configuration
        left_panel = self.create_left_panel()
        top_splitter.addWidget(left_panel)
        
        # Center panel - Motor grid
        grid_panel = self.create_grid_panel()
        top_splitter.addWidget(grid_panel)
        
        # Right panel - Controls
        control_panel = self.create_control_panel()
        top_splitter.addWidget(control_panel)
        
        top_splitter.setStretchFactor(0, 1)
        top_splitter.setStretchFactor(1, 3)
        top_splitter.setStretchFactor(2, 1)
        
        main_layout.addWidget(top_splitter, stretch=2)
        
        # Bottom section - Live monitoring
        monitor_panel = self.create_monitor_panel()
        main_layout.addWidget(monitor_panel, stretch=1)
        self.refresh_header_metrics()

    def create_header(self):
        """Create the WindControl-style top command bar."""
        frame = QFrame()
        frame.setObjectName("TopBar")
        add_soft_shadow(frame, blur=18, y_offset=4, alpha=22)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(12)

        title_block = QVBoxLayout()
        title_block.setSpacing(2)

        title = QLabel("Active Wind Wall")
        title.setObjectName("AppTitle")
        title_block.addWidget(title)

        subtitle = QLabel("64 wind pixels | PWM profiles | tach telemetry | live wall monitor")
        subtitle.setObjectName("AppSubtitle")
        title_block.addWidget(subtitle)

        layout.addLayout(title_block)
        layout.addStretch()

        self.header_pixel_value = self.create_metric_card(layout, "WIND PIXELS", str(NUM_MOTORS))
        self.header_active_value = self.create_metric_card(layout, "ACTIVE", "0")
        self.header_pwm_value = self.create_metric_card(layout, "PWM RANGE", f"{PWM_MIN}-{PWM_MAX}")
        self.header_telemetry_value = self.create_metric_card(layout, "TELEMETRY", "TACH")

        self.header_status_label = QLabel("READY")
        self.header_status_label.setObjectName("HeaderStatus")
        self.header_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.header_status_label)

        return frame

    def create_metric_card(self, parent_layout, label_text, value_text):
        """Add a compact metric card to the header."""
        card = QFrame()
        card.setObjectName("MetricCard")
        card.setFixedWidth(118)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(10, 7, 10, 7)
        card_layout.setSpacing(1)

        label = QLabel(label_text)
        label.setObjectName("MetricLabel")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(label)

        value = QLabel(value_text)
        value.setObjectName("MetricValue")
        value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(value)

        parent_layout.addWidget(card)
        return value
    
    def create_left_panel(self):
        """Create groups and signal configuration panel."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Groups section
        groups_box = QGroupBox("Motor Groups")
        add_soft_shadow(groups_box, blur=18, y_offset=5, alpha=18)
        groups_layout = QVBoxLayout()
        
        self.groups_list = QListWidget()
        self.groups_list.setMinimumHeight(110)
        self.groups_list.currentRowChanged.connect(self.on_group_selected)
        groups_layout.addWidget(self.groups_list)
        
        # Group buttons
        group_btn_layout = QHBoxLayout()
        add_group_btn = QPushButton("Add Group")
        add_group_btn.clicked.connect(self.add_group_clicked)
        delete_group_btn = QPushButton("Delete Group")
        delete_group_btn.clicked.connect(self.delete_group_clicked)
        group_btn_layout.addWidget(add_group_btn)
        group_btn_layout.addWidget(delete_group_btn)
        groups_layout.addLayout(group_btn_layout)
        
        groups_box.setLayout(groups_layout)
        layout.addWidget(groups_box)
        
        # Signal configuration
        config_box = QGroupBox("Signal Configuration")
        add_soft_shadow(config_box, blur=18, y_offset=5, alpha=18)
        config_layout = QVBoxLayout()
        config_layout.setSpacing(8)
        
        self.selected_group_label = QLabel("Selected: None")
        self.selected_group_label.setStyleSheet("font-weight: 800; color: #5eead4;")
        config_layout.addWidget(self.selected_group_label)
        
        config_layout.addWidget(QLabel("Signal Type:"))
        self.signal_type = QComboBox()
        self.signal_type.addItems(["Sine Wave", "Square Wave", "Constant DC", "Custom Fourier"])
        self.signal_type.currentTextChanged.connect(self.on_signal_type_changed)
        config_layout.addWidget(self.signal_type)
        
        # Standard signal parameters
        self.standard_params_widget = QWidget()
        standard_layout = QGridLayout(self.standard_params_widget)
        standard_layout.setContentsMargins(0, 0, 0, 0)
        standard_layout.setHorizontalSpacing(8)
        standard_layout.setVerticalSpacing(7)
        
        standard_layout.addWidget(QLabel("Min"), 0, 0)
        self.amp_min = QDoubleSpinBox()
        self.amp_min.setRange(0.0, 1.0)
        self.amp_min.setSingleStep(0.05)
        self.amp_min.setValue(0.25)
        self.amp_min.setDecimals(2)
        self.amp_min.valueChanged.connect(self.on_param_changed)
        standard_layout.addWidget(self.amp_min, 0, 1)
        
        standard_layout.addWidget(QLabel("Max"), 1, 0)
        self.amp_max = QDoubleSpinBox()
        self.amp_max.setRange(0.0, 1.0)
        self.amp_max.setSingleStep(0.05)
        self.amp_max.setValue(0.75)
        self.amp_max.setDecimals(2)
        self.amp_max.valueChanged.connect(self.on_param_changed)
        standard_layout.addWidget(self.amp_max, 1, 1)
        
        standard_layout.addWidget(QLabel("Period"), 2, 0)
        self.period = QDoubleSpinBox()
        self.period.setRange(0.1, 60.0)
        self.period.setSingleStep(0.5)
        self.period.setValue(2.0)
        self.period.setDecimals(1)
        self.period.valueChanged.connect(self.on_param_changed)
        standard_layout.addWidget(self.period, 2, 1)
        
        standard_layout.addWidget(QLabel("Terms"), 3, 0)
        self.fourier_terms = QSpinBox()
        self.fourier_terms.setRange(1, 20)
        self.fourier_terms.setValue(7)
        self.fourier_terms.valueChanged.connect(self.on_param_changed)
        standard_layout.addWidget(self.fourier_terms, 3, 1)
        
        config_layout.addWidget(self.standard_params_widget)
        
        # Direct constant PWM widget (only for Constant DC)
        self.dc_params_widget = QWidget()
        dc_layout = QGridLayout(self.dc_params_widget)
        dc_layout.setContentsMargins(0, 0, 0, 0)
        dc_layout.setHorizontalSpacing(8)
        dc_layout.setVerticalSpacing(7)
        
        dc_layout.addWidget(QLabel("PWM Preset"), 0, 0)
        self.constant_pwm_preset = QComboBox()
        for preset_name in PWM_TEST_PRESETS:
            self.constant_pwm_preset.addItem(preset_name)
        self.constant_pwm_preset.addItem("Custom")
        self.constant_pwm_preset.setCurrentText(f"{DEFAULT_CONSTANT_PWM_US} us")
        self.constant_pwm_preset.currentTextChanged.connect(self.on_constant_pwm_preset_changed)
        dc_layout.addWidget(self.constant_pwm_preset, 0, 1)

        dc_layout.addWidget(QLabel("PWM us"), 1, 0)
        self.constant_pwm_spinbox = QSpinBox()
        self.constant_pwm_spinbox.setRange(PWM_MIN, PWM_MAX)
        self.constant_pwm_spinbox.setSingleStep(10)
        self.constant_pwm_spinbox.setValue(DEFAULT_CONSTANT_PWM_US)
        self.constant_pwm_spinbox.setSuffix(" us")
        self.constant_pwm_spinbox.valueChanged.connect(self.on_constant_pwm_changed)
        dc_layout.addWidget(self.constant_pwm_spinbox, 1, 1)
        
        config_layout.addWidget(self.dc_params_widget)
        self.dc_params_widget.hide()
        
        # Custom Fourier parameters
        self.custom_params_widget = QWidget()
        custom_layout = QVBoxLayout(self.custom_params_widget)
        custom_layout.setContentsMargins(0, 0, 0, 0)
        
        custom_layout.addWidget(QLabel("Harmonics:"))
        self.harmonics_table = QTableWidget()
        self.harmonics_table.setColumnCount(3)
        self.harmonics_table.setHorizontalHeaderLabels(["#", "Amplitude", "Phase (°)"])
        self.harmonics_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.harmonics_table.setMaximumHeight(150)
        custom_layout.addWidget(self.harmonics_table)
        
        harmonic_btn_layout = QHBoxLayout()
        add_harmonic_btn = QPushButton("Add Harmonic")
        add_harmonic_btn.clicked.connect(self.add_harmonic)
        remove_harmonic_btn = QPushButton("Remove")
        remove_harmonic_btn.clicked.connect(self.remove_harmonic)
        harmonic_btn_layout.addWidget(add_harmonic_btn)
        harmonic_btn_layout.addWidget(remove_harmonic_btn)
        custom_layout.addLayout(harmonic_btn_layout)
        
        config_layout.addWidget(self.custom_params_widget)
        self.custom_params_widget.hide()
        
        config_box.setLayout(config_layout)
        layout.addWidget(config_box)
        
        layout.addStretch()
        
        return widget
    
    def create_grid_panel(self):
        """Create motor grid panel."""
        group = QGroupBox(f"Wind Pixel Wall ({self.grid_rows}x{self.grid_cols})")
        add_soft_shadow(group, blur=24, y_offset=7, alpha=22)
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        info_label = QLabel("Click wind pixels to assign them to the selected group")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setProperty("role", "caption")
        layout.addWidget(info_label)

        grid = QGridLayout()
        grid.setSpacing(7)
        
        for row, row_motors in enumerate(WALL_MOTOR_GRID):
            for col, motor_id in enumerate(row_motors):
                btn = MotorButton(motor_id, self)
                self.motor_buttons[motor_id] = btn
                grid.addWidget(btn, row, col)
        
        grid_shell = QHBoxLayout()
        grid_shell.setSpacing(14)
        grid_shell.addStretch()
        grid_shell.addLayout(grid)
        grid_shell.addWidget(self.create_pwm_legend())
        grid_shell.addStretch()
        layout.addLayout(grid_shell)
        
        # Selection controls
        btn_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all_motors)
        btn_layout.addWidget(select_all_btn)
        
        clear_all_btn = QPushButton("Clear All")
        clear_all_btn.clicked.connect(self.clear_all_motors)
        btn_layout.addWidget(clear_all_btn)
        
        layout.addLayout(btn_layout)
        
        group.setLayout(layout)
        return group

    def create_pwm_legend(self):
        """Create a compact heatmap legend beside the wall."""
        legend = QFrame()
        legend.setObjectName("LegendPanel")
        legend.setFixedWidth(112)
        layout = QVBoxLayout(legend)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        title = QLabel("PWM")
        title.setObjectName("LegendTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        self.wall_legend_title = title
        self.wall_legend_rows = []

        stops = [
            ("Idle", "#e5edf5"),
            ("1200", "#ccfbf1"),
            ("1500", "#7dd3fc"),
            ("1750", "#fbbf24"),
            ("2000", "#ef4444"),
        ]
        for label, color in stops:
            row = QFrame()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(6)

            swatch = QLabel()
            swatch.setFixedSize(18, 18)
            swatch.setStyleSheet(f"background: {color}; border: 1px solid #334155; border-radius: 4px;")
            row_layout.addWidget(swatch)

            text = QLabel(label)
            text.setProperty("role", "caption")
            row_layout.addWidget(text)
            layout.addWidget(row)
            self.wall_legend_rows.append((swatch, text))

        layout.addStretch()
        self.set_wall_legend_pwm()
        return legend

    def set_wall_legend_pwm(self):
        """Restore the side legend to the normal PWM scale."""
        if not hasattr(self, "wall_legend_rows"):
            return
        self.wall_legend_title.setText("PWM")
        stops = [
            ("Idle", "#e5edf5"),
            ("1200", "#ccfbf1"),
            ("1500", "#7dd3fc"),
            ("1750", "#fbbf24"),
            ("2000", "#ef4444"),
        ]
        for (swatch, text), (label, color) in zip(self.wall_legend_rows, stops):
            swatch.setStyleSheet(f"background: {color}; border: 1px solid #334155; border-radius: 4px;")
            text.setText(label)

    def set_wall_legend_testo(self, max_value):
        """Switch the side legend to imported Testo velocity values."""
        if not hasattr(self, "wall_legend_rows"):
            return
        self.wall_legend_title.setText("m/s")
        max_value = max(1.0, float(max_value))
        stops = []
        for ratio in (0.0, 0.25, 0.5, 0.75, 1.0):
            value = max_value * ratio
            fill, _, _ = telemetry_to_color(value, max_value, hot_color="#14b8a6")
            stops.append((f"{value:.1f}", fill))
        for (swatch, text), (label, color) in zip(self.wall_legend_rows, stops):
            swatch.setStyleSheet(f"background: {color}; border: 1px solid #334155; border-radius: 4px;")
            text.setText(label)
    
    def create_control_panel(self):
        """Create experiment control panel."""
        group = QGroupBox("Run Control")
        add_soft_shadow(group, blur=18, y_offset=5, alpha=18)
        layout = QVBoxLayout()
        layout.setSpacing(7)

        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.status_label, stretch=1)

        self.active_count_label = QLabel("0 active wind pixels")
        self.active_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.active_count_label.setStyleSheet("""
            QLabel {
                background: #0f172a;
                border: 1px solid #263244;
                border-radius: 8px;
                padding: 8px;
                font-weight: 800;
                color: #cbd5e1;
            }
        """)
        status_layout.addWidget(self.active_count_label, stretch=1)
        layout.addLayout(status_layout)

        self.run_timer_label = QLabel("Timer 00:00 / 00:00")
        self.run_timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.run_timer_label.setStyleSheet("""
            QLabel {
                background: #0f172a;
                border: 1px solid #263244;
                border-radius: 8px;
                padding: 8px;
                font-weight: 800;
                color: #cbd5e1;
            }
        """)
        layout.addWidget(self.run_timer_label)
        self.set_experiment_status("Ready", "ready")

        tabs = QTabWidget()

        run_tab = QWidget()
        run_layout = QGridLayout(run_tab)
        run_layout.setContentsMargins(10, 10, 10, 10)
        run_layout.setHorizontalSpacing(8)
        run_layout.setVerticalSpacing(8)

        run_layout.addWidget(QLabel("Duration"), 0, 0)
        self.duration = QSpinBox()
        self.duration.setRange(1, MAX_GUI_DURATION_S)
        self.duration.setSingleStep(60)
        self.duration.setSuffix(" s")
        self.duration.setValue(10)
        self.duration.setMinimumWidth(110)
        self.duration.valueChanged.connect(self.on_duration_changed)
        run_layout.addWidget(self.duration, 0, 1)

        run_layout.addWidget(QLabel("PWM Preset"), 1, 0)
        self.output_pwm_preset = QComboBox()
        for preset_name in PWM_SPEED_PRESETS:
            self.output_pwm_preset.addItem(preset_name)
        self.output_pwm_preset.addItem("Custom")
        self.output_pwm_preset.currentTextChanged.connect(self.on_output_pwm_preset_changed)
        run_layout.addWidget(self.output_pwm_preset, 1, 1)

        run_layout.addWidget(QLabel("PWM Min"), 2, 0)
        self.output_pwm_min = QSpinBox()
        self.output_pwm_min.setRange(PWM_MIN, PWM_MAX)
        self.output_pwm_min.setSingleStep(10)
        self.output_pwm_min.setValue(PWM_MIN)
        self.output_pwm_min.valueChanged.connect(self.on_output_pwm_range_changed)
        run_layout.addWidget(self.output_pwm_min, 2, 1)

        run_layout.addWidget(QLabel("PWM Max"), 3, 0)
        self.output_pwm_max = QSpinBox()
        self.output_pwm_max.setRange(PWM_MIN, PWM_MAX)
        self.output_pwm_max.setSingleStep(10)
        self.output_pwm_max.setValue(PWM_MAX)
        self.output_pwm_max.valueChanged.connect(self.on_output_pwm_range_changed)
        run_layout.addWidget(self.output_pwm_max, 3, 1)

        run_layout.addWidget(QLabel("Telemetry"), 4, 0)
        self.telemetry_mode = QComboBox()
        self.telemetry_mode.addItem("No Tach / Legacy")
        self.telemetry_mode.addItem("Tach Return")
        self.telemetry_mode.setCurrentText("Tach Return" if TACH_ENABLED else "No Tach / Legacy")
        self.telemetry_mode.currentTextChanged.connect(self.refresh_header_metrics)
        run_layout.addWidget(self.telemetry_mode, 4, 1)
        run_layout.setRowStretch(5, 1)
        tabs.addTab(run_tab, "Run")

        test_tab = QWidget()
        bench_layout = QGridLayout(test_tab)
        bench_layout.setContentsMargins(10, 10, 10, 10)
        bench_layout.setHorizontalSpacing(8)
        bench_layout.setVerticalSpacing(8)

        bench_layout.addWidget(QLabel("Motor"), 0, 0)
        self.bench_motor_select = QComboBox()
        for i in range(NUM_MOTORS):
            self.bench_motor_select.addItem(f"Motor {i + 1}")
        self.bench_motor_select.setCurrentIndex(33)
        bench_layout.addWidget(self.bench_motor_select, 0, 1)

        bench_layout.addWidget(QLabel("PWM Preset"), 1, 0)
        self.bench_pwm_preset = QComboBox()
        for preset_name in PWM_TEST_PRESETS:
            self.bench_pwm_preset.addItem(preset_name)
        self.bench_pwm_preset.addItem("Custom")
        self.bench_pwm_preset.setCurrentText("1600 us")
        self.bench_pwm_preset.currentTextChanged.connect(self.on_bench_pwm_preset_changed)
        bench_layout.addWidget(self.bench_pwm_preset, 1, 1)

        bench_layout.addWidget(QLabel("PWM"), 2, 0)
        self.bench_pwm = QSpinBox()
        self.bench_pwm.setRange(PWM_MIN, PWM_MAX)
        self.bench_pwm.setSingleStep(10)
        self.bench_pwm.setValue(1600)
        self.bench_pwm.valueChanged.connect(self.on_bench_pwm_changed)
        bench_layout.addWidget(self.bench_pwm, 2, 1)

        bench_layout.addWidget(QLabel("Duration"), 3, 0)
        self.bench_duration = QDoubleSpinBox()
        self.bench_duration.setRange(0.5, float(MAX_GUI_DURATION_S))
        self.bench_duration.setSingleStep(60.0)
        self.bench_duration.setValue(10.0)
        self.bench_duration.setDecimals(1)
        self.bench_duration.setSuffix(" s")
        self.bench_duration.setMinimumWidth(110)
        bench_layout.addWidget(self.bench_duration, 3, 1)

        self.bench_status_label = QLabel("Idle")
        self.bench_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bench_layout.addWidget(self.bench_status_label, 4, 0, 1, 2)

        bench_btn_layout = QHBoxLayout()
        self.bench_start_btn = QPushButton("Run Motor Test")
        self.bench_start_btn.setObjectName("PrimaryButton")
        self.bench_start_btn.clicked.connect(self.start_bench_test)
        bench_btn_layout.addWidget(self.bench_start_btn)

        self.bench_stop_btn = QPushButton("Stop Test")
        self.bench_stop_btn.setObjectName("DangerButton")
        self.bench_stop_btn.setEnabled(False)
        self.bench_stop_btn.clicked.connect(self.stop_bench_test)
        bench_btn_layout.addWidget(self.bench_stop_btn)
        bench_layout.addLayout(bench_btn_layout, 5, 0, 1, 2)
        bench_layout.setRowStretch(6, 1)
        tabs.addTab(test_tab, "Motor Test")
        self.set_bench_status("Idle")

        calibration_tab = QWidget()
        calibration_layout = QVBoxLayout(calibration_tab)
        calibration_layout.setContentsMargins(10, 10, 10, 10)
        calibration_layout.setSpacing(7)

        calibration_layout.addWidget(QLabel("Preset"))
        self.calibration_preset = QComboBox()
        for preset_name in ANEMOMETER_CALIBRATION_PRESETS:
            self.calibration_preset.addItem(preset_name)
        self.calibration_preset.currentTextChanged.connect(self.on_calibration_preset_changed)
        calibration_layout.addWidget(self.calibration_preset)

        calibration_grid = QGridLayout()
        calibration_grid.setHorizontalSpacing(8)
        calibration_grid.setVerticalSpacing(6)

        calibration_grid.addWidget(QLabel("PWM"), 0, 0)
        self.calibration_pwm = QSpinBox()
        self.calibration_pwm.setRange(PWM_MIN, PWM_MAX)
        self.calibration_pwm.setSingleStep(10)
        calibration_grid.addWidget(self.calibration_pwm, 0, 1)

        calibration_grid.addWidget(QLabel("Run"), 1, 0)
        self.calibration_duration = QDoubleSpinBox()
        self.calibration_duration.setRange(1.0, float(MAX_GUI_DURATION_S))
        self.calibration_duration.setSingleStep(60.0)
        self.calibration_duration.setDecimals(1)
        self.calibration_duration.setSuffix(" s")
        self.calibration_duration.setMinimumWidth(110)
        calibration_grid.addWidget(self.calibration_duration, 1, 1)

        calibration_grid.addWidget(QLabel("Warmup"), 2, 0)
        self.calibration_warmup = QDoubleSpinBox()
        self.calibration_warmup.setRange(0.0, 30.0)
        self.calibration_warmup.setSingleStep(0.5)
        self.calibration_warmup.setDecimals(1)
        calibration_grid.addWidget(self.calibration_warmup, 2, 1)
        calibration_layout.addLayout(calibration_grid)

        filter_layout = QHBoxLayout()
        self.calibration_row_filter = QComboBox()
        self.calibration_row_filter.addItem("All Rows")
        for row in range(GRID_ROWS):
            self.calibration_row_filter.addItem(f"Row {row + 1}")
        self.calibration_row_filter.currentIndexChanged.connect(self.render_calibration_heatmap)
        filter_layout.addWidget(self.calibration_row_filter)

        self.calibration_col_filter = QComboBox()
        self.calibration_col_filter.addItem("All Columns")
        for col in range(GRID_COLS):
            self.calibration_col_filter.addItem(f"Column {col + 1}")
        self.calibration_col_filter.currentIndexChanged.connect(self.render_calibration_heatmap)
        filter_layout.addWidget(self.calibration_col_filter)
        calibration_layout.addLayout(filter_layout)

        self.use_flow_compensation = QCheckBox("Use Compensation")
        self.use_flow_compensation.setEnabled(False)
        calibration_layout.addWidget(self.use_flow_compensation)

        self.calibration_status_label = QLabel("No calibration loaded")
        self.calibration_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        calibration_layout.addWidget(self.calibration_status_label)

        calibration_btn_layout = QHBoxLayout()
        self.calibration_start_btn = QPushButton("Run Calibration")
        self.calibration_start_btn.setObjectName("PrimaryButton")
        self.calibration_start_btn.clicked.connect(self.start_anemometer_calibration)
        calibration_btn_layout.addWidget(self.calibration_start_btn)

        self.calibration_stop_btn = QPushButton("Stop")
        self.calibration_stop_btn.setObjectName("DangerButton")
        self.calibration_stop_btn.setEnabled(False)
        self.calibration_stop_btn.clicked.connect(self.stop_anemometer_calibration)
        calibration_btn_layout.addWidget(self.calibration_stop_btn)
        calibration_layout.addLayout(calibration_btn_layout)

        tabs.addTab(calibration_tab, "Calibrate")
        self.on_calibration_preset_changed(self.calibration_preset.currentText())
        self.set_calibration_status("No calibration loaded")

        tabs.addTab(self.create_testo_tab(), "Testo Map")

        layout.addWidget(tabs, stretch=1)
        
        self.start_btn = QPushButton("Start Experiment")
        self.start_btn.setMinimumHeight(40)
        self.start_btn.setObjectName("PrimaryButton")
        self.start_btn.clicked.connect(self.start_experiment)
        
        self.stop_btn = QPushButton("Stop Experiment")
        self.stop_btn.setMinimumHeight(40)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setObjectName("DangerButton")
        self.stop_btn.clicked.connect(self.stop_experiment)

        main_btn_layout = QHBoxLayout()
        main_btn_layout.addWidget(self.start_btn)
        main_btn_layout.addWidget(self.stop_btn)
        layout.addLayout(main_btn_layout)
        
        group.setLayout(layout)
        
        # Timer to update active count
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_active_count)
        self.update_timer.start(500)

        self.run_timer = QTimer()
        self.run_timer.timeout.connect(self.update_run_timer)
        self.set_timer_display(0.0, self.duration.value())
        
        return group

    def create_testo_tab(self):
        """Create Testo 440 dP CSV import and heatmap controls."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(7)

        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)

        grid.addWidget(QLabel("Distance"), 0, 0)
        self.testo_distance = QDoubleSpinBox()
        self.testo_distance.setRange(0.1, 10.0)
        self.testo_distance.setSingleStep(1.0)
        self.testo_distance.setDecimals(1)
        self.testo_distance.setValue(1.0)
        self.testo_distance.setSuffix(" m")
        grid.addWidget(self.testo_distance, 0, 1)

        grid.addWidget(QLabel("GUI Log"), 1, 0)
        self.testo_log_combo = QComboBox()
        grid.addWidget(self.testo_log_combo, 1, 1)
        layout.addLayout(grid)

        self.testo_drop_label = CsvDropLabel(self)
        layout.addWidget(self.testo_drop_label)

        button_layout = QHBoxLayout()
        self.testo_import_btn = QPushButton("Import CSVs")
        self.testo_import_btn.clicked.connect(self.on_import_testo_csv_clicked)
        button_layout.addWidget(self.testo_import_btn)

        self.testo_rebuild_btn = QPushButton("Build Map")
        self.testo_rebuild_btn.clicked.connect(self.rebuild_testo_map)
        button_layout.addWidget(self.testo_rebuild_btn)

        self.testo_clear_btn = QPushButton("Clear")
        self.testo_clear_btn.clicked.connect(self.clear_testo_map)
        button_layout.addWidget(self.testo_clear_btn)
        layout.addLayout(button_layout)

        detail_grid = QGridLayout()
        detail_grid.setHorizontalSpacing(8)
        detail_grid.setVerticalSpacing(4)
        detail_grid.addWidget(QLabel("Test Length"), 0, 0)
        self.testo_length_value = QLabel("--")
        self.testo_length_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        detail_grid.addWidget(self.testo_length_value, 0, 1)

        detail_grid.addWidget(QLabel("PWM Speed"), 1, 0)
        self.testo_pwm_value = QLabel("--")
        self.testo_pwm_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        detail_grid.addWidget(self.testo_pwm_value, 1, 1)

        detail_grid.addWidget(QLabel("GUI Match"), 2, 0)
        self.testo_match_value = QLabel("--")
        self.testo_match_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        detail_grid.addWidget(self.testo_match_value, 2, 1)
        layout.addLayout(detail_grid)

        self.testo_status_label = QLabel("No Testo CSVs loaded")
        self.testo_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.testo_status_label.setStyleSheet("""
            QLabel {
                background: #0f172a;
                border: 1px solid #263244;
                border-radius: 8px;
                padding: 8px;
                font-weight: 800;
                color: #cbd5e1;
            }
        """)
        layout.addWidget(self.testo_status_label)
        layout.addStretch()

        self.populate_testo_log_combo()
        return tab

    def populate_testo_log_combo(self):
        """Load recent flight logs into the Testo import selector."""
        if not hasattr(self, "testo_log_combo"):
            return
        self.testo_log_combo.clear()
        self.testo_log_combo.addItem("Auto match by Testo time", None)
        log_dir = Path("logs")
        if not log_dir.exists():
            return
        logs = sorted(log_dir.glob("flight_log_*.csv"), key=lambda path: path.stat().st_mtime, reverse=True)
        for log_path in logs[:30]:
            self.testo_log_combo.addItem(log_path.name, str(log_path))

    def selected_testo_log_path(self):
        """Return the selected GUI flight log, or None for automatic time matching."""
        data = self.testo_log_combo.currentData() if hasattr(self, "testo_log_combo") else None
        if data:
            return Path(data)
        return None

    def on_import_testo_csv_clicked(self):
        """Open a file picker for Testo CSV imports."""
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Import Testo CSVs",
            str(Path.home() / "Desktop"),
            "CSV files (*.csv)",
        )
        if paths:
            self.import_testo_files(paths)

    def rebuild_testo_map(self):
        """Rebuild the Testo heatmap from the last imported file set."""
        if not self.testo_import_paths:
            self.testo_status_label.setText("No Testo CSVs loaded")
            return
        self.import_testo_files(self.testo_import_paths)

    def import_testo_files(self, paths):
        """Parse Testo CSV files, merge with a GUI log, render, and export if possible."""
        csv_paths = [str(path) for path in paths if str(path).lower().endswith(".csv")]
        if not csv_paths:
            self.testo_status_label.setText("No CSV files selected")
            return

        log_path = self.selected_testo_log_path()
        try:
            result = create_testo_correlation_result(
                csv_paths,
                float(self.testo_distance.value()),
                log_path,
            )
            workbook_path = None
            export_path = None
            try:
                workbook_path = write_testo_correlation_workbook(result, "logs/testo")
                export_path = workbook_path
            except Exception as export_error:
                print(f"[Testo] Workbook export skipped: {export_error}")
                export_path = write_testo_correlation_csv_bundle(result, "logs/testo")

            self.testo_import_paths = csv_paths
            self.testo_result = result
            self.testo_workbook_path = export_path
            self.render_testo_heatmap()
            self.update_testo_summary_fields(result)

            workbook_text = f" | {Path(export_path).name}" if export_path else ""
            log_text = Path(log_path).name if log_path else "auto time match"
            self.testo_status_label.setText(
                f"{len(result.measurements)} points @ {result.distance_m:.1f} m | {log_text}{workbook_text}"
            )
        except Exception as exc:
            self.testo_status_label.setText(f"Import failed: {exc}")
            QMessageBox.warning(self, "Testo Import Error", str(exc))

    def update_testo_summary_fields(self, result):
        """Update Testo import summary fields shown in the GUI."""
        if np.isfinite(result.testo_mean_duration_s):
            if len(result.measurements) > 1 and np.isfinite(result.testo_total_duration_s):
                length_text = (
                    f"{format_timer_seconds(result.testo_mean_duration_s)} each | "
                    f"{format_timer_seconds(result.testo_total_duration_s)} total"
                )
            else:
                length_text = format_timer_seconds(result.testo_mean_duration_s)
        else:
            length_text = "--"

        if np.isfinite(result.gui_mean_pwm_us):
            if np.isfinite(result.gui_min_pwm_us) and np.isfinite(result.gui_max_pwm_us) and abs(result.gui_max_pwm_us - result.gui_min_pwm_us) > 1.0:
                pwm_text = f"{result.gui_mean_pwm_us:.0f} us avg ({result.gui_min_pwm_us:.0f}-{result.gui_max_pwm_us:.0f})"
            else:
                pwm_text = f"{result.gui_mean_pwm_us:.0f} us"
        else:
            pwm_text = "--"

        if result.gui_log_sample_count:
            match_text = f"{result.gui_log_sample_count} GUI rows | {result.matched_log_count} log(s)"
        else:
            match_text = "No matching GUI rows"

        self.testo_length_value.setText(length_text)
        self.testo_pwm_value.setText(pwm_text)
        self.testo_match_value.setText(match_text)

    def render_testo_heatmap(self):
        """Render imported Testo m/s values on the 8x8 wind-pixel wall."""
        if self.testo_result is None:
            return
        values = self.testo_result.expanded_speed_grid_ms
        finite_values = values[np.isfinite(values)]
        max_value = max(1.0, float(np.max(finite_values))) if finite_values.size else 1.0
        self.set_wall_legend_testo(max_value)
        for row, row_motors in enumerate(WALL_MOTOR_GRID):
            for col, motor_id in enumerate(row_motors):
                btn = self.motor_buttons[motor_id]
                value = values[row, col]
                if np.isfinite(value):
                    btn.set_scalar_value(value, "m/s", max_value)
                else:
                    btn.update_style()
        self.live_wall_rendering = True

    def clear_testo_map(self):
        """Clear imported Testo heatmap state."""
        self.testo_import_paths = []
        self.testo_result = None
        self.testo_workbook_path = None
        self.reset_wall_render()
        self.testo_length_value.setText("--")
        self.testo_pwm_value.setText("--")
        self.testo_match_value.setText("--")
        self.testo_status_label.setText("No Testo CSVs loaded")
    
    def create_monitor_panel(self):
        """Create live monitoring panel."""
        group = QGroupBox("Live Wind Data")
        add_soft_shadow(group, blur=20, y_offset=6, alpha=18)
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        # Monitor type and selection
        control_layout = QHBoxLayout()
        control_layout.addWidget(QLabel("Monitor:"))
        
        self.monitor_type = QComboBox()
        self.monitor_type.addItem("Individual Motor")
        self.monitor_type.addItem("Group Average")
        self.monitor_type.currentTextChanged.connect(self.on_monitor_type_changed)
        control_layout.addWidget(self.monitor_type)

        control_layout.addWidget(QLabel("Signal:"))
        self.monitor_signal = QComboBox()
        self.monitor_signal.addItem("PWM")
        self.monitor_signal.addItem("Tach Hz")
        self.monitor_signal.addItem("Tach RPM")
        self.monitor_signal.currentTextChanged.connect(self.on_monitor_signal_changed)
        control_layout.addWidget(self.monitor_signal)
        
        self.monitor_motor_select = QComboBox()
        for i in range(NUM_MOTORS):
            self.monitor_motor_select.addItem(f"Motor {i}")
        self.monitor_motor_select.currentIndexChanged.connect(self.on_monitor_selection_changed)
        control_layout.addWidget(self.monitor_motor_select)
        
        self.monitor_group_select = QComboBox()
        self.monitor_group_select.currentIndexChanged.connect(self.on_monitor_selection_changed)
        self.monitor_group_select.hide()
        control_layout.addWidget(self.monitor_group_select)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # Plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setMinimumHeight(150)
        self.plot_widget.setBackground('#0f172a')
        self.plot_widget.setLabel('left', 'PWM Value', units='us')
        self.plot_widget.setLabel('bottom', 'Time', units='s')
        self.plot_widget.setYRange(900, 2100)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.14)
        self.plot_widget.getAxis('left').setPen(pg.mkPen('#475569'))
        self.plot_widget.getAxis('bottom').setPen(pg.mkPen('#475569'))
        self.plot_widget.getAxis('left').setTextPen(pg.mkPen('#94a3b8'))
        self.plot_widget.getAxis('bottom').setTextPen(pg.mkPen('#94a3b8'))
        self.plot_curve = self.plot_widget.plot(pen=pg.mkPen(color='#14b8a6', width=2))
        layout.addWidget(self.plot_widget, stretch=1)
        self.update_monitor_axis()
        
        group.setLayout(layout)
        return group
    
    def add_group(self, name=None):
        """Add a new motor group."""
        if name is None:
            name = f"Group {len(self.groups) + 1}"
        group = MotorGroup(name, len(self.groups))
        self.groups.append(group)
        self.groups_list.addItem(name)
        self.update_monitor_group_list()
        if len(self.groups) == 1:
            self.groups_list.setCurrentRow(0)
        return group
    
    def add_group_clicked(self):
        """Handle add group button click."""
        self.add_group()
    
    def delete_group_clicked(self):
        """Handle delete group button click."""
        if self.selected_group_index >= 0 and len(self.groups) > 1:
            group = self.groups[self.selected_group_index]
            # Unassign motors from this group
            for btn in self.motor_buttons:
                if btn.assigned_group == group:
                    btn.assigned_group = None
                    btn.update_style()
            # Remove group
            self.groups.pop(self.selected_group_index)
            self.groups_list.takeItem(self.selected_group_index)
            self.update_monitor_group_list()
        elif len(self.groups) == 1:
            QMessageBox.warning(self, "Cannot Delete", "At least one group must exist!")
    
    def on_group_selected(self, index):
        """Handle group selection change."""
        self.selected_group_index = index
        if index >= 0 and index < len(self.groups):
            group = self.groups[index]
            self.selected_group_label.setText(f"Selected: {group.name}")
            bg_color, _ = group.get_color()
            self.selected_group_label.setStyleSheet(f"font-weight: bold; color: {bg_color};")
            
            # Block signals while loading group parameters to prevent on_param_changed
            # from being triggered with partially-updated spinbox values
            self.signal_type.blockSignals(True)
            self.amp_min.blockSignals(True)
            self.amp_max.blockSignals(True)
            self.constant_pwm_preset.blockSignals(True)
            self.constant_pwm_spinbox.blockSignals(True)
            self.period.blockSignals(True)
            self.fourier_terms.blockSignals(True)
            
            try:
                # Load group's signal configuration
                self.signal_type.setCurrentText(group.signal_type)
                self.amp_min.setValue(group.amp_min)
                self.amp_max.setValue(group.amp_max)
                self.constant_pwm_spinbox.setValue(int(round(group.constant_pwm_us)))
                self.constant_pwm_preset.setCurrentText(self.match_pwm_preset(group.constant_pwm_us))
                self.period.setValue(group.period)
                self.fourier_terms.setValue(group.fourier_terms)
                self.load_custom_harmonics(group)
                self.update_signal_control_visibility(group.signal_type)
            finally:
                # Always unblock signals, even if an exception occurs
                self.signal_type.blockSignals(False)
                self.amp_min.blockSignals(False)
                self.amp_max.blockSignals(False)
                self.constant_pwm_preset.blockSignals(False)
                self.constant_pwm_spinbox.blockSignals(False)
                self.period.blockSignals(False)
                self.fourier_terms.blockSignals(False)
    
    def update_signal_control_visibility(self, signal_type):
        """Show only the controls relevant to the selected signal shape."""
        is_sine = signal_type == "Sine Wave"
        is_square = signal_type == "Square Wave"
        is_custom = signal_type == "Custom Fourier"
        is_constant = signal_type == "Constant DC"
        
        self.standard_params_widget.setVisible(is_sine or is_square)
        self.dc_params_widget.setVisible(is_constant)
        self.custom_params_widget.setVisible(is_custom)

    def on_signal_type_changed(self, signal_type):
        """Handle signal type change - show/hide controls dynamically."""
        self.update_signal_control_visibility(signal_type)
        if self.selected_group_index >= 0:
            self.groups[self.selected_group_index].signal_type = signal_type
            self.update_group_list_labels()

    def match_pwm_preset(self, pwm_us):
        """Return the preset name that exactly matches a PWM value."""
        pwm_value = int(round(float(pwm_us)))
        return next(
            (name for name, preset_value in PWM_TEST_PRESETS.items() if preset_value == pwm_value),
            "Custom",
        )

    def on_constant_pwm_preset_changed(self, preset_name):
        """Load a direct PWM preset for Constant DC groups."""
        if preset_name not in PWM_TEST_PRESETS:
            return
        self._loading_constant_pwm_preset = True
        try:
            self.constant_pwm_spinbox.setValue(PWM_TEST_PRESETS[preset_name])
        finally:
            self._loading_constant_pwm_preset = False
        if self.selected_group_index >= 0:
            self.groups[self.selected_group_index].constant_pwm_us = float(self.constant_pwm_spinbox.value())
            self.update_group_list_labels()

    def on_constant_pwm_changed(self, *_):
        """Store the direct PWM value for Constant DC groups."""
        pwm_value = self.constant_pwm_spinbox.value()
        if not self._loading_constant_pwm_preset:
            matching = self.match_pwm_preset(pwm_value)
            self.constant_pwm_preset.blockSignals(True)
            try:
                self.constant_pwm_preset.setCurrentText(matching)
            finally:
                self.constant_pwm_preset.blockSignals(False)
        if self.selected_group_index >= 0:
            self.groups[self.selected_group_index].constant_pwm_us = float(pwm_value)
            span = max(1.0, float(PWM_MAX - PWM_MIN))
            self.groups[self.selected_group_index].dc_value = (float(pwm_value) - PWM_MIN) / span
            self.update_group_list_labels()
    
    def on_param_changed(self, *_):
        """Handle parameter change."""
        if self.selected_group_index >= 0:
            group = self.groups[self.selected_group_index]
            group.amp_min = self.amp_min.value()
            group.amp_max = self.amp_max.value()
            group.period = self.period.value()
            group.fourier_terms = self.fourier_terms.value()
    
    def add_harmonic(self):
        """Add a new harmonic to custom Fourier."""
        row = self.harmonics_table.rowCount()
        self.harmonics_table.insertRow(row)
        self.harmonics_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        self.harmonics_table.setItem(row, 1, QTableWidgetItem("0.1"))
        self.harmonics_table.setItem(row, 2, QTableWidgetItem("0"))
        self.save_custom_harmonics()
    
    def remove_harmonic(self):
        """Remove selected harmonic."""
        current_row = self.harmonics_table.currentRow()
        if current_row >= 0:
            self.harmonics_table.removeRow(current_row)
            # Renumber harmonics
            for i in range(self.harmonics_table.rowCount()):
                self.harmonics_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.save_custom_harmonics()
    
    def load_custom_harmonics(self, group):
        """Load custom harmonics from group."""
        self.harmonics_table.setRowCount(0)
        for harmonic_num, amplitude, phase_deg in group.custom_harmonics:
            row = self.harmonics_table.rowCount()
            self.harmonics_table.insertRow(row)
            self.harmonics_table.setItem(row, 0, QTableWidgetItem(str(harmonic_num)))
            self.harmonics_table.setItem(row, 1, QTableWidgetItem(str(amplitude)))
            self.harmonics_table.setItem(row, 2, QTableWidgetItem(str(phase_deg)))
    
    def save_custom_harmonics(self):
        """Save custom harmonics to current group."""
        if self.selected_group_index >= 0:
            group = self.groups[self.selected_group_index]
            group.custom_harmonics = []
            for i in range(self.harmonics_table.rowCount()):
                try:
                    harmonic_num = int(self.harmonics_table.item(i, 0).text())
                    amplitude = float(self.harmonics_table.item(i, 1).text())
                    phase_deg = float(self.harmonics_table.item(i, 2).text())
                    group.custom_harmonics.append((harmonic_num, amplitude, phase_deg))
                except (ValueError, AttributeError):
                    pass
    
    def on_monitor_type_changed(self, monitor_type):
        """Handle monitor type change."""
        if monitor_type == "Individual Motor":
            self.monitor_motor_select.show()
            self.monitor_group_select.hide()
        else:
            self.monitor_motor_select.hide()
            self.monitor_group_select.show()
        # Clear data when switching monitor type
        self.clear_monitor_data()
    
    def on_monitor_selection_changed(self, *_):
        """Handle motor/group selection change - clear plot for fresh start."""
        self.clear_monitor_data()
    
    def clear_monitor_data(self):
        """Clear monitoring display data (don't reset experiment_start_time)."""
        self.monitor_data_time.clear()
        self.monitor_data_value.clear()
        # NOTE: experiment_start_time persists across selections - it's the reference point!
        self.plot_curve.setData([], [])
    
    def update_monitor_group_list(self):
        """Update the monitor group dropdown."""
        self.monitor_group_select.clear()
        for group in self.groups:
            self.monitor_group_select.addItem(group.name)
        self.update_group_list_labels()

    def update_group_list_labels(self):
        """Show group counts and profile types in the group list."""
        if not hasattr(self, "groups_list"):
            return
        for index, group in enumerate(self.groups):
            item = self.groups_list.item(index)
            if item is not None:
                if group.signal_type == "Constant DC":
                    profile = f"Constant {int(round(group.constant_pwm_us))} us"
                else:
                    profile = group.signal_type
                item.setText(f"{group.name}  |  {len(group.motors)} pixels  |  {profile}")

    def refresh_header_metrics(self, *_):
        """Refresh top-bar dashboard metrics."""
        if not hasattr(self, "header_active_value"):
            return
        active_count = sum(1 for btn in self.motor_buttons if btn is not None and btn.assigned_group is not None)
        pwm_min, pwm_max = self.get_output_pwm_range() if hasattr(self, "output_pwm_min") else (PWM_MIN, PWM_MAX)
        telemetry = self.telemetry_mode.currentText() if hasattr(self, "telemetry_mode") else "No Tach / Legacy"

        self.header_active_value.setText(str(active_count))
        self.header_pwm_value.setText(f"{int(pwm_min)}-{int(pwm_max)}")
        self.header_telemetry_value.setText("TACH" if telemetry == "Tach Return" else "LEGACY")

    def on_output_pwm_preset_changed(self, preset_name):
        """Load the selected experiment PWM range preset."""
        if preset_name not in PWM_SPEED_PRESETS:
            return
        self._loading_output_pwm_preset = True
        try:
            pwm_min, pwm_max = PWM_SPEED_PRESETS[preset_name]
            self.output_pwm_min.setValue(pwm_min)
            self.output_pwm_max.setValue(pwm_max)
        finally:
            self._loading_output_pwm_preset = False
        self.refresh_header_metrics()

    def on_output_pwm_range_changed(self, *_):
        """Mark the output PWM range as custom unless it matches a preset."""
        if self._loading_output_pwm_preset:
            return
        current_range = (self.output_pwm_min.value(), self.output_pwm_max.value())
        matching = next(
            (name for name, preset_range in PWM_SPEED_PRESETS.items() if preset_range == current_range),
            "Custom",
        )
        self.output_pwm_preset.blockSignals(True)
        try:
            self.output_pwm_preset.setCurrentText(matching)
        finally:
            self.output_pwm_preset.blockSignals(False)
        self.refresh_header_metrics()

    def get_output_pwm_range(self):
        """Return the selected experiment PWM min/max in safe order."""
        pwm_min = self.output_pwm_min.value()
        pwm_max = self.output_pwm_max.value()
        if pwm_max < pwm_min:
            pwm_min, pwm_max = pwm_max, pwm_min
        return float(pwm_min), float(pwm_max)

    def tach_return_enabled(self):
        """Return True when the GUI should use tach-return firmware protocol."""
        return self.telemetry_mode.currentText() == "Tach Return"

    def on_bench_pwm_preset_changed(self, preset_name):
        """Load a single-motor PWM preset."""
        if preset_name not in PWM_TEST_PRESETS:
            return
        self._loading_bench_pwm_preset = True
        try:
            self.bench_pwm.setValue(PWM_TEST_PRESETS[preset_name])
        finally:
            self._loading_bench_pwm_preset = False

    def on_bench_pwm_changed(self, *_):
        """Mark bench PWM as custom unless it matches a preset."""
        if self._loading_bench_pwm_preset:
            return
        pwm_value = self.bench_pwm.value()
        matching = next(
            (name for name, preset_value in PWM_TEST_PRESETS.items() if preset_value == pwm_value),
            "Custom",
        )
        self.bench_pwm_preset.blockSignals(True)
        try:
            self.bench_pwm_preset.setCurrentText(matching)
        finally:
            self.bench_pwm_preset.blockSignals(False)

    def on_monitor_signal_changed(self, *_):
        """Handle switching between PWM and tach plots."""
        self.clear_monitor_data()
        self.update_monitor_axis()
        if not self.experiment_running:
            self.reset_wall_render()

    def update_monitor_axis(self):
        """Set plot labels and scaling for the selected monitor signal."""
        if not hasattr(self, 'plot_widget') or not hasattr(self, 'monitor_signal'):
            return
        signal = self.monitor_signal.currentText()
        if signal == "PWM":
            self.plot_widget.setLabel('left', 'PWM Value', units='us')
            self.plot_widget.disableAutoRange(axis='y')
            self.plot_widget.setYRange(900, 2100)
            self.plot_curve.setPen(pg.mkPen(color='#14b8a6', width=2))
        elif signal == "Tach Hz":
            self.plot_widget.setLabel('left', 'Tach Frequency', units='Hz')
            self.plot_widget.enableAutoRange(axis='y')
            self.plot_curve.setPen(pg.mkPen(color='#3b82f6', width=2))
        else:
            self.plot_widget.setLabel('left', 'Tach Speed', units='RPM')
            self.plot_widget.enableAutoRange(axis='y')
            self.plot_curve.setPen(pg.mkPen(color='#f59e0b', width=2))

    def update_wall_render(self, pwm_values, tach_hz):
        """Render the wind-pixel wall as a live heatmap."""
        return
        if not self.experiment_running:
            return
        signal = self.monitor_signal.currentText()
        if signal == "PWM":
            values = pwm_values
            max_value = None
        elif signal == "Tach Hz":
            values = tach_hz
            finite_values = tach_hz[np.isfinite(tach_hz)]
            max_value = max(1.0, float(np.max(finite_values))) if finite_values.size else 1.0
        else:
            values = tach_hz * 60.0 / TACH_PULSES_PER_REV
            finite_values = values[np.isfinite(values)]
            max_value = max(1.0, float(np.max(finite_values))) if finite_values.size else 1.0

        for motor_id, btn in enumerate(self.motor_buttons):
            if btn is not None:
                btn.set_live_value(values[motor_id], signal, max_value)
        self.live_wall_rendering = True

    def reset_wall_render(self):
        """Return the wind-pixel wall to assignment colors."""
        if not self.live_wall_rendering:
            return
        for btn in self.motor_buttons:
            if btn is not None:
                btn.update_style()
        self.set_wall_legend_pwm()
        self.live_wall_rendering = False

    def on_duration_changed(self, *_):
        """Refresh the timer display when idle duration changes."""
        if self.run_timer_started_at is None:
            self.set_timer_display(0.0, self.duration.value())

    def set_timer_display(self, elapsed_s=0.0, duration_s=None):
        """Update the visible elapsed/duration timer."""
        if not hasattr(self, "run_timer_label"):
            return
        if duration_s is None:
            duration_s = self.duration.value() if hasattr(self, "duration") else 0.0
        elapsed_s = max(0.0, float(elapsed_s))
        duration_s = max(0.0, float(duration_s))
        self.run_timer_label.setText(
            f"Timer {format_timer_seconds(elapsed_s)} / {format_timer_seconds(duration_s)}"
        )

    def start_operation_timer(self, duration_s):
        """Start the GUI timer for an experiment, motor test, or calibration run."""
        self.run_timer_duration_s = max(0.0, float(duration_s))
        self.run_timer_started_at = time.perf_counter()
        self.update_run_timer()
        if self.run_timer is not None:
            self.run_timer.start(250)

    def update_run_timer(self):
        """Tick the GUI timer while an operation is active."""
        if self.run_timer_started_at is None:
            self.set_timer_display(0.0, self.duration.value() if hasattr(self, "duration") else 0.0)
            return
        elapsed_s = time.perf_counter() - self.run_timer_started_at
        self.set_timer_display(min(elapsed_s, self.run_timer_duration_s), self.run_timer_duration_s)

    def stop_operation_timer(self):
        """Stop the GUI timer and leave the final elapsed time visible."""
        if self.run_timer is not None:
            self.run_timer.stop()
        if self.run_timer_started_at is None:
            return
        elapsed_s = time.perf_counter() - self.run_timer_started_at
        self.set_timer_display(min(elapsed_s, self.run_timer_duration_s), self.run_timer_duration_s)
        self.run_timer_started_at = None

    def set_experiment_status(self, text, state="ready"):
        """Update run status surfaces with consistent styling."""
        self.status_label.setText(text)
        self.status_label.setStyleSheet(STATUS_STYLES.get(state, STATUS_STYLES["ready"]))
        if hasattr(self, "header_status_label"):
            self.header_status_label.setText(text.upper())
            header_styles = {
                "ready": "background: #0f172a; color: #93c5fd; border: 1px solid #1e3a8a;",
                "running": "background: #0f2f2b; color: #5eead4; border: 1px solid #115e59;",
                "stopping": "background: #342409; color: #fbbf24; border: 1px solid #92400e;",
                "error": "background: #3f1218; color: #fca5a5; border: 1px solid #991b1b;",
            }
            self.header_status_label.setStyleSheet(
                f"{header_styles.get(state, header_styles['ready'])}"
                "border-radius: 8px; padding: 8px 12px; font-weight: 800; letter-spacing: 1px;"
            )

    def set_bench_status(self, text, state="idle"):
        """Update the bench-test status label."""
        styles = {
            "idle": """
                QLabel {
                    background-color: #0f172a;
                    color: #93c5fd;
                    border: 1px solid #1e3a8a;
                    padding: 8px;
                    border-radius: 8px;
                    font-weight: 800;
                }
            """,
            "running": """
                QLabel {
                    background-color: #0f2f2b;
                    border: 1px solid #115e59;
                    padding: 8px;
                    border-radius: 8px;
                    font-weight: 800;
                    color: #5eead4;
                }
            """,
            "stopping": """
                QLabel {
                    background-color: #342409;
                    border: 1px solid #92400e;
                    padding: 8px;
                    border-radius: 8px;
                    font-weight: 800;
                    color: #fbbf24;
                }
            """,
            "error": """
                QLabel {
                    background-color: #3f1218;
                    border: 1px solid #991b1b;
                    padding: 8px;
                    border-radius: 8px;
                    font-weight: 800;
                    color: #fca5a5;
                }
            """,
        }
        self.bench_status_label.setText(text)
        self.bench_status_label.setStyleSheet(styles.get(state, styles["idle"]))

    def set_bench_controls_enabled(self, enabled):
        """Enable or disable motor-test controls that should not change mid-run."""
        self.bench_motor_select.setEnabled(enabled)
        self.bench_pwm_preset.setEnabled(enabled)
        self.bench_pwm.setEnabled(enabled)
        self.bench_duration.setEnabled(enabled)
        self.bench_start_btn.setEnabled(enabled)
        self.telemetry_mode.setEnabled(enabled)

    def set_calibration_status(self, text, state="idle"):
        """Update the uniform-flow calibration status label."""
        styles = {
            "idle": """
                QLabel {
                    background-color: #0f172a;
                    color: #93c5fd;
                    border: 1px solid #1e3a8a;
                    padding: 8px;
                    border-radius: 8px;
                    font-weight: 800;
                }
            """,
            "running": """
                QLabel {
                    background-color: #0f2f2b;
                    border: 1px solid #115e59;
                    padding: 8px;
                    border-radius: 8px;
                    font-weight: 800;
                    color: #5eead4;
                }
            """,
            "stopping": """
                QLabel {
                    background-color: #342409;
                    border: 1px solid #92400e;
                    padding: 8px;
                    border-radius: 8px;
                    font-weight: 800;
                    color: #fbbf24;
                }
            """,
            "error": """
                QLabel {
                    background-color: #3f1218;
                    border: 1px solid #991b1b;
                    padding: 8px;
                    border-radius: 8px;
                    font-weight: 800;
                    color: #fca5a5;
                }
            """,
        }
        self.calibration_status_label.setText(text)
        self.calibration_status_label.setStyleSheet(styles.get(state, styles["idle"]))

    def set_calibration_controls_enabled(self, enabled):
        """Enable or disable uniform-flow calibration controls."""
        self.calibration_preset.setEnabled(enabled)
        self.calibration_pwm.setEnabled(enabled)
        self.calibration_duration.setEnabled(enabled)
        self.calibration_warmup.setEnabled(enabled)
        self.calibration_row_filter.setEnabled(enabled)
        self.calibration_col_filter.setEnabled(enabled)
        self.calibration_start_btn.setEnabled(enabled)
        self.use_flow_compensation.setEnabled(enabled and self.last_calibration_result is not None)

    def on_calibration_preset_changed(self, preset_name):
        """Load a preprogrammed anemometer survey setting."""
        preset = ANEMOMETER_CALIBRATION_PRESETS.get(preset_name)
        if not preset:
            return
        self.calibration_pwm.setValue(int(round(preset["pwm_us"])))
        self.calibration_duration.setValue(float(preset["duration_s"]))
        self.calibration_warmup.setValue(float(preset["warmup_s"]))

    def get_flow_compensation_offsets(self):
        """Return the active per-motor compensation offsets, if enabled."""
        if (
            hasattr(self, "use_flow_compensation")
            and self.use_flow_compensation.isChecked()
            and self.last_calibration_result is not None
        ):
            return self.flow_compensation_offsets.copy()
        return None

    def render_calibration_heatmap(self, *_):
        """Render the latest calibration mean-speed heatmap with row/column filters."""
        if self.last_calibration_result is None or self.experiment_running or self.bench_test_running:
            return

        row_index = self.calibration_row_filter.currentIndex() - 1
        col_index = self.calibration_col_filter.currentIndex() - 1
        row_index = row_index if row_index >= 0 else None
        col_index = col_index if col_index >= 0 else None

        filtered_grid = filter_grid_by_row_col(
            self.last_calibration_result.mean_hz_grid,
            row_index=row_index,
            col_index=col_index,
        )
        motor_values = np.full(NUM_MOTORS, np.nan, dtype=np.float64)
        for row, row_motors in enumerate(WALL_MOTOR_GRID):
            for col, motor_id in enumerate(row_motors):
                motor_values[motor_id] = filtered_grid[row, col]

        finite_values = motor_values[np.isfinite(motor_values)]
        max_value = max(1.0, float(np.max(finite_values))) if finite_values.size else 1.0
        for motor_id, btn in enumerate(self.motor_buttons):
            if btn is None:
                continue
            if np.isfinite(motor_values[motor_id]):
                btn.set_live_value(motor_values[motor_id], "Tach Hz", max_value)
            else:
                btn.update_style()
        self.live_wall_rendering = True

    def start_anemometer_calibration(self):
        """Run a preprogrammed uniform-flow survey and export raw data to Excel."""
        if self.experiment_running:
            QMessageBox.warning(
                self,
                "Experiment Running",
                "Stop the experiment before running calibration.",
            )
            return
        if self.bench_test_running:
            QMessageBox.warning(
                self,
                "Motor Test Active",
                "Stop the motor test before running calibration.",
            )
            return
        if self.calibration_running:
            return
        if not self.tach_return_enabled():
            QMessageBox.warning(
                self,
                "Tach Return Required",
                "Use Tach Return telemetry for anemometer calibration.",
            )
            return

        pwm_us = float(self.calibration_pwm.value())
        duration_s = float(self.calibration_duration.value())
        warmup_s = float(self.calibration_warmup.value())

        if pwm_us <= PWM_MIN:
            QMessageBox.warning(
                self,
                "PWM Too Low",
                f"Choose a calibration PWM above {PWM_MIN}us.",
            )
            return

        self.reset_wall_render()
        self.calibration_running = True
        self.calibration_stop_event = threading.Event()
        self.set_calibration_controls_enabled(False)
        self.calibration_stop_btn.setEnabled(True)
        self.start_btn.setEnabled(False)
        self.set_bench_controls_enabled(False)
        self.calibration_status_signal.emit("Warming flow field", "running")
        self.start_operation_timer(warmup_s + duration_s)

        self.calibration_thread = threading.Thread(
            target=self.run_anemometer_calibration_thread,
            args=(pwm_us, duration_s, warmup_s, self.calibration_stop_event),
            daemon=True,
        )
        self.calibration_thread.start()

    def run_anemometer_calibration_thread(self, pwm_us, duration_s, warmup_s, stop_event):
        """Collect raw tach/anemometer samples for every motor at one uniform PWM."""
        import time
        from datetime import datetime

        interval_s = 1.0 / UPDATE_RATE_HZ
        tach_poll_interval_frames = max(1, int(round(UPDATE_RATE_HZ / max(1, TACH_POLL_HZ))))
        idle_pwm = np.full(NUM_MOTORS, float(PWM_MIN))
        uniform_pwm = np.full(NUM_MOTORS, float(pwm_us))
        hardware = None
        samples = []
        payload = None
        message = "Calibration stopped."
        is_error = False

        try:
            use_mock = platform.system() == "Darwin"
            hardware = HardwareInterface(use_mock=use_mock, enable_tach=True)
            if not use_mock and hardware.use_mock:
                raise RuntimeError("Hardware unavailable; SPI/GPIO sync fell back to mock")

            next_frame_time = time.perf_counter()
            warmup_start = time.perf_counter()
            while not stop_event.is_set() and time.perf_counter() - warmup_start < warmup_s:
                hardware.send_pwm(uniform_pwm)
                next_frame_time += interval_s
                sleep_time = next_frame_time - time.perf_counter()
                if sleep_time > 0:
                    time.sleep(sleep_time)

            if stop_event.is_set():
                self.calibration_finished_signal.emit(message, False, None)
                return

            self.calibration_status_signal.emit(f"Recording @ {int(pwm_us)}us", "running")
            run_start = time.perf_counter()
            next_frame_time = run_start
            run_frame = 0
            while not stop_event.is_set() and time.perf_counter() - run_start < duration_s:
                hardware.send_pwm(uniform_pwm)
                run_frame += 1
                if run_frame % tach_poll_interval_frames == 0:
                    tach_hz = hardware.read_tach_all(uniform_pwm)
                    elapsed_s = time.perf_counter() - run_start
                    samples.append(
                        AnemometerSample(
                            timestamp=datetime.now().isoformat(timespec="milliseconds"),
                            elapsed_s=elapsed_s,
                            tach_hz=tach_hz.copy(),
                        )
                    )
                    if len(samples) % max(1, int(TACH_POLL_HZ)) == 0:
                        finite = tach_hz[np.isfinite(tach_hz)]
                        mean_hz = float(np.mean(finite)) if finite.size else float("nan")
                        self.calibration_status_signal.emit(
                            f"{len(samples)} samples | mean {mean_hz:.1f} Hz",
                            "running",
                        )

                next_frame_time += interval_s
                sleep_time = next_frame_time - time.perf_counter()
                if sleep_time > 0:
                    time.sleep(sleep_time)

            if stop_event.is_set():
                message = "Calibration stopped."
            else:
                result = summarize_anemometer_samples(samples, pwm_us)
                workbook_path = write_calibration_workbook(
                    result,
                    samples,
                    ANEMOMETER_CALIBRATION_DIR,
                )
                payload = {
                    "result": result,
                    "workbook_path": str(workbook_path),
                }
                message = f"Saved {workbook_path.name}"

        except Exception as e:
            message = f"Calibration failed: {e}"
            is_error = True

        finally:
            if hardware is not None:
                try:
                    for _ in range(40):
                        hardware.send_pwm(idle_pwm)
                        time.sleep(interval_s)
                except Exception:
                    pass
                hardware.close()

        self.calibration_finished_signal.emit(message, is_error, payload)

    def stop_anemometer_calibration(self):
        """Stop an active uniform-flow calibration run."""
        if self.calibration_running and self.calibration_stop_event:
            self.calibration_stop_event.set()
            self.calibration_stop_btn.setEnabled(False)
            self.calibration_status_signal.emit("Stopping...", "stopping")

    def on_anemometer_calibration_finished(self, message, is_error, payload):
        """Restore GUI state after calibration and load compensation offsets."""
        self.stop_operation_timer()
        self.calibration_running = False
        self.calibration_thread = None
        self.calibration_stop_event = None
        self.calibration_stop_btn.setEnabled(False)
        self.set_calibration_controls_enabled(True)
        self.set_bench_controls_enabled(True)
        self.start_btn.setEnabled(True)

        if payload and not is_error:
            self.last_calibration_result = payload["result"]
            self.last_calibration_workbook = payload["workbook_path"]
            self.flow_compensation_offsets = self.last_calibration_result.offset_us_by_motor.copy()
            self.use_flow_compensation.setEnabled(True)
            self.use_flow_compensation.setChecked(True)
            self.set_calibration_status(message, "idle")
            self.render_calibration_heatmap()
            QMessageBox.information(
                self,
                "Calibration Complete",
                f"Raw anemometer workbook saved:\n{self.last_calibration_workbook}",
            )
        else:
            self.set_calibration_status(message, "error" if is_error else "idle")
            if is_error:
                QMessageBox.warning(self, "Calibration Error", message)
    
    def get_selected_group(self):
        """Get the currently selected group."""
        if 0 <= self.selected_group_index < len(self.groups):
            return self.groups[self.selected_group_index]
        return None
    
    def select_all_motors(self):
        """Assign all motors to the currently selected group."""
        selected_group = self.get_selected_group()
        if selected_group:
            for btn in self.motor_buttons:
                # Remove from old group if assigned
                if btn.assigned_group and btn.assigned_group != selected_group:
                    btn.assigned_group.motors.discard(btn.motor_id)
                # Assign to selected group
                selected_group.motors.add(btn.motor_id)
                btn.assigned_group = selected_group
                btn.update_style()
        else:
            QMessageBox.warning(self, "No Group Selected", "Please select a group first!")
    
    def clear_all_motors(self):
        """Clear all motor assignments."""
        for btn in self.motor_buttons:
            if btn.assigned_group:
                btn.assigned_group.motors.discard(btn.motor_id)
            btn.assigned_group = None
            btn.update_style()
    
    def update_active_count(self):
        """Update the count of active motors."""
        count = sum(1 for btn in self.motor_buttons if btn.assigned_group is not None)
        self.active_count_label.setText(f"{count} active wind pixels")
        self.update_group_list_labels()
        self.refresh_header_metrics()
    
    def pwm_us_to_signal_value(self, pwm_us, output_pwm_min=None, output_pwm_max=None):
        """Convert a direct PWM target into the normalized signal value used by the flight loop."""
        pwm_min = float(PWM_MIN if output_pwm_min is None else output_pwm_min)
        pwm_max = float(PWM_MAX if output_pwm_max is None else output_pwm_max)
        if pwm_max < pwm_min:
            pwm_min, pwm_max = pwm_max, pwm_min
        span = max(1.0, pwm_max - pwm_min)
        return float(np.clip((float(pwm_us) - pwm_min) / span, 0.0, 1.0))

    def build_fixed_pwm_overrides(self):
        """Return per-motor direct PWM values for Constant DC groups."""
        fixed_pwm = np.full(NUM_MOTORS, np.nan, dtype=np.float64)
        for group in self.groups:
            if group.signal_type != "Constant DC":
                continue
            pwm_us = float(np.clip(group.constant_pwm_us, PWM_MIN, PWM_MAX))
            for motor_id in group.motors:
                fixed_pwm[motor_id] = pwm_us
        return fixed_pwm if np.isfinite(fixed_pwm).any() else None

    def generate_group_coefficients(self, group, output_pwm_min=None, output_pwm_max=None):
        """Generate Fourier coefficients for a specific group."""
        signal_type = group.signal_type
        amp_min = group.amp_min
        amp_max = group.amp_max
        period = group.period
        n_terms = group.fourier_terms
        
        # CRITICAL: Calculate base_freq from period (1/period)
        # This ensures the signal reconstruction uses the correct frequency
        base_freq = 1.0 / period if period > 0 else BASE_FREQUENCY
        
        if signal_type == "Custom Fourier":
            # Generate from custom harmonics
            coeffs = np.zeros((NUM_MOTORS, n_terms))
            for harmonic_num, amplitude, phase_deg in group.custom_harmonics:
                if 0 <= harmonic_num < n_terms:
                    coeffs[:, harmonic_num] = amplitude
                    # Phase will be handled separately if needed
            return coeffs
        
        # Calculate amplitude and DC offset
        amplitude = (amp_max - amp_min) / 2.0
        dc_offset = (amp_max + amp_min) / 2.0
        
        if signal_type == "Sine Wave":
            coeffs = generate_sine_wave(
                n_motors=NUM_MOTORS,
                amplitude=amplitude,
                period=period,
                dc_offset=dc_offset,
                n_terms=n_terms,
                base_freq=base_freq
            )
        elif signal_type == "Square Wave":
            # For square wave between amp_min and amp_max:
            # - Pass HALF the range as amplitude (harmonics swing ±amplitude around DC)
            # - Set DC to midpoint
            amplitude_half_range = (amp_max - amp_min) / 2.0
            coeffs = generate_square_pulse(
                n_motors=NUM_MOTORS,
                amplitude=amplitude_half_range,
                period=period,
                duty_cycle=0.5,
                n_terms=n_terms,
                base_freq=base_freq
            )
            # Correct the DC offset to be the midpoint between min and max
            coeffs[:, 0] = dc_offset  # (amp_max + amp_min) / 2.0
        else:  # Constant DC
            dc_value = self.pwm_us_to_signal_value(
                group.constant_pwm_us,
                output_pwm_min,
                output_pwm_max,
            )
            coeffs = generate_uniform(
                n_motors=NUM_MOTORS,
                value=dc_value,
                n_terms=n_terms
            )
        
        return coeffs
    
    def generate_fourier_coefficients(self, output_pwm_min=None, output_pwm_max=None):
        """Generate combined Fourier coefficients and per-motor omega values."""
        # Determine max number of terms needed
        max_terms = max((g.fourier_terms for g in self.groups), default=7)
        
        # Initialize coefficient matrix and omega array (rad/s per motor)
        final_coeffs = np.zeros((NUM_MOTORS, max_terms))
        omega_per_motor = np.full(NUM_MOTORS, 2.0 * np.pi * BASE_FREQUENCY, dtype=float)
        
        # Process each group
        for group in self.groups:
            if len(group.motors) == 0:
                continue
            
            group_coeffs = self.generate_group_coefficients(group, output_pwm_min, output_pwm_max)
            group_omega = 2.0 * np.pi * (1.0 / group.period) if group.period > 0 else 2.0 * np.pi * BASE_FREQUENCY
            
            # Assign coefficients and omega to motors in this group
            for motor_id in group.motors:
                # Pad or truncate to match final size
                terms_to_copy = min(group_coeffs.shape[1], max_terms)
                final_coeffs[motor_id, :terms_to_copy] = group_coeffs[motor_id, :terms_to_copy]
                omega_per_motor[motor_id] = group_omega
        
        # Motors not in any group get zero coefficients (PWM_MIN); omega left at default
        for i, btn in enumerate(self.motor_buttons):
            if btn.assigned_group is None:
                final_coeffs[i, :] = 0.0
        
        return final_coeffs, omega_per_motor
    
    def start_experiment(self):
        """Start the experiment."""
        if self.bench_test_running:
            QMessageBox.warning(
                self,
                "Motor Test Active",
                "Stop the motor test before starting a full experiment.",
            )
            return
        if self.calibration_running:
            QMessageBox.warning(
                self,
                "Calibration Active",
                "Stop calibration before starting a full experiment.",
            )
            return

        # Check if any motors are assigned
        active_count = sum(1 for btn in self.motor_buttons if btn.assigned_group is not None)
        if active_count == 0:
            QMessageBox.warning(self, "No Motors Assigned", 
                              "Please assign at least one motor to a group!")
            return
        
        # Reset experiment timeline for fresh start
        self.experiment_start_time = None
        
        output_pwm_min, output_pwm_max = self.get_output_pwm_range()
        # Generate coefficients and per-motor omega
        coeffs, omega_per_motor = self.generate_fourier_coefficients(output_pwm_min, output_pwm_max)
        enable_tach = self.tach_return_enabled()
        pwm_compensation = self.get_flow_compensation_offsets()
        fixed_pwm_overrides = self.build_fixed_pwm_overrides()
        
        # Update UI
        self.experiment_running = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.set_experiment_status("Running", "running")
        
        # Disable configuration during experiment
        self.groups_list.setEnabled(False)
        self.signal_type.setEnabled(False)
        self.output_pwm_preset.setEnabled(False)
        self.output_pwm_min.setEnabled(False)
        self.output_pwm_max.setEnabled(False)
        self.telemetry_mode.setEnabled(False)
        self.set_bench_controls_enabled(False)
        self.set_calibration_controls_enabled(False)
        for btn in self.motor_buttons:
            btn.setEnabled(False)
        
        self.start_operation_timer(float(self.duration.value()))

        # Start live monitoring
        self.start_live_monitor()
        
        # Start experiment in separate thread
        import threading
        experiment_thread = threading.Thread(
            target=self.run_experiment_thread,
            args=(
                coeffs,
                omega_per_motor,
                output_pwm_min,
                output_pwm_max,
                enable_tach,
                pwm_compensation,
                fixed_pwm_overrides,
            )
        )
        experiment_thread.daemon = True
        experiment_thread.start()
    
    def run_experiment_thread(
        self,
        coeffs,
        omega_per_motor,
        output_pwm_min,
        output_pwm_max,
        enable_tach,
        pwm_compensation,
        fixed_pwm_overrides,
    ):
        """Run the experiment (called in separate thread)."""
        try:
            duration = self.duration.value()
            
            import platform
            import time
            from src.core.flight_loop import flight_loop
            from config import BASE_FREQUENCY

            # If any group uses Square Wave, loosen slew limit to avoid edge smoothing
            from config import PWM_MAX, PWM_MIN, SLEW_LIMIT
            square_wave_present = any(g.signal_type == "Square Wave" and len(g.motors) > 0 for g in self.groups)
            slew_limit_override = (output_pwm_max - output_pwm_min) if square_wave_present else SLEW_LIMIT
            
            self.stop_event = multiprocessing.Event()
            self.shared_buffer = MotorStateBuffer(create=True)
            
            use_mock = platform.system() == "Darwin"
            
            self.flight_process = multiprocessing.Process(
                target=flight_loop,
                args=(
                    self.stop_event,
                    use_mock,
                    coeffs,
                    BASE_FREQUENCY,
                    omega_per_motor,
                    None,
                    0.0,
                    0.0,
                    1.0,
                    True,
                    40,
                    slew_limit_override,
                    output_pwm_min,
                    output_pwm_max,
                    enable_tach,
                    pwm_compensation,
                    fixed_pwm_overrides,
                ),
                name="FlightLoop",
                daemon=False
            )
            self.flight_process.start()
            
            time.sleep(0.5)
            
            start_time = time.perf_counter()
            while self.flight_process.is_alive():
                time.sleep(0.1)
                if self.stop_event.is_set():
                    break
                if time.perf_counter() - start_time >= duration:
                    self.stop_event.set()
                    break
            
            self.flight_process.join(timeout=2)
            if self.flight_process.is_alive():
                self.flight_process.terminate()
                self.flight_process.join()
            
            self.shared_buffer.close()
            self.shared_buffer.unlink()
            
        except Exception as e:
            print(f"[GUI] Experiment error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            QTimer.singleShot(0, self.experiment_finished)
    
    def start_live_monitor(self):
        """Start live monitoring with fresh data."""
        # Clear previous data for a fresh start
        self.clear_monitor_data()
        # Reset monitor buffer so we attach to the new shared memory
        if hasattr(self, '_monitor_buffer'):
            delattr(self, '_monitor_buffer')
        
        # Reset or create timer
        if self.monitor_timer is not None:
            self.monitor_timer.stop()
            self.monitor_timer = None
        
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.update_live_monitor)
        self.monitor_timer.start(100)  # 10 Hz GUI update; hardware loop still runs at 400 Hz
    
    def update_live_monitor(self):
        """Update live monitor plot with oscilloscope-style continuous timeline."""
        if not self.experiment_running or self.shared_buffer is None:
            # Stop timer if experiment is no longer running
            if self.monitor_timer is not None:
                self.monitor_timer.stop()
            return
        
        try:
            import time
            # Use experiment start time (never changes) for continuous timeline
            if self.experiment_start_time is None:
                self.experiment_start_time = time.perf_counter()
            
            # Current elapsed time since experiment started
            current_time = time.perf_counter() - self.experiment_start_time
            
            # Attach to shared memory if not already
            if not hasattr(self, '_monitor_buffer'):
                self._monitor_buffer = MotorStateBuffer(create=False)
            
            pwm_values, tach_hz = self._monitor_buffer.get_state()
            monitor_signal = self.monitor_signal.currentText()
            
            # Get value based on monitor type
            if self.monitor_type.currentText() == "Individual Motor":
                motor_id = self.monitor_motor_select.currentIndex()
                pwm_value = pwm_values[motor_id]
                tach_value = tach_hz[motor_id]
            else:  # Group Average
                group_index = self.monitor_group_select.currentIndex()
                if 0 <= group_index < len(self.groups):
                    group = self.groups[group_index]
                    if len(group.motors) > 0:
                        group_pwms = [pwm_values[m] for m in group.motors]
                        pwm_value = np.mean(group_pwms)
                        group_tach = [tach_hz[m] for m in group.motors if np.isfinite(tach_hz[m])]
                        tach_value = np.mean(group_tach) if group_tach else np.nan
                    else:
                        pwm_value = PWM_MIN
                        tach_value = np.nan
                else:
                    pwm_value = PWM_MIN
                    tach_value = np.nan

            if monitor_signal == "PWM":
                plot_value = pwm_value
            elif monitor_signal == "Tach Hz":
                plot_value = tach_value
            else:
                plot_value = tach_value * 60.0 / TACH_PULSES_PER_REV
            
            self.monitor_data_time.append(current_time)
            self.monitor_data_value.append(plot_value)
            
            # Update plot with sliding 5-second window
            time_data = list(self.monitor_data_time)
            value_data = list(self.monitor_data_value)
            self.plot_curve.setData(time_data, value_data)
            
            # Auto-scale X-axis to show last 5 seconds (sliding window)
            if len(time_data) > 0:
                max_time = time_data[-1]
                min_time = max(0, max_time - 5.0)  # Show 5-second window
                self.plot_widget.setXRange(min_time, max_time + 0.5, padding=0)
            
        except Exception as e:
            print(f"[Monitor] Error: {e}")
    
    def stop_experiment(self):
        """Stop the running experiment immediately."""
        if self.experiment_running and self.stop_event:
            print("[GUI] Stop button pressed - stopping experiment...")
            self.stop_event.set()
            
            # Stop live monitoring timer completely
            if self.monitor_timer is not None:
                self.monitor_timer.stop()
                self.monitor_timer = None  # Reset timer object
            if hasattr(self, '_monitor_buffer'):
                delattr(self, '_monitor_buffer')
            
            self.set_experiment_status("Stopping", "stopping")
    
    def experiment_finished(self):
        """Called when experiment finishes."""
        self.stop_operation_timer()
        self.experiment_running = False
        
        # Stop and clear live monitoring
        if self.monitor_timer is not None:
            self.monitor_timer.stop()
        
        # Reset experiment timeline for next experiment
        self.experiment_start_time = None
        self.clear_monitor_data()
        self.reset_wall_render()
        if hasattr(self, '_monitor_buffer'):
            delattr(self, '_monitor_buffer')
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.set_experiment_status("Finished", "ready")
        
        # Stop live monitoring
        if self.monitor_timer:
            self.monitor_timer.stop()
        
        # Re-enable configuration
        self.groups_list.setEnabled(True)
        self.signal_type.setEnabled(True)
        self.output_pwm_preset.setEnabled(True)
        self.output_pwm_min.setEnabled(True)
        self.output_pwm_max.setEnabled(True)
        self.telemetry_mode.setEnabled(True)
        self.set_bench_controls_enabled(True)
        self.set_calibration_controls_enabled(True)
        for btn in self.motor_buttons:
            btn.setEnabled(True)
        
        QMessageBox.information(self, "Experiment Complete", 
                              "Experiment finished! Check the logs folder for data.")

    def start_bench_test(self):
        """Run a single-motor hardware test from the GUI."""
        if self.experiment_running:
            QMessageBox.warning(
                self,
                "Experiment Running",
                "Stop the experiment before running a motor test.",
            )
            return
        if self.calibration_running:
            QMessageBox.warning(
                self,
                "Calibration Active",
                "Stop calibration before running a motor test.",
            )
            return
        if self.bench_test_running:
            return

        motor_id = self.bench_motor_select.currentIndex()
        pwm_us = float(self.bench_pwm.value())
        duration_s = float(self.bench_duration.value())
        enable_tach = self.tach_return_enabled()

        if pwm_us <= PWM_MIN:
            QMessageBox.warning(
                self,
                "PWM Too Low",
                f"Choose a PWM value above {PWM_MIN}us for a spin test.",
            )
            return

        self.bench_test_running = True
        self.bench_stop_event = threading.Event()
        self.set_bench_controls_enabled(False)
        self.set_calibration_controls_enabled(False)
        self.bench_stop_btn.setEnabled(True)
        self.start_btn.setEnabled(False)
        self.set_bench_status(f"Arming Motor {motor_id + 1}", "running")
        self.start_operation_timer(duration_s)

        self.bench_test_thread = threading.Thread(
            target=self.run_bench_test_thread,
            args=(motor_id, pwm_us, duration_s, enable_tach, self.bench_stop_event),
            daemon=True,
        )
        self.bench_test_thread.start()

    def run_bench_test_thread(self, motor_id, pwm_us, duration_s, enable_tach, stop_event):
        """Send idle, then a fixed PWM command to one motor."""
        import time

        interval_s = 1.0 / UPDATE_RATE_HZ
        tach_poll_interval_frames = max(1, int(round(UPDATE_RATE_HZ / max(1, TACH_POLL_HZ))))
        idle_pwm = np.full(NUM_MOTORS, float(PWM_MIN))
        active_pwm = idle_pwm.copy()
        active_pwm[motor_id] = pwm_us
        hardware = None
        message = f"Motor {motor_id + 1} test finished."
        is_error = False

        try:
            use_mock = platform.system() == "Darwin"
            hardware = HardwareInterface(use_mock=use_mock, enable_tach=enable_tach)
            if not use_mock and hardware.use_mock:
                raise RuntimeError("Hardware unavailable; SPI/GPIO sync fell back to mock")

            next_frame_time = time.perf_counter()
            arm_start_time = time.perf_counter()
            while not stop_event.is_set() and time.perf_counter() - arm_start_time < 3.0:
                hardware.send_pwm(idle_pwm)
                next_frame_time += interval_s
                sleep_time = next_frame_time - time.perf_counter()
                if sleep_time > 0:
                    time.sleep(sleep_time)

            if not stop_event.is_set():
                self.bench_status_signal.emit(
                    f"Running Motor {motor_id + 1} @ {int(pwm_us)}us",
                    "running",
                )

            run_start_time = time.perf_counter()
            next_frame_time = run_start_time
            run_frame = 0
            while not stop_event.is_set() and time.perf_counter() - run_start_time < duration_s:
                hardware.send_pwm(active_pwm)
                run_frame += 1
                if enable_tach and run_frame % tach_poll_interval_frames == 0:
                    tach_hz = hardware.read_tach_all(active_pwm)
                    motor_hz = tach_hz[motor_id]
                    if np.isfinite(motor_hz):
                        motor_rpm = motor_hz * 60.0 / TACH_PULSES_PER_REV
                        self.bench_status_signal.emit(
                            f"Motor {motor_id + 1}: {int(pwm_us)}us | {motor_hz:.1f} Hz / {motor_rpm:.0f} RPM",
                            "running",
                        )
                next_frame_time += interval_s
                sleep_time = next_frame_time - time.perf_counter()
                if sleep_time > 0:
                    time.sleep(sleep_time)

            if stop_event.is_set():
                message = f"Motor {motor_id + 1} test stopped."

        except Exception as e:
            message = f"Motor test failed: {e}"
            is_error = True

        finally:
            if hardware is not None:
                try:
                    for _ in range(40):
                        hardware.send_pwm(idle_pwm)
                        time.sleep(interval_s)
                except Exception:
                    pass
                hardware.close()

        self.bench_test_finished_signal.emit(message, is_error)

    def stop_bench_test(self):
        """Stop an active motor test and reset outputs to idle."""
        if self.bench_test_running and self.bench_stop_event:
            self.bench_stop_event.set()
            self.bench_stop_btn.setEnabled(False)
            self.set_bench_status("Stopping...", "stopping")

    def on_bench_test_finished(self, message, is_error):
        """Restore GUI state after a motor test ends."""
        self.stop_operation_timer()
        self.bench_test_running = False
        self.bench_test_thread = None
        self.bench_stop_event = None
        self.set_bench_controls_enabled(True)
        self.set_calibration_controls_enabled(True)
        self.bench_stop_btn.setEnabled(False)
        self.start_btn.setEnabled(True)
        self.set_bench_status(message, "error" if is_error else "idle")

        if is_error:
            QMessageBox.warning(self, "Motor Test Error", message)


def main_gui():
    """Main entry point for GUI."""
    multiprocessing.set_start_method('fork', force=True)

    if (
        platform.system() == "Linux"
        and os.environ.get("XDG_SESSION_TYPE") == "wayland"
        and os.environ.get("DISPLAY")
        and not os.environ.get("QT_QPA_PLATFORM")
    ):
        os.environ["QT_QPA_PLATFORM"] = "xcb"
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    font = QFont("Arial", 10)
    app.setFont(font)
    
    window = WindWallGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main_gui()
