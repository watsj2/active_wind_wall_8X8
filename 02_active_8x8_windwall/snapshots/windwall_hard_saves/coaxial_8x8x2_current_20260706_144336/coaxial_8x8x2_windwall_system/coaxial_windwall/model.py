"""Addressing and validation helpers for the 128-motor coaxial wall."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from config import (
    COAXIAL_LAYERS,
    CONTROLLER_COUNT,
    GRID_COLS,
    GRID_ROWS,
    LAYER_LABELS,
    LAYER_NAMES,
    MOTORS_PER_CONTROLLER,
    NUM_MOTORS,
    PWM_MAX,
    PWM_MIN,
)


@dataclass(frozen=True)
class CoaxialAddress:
    """A physical motor address in row, column, and coaxial layer form."""

    row: int
    col: int
    layer: int

    def __post_init__(self) -> None:
        if not 0 <= self.row < GRID_ROWS:
            raise ValueError(f"row out of range: {self.row}")
        if not 0 <= self.col < GRID_COLS:
            raise ValueError(f"col out of range: {self.col}")
        if not 0 <= self.layer < COAXIAL_LAYERS:
            raise ValueError(f"layer out of range: {self.layer}")

    @property
    def pixel_index(self) -> int:
        return self.row * GRID_COLS + self.col

    @property
    def pixel_number(self) -> int:
        return self.pixel_index + 1

    @property
    def motor_index(self) -> int:
        return self.pixel_index * COAXIAL_LAYERS + self.layer

    @property
    def controller_index(self) -> int:
        return self.motor_index // MOTORS_PER_CONTROLLER

    @property
    def controller_channel(self) -> int:
        return self.motor_index % MOTORS_PER_CONTROLLER

    @property
    def layer_label(self) -> str:
        return LAYER_LABELS[self.layer]

    @property
    def layer_name(self) -> str:
        return LAYER_NAMES[self.layer]

    @property
    def label(self) -> str:
        return f"{self.layer_label}{self.pixel_number:02d}"

    @property
    def location_label(self) -> str:
        return f"R{self.row + 1}C{self.col + 1}{self.layer_label}"

    @property
    def pair_label(self) -> str:
        return f"P{self.pixel_number:02d}"

    @property
    def signed_alias(self) -> str:
        sign = "+" if self.layer == 0 else "-"
        return f"{sign}{self.pixel_number:02d}"


def iter_addresses() -> Iterable[CoaxialAddress]:
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            for layer in range(COAXIAL_LAYERS):
                yield CoaxialAddress(row=row, col=col, layer=layer)


def address_from_motor_index(motor_index: int) -> CoaxialAddress:
    if not 0 <= motor_index < NUM_MOTORS:
        raise ValueError(f"motor_index out of range: {motor_index}")
    pixel_index, layer = divmod(motor_index, COAXIAL_LAYERS)
    row, col = divmod(pixel_index, GRID_COLS)
    return CoaxialAddress(row=row, col=col, layer=layer)


def paired_motor_indices(row: int, col: int) -> tuple[int, int]:
    return (
        CoaxialAddress(row=row, col=col, layer=0).motor_index,
        CoaxialAddress(row=row, col=col, layer=1).motor_index,
    )


def clamp_pwm(value: int | float) -> int:
    return max(PWM_MIN, min(PWM_MAX, int(round(value))))


def validate_pwm_frame(values: list[int]) -> list[int]:
    if len(values) != NUM_MOTORS:
        raise ValueError(f"expected {NUM_MOTORS} PWM values, got {len(values)}")
    return [clamp_pwm(value) for value in values]


def controller_frame(values: list[int], controller_index: int) -> list[int]:
    if not 0 <= controller_index < CONTROLLER_COUNT:
        raise ValueError(f"controller_index out of range: {controller_index}")
    frame = validate_pwm_frame(values)
    start = controller_index * MOTORS_PER_CONTROLLER
    return frame[start : start + MOTORS_PER_CONTROLLER]
