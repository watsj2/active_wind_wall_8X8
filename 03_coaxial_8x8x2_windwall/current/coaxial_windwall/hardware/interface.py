"""Hardware boundary for the 128-motor shared-SPI controller bus."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from threading import Condition, Thread
from time import monotonic
from typing import Protocol, Sequence

from config import (
    GPIO_CHIP_LABEL,
    NUM_MOTORS,
    PWM_IDLE,
    SPI_BUS,
    SPI_DEVICE,
    SPI_SPEED_HZ,
    SYNC_PIN,
)
from coaxial_windwall.model import validate_pwm_frame
from coaxial_windwall.protocol import SYNC_PULSE_US, build_idle_frame, build_pwm_us_frame


class SPITransport(Protocol):
    def write_frame(self, frame: bytes) -> None: ...

    def close(self) -> None: ...


class SyncTransport(Protocol):
    def pulse(self) -> None: ...

    def close(self) -> None: ...


class RealSPI:
    """Byte-paced SPI0 transport matching the proven 8x8 host behavior."""

    def __init__(
        self,
        bus: int = SPI_BUS,
        device: int = SPI_DEVICE,
        speed_hz: int = SPI_SPEED_HZ,
    ) -> None:
        import spidev  # type: ignore

        self._spi = spidev.SpiDev()
        self._spi.open(bus, device)
        self._spi.max_speed_hz = speed_hz
        self._spi.mode = 0
        self._spi.bits_per_word = 8

    def write_frame(self, frame: bytes) -> None:
        # The Pico firmware polls SPI, so send one transfer per byte to avoid
        # overrunning its receive FIFO.
        for value in frame:
            self._spi.xfer2([value])

    def close(self) -> None:
        self._spi.close()


class RealSync:
    """GPIO22 latch pulse supporting both gpiod 1.x and 2.x."""

    def __init__(
        self,
        pin: int = SYNC_PIN,
        chip_label: str = GPIO_CHIP_LABEL,
    ) -> None:
        import gpiod  # type: ignore

        chip_path = self._find_chip_path(gpiod, chip_label)
        self._pin = pin
        self._line_request = None
        self._line = None
        self._chip = None
        self._value_enum = None

        try:
            from gpiod.line import Direction, Value  # type: ignore

            self._value_enum = Value
            self._line_request = gpiod.request_lines(
                chip_path,
                consumer="coaxial-windwall-control",
                config={pin: gpiod.LineSettings(direction=Direction.OUTPUT)},
            )
            self._line_request.set_value(pin, Value.INACTIVE)
        except (ImportError, AttributeError):
            self._chip = gpiod.Chip(chip_path)
            self._line = self._chip.get_line(pin)
            self._line.request(
                consumer="coaxial-windwall-control",
                type=gpiod.LINE_REQ_DIR_OUT,
                default_vals=[0],
            )

    @staticmethod
    def _find_chip_path(gpiod_module, chip_label: str) -> str:
        for candidate in sorted(Path("/dev").glob("gpiochip*")):
            chip = None
            try:
                chip = gpiod_module.Chip(str(candidate))
                if hasattr(chip, "get_info"):
                    label = chip.get_info().label
                else:
                    label = chip.label()
                if label == chip_label:
                    return str(candidate)
            except OSError:
                continue
            finally:
                if chip is not None:
                    chip.close()
        raise FileNotFoundError(
            f"GPIO chip with label {chip_label!r} was not found under /dev"
        )

    def pulse(self) -> None:
        if self._line is not None:
            self._line.set_value(1)
            time.sleep(SYNC_PULSE_US / 1_000_000)
            self._line.set_value(0)
            return
        if self._line_request is None or self._value_enum is None:
            raise RuntimeError("sync GPIO is not initialized")
        self._line_request.set_value(self._pin, self._value_enum.ACTIVE)
        time.sleep(SYNC_PULSE_US / 1_000_000)
        self._line_request.set_value(self._pin, self._value_enum.INACTIVE)

    def close(self) -> None:
        if self._line is not None:
            self._line.release()
            self._line = None
        if self._line_request is not None:
            self._line_request.release()
            self._line_request = None
        if self._chip is not None:
            self._chip.close()
            self._chip = None


@dataclass(frozen=True)
class TelemetrySnapshot:
    available: bool
    tach_hz: tuple[float | None, ...]
    source: str
    timestamp_s: float


class HardwareInterface:
    """Encode full-wall frames, transmit them, then atomically pulse sync."""

    def __init__(
        self,
        *,
        spi: SPITransport | None = None,
        sync: SyncTransport | None = None,
    ) -> None:
        if (spi is None) != (sync is None):
            raise ValueError("spi and sync test transports must be supplied together")
        self.frame_count = 0
        self.last_frame = [PWM_IDLE] * NUM_MOTORS
        self.last_protocol_frame = build_idle_frame(sequence=0)
        self.last_send_time_s = monotonic()
        self._spi: SPITransport | None = None
        self._sync: SyncTransport | None = None
        self._closed = False

        try:
            self._spi = spi if spi is not None else RealSPI()
            self._sync = sync if sync is not None else RealSync()
            self.send_pwm_frame(self.last_frame, output_armed=False)
        except Exception:
            self.close()
            raise

    def send_pwm_frame(
        self,
        values: Sequence[int | float],
        *,
        output_armed: bool = False,
    ) -> None:
        if self._closed:
            raise RuntimeError("hardware interface is closed")
        frame = validate_pwm_frame(values)
        sequence = (self.frame_count + 1) & 0xFF
        protocol_frame = build_pwm_us_frame(
            frame,
            sequence=sequence,
            output_armed=output_armed,
        )

        if self._spi is None or self._sync is None:
            raise RuntimeError("real transport is not initialized")
        self._spi.write_frame(protocol_frame)
        self._sync.pulse()

        self.frame_count += 1
        self.last_frame = frame
        self.last_protocol_frame = protocol_frame
        self.last_send_time_s = monotonic()

    def read_telemetry(self) -> TelemetrySnapshot:
        return TelemetrySnapshot(
            available=False,
            tach_hz=(None,) * NUM_MOTORS,
            source="not-configured",
            timestamp_s=monotonic(),
        )

    def shutdown(self) -> None:
        if self._closed:
            return
        try:
            self.send_pwm_frame([PWM_IDLE] * NUM_MOTORS, output_armed=False)
        finally:
            self.close()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._sync is not None:
            self._sync.close()
            self._sync = None
        if self._spi is not None:
            self._spi.close()
            self._spi = None


class LatestFrameDispatcher:
    """Send only the newest queued runtime frame outside the GUI thread.

    The physical transport deliberately performs one SPI transaction per byte.
    Keeping those 266 transactions off the Qt event loop prevents motor traffic
    from freezing painting and input.  The queue is bounded to one frame so a
    slow transport never replays stale motor commands.
    """

    def __init__(self, hardware: HardwareInterface) -> None:
        self._hardware = hardware
        self._condition = Condition()
        self._pending: tuple[tuple[int, ...], bool] | None = None
        self._active = False
        self._closed = False
        self._failure: Exception | None = None
        self._thread = Thread(
            target=self._run,
            name="windwall-frame-dispatch",
            daemon=True,
        )
        self._thread.start()

    def submit(
        self,
        values: Sequence[int | float],
        *,
        output_armed: bool,
    ) -> bool:
        """Queue the newest frame and return false if dispatch has failed."""

        frame = tuple(validate_pwm_frame(values))
        with self._condition:
            if self._closed or self._failure is not None:
                return False
            self._pending = (frame, output_armed)
            self._condition.notify()
        return True

    def discard_pending(self) -> None:
        with self._condition:
            self._pending = None

    def wait_until_idle(self, timeout_s: float = 1.0) -> bool:
        deadline = monotonic() + timeout_s
        with self._condition:
            while self._active or self._pending is not None:
                remaining = deadline - monotonic()
                if remaining <= 0:
                    return False
                self._condition.wait(remaining)
        return True

    def failure(self) -> Exception | None:
        with self._condition:
            return self._failure

    def close(self, timeout_s: float = 1.0) -> bool:
        with self._condition:
            self._pending = None
            self._closed = True
            self._condition.notify()
        self._thread.join(timeout_s)
        return not self._thread.is_alive()

    def _run(self) -> None:
        while True:
            with self._condition:
                while self._pending is None and not self._closed:
                    self._condition.wait()
                if self._closed:
                    return
                request = self._pending
                self._pending = None
                self._active = True

            try:
                if request is not None:
                    values, output_armed = request
                    self._hardware.send_pwm_frame(
                        values,
                        output_armed=output_armed,
                    )
            except Exception as exc:  # surfaced to the GUI on its next tick
                with self._condition:
                    self._failure = exc
                    self._pending = None
            finally:
                with self._condition:
                    self._active = False
                    self._condition.notify_all()
