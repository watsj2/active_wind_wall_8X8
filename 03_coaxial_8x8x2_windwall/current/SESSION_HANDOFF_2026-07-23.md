# Coaxial 8x8x2 Windwall Handoff - 2026-07-23

## B08 Propeller-Loss and B28 Strike Incident

The user reports that the blade/propeller came off `B08`, struck `B28`, and
that `B08` plus every motor assigned to `C04` no longer work. This is a new
mechanical-strike and possible electrical-damage event. No post-impact motor
operation is safe until the wall has been mechanically inspected and the
affected wiring has passed power-off checks.

The affected authoritative mapping is:

```text
B08 -> C01 CH8/GP7

C04 CH1/GP0 -> F25
C04 CH2/GP1 -> B25
C04 CH3/GP2 -> F28
C04 CH4/GP3 -> B28 (reported impact location)
C04 CH5/GP4 -> F29
C04 CH6/GP5 -> B29
C04 CH7/GP6 -> F32
C04 CH8/GP7 -> B32
```

Because `B08` is on `C01` while all eight C04 outputs stopped after the strike
at `B28`, do not treat this as nine independent motor failures. With all
propulsion batteries physically disconnected, inspect the failed B08
propeller retention, motor bell/shaft/mount, B28 and neighboring propellers,
the B28 motor/ESC leads, and the C04 shared Pico USB power, ground, controller
connector, and local SPI/sync harness. Look for displaced connectors, cut or
pinched insulation, exposed conductors, bent hardware, board contact, or
burning/discoloration before applying control power.

The real GUI was not running during the read-only host check after the report.
No command was sent, no firmware was flashed, and no hardware state was
changed. The controlling shutdown order remains propulsion power off first,
verify all rotors stopped, then controller power. Do not remove or reconnect
controller USB, signal leads, or impacted wiring while propulsion power is
present.

At the user's subsequent request, physical Pico 4/C04 was put into BOOTSEL and
identified by its previously recorded serial:

```text
RP2350 USB serial 755F04F32D54ABCA
pico/firmware_c04.uf2
SHA-256 e3ee3f1870d282c02f729706c136f242ea08340a3a9942a9382fc14db7cc40a9
controller_id 3
HOST_INDICES 24, 88, 27, 91, 28, 92, 31, 95
```

The user explicitly confirmed that the propulsion batteries were
disconnected, and the real GUI was stopped. The verified C04 image was copied
to the confirmed BOOTSEL volume and `sync` completed. The RP2350 mass-storage
device then disappeared, confirming that Pico 4 accepted the image and
rebooted. No motor command was sent. This reflash does not resolve or clear
the B08/B28 mechanical-strike state; do not perform a powered motor test until
the impacted propellers, retention hardware, motors/mounts, and C04 wiring
have been inspected and any damage corrected.

The user subsequently reported that the strike damage has been fixed, but
Pico 4/C04 still seems nonresponsive. A read-only host check found no real GUI
process and no RP2350 mass-storage device, which is the normal post-flash state
after C04 exits BOOTSEL. Absence of a normal USB serial device or visible
onboard-LED activity does not prove application failure: runtime USB stdio is
disabled, and the current `pico2` firmware drives GP25 rather than the Pico 2 W
CYW43 `WL_GPIO0` onboard LED. The successful serial-matched BOOTSEL
enumeration, UF2 copy, sync, and reboot prove that the RP2350 boot
ROM/USB/flash path was responsive at the time of flashing.

The remaining safe diagnostic split is whether C04 produces idle PWM but does
not receive above-idle commands, or produces no local PWM at all. With
propulsion physically disconnected, first verify C04 controller USB power,
the eight-channel connector, signal ground, and local harness. Do not reflash
again from the current evidence.

## C01 Code Verification and Requested Reflash

At the user's request, the host code, generated mapping, tests, mock GUI, and
C01 firmware artifact were rechecked before reflashing physical Pico 1.

Verification passed:

- Python compilation completed without errors;
- `scripts/generate_motor_mapping.py --check` passed;
- all 16 unit, GUI-workflow, signal, and mocked real-transport tests passed;
- the mock GUI smoke test passed with `QT_QPA_PLATFORM=offscreen` (the first
  attempt could not access display `:0` from the sandbox);
- executable host-control and firmware sources have not changed since the
  previously working period;
- generated C01 source exactly matches the current firmware template and
  authoritative mapping;
- the UF2 application payload exactly matches its compiled BIN, including
  zero-only trailing block padding.

The verified image and physical BOOTSEL identity were:

```text
pico/firmware_c01.uf2
SHA-256 bc75d1c1746c08ac0d424221fefe734af88f3008d888f30923839eaea899700c
RP2350 USB serial F68B8438147951D7
CONTROLLER_ID 0
HOST_INDICES 0, 64, 3, 67, 4, 68, 7, 71
CH1-CH8 F01, B01, F04, B04, F05, B05, F08, B08
```

The hash and serial exactly match the C01 image and physical board recorded as
working on 2026-07-19. The user explicitly confirmed that all propulsion
batteries were physically disconnected. The real GUI was stopped. The UF2 was
copied to the confirmed C01 BOOTSEL volume and `sync` completed; the RP2350
then disconnected from USB mass storage and exited BOOTSEL normally. No motor
command was sent. Functional testing after this reflash has not yet been
reported.

## New Full-Wall Non-Run Report

The user subsequently reported that no motor on the wall would run. This is a
new common-path symptom and supersedes the 121-of-128 result for immediate
diagnosis, but it does not yet prove that all 128 local motor paths have
regressed.

Read-only host inspection found:

- `python3 main.py` running on the Raspberry Pi;
- the GUI in real mode, with the process owning `/dev/spidev0.0`;
- `GPIO22` claimed as an output by `coaxial-windwall-control`;
- SPI0/CE0 and the GPIO device nodes present;
- the visible GUI at `ARMED / REAL`, not `RUNNING / REAL`;
- every displayed channel and the wall average at the intentional `1000 us`
  idle value, with `START EXPERIMENT` still enabled.

The GUI returns to `ARMED / REAL` and `1000 us` after a timed run when
auto-disarm is unchecked. The user confirmed that the attempted run did
visibly show `RUNNING / REAL` and an average of `1200 us`, all 16 Pico power
indicators were on, and the ESCs expected to work were not giving their
no-connection/no-signal alarm. This establishes that the Picos remained
powered and those ESCs continued to recognize Pico-generated PWM, but no
motor responded to the above-idle host command.

Additional read-only host checks confirmed that the live process working
directory is the canonical 8x8x2 project, SPI0 MOSI/SCLK are in their SPI
functions, CE0 is claimed, GPIO22 sync is claimed and low at idle, and the
executable control files have not changed since the preceding 121-of-128
result. A software-version regression is therefore unlikely. The shared
Pi-to-Pico MOSI/SCLK/CE0/sync/ground command/latch path is now the leading
fault domain.

The decisive safe test is to keep all propulsion batteries physically
disconnected and use control power only. Command one formerly working channel,
preferably `F01` on `C01 CH1/GP0`, and measure whether its Pico PWM output
changes from approximately `1000 us` idle to `1200 us`. If it remains at idle,
trace MOSI/SCLK/CE0/sync and signal ground from the Pi header to C01. If GP0
does reach `1200 us`, the shared command bus is working and common propulsion
power or ESC arming becomes the leading domain.

The user does not have an oscilloscope or logic analyzer. Existing firmware
already provides a no-instrument diagnostic on Pico `GP25` / the onboard LED:

- while `RUNNING / REAL` at the configured 50 Hz command rate, continuing
  valid frames toggle the LED every 20 sync pulses, or approximately every
  `0.4 s` (one full blink cycle in approximately `0.8 s`);
- after `250 ms` without a valid frame, the watchdog drives a faster pattern,
  changing every `0.1 s` (one full cycle in `0.2 s`);
- ARMED-but-not-running and DISARMED do not send continuing frames, so observe
  the LED only during the active `RUNNING / REAL` interval.

With propulsion physically disconnected, reduce the GUI assignment to only
formerly working `F01`, run a short control-only command, and watch C01's
onboard LED. A slow pattern proves that valid frames reach C01; a fast or
irregular watchdog pattern means the shared frame is not reaching/validating
at C01. If C01 is slow, compare the next controller to locate a branch boundary
without energizing propulsion.

The user did not see any LED flashing and then confirmed that the physical
controllers are **Pico 2 W**, not non-wireless Pico 2 boards. The current
firmware was built with `PICO_BOARD=pico2` and hard-codes `LED_PIN 25`. On a
Pico 2 W, the onboard LED is connected through the CYW43 wireless chip as
`WL_GPIO0`; `GP25` is an internal CYW43 chip-select signal. Therefore the
existing firmware cannot visibly drive the Pico 2 W onboard LED and the
proposed blink diagnostic is invalid. No-flash/no-blink is expected and says
nothing about SPI frame reception.

The Pico 2 and Pico 2 W definitions use the same external SPI0 pins
`GP16-GP19`, the same RP2350A variant, and the same 4 MiB flash size. The
existing images also previously ran 121 motors on these same boards, so the
board-target mismatch does not by itself explain the new sudden full-wall
failure. Future firmware should nevertheless use the correct `pico2_w` target
and a CYW43-aware status LED implementation. Do not mass-reflash to correct
this during the current fault isolation. Use a power-off continuity check or
prepare and bench-test one explicitly identified diagnostic controller first.

The current group assigns all 128 motors at `1200 us`; do not start that
all-wall group during diagnosis. The user was asked to disarm. No motor command
was sent, no firmware was flashed, and no hardware state was changed during
the inspection.

## Latest Hardware Result

The user reports that 121 of the wall's 128 motors now work. The seven
remaining nonworking motors are:

```text
B02, F06, F07, B11, B14, B15, F27
```

Authoritative controller/channel mapping:

```text
C09 CH2/GP1 B02  failed
C09 CH5/GP4 F06  failed
C09 CH7/GP6 F07  failed

C10 CH4/GP3 B11  failed
C10 CH6/GP5 B14  failed
C10 CH8/GP7 B15  failed

C12 CH3/GP2 F27  failed
```

The originally reported eight-motor list contained exactly one failure on each
output `GP0-GP7`. The fast/loud-beeping Pichler QX-45 ESC on F02 was then
identified as faulty, and F02 worked with the fault removed. This proves the
C09 CH1/GP0 signal path. The remaining seven failures cover `GP1-GP7` exactly
once; do not continue using the earlier eight-of-32 probability as evidence
that all eight shared one harness cause.

`C09`, `C10`, and `C12` have both working and nonworking outputs. Despite an
earlier general statement that C09-C12 all had mixed results, the exact list
contains no C11 output; therefore C11 is currently treated as fully working
unless the user identifies another failed motor.

The mixed output proves the controllers are booting and receiving usable wall
commands. Shared Pi SPI/sync failure, total Pico USB-power failure, and four
incorrect firmware images do not explain the remaining eight faults. The
one-of-each-GP pattern is non-random enough to record before moving wiring. It
may indicate a systematic harness, connector, layer-routing, or test-selection
pattern, but it does not yet identify the cause.

The current saved group contains all seven remaining failed host indices, so
simple omission from that saved group does not explain the result.

## Remaining Seven Have Valid Signal Presence

The user reports that none of the seven remaining ESCs now gives the
disconnected/no-signal beep while its GPIO signal is connected. Pulling an
individual GPIO/signal connection makes that ESC start the no-signal beep;
plugging it back in stops the beep. All seven therefore receive and recognize
at least the Pico-generated idle pulse through their signal and ground paths.

This rules out a completely open signal wire or absent signal ground on those
channels. It does **not** prove that the pulse width rises above the
approximately 1000 us idle value when the host commands that motor. The next
decisive split is:

```text
Command remains ~1000 us -> host selection/mapping/frame/latch path
Command rises to requested value -> QX-45 arming/configuration/power/motor path
```

Perform this measurement with propulsion batteries physically disconnected:
USB/control power and the Pi command bus can exercise the Pico PWM output
without energizing the ESC power stage. Select only one failed motor, measure
its pulse at idle and during a command, and compare it with a working motor on
the same controller.

Never pull or reconnect an I/O lead while propulsion batteries are connected.
The prior controller-power-loss incident produced unexpected full-speed motor
operation; current no-signal beeping is not a sufficient fail-safe guarantee.

## C13/C15/C16 Regression and BOOTSEL Identity

The user subsequently reported that C13, C15, and C16 are not working. The
exact per-channel behavior and no-signal beep state for those three
controllers have not yet been recorded.

At that time one RP2350 was enumerated in BOOTSEL as `/dev/sdb`, mounted
read-only at `/media/jwatson/RP2350`, with serial:

```text
9215A5CE8E496A38
```

This serial was not in the previously recorded C02/C04/C09-C12 identity list.
The ROM volume identifies only a generic RP2350 and does not reveal the
installed `coaxial_cNN` image. A locally available `picotool` binary was also
compiled without USB support, so no flash metadata was read. It was left
untouched until the user later physically identified it as C15.

## C13 Reflash

The BOOTSEL target later changed to serial `00FD8CDB8C792B84`. The user
confirmed that this serial was physical Pico/C13 and that all propulsion
batteries were physically disconnected. The real GUI was not running.

The verified image was:

```text
pico/firmware_c13.uf2
SHA-256 bf563330734c29f065214b62595636f9c1b7022cf2f3cd01b1c9a1eca1d0ba6d
controller_id 12
HOST_INDICES 33, 97, 34, 98, 37, 101, 38, 102
```

Those indices are P34, P35, P38, and P39 on both layers. The UF2 was copied to
the confirmed C13 BOOTSEL volume and `sync` completed. The RP2350 device then
disappeared from `lsblk`, as expected after accepting the image and rebooting.
No motor command was sent. Functional testing after this reflash has not yet
been reported.

## C16 Reflash

BOOTSEL serial `57471CD1D7E2E6C2` was physically identified by the user as
Pico/C16. The user confirmed that all propulsion batteries were physically
disconnected, and the real GUI was not running.

The verified image was:

```text
pico/firmware_c16.uf2
SHA-256 940ea88cf29ecc1131fb278df9a5f0fbc99e84a4e5c2766694e365bb49f8aab5
controller_id 15
HOST_INDICES 57, 121, 58, 122, 61, 125, 62, 126
```

Those indices are P58, P59, P62, and P63 on both layers. The UF2 was copied to
the confirmed C16 BOOTSEL volume and `sync` completed. The RP2350 device then
disappeared from `lsblk`, as expected after accepting the image and rebooting.
No motor command was sent. Functional testing after this reflash has not yet
been reported.

## C15 Reflash

BOOTSEL serial `9215A5CE8E496A38` was physically identified by the user as
Pico/C15. The earlier confirmation that all propulsion batteries were
physically disconnected remained in force, and the real GUI was not running.

The verified image was:

```text
pico/firmware_c15.uf2
SHA-256 452949f63aaa0da5b0944bec8ef4a400de7c35e60edd66d9043d822076abc6fe
controller_id 14
HOST_INDICES 49, 113, 50, 114, 53, 117, 54, 118
```

Those indices are P50, P51, P54, and P55 on both layers. The UF2 was copied to
the confirmed C15 BOOTSEL volume and `sync` completed. The RP2350 device then
disappeared from `lsblk`, as expected after accepting the image and rebooting.
No motor command was sent. Functional testing after this reflash has not yet
been reported.

## ESC Population Correction

The user clarified that all T-MOTOR AIR 40 ESCs have been removed from the
wall. All 128 front- and back-layer ESCs are now **Pichler QX-45** units.
Earlier AIR 40 substitution and repinning notes are historical only and must
not be used to diagnose or wire the current wall. Current mapping data, wiring
documentation, and the generated PDF were updated to identify QX-45 on both
layers.

The user explicitly reconfirmed that no ESC BEC output is used anywhere on
the wall. Every QX-45 red/BEC lead remains disconnected and individually
insulated. Pico/controller power comes only from the separate USB hub power
system; do not diagnose the wall as if an ESC BEC powers a Pico or shared
control rail.

## Controller USB-Hub Power Architecture

The four Waveshare hubs are `USB3.2-Gen1-HUB-2IN-4OUT` units, one hub for four
Picos. In normal wall operation the USB cables power the Pico controllers; they
do **not** carry motor commands. The Pi sends the 266-byte command frame over
the shared GPIO/SPI wiring (`MOSI`, `SCLK`, `CE0`, and `GPIO22` sync), and each
Pico generates its eight local ESC PWM outputs on `GP0-GP7`. USB data is useful
for BOOTSEL/flashing, but the runtime firmware has USB stdio disabled.

The Pi itself remains on its separate USB-C supply. For each Waveshare hub:

- the two switchable USB-A host inputs accept normal 5 V USB power;
- the separate screw terminal and round DC jack require 7-36 V and must not
  receive a 5 V phone-charger output;
- an old 5 V USB-A iPhone charger can therefore power one hub through the
  selected USB-A input using the supplied USB-A cable;
- use one charger per hub, not one charger for all four hubs;
- an old 5 V/1 A Apple charger may be enough for one hub plus four lightly
  loaded Picos, but this has not been measured and gives limited brownout
  margin; a dependable 5 V/2 A-or-greater supply per hub is preferred;
- with the charger selected, the hub is not a USB data path to the Pi. Normal
  motor commands still arrive over GPIO/SPI, but BOOTSEL/flashing requires a
  Pi data connection.

A single separate 24 V/5 A control supply feeding all four hubs through their
7-36 V terminals remains an optional alternative, not a requirement. Do not
power the hubs directly and unfused from the noisy ESC bus bars.

Never switch hub inputs, unplug a controller USB cable, or change between
charger and Pi USB while propulsion batteries are connected. A momentary
controller brownout/reset is safety-critical because the wall has already
shown random full-speed operation after Pico power loss. Keep control power on
first and off last.

## ESC Alarm and Safety State

Immediately before this result, the user reported that one ESC was beeping
much faster and louder. The ESC was subsequently identified as the Pichler
QX-45 on `F02`, and it was faulty. F02 now works, proving `C09 CH1/GP0`.
`B02` (`C09 CH2/GP1`) still fails and must be diagnosed independently. The
assistant instructed the user to remove propulsion power using the external
cutoff from outside the propeller hazard area, then remove Pico/control power
only after all motors stopped.

The prior fail-unsafe incident remains controlling: removing Pico USB power
while propulsion batteries were connected caused random full-speed motors.
Never remove controller power first and never work on signal plugs with
propulsion power present.

Required order:

```text
Power-up:   Pico/control USB first -> verify idle PWM -> propulsion battery last
Power-down: propulsion battery first -> verify motors stopped -> Pico USB last
```

Do not reuse the faulty fast-beeping F02 ESC.

## Next Safe Diagnostic

Keep propulsion batteries physically disconnected. With Pico USB/control power
only, compare each failed channel against a working channel on the same Pico:

1. Check for 50 Hz, approximately 1000 us idle PWM directly from the relevant
   `GP0-GP7` pin to Pico ground.
2. If present at the Pico, check for the pulse at the ESC signal connector. A
   loss between those points identifies the connector/harness/ground path.
3. If it reaches the ESC connector, inspect signal/ground orientation and use
   only a power-off substitution to distinguish the ESC/motor path.
4. If absent directly at one Pico pin while adjacent pins work, inspect that
   header, solder joint, and board output before considering firmware action.

First verify that the GUI/test selection truly commanded all eight channels;
then compare the failure pattern with connector and harness topology. Do not
mass-reflash.

## Software and Configuration State

The ESC identity correction changed documentation only; controller ownership,
host indices, firmware, and runtime control logic did not change. The mapping
CSV/Markdown and wiring-manual PDF were regenerated for Pichler QX-45 on both
layers.

The current saved GUI group contains all 128 motors at `1200 us`. It includes
all seven remaining failed host indices. This does not prove the unsaved state
of a currently running GUI, and the all-wall group must not be used for
channel fault isolation.

For the complete flash history, serial identities, software audit, and
controller-power-loss incident, see:

```text
/home/jwatson/coaxial_8x8x2_windwall_system/SESSION_HANDOFF_2026-07-22.md
```
