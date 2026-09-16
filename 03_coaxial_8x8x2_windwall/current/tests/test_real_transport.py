from __future__ import annotations

import unittest
from threading import Event
from time import monotonic, sleep

from config import NUM_MOTORS, PWM_IDLE
from coaxial_windwall.hardware.interface import HardwareInterface, LatestFrameDispatcher
from coaxial_windwall.protocol import PWM_FRAME_BYTES, decode_pwm_us_frame


class FakeSPI:
    def __init__(self, events: list[tuple[str, bytes | None]]) -> None:
        self.events = events

    def write_frame(self, frame: bytes) -> None:
        self.events.append(("write", frame))

    def close(self) -> None:
        self.events.append(("spi_close", None))


class SlowSPI(FakeSPI):
    def __init__(self, events: list[tuple[str, bytes | None]]) -> None:
        super().__init__(events)
        self.delay_s = 0.0

    def write_frame(self, frame: bytes) -> None:
        sleep(self.delay_s)
        super().write_frame(frame)


class GatedSPI(FakeSPI):
    def __init__(self, events: list[tuple[str, bytes | None]]) -> None:
        super().__init__(events)
        self.block_next = False
        self.entered = Event()
        self.release = Event()

    def write_frame(self, frame: bytes) -> None:
        if self.block_next:
            self.block_next = False
            self.entered.set()
            self.release.wait(timeout=1.0)
        super().write_frame(frame)


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
        self.assertFalse(hasattr(interface, "use_mock"))
        self.assertFalse(hasattr(interface, "mode_name"))
        interface.shutdown()

    def test_test_transports_must_be_supplied_as_a_pair(self) -> None:
        events: list[tuple[str, bytes | None]] = []
        with self.assertRaises(ValueError):
            HardwareInterface(spi=FakeSPI(events))

    def test_latest_frame_dispatch_does_not_block_the_gui_caller(self) -> None:
        events: list[tuple[str, bytes | None]] = []
        spi = SlowSPI(events)
        interface = HardwareInterface(spi=spi, sync=FakeSync(events))
        dispatcher = LatestFrameDispatcher(interface)
        spi.delay_s = 0.15

        started = monotonic()
        queued = dispatcher.submit(
            [PWM_IDLE] * NUM_MOTORS,
            output_armed=True,
        )
        queue_time = monotonic() - started

        self.assertTrue(queued)
        self.assertLess(queue_time, 0.05)
        self.assertTrue(dispatcher.wait_until_idle(timeout_s=1.0))
        self.assertTrue(dispatcher.close())
        interface.shutdown()

    def test_latest_frame_dispatch_replaces_stale_pending_frame(self) -> None:
        events: list[tuple[str, bytes | None]] = []
        spi = GatedSPI(events)
        interface = HardwareInterface(spi=spi, sync=FakeSync(events))
        dispatcher = LatestFrameDispatcher(interface)
        spi.block_next = True

        first = [PWM_IDLE] * NUM_MOTORS
        first[0] = 1100
        stale = [PWM_IDLE] * NUM_MOTORS
        stale[0] = 1200
        newest = [PWM_IDLE] * NUM_MOTORS
        newest[0] = 1300

        self.assertTrue(dispatcher.submit(first, output_armed=True))
        self.assertTrue(spi.entered.wait(timeout=1.0))
        self.assertTrue(dispatcher.submit(stale, output_armed=True))
        self.assertTrue(dispatcher.submit(newest, output_armed=True))
        spi.release.set()
        self.assertTrue(dispatcher.wait_until_idle(timeout_s=1.0))

        written = [
            decode_pwm_us_frame(frame)
            for event, frame in events
            if event == "write" and frame is not None
        ]
        self.assertEqual(len(written), 3)
        self.assertEqual(written[1].pwm_us[0], 1100)
        self.assertEqual(written[2].pwm_us[0], 1300)

        self.assertTrue(dispatcher.close())
        interface.shutdown()


if __name__ == "__main__":
    unittest.main()
