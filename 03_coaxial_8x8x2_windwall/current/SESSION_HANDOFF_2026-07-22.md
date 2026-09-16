# Coaxial 8x8x2 Windwall Handoff - 2026-07-22

## Latest C01-C08 Result

The user corrected the physical wiring so controller labels again match their
intended roles:

```text
Pico 2 / C02 -> P09, P12, P13, P16
Pico 4 / C04 -> P25, P28, P29, P32
```

Before this correction, both relevant boards were running the C04 image, so
C04 commands drove both physical motor banks. The board now confirmed as Pico
2 was put into BOOTSEL and identified as serial `5D0AF10E890A0474`. It was
flashed on 2026-07-22 with:

```text
pico/firmware_c02.uf2
SHA-256 d60b4d377de78bc0df0f3fcb77601be0e5b42991cf6745791559bb936ed0c3a9
controller_id 1
HOST_INDICES 8, 72, 11, 75, 12, 76, 15, 79
```

The copy and `sync` completed, and the RP2350 BOOTSEL device disappeared as
expected after reboot. Pico 4 was not touched during this correction and should
retain `firmware_c04.uf2` for P25/P28/P29/P32.

The user has now confirmed that C01-C08 all work after the final C02 reflash
and C02/C04 wiring correction. The complete old-harness controller bank is
functionally confirmed.

## C12 Reflash

At the user's request, physical Pico 12 was put into BOOTSEL and identified as
serial `8BD9571726565DC8`. It was reflashed on 2026-07-22 with:

```text
pico/firmware_c12.uf2
SHA-256 7eaef6594209642a77256c00ca2c8cfdf450d3013261dc4aa82bd6d4dc936a3d
controller_id 11
HOST_INDICES 25, 89, 26, 90, 29, 93, 30, 94
```

Those indices are P26, P27, P30, and P31 on both layers. The copy and `sync`
completed successfully, and the RP2350 BOOTSEL device disappeared after the
write, confirming that the board accepted the image and rebooted. No motor
commands were sent during flashing. In the user's subsequent live test, C12
attempted to start a couple of times but appeared to stall. This shows some
response on the C12 path, but does not yet distinguish intermittent valid
frames/watchdog action from a power, ESC, motor, or too-low-start-command
problem. The exact physical motor(s) and PWM value still need to be recorded.
After the C09-C11 flashing pass, C12 was put into BOOTSEL again; its serial
matched `8BD9571726565DC8`, and the same verified C12 image was copied and
synced a second time. The board again exited BOOTSEL and rebooted normally. No
motor command was sent during this second flash.

After the later BOOTSEL troubleshooting, the same C12 serial appeared again.
With the real GUI closed, the user explicitly requested another C12 reflash.
The same verified image and hash were copied and synced a third time; the
RP2350 volume disappeared and the board rebooted normally. No motor command was
sent. The critical propulsion-power fail-safe restriction remains in force.

## C09 Reflash

Physical Pico 9 was put into BOOTSEL and identified as serial
`BA0F8CD9D7DB68F7`. It was reflashed on 2026-07-22 with:

```text
pico/firmware_c09.uf2
SHA-256 cec52021ebfd1911c70593115ff6e9c5ee1c3a4c471cb141d3cb1c0a0432546b
controller_id 8
HOST_INDICES 1, 65, 2, 66, 5, 69, 6, 70
```

Those indices are P02, P03, P06, and P07 on both layers. The copy and `sync`
completed successfully, and the RP2350 BOOTSEL device disappeared after the
write, confirming that the board accepted the image and rebooted. No motor
commands were sent; C09's functional test remains pending.

After the later BOOTSEL troubleshooting, C09 appeared again with the same
recorded serial `BA0F8CD9D7DB68F7`. With the real GUI closed, the user explicitly
requested another C09 reflash. The same verified image and hash were copied and
synced; the RP2350 volume disappeared and the board rebooted normally. No motor
command was sent. The critical propulsion-power fail-safe restriction remains
in force.

## C10 Reflash

Physical Pico 10 was put into BOOTSEL and identified as serial
`04AD9C1382F0E250`. It was reflashed on 2026-07-22 with:

```text
pico/firmware_c10.uf2
SHA-256 27c7aa8166c2637649966d9e6d8029c40839e2bfcf34a54cb3f4935852065563
controller_id 9
HOST_INDICES 9, 73, 10, 74, 13, 77, 14, 78
```

Those indices are P10, P11, P14, and P15 on both layers. The copy and `sync`
completed successfully, and the RP2350 BOOTSEL device disappeared after the
write, confirming that the board accepted the image and rebooted. No motor
commands were sent; C10's functional test remains pending.

After the later BOOTSEL troubleshooting, C10 appeared again with the same
recorded serial `04AD9C1382F0E250`. With the real GUI closed, the user explicitly
requested another C10 reflash. The same verified image and hash were copied and
synced; the RP2350 volume disappeared and the board rebooted normally. No motor
command was sent. The critical propulsion-power fail-safe restriction remains
in force.

## C11 Reflash

Physical Pico 11 was put into BOOTSEL and identified as serial
`19D7ABD191DD6213`. It was reflashed on 2026-07-22 with:

```text
pico/firmware_c11.uf2
SHA-256 cf564b2ced123f0927dcac42fd665be2b2166dbfb8b278e589d4b329895ccd38
controller_id 10
HOST_INDICES 17, 81, 18, 82, 21, 85, 22, 86
```

Those indices are P18, P19, P22, and P23 on both layers. The copy and `sync`
completed successfully, and the RP2350 BOOTSEL device disappeared after the
write, confirming that the board accepted the image and rebooted. No motor
commands were sent; C11's functional test remains pending.

After the later BOOTSEL troubleshooting, C11 appeared again with the same
recorded serial `19D7ABD191DD6213`. With the real GUI closed, the user explicitly
requested another C11 reflash. The same verified image and hash were copied and
synced; the RP2350 volume disappeared and the board rebooted normally. No motor
command was sent. The critical propulsion-power fail-safe restriction remains
in force.

## Controller Identity Notes

```text
Pico 2 BOOTSEL serial -> 5D0AF10E890A0474 -> firmware_c02.uf2
Pico 4 BOOTSEL serial -> 755F04F32D54ABCA -> firmware_c04.uf2
Pico 9 BOOTSEL serial -> BA0F8CD9D7DB68F7 -> firmware_c09.uf2
Pico 10 BOOTSEL serial -> 04AD9C1382F0E250 -> firmware_c10.uf2
Pico 11 BOOTSEL serial -> 19D7ABD191DD6213 -> firmware_c11.uf2
Pico 12 BOOTSEL serial -> 8BD9571726565DC8 -> firmware_c12.uf2
```

The Pico 4 serial was recorded during an accidental BOOTSEL entry. No file was
copied during that event.

## Other Hardware Findings

- A loose `GP16` / SPI MOSI wire feeding the P33-P64 side was corrected on
  2026-07-21; C05-C08 began working afterward.
- The earlier AIR 40 throttle-plug fault remains resolved: AIR 40 black goes to
  the XQ-45 black/ground harness position and AIR 40 yellow goes to the XQ-45
  white/PWM position.
- The user subsequently confirmed C13-C16 working. Together with the earlier
  C01-C08 result, only C09-C12 remain unresolved:

  ```text
  C09 -> P02, P03, P06, P07
  C10 -> P10, P11, P14, P15
  C11 -> P18, P19, P22, P23
  C12 -> P26, P27, P30, P31
  ```

  Their common infill-bus MOSI, clock, CE0, sync, and ground feeds should be
  checked before assuming multiple firmware failures.

- Serial `19D7ABD191DD6213`, which appeared earlier without a physical label,
  was subsequently confirmed as Pico 11 and flashed with C11 as listed above.

## Software Verification

The 8x8x2 control path was compared with the known-working legacy 8x8 wall:

- SPI0/CE0, mode 0, 1 MHz, byte-paced transfer, 10 us sync, Pico SPI pins,
  GP0-GP7 PWM pins, 50 Hz PWM, and 1000 us idle all match.
- All sixteen generated controller sources are identical after normalizing only
  `CONTROLLER_ID` and `HOST_INDICES`.
- Each C01-C16 UF2 application payload matches its compiled binary.
- Mapping validation and all 16 software tests passed.

The longer 266-byte frame, CRC validation, explicit arm flag, 250 ms valid-frame
watchdog, and harness-preserving controller mapping are intentional 8x8x2
differences.

## Saved GUI State

The saved GUI preset now assigns all 128 motors to `Group 3` in Constant mode at
`1200 us`. Do not rerun that full-wall preset during diagnosis; reduce it to
one known-working motor first.

## C01-C04 vs C09-C12 Code Audit

A read-only, code-only audit compared generated source, build configuration,
ELF/BIN/UF2 artifacts, host mapping/protocol logic, and tests. No hardware
output or flashing occurred during the audit.

Findings:

- After normalizing only `CONTROLLER_ID` and `HOST_INDICES`, all eight generated
  C sources have the same SHA-256
  `fb0d8bfe18abf669293d429565cc6997e713842a408237560348a6c247a4fcb5`.
- `CONTROLLER_ID` differs in source but is never referenced, so it has no
  runtime effect. Runtime ownership comes only from `HOST_INDICES`.
- GP0-GP7 motor order, 50 Hz PWM, 1000 us startup/idle, 2000 us maximum,
  SPI0 slave configuration and pins, 1 MHz rate, sync GP22, frame parser, CRC,
  arm flag, and 250 ms watchdog are identical.
- Normalized compiler flags and normalized linker commands are identical for
  all eight builds: Pico 2/RP2350 Arm Secure, Release, GCC, `-O3`.
- Every ELF has text/data/BSS sizes `15524/0/1172`; every BIN is 11,428 bytes;
  every UF2 is 23,552 bytes/46 blocks.
- Every UF2 application payload exactly matches its corresponding BIN; UF2
  metadata and wrapper blocks are identical apart from the application bytes.
- Paired BINs C01/C09, C02/C10, C03/C11, and C04/C12 differ in exactly eight
  compiled host-index instruction bytes plus the one or two ASCII digits in
  the embedded program name. No other loadable bytes differ.
- The host broadcasts one identical 266-byte frame to every controller. There
  is no runtime old-harness/new-infill branch. The build script's
  `--old-harness` and `--new-infill` options only choose which images to build.
- The authoritative mapping, generated CSV, generated firmware, and primary
  mapping/protocol docs agree. One stale example in
  `docs/LAYER_FIRST_WIRING_PLAN.md` incorrectly says C09 GP4-GP7 serve
  P10/P11; the correct C09 assignments are P06/P07. No executable code uses
  that stale example.

Verification passed:

```text
python3 scripts/generate_motor_mapping.py --check
python3 -m unittest discover -s tests -v     # 16 passed
QT_QPA_PLATFORM=offscreen python3 main.py --mock --smoke-test
```

Conclusion: no code difference explains why C10-C12 report no ESC signal while
C09 and the established banks work. Since every image autonomously emits idle
PWM before receiving SPI, continue treating C10-C12 as local Pico power,
GP0-GP7 wiring, connector orientation/offset, or ESC signal-ground faults.

## C12 Substitution Test

The user connected known-working Pico 4 to Pico 12's motor/ESC leads, and the
motors spun. This proves the C12 downstream motor leads, ESCs, and motors can
operate. The fault is therefore on the C12 controller side: the Pico board,
USB supply, header/solder joints, board-to-lead connector, local signal ground,
or firmware execution. It is not explained by C12's intended host mapping.

With propulsion batteries disconnected, compare C12 GP0-to-GND against
working C04 using a scope or logic analyzer. A running image must produce a
50 Hz, approximately 1000 us idle pulse before any host command. Also verify
C12 3.3 V and continuity from Pico GND and GP0-GP7 through its local connector.
If the pulse is absent directly on the Pico while supply and ground are valid,
the failure has followed the C12 board.

The user subsequently confirmed C12 working. C09-C11 remain nonfunctional;
their most recently reported detailed symptom was ESC no-signal beeping. This
proves the C12 image family, mapping pattern, and flash procedure can operate
and leaves C09-C11 local controller paths unresolved. C09 had worked after the
earlier rewiring but stopped again after later isolation/reflash work, making a
disturbed USB power, signal ground, or local connector particularly likely.
Check for any supply/hub/ground/connector element shared by C09-C11 but not C12.

## Full-Wall No-Output Result

After C09-C12 were reflashed, the user armed and started the saved test. The
GUI displayed `RUNNING / REAL`, but no motors spun, including the previously
confirmed C01-C08 and C13-C16 banks. Read-only host checks found:

- `main.py` remained running;
- `/dev/spidev0.0` and the GPIO devices exist;
- the Python GUI process held `/dev/spidev0.0` and `/dev/gpiochip0` (the
  configured `/dev/gpiochip4` symlink target);
- the saved group commanded all 128 motors at `1200 us`, not idle.

Sixteen simultaneous firmware failures are therefore unlikely. The leading
fault domain is the shared physical host bus or signal ground. With power
removed, inspect the common entry connection: Pi GPIO10/MOSI to Pico GP16, Pi
GPIO11/SCLK to GP18, Pi GPIO8/CE0 to GP17, Pi GPIO22/sync to GP22, and signal
ground. Do not rerun the full-wall group while isolating this fault.

Afterward, the user reported that all ESCs gave their normal connected chime
and stopped the no-signal beeping. This confirms that the Picos are powered and
their local PWM-to-ESC paths are producing valid idle pulses. It does not by
itself confirm host communication because each flashed Pico generates its own
1000 us idle PWM even without valid SPI/sync frames. The remaining diagnostic
is whether one known-good output can be commanded above idle through the host
bus.

The user then noted that all Picos remained connected and the propulsion
batteries were connected during the C09-C12 BOOTSEL flashes. This can explain
the no-signal beeping and delayed readiness: each target Pico temporarily stops
PWM while in BOOTSEL/reboot, then resumes 1000 us idle after firmware starts,
allowing its ESCs to re-arm. It does not cause other connected Picos to receive
the target UF2; flashing was scoped to each selected USB BOOTSEL volume. No
unexpected motor start or overheating was reported, and all ESCs subsequently
reported valid signal, so damage is not indicated. Nevertheless, do not flash
with propulsion batteries connected again because a transient or wrong image
could command a motor unexpectedly.

A subsequent clean ESC power cycle with Picos already generating idle PWM did
not restore motor operation; one previously working motor still did nothing.
Read-only `pinctrl` checks showed the expected Pi configuration:

```text
GPIO8  -> output, idle high (CE0)
GPIO10 -> SPI0_MOSI
GPIO11 -> SPI0_SCLK
GPIO22 -> output, idle low (sync)
```

Together with the GUI process owning SPI0/CE0 and GPIO22, this narrows the
fault to the physical shared bus or a connected branch loading it. Because the
loss of all output followed work on C09-C12, isolate their signal-bus taps with
all USB and battery power removed, then test one known C01 output. If C01
returns, reconnect C09-C12 one at a time with power removed between changes to
identify the loading branch. If C01 remains dead, check continuity from the Pi
to C01, especially sync and MOSI, before the downstream branches.

## Critical USB-Power-Loss Incident

During that isolation attempt, C09-C12 USB power was unplugged while propulsion
batteries remained connected. Motors then behaved erratically and randomly
went to full speed. The user was instructed to disconnect propulsion batteries
immediately using the physical cutoff from a safe distance and not approach the
motors or unplug anything else while energized.

This is a critical fail-unsafe condition. USB is the Pico power source; removing
it while ESC power remains present removes or floats the PWM outputs, and these
ESCs did not reliably fail to zero thrust. Do not rely on the GUI, Pico
firmware, or loss of PWM as an emergency stop. Do not perform another powered
test until controller-power-loss behavior is made fail-safe.

The user later reported difficulty getting the Picos into BOOTSEL. The real-mode
GUI was still running as `python3 main.py`, leaving the Pi SPI/sync bus driven.
This and the earlier observation that BOOTSEL worked only with the wall harness
unplugged strongly indicate that Pi GPIO signals can back-power an otherwise
USB-unplugged Pico enough to prevent a clean reset/power cycle. The firmware
does not disable RP2350 BOOTSEL.

Removing the target from the wall harness did not by itself restore BOOTSEL.
With the isolated Pico reportedly connected, both `lsblk` and a host-level
`lsusb` check showed no RP2350 or other Pico USB device. This rules out only an
auto-mount failure: the board is not entering/enumerating in ROM USB mode. The
next checks are the exact power-cycle sequence (hold BOOTSEL before and during
USB insertion), a known data-capable cable and Pi data port, then the physical
BOOTSEL/RUN reset controls. A powered Pico does not reset merely because the
BOOTSEL button is pressed.

Required power order after a safety review:

```text
Power-up:   Pico/control USB first -> verify idle PWM -> propulsion battery last
Power-down: propulsion battery first -> verify motors stopped -> Pico USB last
```

A physical propulsion-power cutoff must remain accessible outside the motor
hazard area. Before operation resumes, inspect for damage/overheating and review
ESC signal fail-safe behavior, signal grounding, unpowered-Pico backfeeding,
and a hardware interlock that removes propulsion power independently of
software.

For a safe BOOTSEL entry, keep propulsion batteries disconnected, close the GUI
completely, power down the Pi/control bus before unplugging the target harness,
isolate the target Pico from the wall harness, then start the Pi and connect
only that Pico using a known data-capable USB cable while holding BOOTSEL. If a
carrier provides a proper RUN/reset control, holding BOOTSEL during that reset
also avoids relying on USB removal for reset.

## Post-Rewire Isolation Result

The user rewired C09-C12. C09 then worked normally together with the previously
working controllers, proving that the common Pi SPI/sync path is operational.
C10, C11, and C12 did not run, and their ESCs gave the no-signal beep.

Each verified Pico image generates 50 Hz, 1000 us idle PWM on GP0-GP7 without
requiring host SPI frames. Therefore, simultaneous no-signal behavior across a
controller's ESCs now points to its local Pico power, PWM wiring, or ESC signal
ground—not the shared host bus. Because C10-C12 were just rewired and C09 works,
inspect for reversed/offset connectors and missing common ground first. Do not
reflash from this evidence.

## Next Safe Step

Keep propulsion batteries disconnected for diagnosis and never remove Pico USB
power while ESC batteries are connected. With batteries removed but Pico USB
power present, compare C10-C12 GP0-to-ground against working C09 using a scope
or logic analyzer; expect a 50 Hz, approximately 1000 us pulse. If present at
the Pico but absent at the ESC connector, repair the PWM/ground harness. If
absent directly at GP0, check Pico USB/3.3 V and firmware execution before any
reflash. Establish the independent physical cutoff before broader live tests.

For future flashing, disconnect propulsion batteries first, leave the GUI
stopped/disarmed, flash and verify the target Pico, and confirm that all Picos
are running at idle before reconnecting battery power with the wall physically
safe.
