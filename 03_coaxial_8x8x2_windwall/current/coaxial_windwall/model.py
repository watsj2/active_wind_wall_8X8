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


# Physical motor numbering inherited from the proven 8x8 Pi/Pico wall.
# Each value is the one-based pair number installed at that grid location.
PIXEL_NUMBER_GRID: tuple[tuple[int, ...], ...] = (
    (1, 2, 3, 4, 33, 34, 35, 36),
    (5, 6, 7, 8, 37, 38, 39, 40),
    (9, 10, 11, 12, 41, 42, 43, 44),
    (13, 14, 15, 16, 45, 46, 47, 48),
    (17, 18, 19, 20, 49, 50, 51, 52),
    (21, 22, 23, 24, 53, 54, 55, 56),
    (25, 26, 27, 28, 57, 58, 59, 60),
    (29, 30, 31, 32, 61, 62, 63, 64),
)

_pixel_numbers = [number for row in PIXEL_NUMBER_GRID for number in row]
if sorted(_pixel_numbers) != list(range(1, GRID_ROWS * GRID_COLS + 1)):
    raise ValueError("PIXEL_NUMBER_GRID must contain each pair number 1-64 once")

PIXEL_LOCATION_BY_INDEX: tuple[tuple[int, int], ...] = tuple(
    next(
        (row, col)
        for row in range(GRID_ROWS)
        for col in range(GRID_COLS)
        if PIXEL_NUMBER_GRID[row][col] == pixel_number
    )
    for pixel_number in range(1, GRID_ROWS * GRID_COLS + 1)
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
        return PIXEL_NUMBER_GRID[self.row][self.col] - 1

    @property
    def pixel_number(self) -> int:
        return self.pixel_index + 1

    @property
    def motor_index(self) -> int:
        motors_per_layer = GRID_ROWS * GRID_COLS
        return self.layer * motors_per_layer + self.pixel_index

    @property
    def controller_index(self) -> int:
        return MOTOR_TO_CONTROLLER_CHANNEL[self.motor_index][0]

    @property
    def controller_number(self) -> int:
        return self.controller_index + 1

    @property
    def controller_label(self) -> str:
        return f"C{self.controller_number:02d}"

    @property
    def controller_channel(self) -> int:
        return MOTOR_TO_CONTROLLER_CHANNEL[self.motor_index][1]

    @property
    def controller_channel_number(self) -> int:
        return self.controller_channel + 1

    @property
    def controller_channel_label(self) -> str:
        return f"CH{self.controller_channel_number}"

    @property
    def controller_pwm_pin(self) -> str:
        return f"GP{self.controller_channel}"

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
    motors_per_layer = GRID_ROWS * GRID_COLS
    layer, pixel_index = divmod(motor_index, motors_per_layer)
    row, col = PIXEL_LOCATION_BY_INDEX[pixel_index]
    return CoaxialAddress(row=row, col=col, layer=layer)


def paired_motor_indices(row: int, col: int) -> tuple[int, int]:
    return (
        CoaxialAddress(row=row, col=col, layer=0).motor_index,
        CoaxialAddress(row=row, col=col, layer=1).motor_index,
    )


def _motor_index_for_pixel(pixel_index: int, layer: int) -> int:
    motors_per_layer = GRID_ROWS * GRID_COLS
    return layer * motors_per_layer + pixel_index


def _pixel_index_at_location(row: int, col: int) -> int:
    return PIXEL_NUMBER_GRID[row][col] - 1


def _front_back_channel_group(pixel_indices: Iterable[int]) -> tuple[int, ...]:
    channel_indices: list[int] = []
    for pixel_index in pixel_indices:
        channel_indices.append(_motor_index_for_pixel(pixel_index, 0))
        channel_indices.append(_motor_index_for_pixel(pixel_index, 1))
    return tuple(channel_indices)


# Controller wiring plan:
# - C01-C08 reuse the original 8x8 harness outputs.
# - Adjacent legacy outputs become one coaxial front/back pair.
# - C09-C16 are new infill controllers for the middle columns.
# Each controller owns four wind pixels, with channels ordered F/B per pixel.
CONTROLLER_HOST_INDICES: tuple[tuple[int, ...], ...] = (
    _front_back_channel_group(
        _pixel_index_at_location(row, col)
        for row in (0, 1)
        for col in (0, 3)
    ),
    _front_back_channel_group(
        _pixel_index_at_location(row, col)
        for row in (2, 3)
        for col in (0, 3)
    ),
    _front_back_channel_group(
        _pixel_index_at_location(row, col)
        for row in (4, 5)
        for col in (0, 3)
    ),
    _front_back_channel_group(
        _pixel_index_at_location(row, col)
        for row in (6, 7)
        for col in (0, 3)
    ),
    _front_back_channel_group(
        _pixel_index_at_location(row, col)
        for row in (0, 1)
        for col in (4, 7)
    ),
    _front_back_channel_group(
        _pixel_index_at_location(row, col)
        for row in (2, 3)
        for col in (4, 7)
    ),
    _front_back_channel_group(
        _pixel_index_at_location(row, col)
        for row in (4, 5)
        for col in (4, 7)
    ),
    _front_back_channel_group(
        _pixel_index_at_location(row, col)
        for row in (6, 7)
        for col in (4, 7)
    ),
    _front_back_channel_group(
        _pixel_index_at_location(row, col)
        for row in (0, 1)
        for col in (1, 2)
    ),
    _front_back_channel_group(
        _pixel_index_at_location(row, col)
        for row in (2, 3)
        for col in (1, 2)
    ),
    _front_back_channel_group(
        _pixel_index_at_location(row, col)
        for row in (4, 5)
        for col in (1, 2)
    ),
    _front_back_channel_group(
        _pixel_index_at_location(row, col)
        for row in (6, 7)
        for col in (1, 2)
    ),
    _front_back_channel_group(
        _pixel_index_at_location(row, col)
        for row in (0, 1)
        for col in (5, 6)
    ),
    _front_back_channel_group(
        _pixel_index_at_location(row, col)
        for row in (2, 3)
        for col in (5, 6)
    ),
    _front_back_channel_group(
        _pixel_index_at_location(row, col)
        for row in (4, 5)
        for col in (5, 6)
    ),
    _front_back_channel_group(
        _pixel_index_at_location(row, col)
        for row in (6, 7)
        for col in (5, 6)
    ),
)


def _build_motor_controller_channel_lookup() -> dict[int, tuple[int, int]]:
    lookup: dict[int, tuple[int, int]] = {}
    for controller_index, host_indices in enumerate(CONTROLLER_HOST_INDICES):
        if len(host_indices) != MOTORS_PER_CONTROLLER:
            raise ValueError(
                f"controller {controller_index} has {len(host_indices)} channels"
            )
        for channel_index, motor_index in enumerate(host_indices):
            if motor_index in lookup:
                raise ValueError(f"motor {motor_index} assigned more than once")
            lookup[motor_index] = (controller_index, channel_index)
    if len(lookup) != NUM_MOTORS:
        missing = sorted(set(range(NUM_MOTORS)) - set(lookup))
        raise ValueError(f"controller map missing motors: {missing}")
    return lookup


MOTOR_TO_CONTROLLER_CHANNEL: dict[int, tuple[int, int]] = (
    _build_motor_controller_channel_lookup()
)


def controller_host_indices(controller_index: int) -> tuple[int, ...]:
    if not 0 <= controller_index < CONTROLLER_COUNT:
        raise ValueError(f"controller_index out of range: {controller_index}")
    return CONTROLLER_HOST_INDICES[controller_index]


def clamp_pwm(value: int | float) -> int:
    return max(PWM_MIN, min(PWM_MAX, int(round(value))))


def validate_pwm_frame(values: Sequence[int | float]) -> list[int]:
    if len(values) != NUM_MOTORS:
        raise ValueError(f"expected {NUM_MOTORS} PWM values, got {len(values)}")
    return [clamp_pwm(value) for value in values]


def controller_frame(values: list[int], controller_index: int) -> list[int]:
    if not 0 <= controller_index < CONTROLLER_COUNT:
        raise ValueError(f"controller_index out of range: {controller_index}")
    frame = validate_pwm_frame(values)
    return [frame[motor_index] for motor_index in controller_host_indices(controller_index)]
