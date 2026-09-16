# Coaxial 8x8x2 Windwall Handoff - 2026-08-12

## Real-Only GUI Runtime

At the user's explicit request, mock mode was removed from the application
rather than merely hidden from the GUI:

- `main.py` no longer defines `--mock` or `--smoke-test`; passing `--mock`
  exits with argparse status 2 and reports an unrecognized argument;
- `DEFAULT_HARDWARE_MODE` was removed from configuration;
- `HardwareInterface` no longer has `use_mock`, `mode_name`, or a branch that
  skips SPI/sync writes;
- `CoaxialWindwallWindow` and `run_app()` no longer accept a mock-mode choice;
- every normal GUI launch now constructs the real SPI0/GPIO22 transport;
- hardware-free automated verification remains possible only through explicit
  test dependency injection of paired no-output SPI and sync transports. This
  is not exposed by the application or launcher.

The README, host protocol, and physical checklist now state that application
startup is real hardware activity. The launcher remains `scripts/launch_gui.sh`
and invokes `python3 main.py` with no runtime mode switch.

## GPIO Chip Discovery Fix

The first real-only launch on 2026-08-12 correctly refused to start when the
old hardcoded `/dev/gpiochip4` path did not exist. Current device enumeration
places the Raspberry Pi header controller at:

```text
/dev/gpiochip15 [pinctrl-rp1] (54 lines)
```

The code now discovers the GPIO character device by the stable
`pinctrl-rp1` label at startup instead of assuming a numeric `gpiochipN` path.
This supports the installed libgpiod 1.6 API and retains the existing gpiod 2.x
request path.

After the fix, the real GUI opened successfully. Read-only checks confirmed:

- process `python3 main.py` is running;
- the visible X11 window is titled `Windwall`;
- GPIO22 is owned by `coaxial-windwall-control` as an output;
- SPI0 CE0 remains present at `/dev/spidev0.0`.

Startup sent only the existing disarmed `1000 us` idle frame. No Arm or Start
action was taken by Codex.

## Verification

No-output verification after both changes passed:

```text
Python compilation                         PASS
generated motor mapping --check            PASS
26 unit/GUI/signal/transport tests          PASS
python3 main.py --mock                      REJECTED (exit 2)
```

The authoritative controller mapping, `HOST_INDICES`, protocol, firmware, and
saved motor assignments were not changed.

## Hardware and Safety Continuity

The exact latest channel result remains 121 of 128 motors working, with
`B02`, `F06`, `F07`, `B11`, `B14`, `B15`, and `F27` unresolved.

The controller-power-loss incident remains controlling: removing or switching
Pico/controller USB power while propulsion batteries were connected caused
erratic/random full-speed operation. Never remove or switch controller power
with propulsion connected. Required order remains:

```text
Power-up:   Pico/control USB first -> verify idle PWM -> propulsion battery last
Power-down: propulsion battery first -> verify motors stopped -> Pico USB last
```

Because the application is now real-only, treat every GUI launch as real bus
activity and verify the physical safe state first. The GUI still requires an
explicit Arm and Start before sending an above-idle command.

## Confirmed Control-Only Real Transport Trace

After the user reported that a `SYSTEM RUNNING` / `1400 us` attempt still
produced no motor response, read-only checks confirmed that the live GUI held
`/dev/spidev0.0`, `/dev/gpiochip15`, and the GPIO22 line handle. Pin functions
were correct for SPI0 MOSI/SCLK/MISO and GPIO22 sync, and the current process
had no runtime exception.

The user then stopped/disarmed, physically disconnected propulsion batteries,
left controller USB powered, and confirmed that safe state. During a subsequent
control-only Arm/Start/Stop sequence, an attached syscall trace recorded:

```text
SPI0 fd 6:       94,164 successful SPI_IOC_MESSAGE calls
frame length:       266 byte transfers per full-wall frame
complete frames:    354
GPIO22 fd 8:        708 successful set-line calls
sync pulses:        354 (one high/low pair per frame)
trace interval:     approximately 8.35 seconds
```

The counts divide exactly into 354 complete 266-byte frames and 354 matching
sync pulses. Every observed SPI and GPIO kernel call succeeded. Strace overhead
reduced the observed rate below the normal untraced target, so the trace is
evidence of frame issuance and sync pairing rather than a timing benchmark.

The active saved group commanded five upstream/downstream pairs at `1400 us`:
F22/B22 and F23/B23 on C11, F26/B26 and F27/B27 on C12, and F33/B33 on C05.
C05 was previously confirmed working, C11 had no channel in the unresolved
seven-motor list, and C12 had mixed working outputs. Failure across all three
therefore isolates the current fault downstream of the Pi application and
kernel device drivers, in the shared physical MOSI/SCLK/CE0/sync/ground path
or Pico frame reception. Do not reintroduce mock mode or change the generated
mapping/protocol in response to this symptom.

With propulsion still disconnected, the next safest check is power-off
continuity of the five common command conductors from the Pi header to a
known-working controller such as C05. Close the GUI first, then controller USB
may be removed. Do not reconnect propulsion until controller power and idle
PWM are restored and verified in the documented safe order.
