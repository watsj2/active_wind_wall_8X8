"""German 6x6-derived operator GUI for the Coaxial 8x8x2 windwall."""

from __future__ import annotations

import json
import sys
import time
from collections import deque
from statistics import mean

from PyQt6.QtCore import QEvent, QPoint, QRect, QRectF, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QKeySequence, QPainter, QPen, QPixmap, QShortcut
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
    QLayout,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRubberBand,
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
    GRID_COLS,
    GRID_ROWS,
    GUI_REFRESH_HZ,
    GUI_PRESETS_PATH,
    LAYER_LABELS,
    NUM_MOTORS,
    PROJECT_ROOT,
    PWM_IDLE,
    PWM_MAX,
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
from coaxial_windwall.hardware.interface import LatestFrameDispatcher
from coaxial_windwall.model import CoaxialAddress
from coaxial_windwall.gui.group_library import GroupLibraryDialog, template_motors


MAX_GROUPS = 32

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

ASSIGN_BOTH = "Both planes"
ASSIGN_FRONT = "Upstream plane only"
ASSIGN_BACK = "Downstream plane only"

MONITOR_UPSTREAM = "Selected upstream plane"
MONITOR_DOWNSTREAM = "Selected downstream plane"


APP_STYLESHEET = """
QWidget { color: #dedfe1; font-family: 'DejaVu Sans'; font-size: 12px; }
QMainWindow, QWidget#AppRoot, QDialog { background: #101113; }
QFrame#TopBar { background: #101113; border: none; border-bottom: 1px solid #34373b; }
QFrame#BottomBar { background: #191b1e; border: 1px solid #34373b; border-radius: 10px; }
QFrame#Section { background: #191b1e; border: 1px solid #34373b; border-radius: 14px; }
QFrame#Subsection { background: transparent; border-top: 1px solid #34373b; }
QLabel { background: transparent; }
QLabel#Title { color: #f5f5f7; font-size: 27px; font-weight: 700; }
QLabel#BrandLogo { background: transparent; }
QLabel#SectionTitle { color: #f5f5f7; font-size: 15px; font-weight: 700; }
QLabel#Caption { color: #999da4; font-size: 11px; }
QLabel#Value { color: #e6e7e9; font-size: 13px; font-weight: 600; }
QLabel#Clock { color: #e6e7e9; font-size: 26px; font-family: 'DejaVu Sans Mono'; }
QLabel#Status[state="armed"] { color: #ffe0a1; background: #40321d; border-color: #806638; }
QLabel#Status[state="running"] { color: #a4efd4; background: #19382c; border-color: #497d63; }
QLabel#Status { color: #87dac4; background: #193330; border: 1px solid #31544c;
    border-radius: 10px; padding: 6px 12px; font-size: 11px; font-weight: 700; }
QPushButton { background: #292c30; color: #e1e2e5; border: 1px solid #41454b;
    border-radius: 7px; padding: 9px 10px; font-weight: 600; }
QPushButton:hover { background: #373b40; border-color: #858c95; }
QPushButton:disabled { background: #202226; color: #737880; border-color: #34383e; }
QPushButton#Primary { background: #d0d7c3; border-color: #d0d7c3; color: #20251c; }
QPushButton#Primary:hover { background: #e3e8da; }
QPushButton#Arm { background: #30352d; border: 1px solid #717967; color: #e7ebdf;
    padding: 4px 12px; font-size: 11px; }
QPushButton#Arm[state="armed"] { background: #483620; border-color: #b58a45; color: #ffe0a1; }
QPushButton#Arm[state="running"] { background: #1b4037; border-color: #63b99f; color: #a4efd4; }
QPushButton#Stop { background: #451f2a; color: #ffc1c7; border: 1px solid #b35b68;
    padding: 4px 12px; font-size: 11px; font-weight: 700; }
QPushButton#Stop:hover { background: #682b38; border-color: #ea8c99; }
QPushButton#ExperimentToggle { background: #d0d7c3; color: #20251c; border: 1px solid #d0d7c3;
    border-radius: 10px; min-height: 64px; padding: 0 8px; font-size: 15px; font-weight: 700; }
QPushButton#ExperimentToggle:hover { background: #e3e8da; }
QPushButton#ExperimentToggle[running="true"] { background: #702d39; color: #ffe4e8; border-color: #d27685; }
QPushButton#ExperimentToggle:disabled { background: #2a2e29; color: #92998c; border-color: #52594b; }
QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit { background: #121416; color: #e5e7eb;
    border: 1px solid #41454b; border-radius: 6px; padding: 5px 7px; min-height: 23px; }
QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus { border-color: #d0d7c3; }
QComboBox QAbstractItemView, QListWidget, QTableWidget { background: #141619;
    color: #e1e2e5; border: 1px solid #41454b; border-radius: 6px;
    selection-background-color: #343b32; selection-color: #f5f5f7; }
QListWidget::item { padding: 10px 6px; border-bottom: 1px solid #292c30; }
QHeaderView::section { background: #2c2f33; color: #b4b8bf; border: 0; padding: 5px; }
QCheckBox { color: #b1b5bc; spacing: 7px; font-size: 11px; }
QScrollArea { border: 0; background: transparent; }
QWidget#ScrollContent, QScrollArea QWidget#qt_scrollarea_viewport { background: #191b1e; }
QScrollBar:vertical { background: #191b1e; width: 7px; }
QScrollBar::handle:vertical { background: #4b4f55; border-radius: 3px; min-height: 25px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""


class PairCell(QWidget):
    """Wind pixel with direct upstream, pair, and downstream targets."""

    clicked = pyqtSignal(int, int, str)
    DISPLAY_LABEL_POINT_SIZE = 15
    MINIMUM_SIDE = 64

    def __init__(self, row: int, col: int) -> None:
        super().__init__()
        self.row = row
        self.col = col
        self.display_number = CoaxialAddress(row, col, 0).pixel_number
        self.display_label = f"{self.display_number:02d}"
        self.front_color: str | None = None
        self.back_color: str | None = None
        self.front_pwm = PWM_IDLE
        self.back_pwm = PWM_IDLE
        self.selected = False
        front = CoaxialAddress(row, col, 0)
        back = CoaxialAddress(row, col, 1)
        if front.controller_index != back.controller_index:
            raise ValueError("A wind-pixel pair must use one Pico controller")
        self.front_motor_index = front.motor_index
        self.back_motor_index = back.motor_index
        self.controller_index = front.controller_index
        self.controller_label = front.controller_label
        self.pico_label = f"Pico {front.controller_number:02d}"
        self.controller_overlay = False
        self.hover_scope: str | None = None
        self.setMinimumSize(self.MINIMUM_SIDE, self.MINIMUM_SIDE)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(
            f"{self.display_label} / R{row + 1}C{col + 1} · "
            f"click or start a box drag on UP for Upstream {front.label}, "
            f"the number for both, or DN for Downstream {back.label} · "
            f"Pico {self.controller_label}"
        )

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(90, 90)

    def set_state(
        self,
        front_color: str | None,
        back_color: str | None,
        front_pwm: int,
        back_pwm: int,
        selected: bool,
    ) -> None:
        state = (front_color, back_color, front_pwm, back_pwm, selected)
        current = (
            self.front_color,
            self.back_color,
            self.front_pwm,
            self.back_pwm,
            self.selected,
        )
        if state != current:
            (
                self.front_color,
                self.back_color,
                self.front_pwm,
                self.back_pwm,
                self.selected,
            ) = state
            self.update()

    def set_controller_overlay(self, visible: bool) -> None:
        visible = bool(visible)
        if visible != self.controller_overlay:
            self.controller_overlay = visible
            self.update()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(
                self.row,
                self.col,
                self.assignment_scope_at(event.position().y()),
            )
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        scope = self.assignment_scope_at(event.position().y())
        if scope != self.hover_scope:
            self.hover_scope = scope
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        if self.hover_scope is not None:
            self.hover_scope = None
            self.update()
        super().leaveEvent(event)

    def assignment_scope_at(self, y: float) -> str:
        third = max(1.0, self.height() / 3.0)
        if y < third:
            return ASSIGN_FRONT
        if y >= third * 2.0:
            return ASSIGN_BACK
        return ASSIGN_BOTH

    def _zone_rects(self) -> tuple[QRectF, QRectF, QRectF]:
        content = QRectF(self.rect().adjusted(5, 5, -5, -5))
        gap = 3.0
        zone_height = max(1.0, (content.height() - gap * 2.0) / 3.0)
        upstream = QRectF(content.left(), content.top(), content.width(), zone_height)
        pair = QRectF(
            content.left(),
            upstream.bottom() + gap,
            content.width(),
            zone_height,
        )
        downstream = QRectF(
            content.left(),
            pair.bottom() + gap,
            content.width(),
            zone_height,
        )
        return upstream, pair, downstream

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)
        border = "#d0d7c3" if self.selected else "#393d42"
        border_width = 2 if self.selected else 1
        painter.setPen(QPen(QColor(border), border_width))
        painter.setBrush(QColor("#1c1f22"))
        painter.drawRoundedRect(QRectF(rect), 6, 6)

        upstream_rect, pair_rect, downstream_rect = self._zone_rects()
        self._draw_layer(
            painter,
            upstream_rect,
            "UP",
            self.front_color,
            self.front_pwm,
            self.hover_scope == ASSIGN_FRONT,
        )

        painter.setPen(Qt.PenStyle.NoPen)
        pair_fill = QColor("#1c1f22")
        if self.hover_scope == ASSIGN_BOTH:
            pair_fill = pair_fill.lighter(135)
        painter.setBrush(pair_fill)
        painter.drawRoundedRect(pair_rect, 2, 2)
        font = QFont(self.font())
        font.setPointSize(max(12, min(self.DISPLAY_LABEL_POINT_SIZE, int(self.width() * 15 / 74))))
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor("#edf1ea"))
        number_rect = QRectF(pair_rect)
        if self.controller_overlay:
            number_rect.setWidth(pair_rect.width() * 0.43)
        painter.drawText(number_rect, Qt.AlignmentFlag.AlignCenter, self.display_label)
        if self.controller_overlay:
            pico_rect = QRectF(pair_rect)
            pico_rect.setLeft(number_rect.right() + 2)
            font.setPointSizeF(7.5 if self.width() >= 74 else 6.5)
            font.setBold(False)
            painter.setFont(font)
            painter.setPen(QColor("#a4a9ad"))
            painter.drawText(pico_rect, Qt.AlignmentFlag.AlignCenter, self.pico_label)

        self._draw_layer(
            painter,
            downstream_rect,
            "DN",
            self.back_color,
            self.back_pwm,
            self.hover_scope == ASSIGN_BACK,
        )

    def _draw_layer(
        self,
        painter: QPainter,
        rect: QRectF,
        label: str,
        color: str | None,
        pwm: int,
        hovered: bool,
    ) -> None:
        painter.setPen(Qt.PenStyle.NoPen)
        fill = QColor("#25292d")
        if color:
            accent = QColor(color)
            fill = QColor(
                int(fill.red() * 0.82 + accent.red() * 0.18),
                int(fill.green() * 0.82 + accent.green() * 0.18),
                int(fill.blue() * 0.82 + accent.blue() * 0.18),
            )
        if hovered:
            fill = fill.lighter(130)
        painter.setBrush(fill)
        painter.drawRoundedRect(rect, 2, 2)
        font = QFont(self.font())
        if color:
            painter.setBrush(QColor(color))
            painter.drawRoundedRect(QRectF(rect.left(), rect.top() + 3, 3, rect.height() - 6), 1, 1)
        font.setPointSize(8)
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(QColor("#e4e7eb" if color else "#9ba2a9"))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{label}  {pwm}")


class SquareGridLayout(QLayout):
    """Place equal square cells in the layout pass, without resize feedback."""

    def __init__(self, parent):
        super().__init__(parent)
        self.items = []

    def addItem(self, item):  # noqa: N802
        self.items.append(item)
        self.invalidate()

    def count(self):
        return len(self.items)

    def itemAt(self, index):  # noqa: N802
        return self.items[index] if 0 <= index < len(self.items) else None

    def takeAt(self, index):  # noqa: N802
        return self.items.pop(index) if 0 <= index < len(self.items) else None

    def sizeHint(self):  # noqa: N802
        return QSize(8 * 90 + 52, 8 * 90 + 35)

    def minimumSize(self):  # noqa: N802
        return QSize(8 * PairCell.MINIMUM_SIDE + 52, 8 * PairCell.MINIMUM_SIDE + 35)

    def setGeometry(self, rect):  # noqa: N802
        super().setGeometry(rect)
        side = max(PairCell.MINIMUM_SIDE, min((rect.width() - 52) // 8, (rect.height() - 35) // 8))
        x = rect.x() + (rect.width() - (8 * side + 52)) // 2
        y = rect.y() + (rect.height() - (8 * side + 35)) // 2
        for index, item in enumerate(self.items):
            row, col = divmod(index, 8)
            item.setGeometry(QRect(x + col * (side + 5) + (17 if col >= 4 else 0),
                                   y + row * (side + 5), side, side))


class MotorCellGrid(QWidget):
    """Responsive 8x8 square grid with a central left/right gutter."""

    cells_selected = pyqtSignal(object, str)

    def __init__(self) -> None:
        super().__init__()
        self.cells: list[PairCell] = []
        self.drag_origin: QPoint | None = None
        self.drag_scope = ASSIGN_BOTH
        self.dragging = False
        self.rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self.rubber_band.setStyleSheet(
            "QRubberBand {"
            " background-color: rgba(129, 146, 121, 72);"
            " border: 1px solid #a8b99e;"
            "}"
        )
        self.grid = SquareGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(5)
        minimum = PairCell.MINIMUM_SIDE * GRID_COLS + self.grid.spacing() * (
            GRID_COLS - 1
        )
        self.setMinimumSize(minimum + 17, minimum)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

    def add_cell(self, cell: PairCell, row: int, col: int) -> None:
        self.cells.append(cell)
        cell.installEventFilter(self)
        self.grid.addWidget(cell)

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        if not isinstance(watched, PairCell):
            return super().eventFilter(watched, event)

        event_type = event.type()
        if (
            event_type == QEvent.Type.MouseButtonPress
            and event.button() == Qt.MouseButton.LeftButton
        ):
            point = watched.mapTo(self, event.position().toPoint())
            self._begin_drag(point, watched.assignment_scope_at(event.position().y()))
        elif event_type == QEvent.Type.MouseMove and self.drag_origin is not None:
            point = watched.mapTo(self, event.position().toPoint())
            self._update_drag(point)
            return self.dragging
        elif (
            event_type == QEvent.Type.MouseButtonRelease
            and event.button() == Qt.MouseButton.LeftButton
            and self.drag_origin is not None
        ):
            point = watched.mapTo(self, event.position().toPoint())
            if self.dragging:
                self._finish_drag(point)
                return True
            self._reset_drag()
        return super().eventFilter(watched, event)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self.drag_origin is None
        ):
            self._begin_drag(event.position().toPoint(), ASSIGN_BOTH)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self.drag_origin is not None:
            self._update_drag(event.position().toPoint())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self.drag_origin is not None
        ):
            if self.dragging:
                self._finish_drag(event.position().toPoint())
            else:
                self._reset_drag()
        super().mouseReleaseEvent(event)

    def _begin_drag(self, point: QPoint, scope: str) -> None:
        self.drag_origin = point
        self.drag_scope = scope
        self.dragging = False
        self.rubber_band.hide()

    def _selection_rect(self, point: QPoint) -> QRect:
        if self.drag_origin is None:
            return QRect()
        return QRect(self.drag_origin, point).normalized()

    def _update_drag(self, point: QPoint) -> None:
        if self.drag_origin is None:
            return
        distance = (point - self.drag_origin).manhattanLength()
        if not self.dragging and distance < QApplication.startDragDistance():
            return
        self.dragging = True
        self.rubber_band.setGeometry(self._selection_rect(point))
        self.rubber_band.show()

    def _finish_drag(self, point: QPoint) -> None:
        selection = self._selection_rect(point)
        scope = self.drag_scope
        selected = [
            (cell.row, cell.col)
            for cell in self.cells
            if selection.intersects(cell.geometry())
        ]
        self._reset_drag()
        if selected:
            self.cells_selected.emit(selected, scope)

    def _reset_drag(self) -> None:
        self.rubber_band.hide()
        self.drag_origin = None
        self.dragging = False



class SignalPlot(QWidget):
    """Small dependency-free oscilloscope used for preview and live PWM."""

    def __init__(self) -> None:
        super().__init__()
        self.points: list[tuple[float, int]] = []
        self.output_max = PWM_UI_MAX
        self.setMinimumHeight(100)

    def set_points(self, points: list[tuple[float, int]], output_max: int) -> None:
        self.points = points
        self.output_max = max(PWM_IDLE + 1, output_max)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(48, 12, -15, -28)
        painter.fillRect(self.rect(), QColor("#1c1f22"))
        painter.setPen(QPen(QColor("#273128"), 1))
        for index in range(5):
            y = rect.top() + index * rect.height() / 4
            painter.drawLine(rect.left(), int(y), rect.right(), int(y))
        painter.setPen(QColor("#849084"))
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
        painter.setPen(QPen(QColor("#9bb987"), 2))
        for first, second in zip(path_points, path_points[1:]):
            painter.drawLine(first[0], first[1], second[0], second[1])
        painter.setPen(QColor("#849084"))
        painter.drawText(rect.left(), self.height() - 8, f"{t_min:.1f} s")
        painter.drawText(rect.right() - 38, self.height() - 8, f"{t_max:.1f} s")


class CoaxialWindwallWindow(QMainWindow):
    """8x8x2 extrapolation of the original German group/signal GUI."""

    def __init__(self, *, hardware: HardwareInterface | None = None) -> None:
        super().__init__()
        self.setWindowTitle("Windwall")
        self.resize(1600, 1000)

        self.hardware = hardware if hardware is not None else HardwareInterface()
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
        self.ui_timer.setInterval(max(1, int(1000 / GUI_REFRESH_HZ)))
        self.ui_timer.timeout.connect(self.refresh_runtime)
        self.ui_timer.start()
        self.frame_dispatcher = LatestFrameDispatcher(self.hardware)
        self.hardware_failure_reported = False

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
        brand = QHBoxLayout()
        brand.setSpacing(12)
        self.brand_logo = QLabel()
        self.brand_logo.setObjectName("BrandLogo")
        logo_pixmap = QPixmap(
            str(PROJECT_ROOT / "assets" / "branding" / "rival_lab_logo_white.png")
        )
        if not logo_pixmap.isNull():
            self.brand_logo.setPixmap(
                logo_pixmap.scaledToHeight(
                    58, Qt.TransformationMode.SmoothTransformation
                )
            )
        self.brand_logo.setFixedSize(75, 58)
        self.brand_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.brand_logo.setToolTip("Rival Lab")
        brand.addWidget(self.brand_logo)
        self.brand_title = QLabel("Windwall")
        self.brand_title.setObjectName("Title")
        brand_text = QVBoxLayout()
        brand_text.setSpacing(1)
        brand_text.addWidget(self.brand_title)
        subtitle = QLabel("RIVAL LAB   /   8 × 8 × 2")
        subtitle.setObjectName("Caption")
        brand_text.addWidget(subtitle)
        brand.addLayout(brand_text)
        layout.addLayout(brand)
        layout.addStretch(1)
        self.status_badge = QLabel("DISARMED")
        self.status_badge.setObjectName("Status")
        self.status_badge.setFixedHeight(30)
        layout.addWidget(self.status_badge)
        self.timer_label = QLabel("00:00.0")
        self.timer_label.setObjectName("Clock")
        self.timer_label.setMinimumWidth(145)
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.timer_label)

        self.safety_controls = QVBoxLayout()
        self.safety_controls.setContentsMargins(0, 0, 0, 0)
        self.safety_controls.setSpacing(4)
        self.emergency_stop_button = QPushButton("EMERGENCY STOP")
        self.emergency_stop_button.setObjectName("Stop")
        self.emergency_stop_button.setFixedSize(210, 30)
        self.emergency_stop_button.setToolTip("Stop, send idle, and disarm (Esc)")
        self.emergency_stop_button.clicked.connect(self.emergency_stop)
        self.safety_controls.addWidget(self.emergency_stop_button)
        self.arm_button = QPushButton("ARM SYSTEM")
        self.arm_button.setObjectName("Arm")
        self.arm_button.setFixedSize(210, 30)
        self.arm_button.setToolTip("Arm or disarm motor output")
        self.arm_button.clicked.connect(self.toggle_arm)
        self.safety_controls.addWidget(self.arm_button)
        layout.addLayout(self.safety_controls)
        return bar

    def build_group_signal_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("Section")
        panel.setFixedWidth(235)
        outer = QVBoxLayout(panel)
        outer.setContentsMargins(16, 16, 16, 16)
        title = QLabel("Motor groups")
        title.setObjectName("SectionTitle")
        outer.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        content.setObjectName("ScrollContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 4, 4, 0)
        layout.setSpacing(8)

        self.group_list = QListWidget()
        self.group_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.group_list.setTextElideMode(Qt.TextElideMode.ElideRight)
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

        self.library_button = QPushButton("New from template…")
        self.library_button.clicked.connect(self.open_group_library)
        layout.addWidget(self.library_button)

        self.group_name = QLineEdit()
        self.group_name.editingFinished.connect(self.rename_group)
        layout.addWidget(self.labeled("Group name", self.group_name))

        group_layout = layout
        self.signal_panel = QWidget()
        layout = QVBoxLayout(self.signal_panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        signal_title = QLabel("Selected group signal")
        signal_title.setObjectName("SectionTitle")
        layout.addWidget(signal_title)
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
        layout.addWidget(self.labeled("Fourier baseline", self.constant))

        self.constant_pwm = QSpinBox()
        self.constant_pwm.setRange(PWM_IDLE, PWM_MAX)
        self.constant_pwm.setSingleStep(10)
        self.constant_pwm.setValue(1400)
        self.constant_pwm.setSuffix(" us")
        self.constant_pwm.setToolTip(
            "Exact PWM command for Constant mode (1000-2000 us)"
        )
        self.constant_pwm.valueChanged.connect(self.signal_controls_changed)
        layout.addWidget(self.labeled("Constant PWM", self.constant_pwm))

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
        self.harmonic_controls = QWidget()
        harmonic_buttons = QHBoxLayout(self.harmonic_controls)
        harmonic_buttons.setContentsMargins(0, 0, 0, 0)
        add_harmonic = QPushButton("Add harmonic")
        add_harmonic.clicked.connect(self.add_harmonic)
        remove_harmonic = QPushButton("Remove")
        remove_harmonic.clicked.connect(self.remove_harmonic)
        harmonic_buttons.addWidget(add_harmonic)
        harmonic_buttons.addWidget(remove_harmonic)
        layout.addWidget(self.harmonic_controls)

        layout = group_layout
        preset_buttons = QHBoxLayout()
        save_button = QPushButton("Save preset…")
        save_button.clicked.connect(self.save_preset_as)
        load_button = QPushButton("Load…")
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
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)
        header = QHBoxLayout()
        title = QLabel("Motor array")
        title.setObjectName("SectionTitle")
        header.addWidget(title)
        header.addStretch(1)
        self.show_pico_grid = QCheckBox("Show Pico grid")
        self.show_pico_grid.setToolTip(
            "Show small Pico 01-16 labels beside the physical pair numbers"
        )
        self.show_pico_grid.toggled.connect(self.set_pico_grid_visible)
        header.addWidget(self.show_pico_grid)
        layout.addLayout(header)

        caption = QLabel(
            "Click or drag a box from UP, the number (both), or DN"
        )
        caption.setObjectName("Caption")
        caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(caption)

        self.cell_grid = MotorCellGrid()
        self.cell_grid.cells_selected.connect(self.assign_pixels)
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                cell = PairCell(row, col)
                cell.clicked.connect(self.assign_pixel)
                self.cells[(row, col)] = cell
                self.cell_grid.add_cell(cell, row, col)
        patch_bar = QHBoxLayout()
        self.quick_scope = QComboBox()
        self.quick_scope.addItem("Both layers", (0, 1))
        self.quick_scope.addItem("Upstream", (0,))
        self.quick_scope.addItem("Downstream", (1,))
        patch_bar.addWidget(self.quick_scope)
        self.quick_buttons = {}
        for size in range(2, 8):
            key = f"square:{size}"
            button = QPushButton(f"{size} × {size}")
            button.setToolTip("Assign a centered patch to the selected group")
            button.clicked.connect(lambda checked=False, key=key: self.assign_quick_shape(key))
            self.quick_buttons[key] = button
            patch_bar.addWidget(button)
        layout.addLayout(patch_bar)
        grid_row = QHBoxLayout()
        grid_row.setSpacing(8)
        grid_row.addWidget(self.build_side_shortcuts("left"))
        grid_row.addWidget(self.cell_grid, 1)
        grid_row.addWidget(self.build_side_shortcuts("right"))
        layout.addLayout(grid_row, 1)
        halves = QLabel("LEFT HALF  ·  01–32                         RIGHT HALF  ·  33–64")
        halves.setObjectName("Caption")
        halves.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(halves)

        buttons = QHBoxLayout()
        assign_all_upstream = QPushButton("All upstream")
        assign_all_upstream.clicked.connect(
            lambda: self.assign_all(ASSIGN_FRONT)
        )
        assign_all_pairs = QPushButton("All pairs")
        assign_all_pairs.clicked.connect(lambda: self.assign_all(ASSIGN_BOTH))
        assign_all_downstream = QPushButton("All downstream")
        assign_all_downstream.clicked.connect(
            lambda: self.assign_all(ASSIGN_BACK)
        )
        clear_group = QPushButton("Clear selected group")
        clear_group.clicked.connect(self.clear_selected_group)
        clear_wall = QPushButton("Clear wall")
        clear_wall.clicked.connect(self.clear_wall)
        buttons.addWidget(assign_all_upstream)
        buttons.addWidget(assign_all_pairs)
        buttons.addWidget(assign_all_downstream)
        buttons.addWidget(clear_group)
        buttons.addWidget(clear_wall)
        layout.addLayout(buttons)
        return panel

    def build_side_shortcuts(self, side: str) -> QWidget:
        panel = QWidget()
        panel.setFixedWidth(102)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        title = QLabel(f"{side.upper()} SIDE")
        title.setObjectName("Caption")
        layout.addWidget(title)
        for label, layers in (("Both", (0, 1)), ("Upstream", (0,)), ("Downstream", (1,))):
            button = QPushButton(label)
            button.setToolTip(f"Assign the {side} half to the selected group: {label.lower()}")
            button.clicked.connect(lambda checked=False, side=side, layers=layers: self.assign_quick_shape(side, layers))
            self.quick_buttons[f"{side}:{label}"] = button
            layout.addWidget(button)
        layout.addSpacing(10)
        label = QLabel("PICO")
        label.setObjectName("Caption")
        layout.addWidget(label)
        numbers = (1, 2, 3, 4, 9, 10, 11, 12) if side == "left" else (5, 6, 7, 8, 13, 14, 15, 16)
        for number in numbers:
            key = f"pico:{number}"
            button = QPushButton(f"Pico {number:02d}")
            button.clicked.connect(lambda checked=False, key=key: self.assign_quick_shape(key))
            self.quick_buttons[key] = button
            layout.addWidget(button)
        layout.addStretch(1)
        return panel

    def assign_quick_shape(self, key: str, layers: tuple[int, ...] | None = None) -> None:
        if self.experiment_running or self.selected_group() is None:
            return
        if layers is None:
            layers = self.quick_scope.currentData()
        origin = (8 - int(key.split(":")[1])) // 2 if key.startswith("square:") else 0
        motors = template_motors(key, layers, origin, origin)
        index = self.selected_group_index
        for motor in motors:
            self.motor_owner[motor] = index
        self.rebuild_group_members()
        self.refresh_group_list()
        self.group_list.setCurrentRow(index)
        self.save_session()
        self.refresh_all()

    def set_pico_grid_visible(self, visible: bool) -> None:
        for cell in self.cells.values():
            cell.set_controller_overlay(visible)

    def build_experiment_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("Section")
        panel.setFixedWidth(280)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        outer = layout
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        content.setObjectName("ScrollContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 4, 0)
        layout.setSpacing(12)
        layout.addWidget(self.signal_panel)
        layout.addSpacing(10)
        title = QLabel("Experiment")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        self.duration = QSpinBox()
        self.duration.setRange(1, 3600)
        self.duration.setValue(10)
        self.duration.setSuffix(" s")
        layout.addWidget(self.labeled("Duration", self.duration))

        self.auto_disarm = QCheckBox("Auto-disarm after experiment")
        self.auto_disarm.setChecked(True)
        layout.addWidget(self.auto_disarm)

        self.start_button = QPushButton("START EXPERIMENT")
        self.start_button.setObjectName("ExperimentToggle")
        self.start_button.setMinimumHeight(68)
        self.start_button.setProperty("running", False)
        self.start_button.setToolTip("Start or stop the experiment")
        self.start_button.clicked.connect(self.toggle_experiment)
        layout.addWidget(self.start_button)

        summary = QFrame()
        summary.setObjectName("Subsection")
        summary_layout = QGridLayout(summary)
        summary_layout.setContentsMargins(0, 10, 0, 0)
        self.active_total = self.summary_row(summary_layout, 0, "Assigned", "0 / 128")
        self.active_front = self.summary_row(summary_layout, 1, "Upstream", "0 / 64")
        self.active_back = self.summary_row(summary_layout, 2, "Downstream", "0 / 64")
        self.frame_count = self.summary_row(summary_layout, 3, "Frames sent", "0")
        self.average_pwm = self.summary_row(summary_layout, 4, "Average PWM", "1000 us")
        layout.addWidget(summary)

        selected = QFrame()
        selected.setObjectName("Subsection")
        selected_layout = QVBoxLayout(selected)
        selected_layout.setContentsMargins(0, 10, 0, 0)
        selected_title = QLabel("Selected Pixel")
        selected_title.setObjectName("SectionTitle")
        selected_layout.addWidget(selected_title)
        self.selected_pair = QLabel()
        self.selected_pair.setObjectName("Value")
        self.selected_pair.setWordWrap(True)
        self.selected_pair.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        selected_layout.addWidget(self.selected_pair)
        layout.addWidget(selected)
        layout.addStretch(1)
        scroll.setWidget(content)
        outer.addWidget(scroll)
        return panel

    def build_monitor_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("BottomBar")
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(11, 9, 11, 9)
        title = QLabel("Live Monitor")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)
        self.monitor_mode = QComboBox()
        self.monitor_mode.addItems(
            [MONITOR_UPSTREAM, MONITOR_DOWNSTREAM, "Selected group average", "Wall average"]
        )
        self.monitor_mode.setFixedWidth(240)
        self.monitor_mode.currentIndexChanged.connect(self.preview_selected_signal)
        layout.addWidget(self.monitor_mode)
        self.monitor_value = QLabel("1000 us")
        self.monitor_value.setObjectName("Value")
        self.monitor_value.setMinimumWidth(72)
        layout.addWidget(self.monitor_value)
        self.monitor_plot_button = QPushButton("Show plot")
        self.monitor_plot_button.setFixedWidth(110)
        self.monitor_plot_button.clicked.connect(self.toggle_monitor_plot)
        layout.addWidget(self.monitor_plot_button)
        self.plot = SignalPlot()
        self.plot.setVisible(False)
        layout.addWidget(self.plot, 1)
        return panel

    def toggle_monitor_plot(self) -> None:
        show_plot = self.plot.isHidden()
        self.plot.setVisible(show_plot)
        self.monitor_plot_button.setText("Hide plot" if show_plot else "Show plot")

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
        value.setMinimumWidth(100)
        value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(label, row, 0)
        layout.addWidget(value, row, 1)
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
        if len(self.groups) >= MAX_GROUPS:
            QMessageBox.warning(self, "Group limit", f"A maximum of {MAX_GROUPS} groups is supported.")
            return
        group_name = name or f"Group {len(self.groups) + 1}"
        self.groups.append(SignalGroup(group_name, GROUP_COLORS[len(self.groups) % len(GROUP_COLORS)]))
        self.refresh_group_list()
        self.group_list.setCurrentRow(len(self.groups) - 1)
        self.save_session()

    def open_group_library(self) -> None:
        if self.experiment_running:
            return
        if len(self.groups) >= MAX_GROUPS:
            QMessageBox.warning(self, "Group limit", f"A maximum of {MAX_GROUPS} groups is supported.")
            return
        dialog = GroupLibraryDialog(self)
        if dialog.exec() == GroupLibraryDialog.DialogCode.Accepted:
            self.add_template_group(dialog.group_name(), dialog.selected_motors())

    def add_template_group(self, name: str, motors: set[int]) -> None:
        if self.experiment_running or len(self.groups) >= MAX_GROUPS:
            return
        if not motors or any(motor < 0 or motor >= NUM_MOTORS for motor in motors):
            raise ValueError("A premade group must contain valid wall motors")
        group_index = len(self.groups)
        self.groups.append(SignalGroup(
            name,
            GROUP_COLORS[group_index % len(GROUP_COLORS)],
            signal=GroupSignal(signal_type=SIGNAL_CONSTANT, constant_pwm_us=PWM_IDLE),
        ))
        for motor in motors:
            self.motor_owner[motor] = group_index
        self.rebuild_group_members()
        self.refresh_group_list()
        self.group_list.setCurrentRow(group_index)
        self.load_selected_group()
        self.save_session()
        self.refresh_all()

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
            item.setToolTip(f"{group.name}\n{len(group.motors)} motors")
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
        self.constant_pwm.setValue(int(signal.constant_pwm_us or PWM_IDLE))
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
            constant_pwm_us=self.constant_pwm.value(),
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
        self.constant.parentWidget().setVisible(signal_type == SIGNAL_CUSTOM)
        self.constant_pwm.parentWidget().setVisible(signal_type == SIGNAL_CONSTANT)
        self.duty.parentWidget().setVisible(signal_type == SIGNAL_SQUARE)
        self.harmonics.parentWidget().setVisible(signal_type == SIGNAL_CUSTOM)
        self.harmonic_controls.setVisible(signal_type == SIGNAL_CUSTOM)
        self.minimum.parentWidget().setVisible(signal_type != SIGNAL_CONSTANT)
        self.maximum.parentWidget().setVisible(signal_type != SIGNAL_CONSTANT)
        self.period.parentWidget().setVisible(signal_type != SIGNAL_CONSTANT)
        self.phase.parentWidget().setVisible(signal_type != SIGNAL_CONSTANT)

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

    def target_motor_indices(
        self,
        row: int,
        col: int,
        scope: str = ASSIGN_BOTH,
    ) -> tuple[int, ...]:
        front = CoaxialAddress(row, col, 0).motor_index
        back = CoaxialAddress(row, col, 1).motor_index
        if scope == ASSIGN_FRONT:
            return (front,)
        if scope == ASSIGN_BACK:
            return (back,)
        return front, back

    def assign_pixel(
        self,
        row: int,
        col: int,
        scope: str = ASSIGN_BOTH,
    ) -> None:
        self.assign_pixels([(row, col)], scope)

    def assign_pixels(
        self,
        pixels: list[tuple[int, int]],
        scope: str = ASSIGN_BOTH,
    ) -> None:
        if self.experiment_running:
            return
        group_index = self.selected_group_index
        if not 0 <= group_index < len(self.groups):
            return
        valid_pixels = list(
            dict.fromkeys(
                (row, col)
                for row, col in pixels
                if 0 <= row < GRID_ROWS and 0 <= col < GRID_COLS
            )
        )
        if not valid_pixels:
            return
        self.selected_row, self.selected_col = valid_pixels[0]
        targets = tuple(
            dict.fromkeys(
                motor_index
                for row, col in valid_pixels
                for motor_index in self.target_motor_indices(row, col, scope)
            )
        )
        remove = all(self.motor_owner[index] == group_index for index in targets)
        for motor_index in targets:
            self.motor_owner[motor_index] = None if remove else group_index
        self.rebuild_group_members()
        self.refresh_group_list()
        self.group_list.setCurrentRow(group_index)
        self.save_session()
        self.refresh_wall()
        self.refresh_summary()

    def assign_all(self, scope: str = ASSIGN_BOTH) -> None:
        if self.experiment_running:
            return
        group_index = self.selected_group_index
        if not 0 <= group_index < len(self.groups):
            return
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
        self.refresh_wall()
        self.refresh_summary()

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
        return PWM_MAX

    def quiesce_frame_dispatcher(self) -> None:
        """Discard stale runtime frames before a synchronous safety command."""

        self.frame_dispatcher.discard_pending()
        if not self.frame_dispatcher.wait_until_idle():
            raise TimeoutError("motor frame transport did not become idle")

    def toggle_arm(self) -> None:
        if self.is_armed:
            self.disarm()
        else:
            self.arm()

    def toggle_experiment(self) -> None:
        if self.experiment_running:
            self.stop_experiment()
        else:
            self.start_experiment()

    def arm(self) -> None:
        self.quiesce_frame_dispatcher()
        self.is_armed = True
        self.current_pwm = [PWM_IDLE] * NUM_MOTORS
        self.hardware.send_pwm_frame(self.current_pwm, output_armed=True)
        self.refresh_all()

    def disarm(self) -> None:
        if self.experiment_running:
            self.command_timer.stop()
            self.experiment_running = False
        self.quiesce_frame_dispatcher()
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
        self.command_tick(immediate=True)
        self.command_timer.start()
        self.refresh_all()

    def stop_experiment(self) -> None:
        if self.experiment_running and self.experiment_started_s is not None:
            self.last_elapsed_s = time.monotonic() - self.experiment_started_s
        self.command_timer.stop()
        self.experiment_running = False
        self.quiesce_frame_dispatcher()
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
        self.quiesce_frame_dispatcher()
        self.is_armed = False
        self.current_pwm = [PWM_IDLE] * NUM_MOTORS
        self.hardware.send_pwm_frame(self.current_pwm, output_armed=False)
        self.refresh_all()

    def elapsed_s(self) -> float:
        if self.experiment_running and self.experiment_started_s is not None:
            return time.monotonic() - self.experiment_started_s
        return self.last_elapsed_s

    def command_tick(self, *, immediate: bool = False) -> None:
        if not self.experiment_running or not self.is_armed:
            return
        elapsed = self.elapsed_s()
        if elapsed >= self.duration.value():
            self.stop_experiment()
            return
        self.current_pwm = build_group_frame(
            self.groups,
            elapsed,
            self.output_maximum(),
        )
        if immediate:
            self.quiesce_frame_dispatcher()
            self.hardware.send_pwm_frame(self.current_pwm, output_armed=True)
        elif not self.frame_dispatcher.submit(
            self.current_pwm,
            output_armed=True,
        ):
            failure = self.frame_dispatcher.failure()
            self.handle_dispatch_failure(failure or RuntimeError("frame dispatcher stopped"))
            return
        self.capture_monitor(elapsed)

    def handle_dispatch_failure(self, error: Exception) -> None:
        if self.hardware_failure_reported:
            return
        self.hardware_failure_reported = True
        self.command_timer.stop()
        self.experiment_running = False
        self.is_armed = False
        self.current_pwm = [PWM_IDLE] * NUM_MOTORS
        self.refresh_all()
        QMessageBox.critical(
            self,
            "Motor transport stopped",
            f"Motor commands stopped after a transport error:\n{error}",
        )

    def monitored_pwm(self) -> int:
        mode = self.monitor_mode.currentText()
        if mode == MONITOR_UPSTREAM:
            index = CoaxialAddress(self.selected_row, self.selected_col, 0).motor_index
            return self.current_pwm[index]
        if mode == MONITOR_DOWNSTREAM:
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
        self.plot.set_points(
            preview_signal(
                group.signal,
                duration,
                160,
                self.output_maximum(),
            ),
            self.output_maximum(),
        )

    def refresh_runtime(self) -> None:
        failure = self.frame_dispatcher.failure()
        if failure is not None:
            self.handle_dispatch_failure(failure)
            return
        elapsed = self.elapsed_s()
        minutes, seconds = divmod(elapsed, 60)
        self.timer_label.setText(f"{int(minutes):02d}:{seconds:04.1f}")
        if self.experiment_running:
            self.refresh_wall()
            if not self.plot.isHidden():
                self.plot.set_points(
                    list(self.monitor_samples),
                    self.output_maximum(),
                )
        self.monitor_value.setText(f"{self.monitored_pwm()} us")
        self.refresh_summary()

    def refresh_all(self) -> None:
        self.refresh_status()
        self.refresh_wall()
        self.refresh_summary()
        self.preview_selected_signal()

    def refresh_status(self) -> None:
        if self.experiment_running:
            arm_text = "SYSTEM RUNNING"
            arm_state = "running"
        elif self.is_armed:
            arm_text = "DISARM SYSTEM"
            arm_state = "armed"
        else:
            arm_text = "ARM SYSTEM"
            arm_state = "safe"
        self.arm_button.setText(arm_text)
        self.arm_button.setProperty("state", arm_state)
        self.arm_button.style().unpolish(self.arm_button)
        self.arm_button.style().polish(self.arm_button)
        self.arm_button.setEnabled(not self.experiment_running)
        self.library_button.setEnabled(not self.experiment_running)
        self.quick_scope.setEnabled(not self.experiment_running)
        for button in self.quick_buttons.values():
            button.setEnabled(not self.experiment_running)
        self.status_badge.setText("RUNNING" if self.experiment_running else "ARMED" if self.is_armed else "DISARMED")
        self.status_badge.setProperty("state", arm_state)
        self.status_badge.style().unpolish(self.status_badge)
        self.status_badge.style().polish(self.status_badge)
        self.start_button.setText(
            "STOP EXPERIMENT" if self.experiment_running else "START EXPERIMENT"
        )
        self.start_button.setProperty("running", self.experiment_running)
        self.start_button.style().unpolish(self.start_button)
        self.start_button.style().polish(self.start_button)
        self.start_button.setEnabled(self.is_armed)

    def refresh_wall(self) -> None:
        for cell in self.cells.values():
            front_owner = self.motor_owner[cell.front_motor_index]
            back_owner = self.motor_owner[cell.back_motor_index]
            front_color = (
                self.groups[front_owner].color if front_owner is not None else None
            )
            back_color = (
                self.groups[back_owner].color if back_owner is not None else None
            )
            cell.set_state(
                front_color,
                back_color,
                self.current_pwm[cell.front_motor_index],
                self.current_pwm[cell.back_motor_index],
                cell.row == self.selected_row and cell.col == self.selected_col,
            )
        front = CoaxialAddress(self.selected_row, self.selected_col, 0)
        back = CoaxialAddress(self.selected_row, self.selected_col, 1)
        display_label = f"{front.pixel_number:02d}"
        self.selected_pair.setText(
            f"{display_label} / R{front.row + 1}C{front.col + 1}\n"
            f"Upstream {front.label}: {front.controller_label} {front.controller_channel_label}\n"
            f"{self.current_pwm[front.motor_index]} us\n"
            f"Downstream {back.label}: {back.controller_label} {back.controller_channel_label}\n"
            f"{self.current_pwm[back.motor_index]} us"
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
            for index, item in enumerate(data["groups"][:MAX_GROUPS])
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
        dispatcher_stopped = self.frame_dispatcher.close()
        if dispatcher_stopped:
            self.hardware.shutdown()
        else:
            print(
                "Could not stop motor frame dispatcher before GUI shutdown",
                file=sys.stderr,
            )
        event.accept()


def run_app() -> int:
    app = QApplication(sys.argv[:1])
    app.setFont(QFont("Arial", 9))
    window = CoaxialWindwallWindow()
    screen = window.screen()
    if screen is not None:
        window.setGeometry(screen.availableGeometry())
    window.showMaximized()
    return app.exec()
