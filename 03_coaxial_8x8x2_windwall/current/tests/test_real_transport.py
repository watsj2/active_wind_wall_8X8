from __future__ import annotations

import unittest

from config import NUM_MOTORS, PWM_IDLE
from coaxial_windwall.hardware.interface import HardwareInterface
from coaxial_windwall.protocol import PWM_FRAME_BYTES, decode_pwm_us_frame


class FakeSPI:
    def __init__(self, events: list[tuple[str, bytes | None]]) -> None:
        self.events = events

    def write_frame(self, frame: bytes) -> None:
        self.events.append(("write", frame))

    def close(self) -> None:
        self.events.append(("spi_close", None))


class FakeSync:
    def __init__(self, events: list[tuple[str, bytes | None]]) -> None:
        self.events = events

    def pulse(self) -> None:
        self.events.append(("sync", None))

    def close(self) -> None:
        self.events.append(("sync_close", None))


class RealTransportTests(unittest.TestCase):
    def test_complete_frame_is_written_before_each_sync(self) -> None:
        events: list[tuple[str, bytes | None]] = []
        interface = HardwareInterface(
            use_mock=False,
            spi=FakeSPI(events),
            sync=FakeSync(events),
        )
        self.assertEqual([event[0] for event in events], ["write", "sync"])
        startup_frame = events[0][1]
        self.assertIsNotNone(startup_frame)
        startup = decode_pwm_us_frame(startup_frame or b"")
        self.assertFalse(startup.output_armed)
        self.assertTrue(all(value == PWM_IDLE for value in startup.pwm_us))

        values = [PWM_IDLE] * NUM_MOTORS
        values[0] = 1150
        interface.send_pwm_frame(values, output_armed=True)
        self.assertEqual([event[0] for event in events[-2:]], ["write", "sync"])
        command_frame = events[-2][1]
        self.assertIsNotNone(command_frame)
        self.assertEqual(len(command_frame or b""), PWM_FRAME_BYTES)
        command = decode_pwm_us_frame(command_frame or b"")
        self.assertTrue(command.output_armed)
        self.assertEqual(command.pwm_us[0], 1150)
        interface.shutdown()


if __name__ == "__main__":
    unittest.main()
