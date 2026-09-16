# German-reference C01 one-motor bench

This is an isolated diagnostic derived from the pinned German reference
revision `0280f876e587c41cd54a499913e4e208465c6d3e` in
`SOURCE.json`. It is separate from the operator GUI and the 128-motor
application.

The firmware keeps the original 36-byte SPI frame, byte-paced SPI0/CE0,
GPIO22 rising-edge latch, GP0 50 Hz PWM, and 1000/2000 us pulse range. It
adds USB CDC status and bounded tests. Only GP0 is configured as PWM; GP1-GP8
and MISO are inputs. USB `PULSE USB` gives one 1200 us pulse for one second,
then stops. SPI `ARM SPI` permits one 1200 us pulse from a valid frame and
requires valid 36-byte frames; the watchdog stops it after 200 ms without
frames. The host must see the exact C01 serial `F68B8438147951D7`.

## Build and software tests

```bash
cmake -S . -B build -DPICO_SDK_PATH=/home/jwatson/pico-sdk
cmake --build build -j4
cc -std=c11 -Wall -Wextra -Werror test_receiver.c -o /tmp/test_german_receiver
/tmp/test_german_receiver
python3 make_uf2.py
```

`test_receiver.c` exercises boot idle, exact frame length, every forbidden
channel byte, overflow, idle/stop, watchdog, USB deadline, SPI deadline, and
lease expiry. No hardware is accessed by that test.

## Physical setup

Keep the motor battery disconnected while flashing and while running the
initial `status` or USB test. Connect only one serial-matched C01 Pico, one ESC
signal on C01 GP0, the five Pi links (MOSI GP16, CE0 GP17, SCLK GP18, sync
GP22, ground), and GP0 to Pi GPIO23 for the input-only measurement. USB must be
direct to the Pi. Do not connect an ESC BEC lead to Pi GPIO23.

Enter BOOTSEL on the serial-matched C01, copy `german_one_motor.uf2`, and
wait for reboot. The USB diagnostic port then appears as a `ttyACM*` device.

## Bounded tests

```bash
python3 bench.py status
python3 bench.py usb --run
python3 bench.py spi --run
python3 bench.py suite --run
```

`status` is read-only. The other modes send bounded commands and require
`--run`. `suite` runs idle, USB pulse/deadline, exact SPI receive counts,
single-channel SPI pulse, stop, watchdog, and malformed-frame rejection. It
records a JSON report under `logs/` and always sends `STOP` during cleanup.

The initial bench pass is complete only when `usb --run` reports a clean
1200 us measurement and `spi --run` reports sent bytes = received bytes and
syncs, valid frames equal to the sent frame count, followed by a clean 1200 us
GPIO23 measurement. Keep propulsion disconnected until both tests pass.
