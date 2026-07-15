"""Mock-safe hardware boundary for the new 128-motor system."""

from __future__ import annotations

from dataclasses import dataclass
from time import monotonic

from config import NUM_MOTORS
from coaxial_windwall.model import validate_pwm_frame
from coaxial_windwall.protocol import build_idle_frame, build_pwm_us_frame


@dataclass(frozen=True)
class TelemetrySnapshot:
    available: bool
    tach_hz: tuple[float | None, ...]
    source: str
    timestamp_s: float


class HardwareInterface:
    """Boundary between command generation and physical controllers.

    The clean baseline is intentionally mock-first. Real output should be added
    only after the 128-motor controller protocol is defined and bench-tested.
    """

    def __init__(self, use_mock: bool = True) -> None:
        self.use_mock = use_mock
        self.frame_count = 0
        self.last_frame = [1000] * NUM_MOTORS
        self.last_protocol_frame = build_idle_frame(sequence=0)
        self.last_send_time_s = monotonic()
        if not self.use_mock:
            raise NotImplementedError(
                "Real 128-motor hardware output is not implemented yet."
            )

    @property
    def mode_name(self) -> str:
        return "MOCK" if self.use_mock else "REAL"

    def send_pwm_frame(self, values: list[int]) -> None:
        frame = validate_pwm_frame(values)
        self.frame_count += 1
        self.last_frame = frame
        self.last_protocol_frame = build_pwm_us_frame(
            frame,
            sequence=self.frame_count,
            output_armed=False,
        )
        self.last_send_time_s = monotonic()

    def read_telemetry(self) -> TelemetrySnapshot:
        return TelemetrySnapshot(
            available=False,
            tach_hz=(None,) * NUM_MOTORS,
            source="not-configured",
            timestamp_s=monotonic(),
        )

    def shutdown(self) -> None:
        self.send_pwm_frame([1000] * NUM_MOTORS)
