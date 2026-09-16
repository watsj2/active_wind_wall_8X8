#!/usr/bin/env python3
"""Measure a 3.3 V Pico PWM signal on Pi GPIO23 (physical pin 16).

Input only: no SPI access, motor commands, or GPIO output requests.
With propulsion disconnected and Pi/Pico power off, connect Pico C01 GP0
to Pi GPIO23 and establish common ground. Restore control power only.
Never connect an ESC power/BEC lead to the measurement input.
Kernel edge timestamps provide a diagnostic measurement, not scope accuracy.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import median
from time import monotonic


class PulseStats:
    def __init__(self):
        self.open_rise = None
        self.last_rise = None
        self.last_event = None
        self.widths = []
        self.periods = []
        self.unpaired = 0

    def feed(self, timestamp_ns: int, rising: bool) -> None:
        if self.last_event is not None and timestamp_ns <= self.last_event:
            self.unpaired += 1
            self.open_rise = self.last_rise = None
            self.last_event = timestamp_ns
            return
        self.last_event = timestamp_ns
        if rising:
            if self.open_rise is not None:
                self.unpaired += 1
            if self.last_rise is not None:
                self.periods.append((timestamp_ns - self.last_rise) / 1000)
            self.open_rise = self.last_rise = timestamp_ns
        elif self.open_rise is None:
            self.unpaired += 1
        else:
            self.widths.append((timestamp_ns - self.open_rise) / 1000)
            self.open_rise = None

    def report(self) -> dict:
        result = {
            "samples": len(self.widths),
            "pulse_us_median": round(median(self.widths), 2) if self.widths else None,
            "pulse_us_min": round(min(self.widths), 2) if self.widths else None,
            "pulse_us_max": round(max(self.widths), 2) if self.widths else None,
            "frequency_hz": round(1e6 / median(self.periods), 2) if self.periods else None,
            "unpaired_or_out_of_order_edges": self.unpaired,
        }
        self.widths.clear()
        self.periods.clear()
        self.unpaired = 0
        return result


def self_test() -> None:
    stats = PulseStats()
    stats.feed(1, False)  # Starting mid-pulse must not invent a width.
    for index in range(5):
        start = 1_000_000_000 + index * 20_000_000
        stats.feed(start, True)
        stats.feed(start + 1_000_000, False)
    idle = stats.report()
    assert idle["samples"] == 5 and idle["pulse_us_median"] == 1000
    assert idle["frequency_hz"] == 50 and idle["unpaired_or_out_of_order_edges"] == 1
    for index in range(5, 10):
        start = 1_000_000_000 + index * 20_000_000
        stats.feed(start, True)
        stats.feed(start + 1_200_000, False)
    running = stats.report()
    assert running["samples"] == 5 and running["pulse_us_median"] == 1200
    assert running["frequency_hz"] == 50
    stats.feed(2_000_000_000, True)
    stats.feed(2_020_000_000, True)  # Missing fall: discard the open pulse.
    stats.feed(2_021_200_000, False)
    damaged = stats.report()
    assert damaged["samples"] == 1 and damaged["pulse_us_median"] == 1200
    assert damaged["unpaired_or_out_of_order_edges"] == 1
    stats.feed(10, True)  # Non-monotonic input must be rejected.
    assert stats.report()["unpaired_or_out_of_order_edges"] == 1
    print("PASS: synthetic 1000/1200 us pulses, 50 Hz, and missing/out-of-order edges")


def capture(seconds: float) -> None:
    import gpiod  # Installed 1.6 API; imported only for a real input capture.

    chip = None
    line = None
    requested = False
    try:
        for path in sorted(Path("/dev").glob("gpiochip*")):
            candidate = gpiod.Chip(str(path))
            if candidate.label() == "pinctrl-rp1":
                chip = candidate
                break
            candidate.close()
        if chip is None:
            raise RuntimeError("Raspberry Pi header GPIO chip was not found")
        line = chip.get_line(23)
        if line.name() != "GPIO23" or line.is_used():
            raise RuntimeError("GPIO23 is unavailable; no line requested")
        line.request(
            consumer="windwall-passive-pwm-input",
            type=gpiod.LINE_REQ_EV_BOTH_EDGES,
            flags=gpiod.LINE_REQ_FLAG_BIAS_DISABLE,
        )
        requested = True
        print("Listening on GPIO23 / physical pin 16 (input only)", flush=True)
        stats = PulseStats()
        started = monotonic()
        next_report = started + 1
        while monotonic() - started < seconds:
            if line.event_wait(sec=0, nsec=250_000_000):
                event = line.event_read()
                stats.feed(event.sec * 1_000_000_000 + event.nsec,
                           event.type == gpiod.LineEvent.RISING_EDGE)
            now = monotonic()
            if now >= next_report:
                print(json.dumps({"elapsed_s": round(now - started, 2), **stats.report()}),
                      flush=True)
                next_report = now + 1
        print(json.dumps({"elapsed_s": round(monotonic() - started, 2),
                          "final": True, **stats.report()}), flush=True)
    finally:
        if requested:
            line.release()
        if chip is not None:
            chip.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=15)
    parser.add_argument("--self-test", action="store_true", help="no hardware access")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    elif not 1 <= args.seconds <= 60:
        parser.error("--seconds must be between 1 and 60")
    else:
        capture(args.seconds)
