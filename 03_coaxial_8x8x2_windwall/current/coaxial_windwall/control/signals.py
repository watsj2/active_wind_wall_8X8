"""German-wall-style group signal generation for the coaxial wall."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable

from config import NUM_MOTORS, PWM_IDLE, PWM_UI_MAX
from coaxial_windwall.model import clamp_pwm


SIGNAL_SINE = "Sine Wave"
SIGNAL_SQUARE = "Square Wave"
SIGNAL_CONSTANT = "Constant"
SIGNAL_CUSTOM = "Custom Fourier"
SIGNAL_TYPES = (SIGNAL_SINE, SIGNAL_SQUARE, SIGNAL_CONSTANT, SIGNAL_CUSTOM)


@dataclass
class Harmonic:
    number: int = 1
    amplitude: float = 0.1
    phase_deg: float = 0.0

    def to_dict(self) -> dict[str, float | int]:
        return {
            "number": self.number,
            "amplitude": self.amplitude,
            "phase_deg": self.phase_deg,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Harmonic":
        return cls(
            number=max(1, int(data.get("number", 1))),
            amplitude=float(data.get("amplitude", 0.1)),
            phase_deg=float(data.get("phase_deg", 0.0)),
        )


@dataclass
class GroupSignal:
    signal_type: str = SIGNAL_SINE
    minimum: float = 0.25
    maximum: float = 0.75
    constant: float = 0.50
    period_s: float = 2.0
    phase_s: float = 0.0
    duty_cycle: float = 0.50
    harmonics: list[Harmonic] = field(default_factory=list)

    def normalized(self) -> "GroupSignal":
        signal_type = self.signal_type if self.signal_type in SIGNAL_TYPES else SIGNAL_SINE
        minimum = max(0.0, min(1.0, float(self.minimum)))
        maximum = max(minimum, min(1.0, float(self.maximum)))
        return GroupSignal(
            signal_type=signal_type,
            minimum=minimum,
            maximum=maximum,
            constant=max(0.0, min(1.0, float(self.constant))),
            period_s=max(0.1, float(self.period_s)),
            phase_s=float(self.phase_s),
            duty_cycle=max(0.01, min(0.99, float(self.duty_cycle))),
            harmonics=list(self.harmonics),
        )

    def to_dict(self) -> dict:
        return {
            "signal_type": self.signal_type,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "constant": self.constant,
            "period_s": self.period_s,
            "phase_s": self.phase_s,
            "duty_cycle": self.duty_cycle,
            "harmonics": [harmonic.to_dict() for harmonic in self.harmonics],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GroupSignal":
        return cls(
            signal_type=str(data.get("signal_type", SIGNAL_SINE)),
            minimum=float(data.get("minimum", data.get("amp_min", 0.25))),
            maximum=float(data.get("maximum", data.get("amp_max", 0.75))),
            constant=float(data.get("constant", data.get("dc_value", 0.50))),
            period_s=float(data.get("period_s", data.get("period", 2.0))),
            phase_s=float(data.get("phase_s", data.get("phase_offset", 0.0))),
            duty_cycle=float(data.get("duty_cycle", 0.50)),
            harmonics=[
                Harmonic.from_dict(item)
                for item in data.get("harmonics", [])
                if isinstance(item, dict)
            ],
        ).normalized()


@dataclass
class SignalGroup:
    name: str
    color: str
    motors: set[int] = field(default_factory=set)
    signal: GroupSignal = field(default_factory=GroupSignal)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "color": self.color,
            "motors": sorted(self.motors),
            "signal": self.signal.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict, fallback_color: str) -> "SignalGroup":
        motors = {
            int(value)
            for value in data.get("motors", [])
            if 0 <= int(value) < NUM_MOTORS
        }
        signal_data = data.get("signal", data)
        return cls(
            name=str(data.get("name") or "Group"),
            color=str(data.get("color") or fallback_color),
            motors=motors,
            signal=GroupSignal.from_dict(signal_data),
        )


def signal_fraction(signal: GroupSignal, elapsed_s: float) -> float:
    """Evaluate one German-style group signal as a normalized speed."""

    cfg = signal.normalized()
    shifted_s = float(elapsed_s) - cfg.phase_s
    angle = 2.0 * math.pi * shifted_s / cfg.period_s

    if cfg.signal_type == SIGNAL_CONSTANT:
        value = cfg.constant
    elif cfg.signal_type == SIGNAL_SQUARE:
        cycle = (shifted_s / cfg.period_s) % 1.0
        value = cfg.maximum if cycle < cfg.duty_cycle else cfg.minimum
    elif cfg.signal_type == SIGNAL_CUSTOM:
        value = cfg.constant
        for harmonic in cfg.harmonics:
            value += harmonic.amplitude * math.sin(
                harmonic.number * angle + math.radians(harmonic.phase_deg)
            )
    else:
        midpoint = (cfg.minimum + cfg.maximum) / 2.0
        amplitude = (cfg.maximum - cfg.minimum) / 2.0
        value = midpoint + amplitude * math.sin(angle)

    return max(0.0, min(1.0, value))


def fraction_to_pwm(fraction: float, output_max: int = PWM_UI_MAX) -> int:
    fraction = max(0.0, min(1.0, float(fraction)))
    if fraction <= 0.0:
        return PWM_IDLE
    return clamp_pwm(PWM_IDLE + fraction * (output_max - PWM_IDLE))


def build_group_frame(
    groups: Iterable[SignalGroup],
    elapsed_s: float,
    output_max: int = PWM_UI_MAX,
) -> list[int]:
    """Build one layer-first, row-major 128-motor frame."""

    frame = [PWM_IDLE] * NUM_MOTORS
    for group in groups:
        pwm = fraction_to_pwm(signal_fraction(group.signal, elapsed_s), output_max)
        for motor_index in group.motors:
            if 0 <= motor_index < NUM_MOTORS:
                frame[motor_index] = pwm
    return frame


def preview_signal(
    signal: GroupSignal,
    duration_s: float,
    sample_count: int,
    output_max: int = PWM_UI_MAX,
) -> list[tuple[float, int]]:
    if sample_count < 2:
        raise ValueError("sample_count must be at least 2")
    duration_s = max(0.1, float(duration_s))
    return [
        (
            duration_s * index / (sample_count - 1),
            fraction_to_pwm(
                signal_fraction(signal, duration_s * index / (sample_count - 1)),
                output_max,
            ),
        )
        for index in range(sample_count)
    ]
