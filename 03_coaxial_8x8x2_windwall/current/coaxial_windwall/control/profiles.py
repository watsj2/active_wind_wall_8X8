"""Simple command profiles for the clean-start GUI."""

from __future__ import annotations

from config import GRID_COLS, GRID_ROWS, NUM_MOTORS, PWM_IDLE
from coaxial_windwall.model import CoaxialAddress, clamp_pwm


def idle_frame() -> list[int]:
    return [PWM_IDLE] * NUM_MOTORS


def uniform_pair_frame(value: int) -> list[int]:
    pwm = clamp_pwm(value)
    return [pwm] * NUM_MOTORS


def layer_split_frame(base: int, differential: int) -> list[int]:
    layer_a = clamp_pwm(base + differential)
    layer_b = clamp_pwm(base - differential)
    values = idle_frame()
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            values[CoaxialAddress(row, col, 0).motor_index] = layer_a
            values[CoaxialAddress(row, col, 1).motor_index] = layer_b
    return values


def checkerboard_frame(base: int, contrast: int) -> list[int]:
    values = idle_frame()
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            sign = 1 if (row + col) % 2 == 0 else -1
            layer_a = clamp_pwm(base + sign * contrast)
            layer_b = clamp_pwm(base - sign * contrast)
            values[CoaxialAddress(row, col, 0).motor_index] = layer_a
            values[CoaxialAddress(row, col, 1).motor_index] = layer_b
    return values


def single_pixel_frame(
    row: int,
    col: int,
    layer: int | None,
    value: int,
    background: int = PWM_IDLE,
) -> list[int]:
    values = [clamp_pwm(background)] * NUM_MOTORS
    if layer is None:
        values[CoaxialAddress(row, col, 0).motor_index] = clamp_pwm(value)
        values[CoaxialAddress(row, col, 1).motor_index] = clamp_pwm(value)
    else:
        values[CoaxialAddress(row, col, layer).motor_index] = clamp_pwm(value)
    return values
