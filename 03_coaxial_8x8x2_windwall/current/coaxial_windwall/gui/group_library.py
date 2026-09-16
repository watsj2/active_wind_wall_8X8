"""Reusable spatial selections; every motor is resolved through the physical map."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QHBoxLayout, QLabel,
    QSpinBox, QVBoxLayout, QWidget,
)

from coaxial_windwall.model import CoaxialAddress


TEMPLATES = (
    ("Whole wall", "whole"),
    ("Left half", "left"),
    ("Right half", "right"),
    *((f"{size} × {size} patch", f"square:{size}") for size in range(2, 8)),
    *((f"Pico {number:02d}", f"pico:{number}") for number in range(1, 17)),
)


def template_pixels(key: str, row: int = 0, col: int = 0) -> list[tuple[int, int]]:
    grid = [(r, c) for r in range(8) for c in range(8)]
    if key == "whole":
        return grid
    if key in ("left", "right"):
        return [(r, c) for r, c in grid if (c < 4) == (key == "left")]
    kind, value = key.split(":")
    number = int(value)
    if kind == "square" and 2 <= number <= 7:
        if not (0 <= row <= 8 - number and 0 <= col <= 8 - number):
            raise ValueError("Patch extends beyond the wall")
        return [(r, c) for r in range(row, row + number) for c in range(col, col + number)]
    if kind == "pico" and 1 <= number <= 16:
        return [(r, c) for r, c in grid if CoaxialAddress(r, c, 0).controller_number == number]
    raise ValueError(f"Unknown group template: {key}")


def template_motors(key: str, layers: tuple[int, ...], row: int = 0, col: int = 0) -> set[int]:
    return {
        CoaxialAddress(r, c, layer).motor_index
        for r, c in template_pixels(key, row, col)
        for layer in layers
    }


class SelectionPreview(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.pixels: set[tuple[int, int]] = set()
        self.setFixedSize(240, 160)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        for row in range(8):
            for col in range(8):
                painter.setBrush(QColor("#80cfbd" if (row, col) in self.pixels else "#28323f"))
                painter.drawRoundedRect(39 + col * 20 + (4 if col >= 4 else 0), row * 20, 16, 16, 3, 3)


class GroupLibraryDialog(QDialog):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.setWindowTitle("Premade groups")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        title = QLabel("Start with a shape")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)
        self.template = QComboBox()
        for label, key in TEMPLATES:
            self.template.addItem(label, key)
        layout.addWidget(self.template)
        self.layers = QComboBox()
        self.layers.addItem("Both layers", (0, 1))
        self.layers.addItem("Upstream only", (0,))
        self.layers.addItem("Downstream only", (1,))
        layout.addWidget(self.layers)
        self.position = QWidget()
        position_layout = QHBoxLayout(self.position)
        position_layout.setContentsMargins(0, 0, 0, 0)
        self.row = QSpinBox()
        self.col = QSpinBox()
        self.row.setPrefix("Row ")
        self.col.setPrefix("Column ")
        for spin in (self.row, self.col):
            spin.setRange(1, 8)
            position_layout.addWidget(spin)
            spin.valueChanged.connect(self.update_preview)
        self.position.setToolTip("Top-left corner of the patch, as viewed on the grid")
        layout.addWidget(self.position)
        self.preview = SelectionPreview()
        layout.addWidget(self.preview, 0, Qt.AlignmentFlag.AlignHCenter)
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        note = QLabel("New groups start at Constant 1000 µs. Set their signal after adding.")
        note.setObjectName("Caption")
        note.setWordWrap(True)
        layout.addWidget(note)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Add group")
        buttons.button(QDialogButtonBox.StandardButton.Ok).setObjectName("Primary")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.template.currentIndexChanged.connect(self.template_changed)
        self.layers.currentIndexChanged.connect(self.update_preview)
        self.template_changed()

    def template_changed(self) -> None:
        key = self.template.currentData()
        square = key.startswith("square:")
        self.position.setVisible(square)
        if square:
            size = int(key.split(":")[1])
            for spin in (self.row, self.col):
                spin.blockSignals(True)
                spin.setRange(1, 9 - size)
                spin.setValue((8 - size) // 2 + 1)
                spin.blockSignals(False)
        self.update_preview()

    def selected_motors(self) -> set[int]:
        return template_motors(self.template.currentData(), self.layers.currentData(), self.row.value() - 1, self.col.value() - 1)

    def group_name(self) -> str:
        name = self.template.currentText()
        if self.template.currentData().startswith("square:"):
            name += f" · R{self.row.value()} C{self.col.value()}"
        return f"{name} · {self.layers.currentText()}"

    def update_preview(self) -> None:
        self.preview.pixels = set(template_pixels(self.template.currentData(), self.row.value() - 1, self.col.value() - 1))
        self.preview.update()
        motors = self.selected_motors()
        overlap = sum(self.parent().motor_owner[motor] is not None for motor in motors)
        text = f"{len(self.preview.pixels)} pairs · {len(motors)} motors"
        if overlap:
            text += f"\n{overlap} motors will move from their existing groups."
        self.summary.setText(text)
