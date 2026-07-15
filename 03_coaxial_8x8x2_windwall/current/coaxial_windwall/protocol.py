"""Host-to-controller protocol helpers for the 128-motor wall.

The v1 protocol is intentionally command-only. Telemetry/readback can be added
after PWM output has been bench-proven on one controller.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Sequence

from config import (
    CONTROLLER_COUNT,
    NUM_MOTORS,
    PWM_IDLE,
    PWM_MAX,
    PWM_MIN,
)
from coaxial_windwall.model import controller_host_indices


PROTOCOL_MAGIC = b"CW"
PROTOCOL_VERSION = 1

HEADER_BYTES = 8
CRC_BYTES = 2
PWM_US_BYTES = 2
PWM_PAYLOAD_BYTES = NUM_MOTORS * PWM_US_BYTES
PWM_FRAME_BYTES = HEADER_BYTES + PWM_PAYLOAD_BYTES + CRC_BYTES

FLAG_OUTPUT_ARMED = 0x01

CRC16_CCITT_FALSE_INIT = 0xFFFF
CRC16_CCITT_FALSE_POLY = 0x1021

CONTROLLER_WATCHDOG_MS = 250
SYNC_PULSE_US = 10


class MessageType(IntEnum):
    """Protocol message type values."""

    PWM_US_BROADCAST = 0x01


@dataclass(frozen=True)
class DecodedPwmFrame:
    """Validated PWM command frame decoded from transport bytes."""

    sequence: int
    flags: int
    pwm_us: tuple[int, ...]
    crc: int

    @property
    def output_armed(self) -> bool:
        return bool(self.flags & FLAG_OUTPUT_ARMED)


def crc16_ccitt_false(data: bytes | bytearray | memoryview) -> int:
    """Return CRC-16/CCITT-FALSE over data."""

    crc = CRC16_CCITT_FALSE_INIT
    for byte in data:
        crc ^= int(byte) << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ CRC16_CCITT_FALSE_POLY) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def clamp_pwm_us(value: int | float) -> int:
    return max(PWM_MIN, min(PWM_MAX, int(round(value))))


def validate_pwm_us_values(values: Sequence[int | float]) -> tuple[int, ...]:
    if len(values) != NUM_MOTORS:
        raise ValueError(f"expected {NUM_MOTORS} PWM values, got {len(values)}")
    return tuple(clamp_pwm_us(value) for value in values)


def encode_pwm_payload(values: Sequence[int | float]) -> bytes:
    """Encode 128 PWM pulse widths as little-endian uint16 microseconds."""

    payload = bytearray(PWM_PAYLOAD_BYTES)
    for index, pwm_us in enumerate(validate_pwm_us_values(values)):
        offset = index * PWM_US_BYTES
        payload[offset] = pwm_us & 0xFF
        payload[offset + 1] = (pwm_us >> 8) & 0xFF
    return bytes(payload)


def decode_pwm_payload(payload: bytes | bytearray | memoryview) -> tuple[int, ...]:
    if len(payload) != PWM_PAYLOAD_BYTES:
        raise ValueError(
            f"expected {PWM_PAYLOAD_BYTES} PWM payload bytes, got {len(payload)}"
        )

    values = []
    for offset in range(0, PWM_PAYLOAD_BYTES, PWM_US_BYTES):
        value = int(payload[offset]) | (int(payload[offset + 1]) << 8)
        if not PWM_MIN <= value <= PWM_MAX:
            raise ValueError(f"PWM value out of range at byte {offset}: {value}")
        values.append(value)
    return tuple(values)


def build_pwm_us_frame(
    values: Sequence[int | float],
    *,
    sequence: int = 0,
    output_armed: bool = False,
) -> bytes:
    """Build one broadcast frame for all 16 controllers.

    `output_armed=False` is valid for link tests; firmware should treat such a
    frame as a verified idle command.
    """

    payload = encode_pwm_payload(values)
    flags = FLAG_OUTPUT_ARMED if output_armed else 0
    frame = bytearray()
    frame.extend(PROTOCOL_MAGIC)
    frame.append(PROTOCOL_VERSION)
    frame.append(MessageType.PWM_US_BROADCAST)
    frame.append(flags)
    frame.append(sequence & 0xFF)
    frame.extend(len(payload).to_bytes(2, byteorder="little", signed=False))
    frame.extend(payload)
    crc = crc16_ccitt_false(frame)
    frame.extend(crc.to_bytes(2, byteorder="little", signed=False))
    return bytes(frame)


def build_idle_frame(*, sequence: int = 0) -> bytes:
    return build_pwm_us_frame(
        [PWM_IDLE] * NUM_MOTORS,
        sequence=sequence,
        output_armed=False,
    )


def decode_pwm_us_frame(frame: bytes | bytearray | memoryview) -> DecodedPwmFrame:
    """Validate and decode a v1 PWM broadcast frame."""

    if len(frame) != PWM_FRAME_BYTES:
        raise ValueError(f"expected {PWM_FRAME_BYTES} frame bytes, got {len(frame)}")

    view = memoryview(frame)
    if bytes(view[0:2]) != PROTOCOL_MAGIC:
        raise ValueError("protocol magic mismatch")
    if int(view[2]) != PROTOCOL_VERSION:
        raise ValueError(f"unsupported protocol version: {int(view[2])}")
    if int(view[3]) != MessageType.PWM_US_BROADCAST:
        raise ValueError(f"unsupported message type: {int(view[3])}")

    payload_len = int(view[6]) | (int(view[7]) << 8)
    if payload_len != PWM_PAYLOAD_BYTES:
        raise ValueError(f"unexpected payload length: {payload_len}")

    expected_crc = crc16_ccitt_false(view[:-CRC_BYTES])
    received_crc = int(view[-2]) | (int(view[-1]) << 8)
    if received_crc != expected_crc:
        raise ValueError(
            f"CRC mismatch: received 0x{received_crc:04X}, expected 0x{expected_crc:04X}"
        )

    payload_start = HEADER_BYTES
    payload_end = payload_start + PWM_PAYLOAD_BYTES
    return DecodedPwmFrame(
        sequence=int(view[5]),
        flags=int(view[4]),
        pwm_us=decode_pwm_payload(view[payload_start:payload_end]),
        crc=received_crc,
    )


def controller_values(
    values: Sequence[int | float],
    controller_index: int,
) -> tuple[int, ...]:
    """Return the eight PWM values owned by one zero-based controller."""

    if not 0 <= controller_index < CONTROLLER_COUNT:
        raise ValueError(f"controller_index out of range: {controller_index}")
    frame = validate_pwm_us_values(values)
    return tuple(frame[motor_index] for motor_index in controller_host_indices(controller_index))
