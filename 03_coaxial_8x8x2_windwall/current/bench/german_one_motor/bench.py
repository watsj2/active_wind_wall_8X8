#!/usr/bin/env python3
"""Standalone German-protocol C01 test; no wind-wall application imports."""
from __future__ import annotations

import argparse
import fcntl
import json
import os
from pathlib import Path
import select
import signal
import statistics
import struct
import termios
import threading
import time
import tty

BOARD = "F68B8438147951D7"
FIRMWARE = "german-one-motor-v1"
FRAME_BYTES = 36
TEST_RAW = 51


def make_frame(active=False):
    return bytes([TEST_RAW if active else 0]) + bytes(FRAME_BYTES - 1)


def find_port():
    matches = []
    for entry in Path('/sys/class/tty').glob('ttyACM*'):
        for parent in (entry / 'device').resolve().parents:
            serial = parent / 'serial'
            vendor = parent / 'idVendor'
            if serial.exists() and vendor.exists():
                if serial.read_text().strip().upper() == BOARD and vendor.read_text().strip() == '2e8a':
                    matches.append('/dev/' + entry.name)
                break
    if len(matches) != 1:
        raise RuntimeError(f'Expected one diagnostic USB serial for C01 {BOARD}; found {matches}. Flash the new bench UF2 first.')
    return matches[0]


class Serial:
    def __init__(self, path):
        self.fd = os.open(path, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        self.buffer = b''
        try:
            fcntl.ioctl(self.fd, termios.TIOCEXCL)
            tty.setraw(self.fd)
            termios.tcflush(self.fd, termios.TCIOFLUSH)
            # Pico USB CDC does not use modem-control lines. Avoid toggling
            # DTR: on some Pi USB stacks that resets the board and discards
            # the first diagnostic response.
            time.sleep(0.15)
        except BaseException:
            os.close(self.fd)
            raise

    def command(self, command, json_reply=False):
        data = (command + '\n').encode('ascii')
        if os.write(self.fd, data) != len(data):
            raise RuntimeError('Incomplete USB command write')
        end = time.monotonic() + 1.0
        while time.monotonic() < end:
            while b'\n' in self.buffer:
                line, self.buffer = self.buffer.split(b'\n', 1)
                line = line.strip()
                if json_reply and line.startswith(b'{'):
                    result = json.loads(line)
                    if result.get('firmware') != FIRMWARE or result.get('board', '').upper() != BOARD:
                        raise RuntimeError('Wrong firmware or controller; refusing to proceed')
                    return result
                if not json_reply and line == ('OK ' + command).encode():
                    return line.decode()
                if line.startswith(b'ERROR'):
                    raise RuntimeError(line.decode())
            ready, _, _ = select.select([self.fd], [], [], max(0, end-time.monotonic()))
            if ready:
                chunk = os.read(self.fd, 4096)
                if not chunk:
                    raise RuntimeError('Pico USB disconnected')
                self.buffer += chunk
        raise TimeoutError('No valid Pico USB response')

    def close(self):
        os.close(self.fd)


class Pins:
    """Input capture on GPIO23 plus exclusive sync GPIO22; installed gpiod 1.x."""
    def __init__(self):
        import gpiod
        self.gpiod = gpiod
        self.chip = self.sync = self.input = None
        self.thread = None
        self.samples = []
        self.errors = []
        self.stop_event = threading.Event()
        self.failure = None
        try:
            for path in sorted(Path('/dev').glob('gpiochip*')):
                chip = gpiod.Chip(str(path))
                if chip.label() == 'pinctrl-rp1':
                    self.chip = chip
                    break
                chip.close()
            if self.chip is None:
                raise RuntimeError('Pi header GPIO controller not found')
            sync = self.chip.get_line(22)
            if sync.is_used():
                raise RuntimeError('GPIO22 is already owned; close the wind-wall GUI first')
            sync.request(consumer='german-one-motor-sync', type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])
            self.sync = sync
            tap = self.chip.get_line(23)
            if tap.is_used() or tap.name() != 'GPIO23':
                raise RuntimeError('GPIO23 measurement input is unavailable')
            tap.request(consumer='german-one-motor-pwm', type=gpiod.LINE_REQ_EV_BOTH_EDGES,
                        flags=gpiod.LINE_REQ_FLAG_BIAS_DISABLE)
            self.input = tap
            self.thread = threading.Thread(target=self._capture, daemon=True)
            self.thread.start()
        except BaseException:
            self.close()
            raise

    def _capture(self):
        rise = last_rise = last_event = None
        period = None
        try:
            while not self.stop_event.is_set():
                if not self.input.event_wait(sec=0, nsec=50000000):
                    continue
                event = self.input.event_read()
                stamp = event.sec * 1000000000 + event.nsec
                rising = event.type == self.gpiod.LineEvent.RISING_EDGE
                if last_event is not None and stamp <= last_event:
                    self.errors.append(stamp)
                    rise = last_rise = None
                elif rising:
                    if rise is not None: self.errors.append(stamp)
                    period = (stamp-last_rise)/1000 if last_rise is not None else None
                    rise = last_rise = stamp
                elif rise is None:
                    self.errors.append(stamp)
                else:
                    self.samples.append((stamp, (stamp-rise)/1000, period))
                    rise = None
                last_event = stamp
        except BaseException as error:
            self.failure = str(error)

    def pulse_sync(self):
        self.sync.set_value(1)
        try: time.sleep(.00001)
        finally: self.sync.set_value(0)

    def measure(self, begin, end, target):
        if self.failure: raise RuntimeError('PWM capture failed: ' + self.failure)
        samples = [s for s in self.samples if begin <= s[0] <= end]
        widths = [s[1] for s in samples]
        periods = [s[2] for s in samples if s[2] is not None]
        good = [v for v in widths if abs(v-target) <= 30]
        malformed = sum(begin <= t <= end for t in self.errors)
        frequency = 1000000/statistics.median(periods) if periods else None
        return {
            'target_us': target, 'samples': len(widths), 'matching': len(good),
            'median_us': statistics.median(widths) if widths else None,
            'min_us': min(widths) if widths else None, 'max_us': max(widths) if widths else None,
            'frequency_hz': frequency, 'malformed': malformed,
            'pass': bool(len(good) >= 10 and len(good) >= .9*len(widths)
                         and frequency is not None and 48 <= frequency <= 52 and malformed == 0),
        }

    def close(self):
        self.stop_event.set()
        if self.thread: self.thread.join(timeout=1)
        if self.input: self.input.release()
        if self.sync:
            try: self.sync.set_value(0)
            finally: self.sync.release()
        if self.chip: self.chip.close()


class SPI:
    def __init__(self, pins):
        import spidev
        self.pins = pins
        self.spi = spidev.SpiDev()
        try:
            self.spi.open(0, 0)
            self.spi.max_speed_hz = 1000000
            self.spi.mode = 0
            self.spi.bits_per_word = 8
        except BaseException:
            self.spi.close()
            raise

    def send(self, frame):
        # Preserve original German byte-paced xfer2 + 10 us sync order.
        for value in frame: self.spi.xfer2([value])
        self.pins.pulse_sync()

    def stream(self, frame, seconds):
        deadline = time.monotonic() + seconds
        sent = 0
        while time.monotonic() < deadline:
            tick = time.monotonic()
            self.send(frame)
            sent += 1
            time.sleep(max(0, min(.02-(time.monotonic()-tick), deadline-time.monotonic())))
        return sent

    def close(self): self.spi.close()


def run_suite(serial, pins, spi, mode, emit):
    def status(label):
        result = serial.command('STATUS', True)
        emit(label, result)
        return result

    def measured(label, begin, target):
        # Discard the first/last 40 ms to exclude PWM update boundaries.
        report = pins.measure(begin+40000000, time.monotonic_ns()-40000000, target)
        emit(label, report)
        if not report['pass']: raise RuntimeError(label + ' failed; see measured PWM and counters')

    serial.command('STOP')
    initial = status('identity')
    if initial['pwm_us'] != 1000 or initial['armed']:
        raise RuntimeError('Pico did not report stopped idle')
    begin = time.monotonic_ns(); time.sleep(.6)
    measured('boot_idle', begin, 1000)

    if mode in ('usb', 'suite'):
        serial.command('PULSE USB')
        begin = time.monotonic_ns(); time.sleep(.55)
        measured('usb_direct_1200', begin, 1200)
        time.sleep(.65) # Firmware must stop itself without a host STOP command.
        begin = time.monotonic_ns(); time.sleep(.4)
        measured('usb_deadline_idle', begin, 1000)
        result = status('after_usb')
        if result['pwm_us'] != 1000 or result['armed']:
            raise RuntimeError('USB one-second deadline failed')

    if mode in ('spi', 'suite'):
        before = status('before_spi')
        sent = spi.stream(make_frame(), .6)
        after = status('spi_idle_reception')
        report = {'sent': sent, 'bytes': after['bytes']-before['bytes'],
                  'syncs': after['syncs']-before['syncs'], 'valid': after['valid']-before['valid']}
        emit('spi_idle_delta', report)
        if report != {'sent': sent, 'bytes': sent*36, 'syncs': sent, 'valid': sent}:
            raise RuntimeError('SPI receive counts differ from host sends; inspect MOSI/SCLK/CE0/sync')

        serial.command('ARM SPI')
        begin = time.monotonic_ns(); spi.stream(make_frame(True), .6)
        measured('spi_1200', begin, 1200)
        spi.stream(make_frame(), .1)
        begin = time.monotonic_ns(); spi.stream(make_frame(), .4)
        measured('spi_stop_idle', begin, 1000)
        status('after_spi_stop')

        # One more bounded pulse verifies the no-frame watchdog independently.
        serial.command('ARM SPI')
        spi.stream(make_frame(True), .3)
        active = status('watchdog_initial_active')
        if active['pwm_us'] != 1200: raise RuntimeError('Watchdog test never entered active state')
        time.sleep(.3)
        begin = time.monotonic_ns(); time.sleep(.4)
        measured('watchdog_idle', begin, 1000)
        result = status('after_watchdog')
        if result['armed'] or result['timeouts'] <= active['timeouts']:
            raise RuntimeError('No-frame watchdog did not disarm')

        bad_other = bytearray(make_frame(True)); bad_other[1] = TEST_RAW
        for label, frame in [('short', make_frame(True)[:-1]),
                             ('oversize', make_frame(True)+bytes(230)),
                             ('other_channel', bad_other)]:
            serial.command('ARM SPI')
            before = status('before_' + label)
            spi.send(frame); time.sleep(.05)
            result = status('reject_' + label)
            if result['invalid'] != before['invalid']+1 or result['pwm_us'] != 1000 or result['armed']:
                raise RuntimeError('Malformed frame was not rejected: ' + label)
    serial.command('STOP')
    status('final_idle')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('status', 'usb', 'spi', 'suite'))
    parser.add_argument('--run', action='store_true', help='explicitly enable bounded 1200 us tests')
    args = parser.parse_args(argv)
    if args.mode != 'status' and not args.run:
        parser.error('Tests change GP0 output; --run is required')
    events = []
    def emit(label, result):
        event = {'time': time.time(), 'stage': label, 'result': result}
        events.append(event); print(json.dumps(event), flush=True)
    def interrupted(signum, frame): raise RuntimeError(f'Interrupted by signal {signum}')
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGALRM): signal.signal(sig, interrupted)
    serial = pins = spi = None
    success = False
    try:
        signal.alarm(30)
        serial = Serial(find_port())
        identity = serial.command('STATUS', True)
        emit('connected', identity)
        if args.mode == 'status': return 0
        pins = Pins()
        if args.mode in ('spi', 'suite'): spi = SPI(pins)
        run_suite(serial, pins, spi, args.mode, emit)
        success = True
        return 0
    except Exception as error:
        emit('error', str(error))
        return 1
    finally:
        signal.alarm(0)
        if serial:
            try:
                if args.mode != 'status': serial.command('STOP')
            except Exception as error: emit('stop_error', str(error))
            finally: serial.close()
        if spi: spi.close()
        if pins: pins.close()
        if args.mode != 'status':
            emit('complete', {'pass': success})
            logs = Path(__file__).resolve().parent / 'logs'
            logs.mkdir(exist_ok=True)
            path = logs / (time.strftime('%Y%m%d-%H%M%S') + f'-{args.mode}.json')
            path.write_text(json.dumps(events, indent=2)+'\n')
            print('Report:', path, flush=True)

if __name__ == '__main__': raise SystemExit(main())
