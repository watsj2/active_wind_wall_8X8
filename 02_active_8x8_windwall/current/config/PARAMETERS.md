# Configuration Parameters

This file records the timing assumptions behind `config/__init__.py`.

## Hardware Topology

- `NUM_MOTORS = 64`
- `NUM_PICOS = 8`
- `MOTORS_PER_PICO = 8`

The active firmware expects each Pico to control local motor outputs `GP0..GP7`.

## SPI Clock

`SPI_SPEED_HZ = 1_000_000`

The Raspberry Pi is the SPI master. The Pico is the SPI slave, so the Pico
accepts the clock driven by the Pi. The RP2350 SPI slave can technically run
much faster than 1 MHz; the practical ceiling is roughly `sys_clk / 12`, which
is about 12.5 MHz at a 150 MHz system clock.

The current host path intentionally stays at 1 MHz because it sends bytes one
at a time. Python/kernel call overhead dominates total frame time, so raising
the SPI clock has little benefit until the host and firmware are changed to
support larger framed transfers safely. Higher SPI clock rates also reduce
noise margin on the Pi-to-Pico wiring.

## Loop Rate

`UPDATE_RATE_HZ = 400`

The control loop target is 400 Hz. With byte-paced SPI this is an aspirational
target under load; actual timing depends on Pi scheduling and the per-byte SPI
call cost. The 1.2 track keeps the working 1.1 rate for compatibility, but the
rate should be rechecked if SPI framing changes.

## PWM Range

- `PWM_MIN = 1000 us`: ESC armed/idle
- `PWM_MIN_RUNNING = 1200 us`: first non-idle motor command
- `PWM_MAX = 2000 us`: full command

The Pi maps PWM commands into bytes where `0` means idle and `1..255` maps to
`PWM_MIN_RUNNING..PWM_MAX`. The Pico firmware uses the same constants generated
from `config/__init__.py` by `pico/build_all_firmware.py`.

If `PWM_MIN_RUNNING` or `PWM_MAX` changes, rebuild and reflash all Pico UF2
files before using hardware.

## Tach Return

Tach mode uses a 68-byte command frame:

- 4-byte tach header
- 64 motor command bytes

The selected Pico returns a 40-byte response with edge-count deltas for its 8
local tach inputs. The GUI defaults to `No Tach / Legacy` unless tach return is
explicitly selected.
