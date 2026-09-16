# Coaxial 8x8x2 Windwall Handoff - 2026-09-08

## Real five-wire active attempt

At the operator's request, ran the actual five-wire path using the isolated
German bench. Sent `ARM SPI`, then 50 complete active 36-byte frames at 1 MHz
with 50 GPIO22 sync pulses over one second, followed by `STOP`. C01 reported
bytes unchanged at 0, syncs 198 -> 248, valid 0, invalid 198 -> 248, and one
no-frame watchdog timeout. Final status was PWM 1000 us and disarmed. No
movement occurred because sync reaches C01 but MOSI/SCLK/CE0 still produce no
SPI bytes. Raw summary: `logs/german_one_motor_20260909_spi_active.json`.

## Confirmed isolated motor movement over USB

The operator requested movement without another SPI check. The direct USB
bench command `PULSE USB` returned `OK PULSE USB`, held C01 GP0 at 1200 us for
the one-second lease, and then `STOP` returned `OK STOP`. The operator observed
the isolated motor spin. A final status read reports `pwm_us=1000`, `armed=0`,
`direct=0`; the controller is stopped. This proves the C01 GP0 PWM path, the
attached ESC/motor, and the new bench firmware work. It also confirms the
remaining failure is specifically the Pi-to-C01 SPI receive path, since SPI
tests still show zero received bytes. Raw result:
`logs/german_one_motor_20260909_usb_spin.json`.

## Repeated idle SPI isolation

At the operator's request, the isolated idle test was repeated with the
German-reference C01 bench firmware. The host sent 20 complete 36-byte frames
and 20 GPIO22 sync pulses. C01 counters changed from:

```text
bytes=0 syncs=21 valid=0 invalid=21 last_length=0
```

to:

```text
bytes=0 syncs=41 valid=0 invalid=41 last_length=0
```

The repeat is stable: sync reaches C01, but MOSI/SCLK/CE0 produces no received
SPI bytes. No above-idle output was sent. Raw summary:
`logs/german_one_motor_20260909_spi_idle_repeat.json`.

## Clean-room bench result: sync reaches C01, SPI does not

The corrected bench UF2 (USB response timeout fixed) was flashed to the
serial-matched C01 `F68B8438147951D7`. Read-only USB status identifies
`german-one-motor-v1`, reports PWM idle 1000 us, and returns clean counters.
The USB pulse command was accepted and its one-second lease expired. However,
the existing Pi GPIO23 measurement tap saw zero edges during both the bench
idle period and a separate passive three-second capture; recheck the jumper or
GP0 output before using PWM capture as evidence.

A direct host-only idle SPI test then sent 20 complete 36-byte frames at 1 MHz
with 20 GPIO22 rising sync pulses. C01 status changed from:

```text
bytes=0 syncs=0 valid=0 invalid=0 last_length=0
```

to:

```text
bytes=0 syncs=20 valid=0 invalid=20 last_length=0
```

The host sent 720 SPI bytes and 20 sync pulses. Therefore GPIO22 sync is
reaching C01, but C01 sees no MOSI/SCLK/CE0 SPI bytes at all. This clean-room
result isolates the current fault to the Pi-to-C01 SPI data/clock/chip-select
path or pin termination, independent of the GUI and the 128-motor protocol.
No above-idle SPI frame, propulsion power, mass reflash, or mapping change was
used. Raw summary: `logs/german_one_motor_20260909_spi_idle.json`.

## Clean-room German-reference C01 one-motor bench

To reset the diagnosis, created `bench/german_one_motor/` from the pinned
original German Git revision `0280f876e587c41cd54a499913e4e208465c6d3e` in the
local `active_wind_wall_8X8_history.bundle`. `SOURCE.json` hashes the copied
reference files. The new bench is separate from the GUI and the 128-motor
application. It preserves the German 36-byte raw SPI frame, one-byte-per-motor
encoding, SPI0/CE0 byte-paced writes, GPIO22 rising-edge latch, runtime clock
calibration, and 50 Hz PWM. It deliberately enables only C01 GP0; GP1-GP8 and
MISO are inputs.

Added USB CDC `STATUS`, `STOP`, `PULSE USB`, and `ARM SPI` commands. USB pulse
mode commands a single 1200 us GP0 pulse for one second. SPI mode requires a
valid 36-byte frame with only byte 0 = 51 (the original encoding of 1200 us)
and rejects short, overlong, or other-channel frames. It includes receive
byte/sync/valid/invalid/overflow counters, input levels, a 200 ms no-frame
watchdog, and a one-shot four-second lease. The new host `bench.py` requires
the exact C01 serial `F68B8438147951D7`, owns GPIO22 and GPIO23 exclusively,
captures GP0, validates 50 Hz widths, checks exact SPI receive counts, and
sends STOP on cleanup. Its timestamps were corrected to use the same realtime
clock as libgpiod edge events before any hardware use.

Build artifacts: `build/german_one_motor.bin` (32,476 bytes) and
`german_one_motor.uf2` (127 RP2350 blocks, family `0xE48BFF59`; payload
verified against BIN). Software checks passed:

```text
cmake --build build -j4                         PASS
cc -Wall -Wextra -Werror test_receiver.c        PASS
receiver exhaustive test                        PASS
python3 -m py_compile bench.py make_uf2.py       PASS
```

The old GUI process was closed before this preparation. No new UF2 has been
flashed and no new motor command has been sent. The next action is to put
physical C01 serial `F68B8438147951D7` into BOOTSEL, verify the mount, copy the
bench UF2, wait for reboot, then run `bench.py status` with propulsion power
disconnected. Only after USB identity and clean idle pass should the bounded
USB and SPI tests be run.

## C01 Reflash and Post-Flash Idle Verification

The operator requested a C01 reflash, put it in BOOTSEL, and then explicitly
confirmed the motor battery was physically disconnected. Immediately before
writing, `/dev/sda1` at `/media/jwatson/RP2350` had recorded C01 serial
`F68B8438147951D7`; `INFO_UF2.TXT` identified RP2350 and no Python GUI process
was running. Firmware verification found:

```text
Image: pico/firmware_c01.uf2
SHA-256: bc75d1c1746c08ac0d424221fefe734af88f3008d888f30923839eaea899700c
CONTROLLER_ID: 0
HOST_INDICES: 0, 64, 3, 67, 4, 68, 7, 71
Outputs: F01, B01, F04, B04, F05, B05, F08, B08
```

All 45 UF2 application blocks match `pico/build_c01/firmware_c01.bin` (the
separate UF2 metadata block is excluded from the application comparison).
Generated mapping validation passed. The verified UF2 was copied successfully
and `sync` completed. Subsequent USB/block enumeration showed the BOOTSEL
device gone, consistent with its expected reboot.

An eight-second input-only capture on the confirmed GP0 -> Pi GPIO23 jumper
then measured 400 pulses at 50.0 Hz, per-report median 996.55-1003.10 us, and
zero unpaired/out-of-order edges. This confirms firmware execution and idle
PWM after flashing. Raw output: `logs/c01_20260908_postflash_idle.txt`.
Command response has not been retested. No SPI or above-idle motor command
was sent during this reflash/check. GUI remains closed; motor battery is
disconnected as last confirmed, with C01 control USB powered.

## Explicitly Authorized One-Second Single-Motor Test

The operator declined a propulsion-disconnected test, explicitly requested
motor movement, and stated the isolated setup was safe. The bounded test
script `/tmp/c01_one_second_test.py` verified the identified GUI process and
window, sent WM_DELETE_WINDOW for normal idle/shutdown, and waited for PID
19495 to exit. It then started the input-only GPIO23 capture and opened the
canonical hardware transport. It sent 1.5 seconds of disarmed idle, exactly
one second of armed F01/C01 GP0 = 1200 us with all other channels at 1000 us,
then immediate disarmed idle, another 1.5 seconds of idle, and final shutdown.
The script completed successfully with SPI/sync released; no retry occurred.

The eight-second input capture saw 400 samples at about 50 Hz. Per-report
median widths remained 997.16-999.21 us; maximum measured width was 1006.95 us.
No sustained 1200 us PWM response was observed. Seven unpaired/out-of-order
edges and some short pulses (minimum 260.37 us) occurred, so this was not a
wholly clean capture; pickup/glitches and timestamp/capture behavior remain
possible. The final three reports after transport release had zero malformed
edges and idle-width medians. This reproduces the response failure without
the GUI command loop, but successful host calls do not prove electrically
valid MOSI/SCLK/CE0/sync reception or identify a faulty component. Physical
motor movement was not directly observed by Codex.

Final state: GUI closed, last commands disarmed at 1000 us, control USB not
switched. Treat propulsion as connected until the user confirms otherwise.
No throttle increase, firmware edit/reflash, or physical wiring change was
performed. Raw transcript: `logs/c01_single_motor_20260908_one_second.txt`.
The temporary script is a one-use diagnostic, not an operator launcher.

## Single C01 and Direct Pi USB Test Still Fails

Follow-up: the operator confirms normal connected-style ESC tones followed
by silence, C01 GP0 as the ESC signal, and the GP0 -> Pi GPIO23 measurement
tap. An eight-second input-only capture measured 400 complete pulses, about
50 Hz (49.99 Hz in one report), median 996.08-997.64 us per report, and zero
unpaired/out-of-order edges. Individual widths ranged 982.12-1003.64 us;
kernel timestamps are diagnostic rather than calibrated scope measurements.
Output remains idle during this capture, but GUI run state was not observed,
so do not infer a fresh above-idle command failure. Current propulsion power
state remains unconfirmed. Before commanding a bounded above-idle comparison,
confirm the motor battery is disconnected while Pi/Pico control USB remains
powered. Raw output is `logs/c01_single_motor_20260908_passive.txt`. No SPI
write, GPIO output request, GUI control action, or firmware change occurred.

After the corrected GUI recovery, the operator reports removing the entire
wall from the Pi and testing one motor/ESC on physical C01. All five command
links remain connected, and C01 USB goes directly to the Pi without a hub.
The same no-spin symptom persists. This reproduces the failure without the
other controllers or hubs but does not establish which component is faulty.
The particular GP output, ESC beep behavior, current propulsion power state,
and presence of the earlier GPIO23 measurement jumper remain unconfirmed.

Read-only host inspection found `python3 main.py` PID 19495 in the canonical
project, owning `/dev/spidev0.0`, `/dev/gpiochip15`, and a GPIO line handle.
Pi MOSI/SCLK modes, CE0 output-high, and sync GPIO22 output-low were consistent
with the application. SPI0.0 counters showed 7,156,464 transmitted bytes since
boot, zero errors, and zero timeouts; these are cumulative, not a trace of
this isolated attempt or proof of electrical C01 reception. Recovered source
hashes still match the installed manifest. The saved `normal` group assigns
all 128 motors at Constant 1400 us; this is saved state, not a live GUI reading.
No hardware output, capture, firmware change, or preset edit was performed.

## Corrected Recovery of the September 3 GUI

The operator clarified that the July 15 snapshot was not the version used on
September 3. The July rollback is superseded by a reconstruction of the source
immediately before the September 4 redesign. The successful edit records in
the September 4 `08-54-14` session provided 41 file patches covering eight
files: GUI, transport, signals, config, three matching test modules, and README.
Reversing them against the saved September-4 files recovered the prior source;
forward replay reproduced all eight baseline files byte for byte. There was
no independently dated September-3 snapshot, so provenance is the recorded
pre-September-4 source rather than a claim about an observed September-3 run.

Installed the recovered files into the canonical project. This restores the
Rival Lab branding and graphite/olive theme, prominent row-major labels,
Upstream/Downstream/Both dropdown, full bottom plot, combined Start/Stop,
real-only application runtime, and stable `pinctrl-rp1` discovery. September-4
direct cell zones, rubber-band selection, Pico overlay, and asynchronous
dispatcher are absent. Current source was preserved first under
`rollback_backup_20260908_before_sep3_recovery/`; the original September-4
backup remains intact.

`recovery_20260908_sep3/` contains the recorded patches, reconstruction script,
original source baselines, recovered files, installed SHA-256 manifest, and
`recovered-gui.png`. Validation passed in staging and after installation:
28 hardware-free tests (26 restored tests plus two GPIO discovery regressions),
mapping validation, Python compilation, and an inspected offscreen GUI render.
Session saving was redirected to a temporary file during rendering. No saved
preset, controller mapping, firmware, Desktop launcher, or other wind-wall
project was changed. No hardware output or real GUI launch occurred. The
Desktop icon loads the recovered version on its next launch; an already-open
window still uses its previously loaded source. The separate C01 response
fault remains unresolved.

## Desktop Startup Repair After GUI Rollback

The operator reported that the Desktop icon did not open the GUI. The icon
and executable launcher point correctly to this project. Repeated startup
tracebacks in `~/.xsession-errors` end at `gpiod.Chip('/dev/gpiochip4')` with
`FileNotFoundError`: the GUI rollback also restored an obsolete GPIO path.

Restored the previously used `pinctrl-rp1` label discovery in `RealSync` and
replaced `GPIO_CHIP_PATH` with `GPIO_CHIP_LABEL` in config. Read-only discovery
against the actual host resolves `/dev/gpiochip15`. This retains the older
GUI and synchronous transport. No firmware, mapping, Desktop launcher, or
preset was changed.

Validation passed: two targeted regression tests covering gpiod 1.x/2.x and
missing labels, Python compilation, generated mapping check, and a 500 ms
offscreen GUI startup using a no-output transport with session saving
disabled. The existing broader September GUI/worker tests remain incompatible
with the prior rollback and were not claimed as passing. No SPI writes, GPIO
output requests, or physical GUI launch occurred during this repair. Actual
Desktop launch remains to be confirmed by the operator. This repair addresses
the startup crash; it does not resolve the separate C01 command-response fault.

## Current Report

The operator reports that the GUI looks normal but no motors spin. This is
the current symptom; the earlier startup sag and 121-of-128 result are
historical context. The preceding implementation handoff remains
`SESSION_HANDOFF_2026-09-04.md`.

## Read-Only Findings

- The live `python3 main.py` process was PID 3463, started at 14:52:32 local,
  with its working directory in this canonical project.
- It held `/dev/spidev0.0`, `/dev/gpiochip15`, and a GPIO line handle. The
  visible X11 window was titled `Windwall`.
- `pinctrl get 8-11,22` showed GPIO10/11 in SPI0 MOSI/SCLK mode, GPIO9 in
  SPI0 MISO mode, GPIO8 as an output high, and GPIO22 as an output low.
  These are static observations, not evidence of live transfers or pulses.
- The Desktop launcher points to this project's `scripts/launch_gui.sh`.
- The session error log showed no Python traceback for this launch. A Qt
  Wayland-plugin warning was present, but the X11 window opened successfully.
- The saved `normal` group initially assigned all 128 motors to Constant
  1200 us. During diagnosis the saved preset changed to 1500 us without a
  Codex edit. An offline evaluation produced 128 values of 1500 us and a
  valid 266-byte armed protocol frame that decoded back to those values.
  Saved state does not establish the live GUI's running/armed state.
- Generated mapping validation and all 36 hardware-free tests passed using
  injected no-output transports. No application, firmware, mapping, or
  preset changes were made by Codex.
- The Git repository still has no commits and the project files are
  untracked; there is no committed baseline for a source diff.

## Pending Fault Isolation

The operator confirms that connecting propulsion batteries produces the
normal motor/ESC startup beeps followed by silence, and pressing Start
displays `SYSTEM RUNNING`. This is consistent with recognized idle PWM
reaching the ESCs, but does not establish that the Picos receive Pi commands.
The current GUI has no real/mock status label; the earlier request to look
for `RUNNING / REAL` used obsolete terminology. Source inspection confirms
the displayed run label is `SYSTEM RUNNING` and runtime transport is real.

The operator initially reported `Average PWM` of 1000 us, then explicitly
clarified that it was 1200 us while the experiment was running. Do not
diagnose this as a GUI stuck at idle: 1000 us is the expected stopped value.
The saved all-128 Constant preset is now back at 1200 us (mtime 15:01:17),
again without any Codex preset edit.

A read-only kernel SPI0.0 statistics check reported 1,558,760 messages,
transfers, transmitted bytes, received bytes, and one-byte transfer histogram
entries, with zero errors and zero timeouts. The count is exactly 5,860
266-byte frames. A subsequent read was unchanged. These counters cover the
device since boot, not just this GUI process or the last failed run; they
do not establish payload values, sync pairing, or electrical reception by
Picos. The X11 window capture returned a black image, so no visual GUI counter
reading was obtained. The GUI process remained PID 3463.

The next useful observation is the existing right-hand `Frames sent`
counter's progression during the failed run. The counter increments
only after a full SPI write and sync pulse return successfully; the PWM
readout is the host command, not measured ESC feedback. A rising counter
with above-idle PWM would narrow investigation toward the shared command
harness/Pico reception, without proving an electrical waveform reaches it.
Firmware inspection confirms startup idle PWM is generated autonomously;
invalid frames or a 250 ms valid-frame timeout also retain/restore idle.
Thus quiet ESCs do not establish a healthy SPI/sync path.

The operator subsequently confirmed propulsion batteries were disconnected
with Pico USB power left connected. A bounded control-only diagnostic was
then completed as described below. No root cause is established.
Host device ownership and passing tests do not prove Pico frame reception.
The August transport trace is historical evidence, not a trace of today's
failure. There is no configured controller/PWM feedback telemetry.

## Confirmed Battery-Disconnected Control-Only Capture

After the operator confirmed the disconnected propulsion state, a first
90-second ioctl trace attached to the existing GUI but captured no calls
because no run occurred during that interval. It detached normally; this
empty trace is not evidence of a transport failure.

A Wayland desktop capture then confirmed the current GUI was disarmed with
128 motors in the `normal` Constant 1200 us group, a 100-second configured
duration, 5,396 frames sent, and 1000 us idle. Codex operated the existing
Emergency Stop, Arm, and Start controls for a short control-only run, then
Emergency Stop again. The configured duration and preset were not changed.
During the capture the GUI showed `SYSTEM RUNNING`, 1200 us average, F01/B01
at 1200 us, and 5,498 frames at approximately 3.3 seconds. The final image
showed `ARM SYSTEM`, disabled Start, 1000 us average and F01/B01 idle, and
5,510 frames at approximately 3.5 seconds.

The complete trace was parsed for transfer success and frame/sync ordering:

```text
Successful SPI one-byte transfers          30,324
Transfers before each sync rising edge        266 (all 114 frames)
Complete frame-transfer sequences             114
Successful GPIO22 line-value calls            228
Sync sequence                             high/low alternating, 114 pairs
Trailing unsynchronized SPI transfers           0
Failed SPI/GPIO calls                            0
GUI frame-counter increase                    114 (5,396 -> 5,510)
```

Four frames were sent by the main GUI thread (initial disarm, arm, initial
running frame, final emergency stop), and 110 by its runtime worker. Kernel
SPI statistics increased by exactly 30,324 to 1,589,084 transmitted bytes,
with zero recorded errors/timeouts. Strace changes timing; do not use this
capture to infer untraced frame rate.

The installed strace prints SPI buffer addresses rather than payload bytes.
Thus the 1200 us values are verified GUI command readouts, supported by the
earlier offline encoder checks; the trace verifies successful transfer counts
and sync call order, not payload bytes, electrical pulse shape, or Pico
reception. There is still no controller acknowledgment/PWM telemetry.

Artifacts are in `/tmp/windwall-trace-iHbeKF/`:
`control-only-ioctl.log`, `running-controls.png`, `stopped-controls.png`,
and the bounded `control_only_capture.py` diagnostic. The latter is not an
operator launcher and must not be reused with propulsion connected.

The existing GUI remains open and verified disarmed at 1000 us. Propulsion
remains disconnected as last confirmed by the operator; Pico USB was not
switched. No firmware, mapping, application code, or preset was changed.
The next fault-isolation step is physical inspection/continuity of the shared
MOSI/SCLK/CE0/sync/ground entry and branches to a previously working Pico,
with all relevant Pi/Pico/propulsion power removed before touching wiring.
Successful host calls do not prove the electrical command reaches a Pico;
do not mass-reflash based on this capture.

## Replacement Harness Did Not Resolve the Failure

The operator subsequently replaced MOSI, SCLK, CE0, sync, and ground between
the Pi and Picos and reports no change. This reduces the likelihood of a
fault in an individual replaced conductor, but does not verify pin placement,
signal quality, branch loading, Pi output levels, or Pico reception. The
operator was asked whether all 16 Picos remained on the bus or one was tested
with the other signal branches isolated; that answer is pending. No further
command run was performed in this follow-up, and current power state after
the operator's wiring work is not inferred from the earlier confirmation.

To obtain a measurement without a scope or firmware change,
`scripts/passive_pwm_capture.py` was added. It requests only GPIO23 as a
both-edge input on the `pinctrl-rp1` chip, rejects an already-used line,
reports one-second pulse-width/frequency summaries from kernel timestamps,
and releases the line on exit. It never opens SPI or requests an output.
The installed libgpiod is 1.6.3. Read-only checks found GPIO23 unused and
not configured as an output; the installed GPIO Zero board metadata confirms
GPIO23 is Pi header physical pin 16 and physical pin 14 is ground.

No input capture has been run yet. The pending physical preparation is:

1. Keep propulsion batteries disconnected; stop/close the GUI and turn off
   Pi/Pico power before adding measurement wiring.
2. Connect physical C01's GP0/CH1 PWM signal to Pi GPIO23 (physical pin 16).
   This is a Pico 3.3 V signal connection, never an ESC BEC/power connection.
3. Connect C01 GND to Pi GND (physical pin 14); keep the existing command
   conductors in place.
4. Restore Pi and Pico control power only, keeping propulsion disconnected,
   and report when the jumper is connected before a command capture.

The capture command, once wiring/control-only state is confirmed, is:

```text
python3 scripts/passive_pwm_capture.py --seconds 15
```

Capture idle, a bounded 1200 us control-only command, and final disarmed idle.
Check the kernel timestamp spread and unpaired-edge counts before interpreting
results; this input diagnostic is not a calibrated oscilloscope. A measured
1000 -> 1200 -> 1000 us change would demonstrate that this Pico output follows
commands, whereas sustained idle would keep investigation upstream of its PWM
output. Do not infer all other channels from a single C01 measurement.

Hardware-free validation passed: compilation and the script's `--self-test`
for 50 Hz, 1000/1200 us, orphan falls, missing falls, and out-of-order events.
The application, firmware, mapping, and saved preset remain unchanged.

## C01 Isolation and Power-Down Preparation

The operator isolated physical C01 (Pico 0) from the shared signal harness:
the Pi's five direct control conductors now go only to C01, mapped as Pi
MOSI -> GP16, CE0 -> GP17, SCLK -> GP18, sync -> GP22, and Pi ground -> a
real Pico GND pin. Pico GP19/MISO and Pico RUN are left unconnected. The
shared conductors to C02-C16 were removed. The operator confirmed the ground
wire is on Pico GND rather than GP19. C01's motor-0/F01 ESC signal remains on
GP0; no measurement tap to Pi GPIO23 was added because accessing Pi physical
pin 16 would require opening the Pi. No PWM capture was run.

The GUI's last controlled state was Emergency Stop/disarmed at 1000 us, with
the earlier control-only run completed while propulsion batteries were
disconnected. Before powering down, use this order:

```text
1. Keep propulsion batteries disconnected.
2. Confirm the GUI remains disarmed/stopped, then close the GUI.
3. Remove Pi/Pico USB/control power.
4. Leave C01 isolated and do not alter the mapping.
```

Do not restore propulsion power while the shared bus is partially disconnected.
After the Pi is accessible and the temporary GP0 -> Pi GPIO23 measurement
connection is intentionally installed, restore control power only for the
passive capture. Application, firmware, mapping, and saved preset are
unchanged. No further motor command was sent in this follow-up.

## Passive C01 GP0 Capture Result

After the operator reported the GPIO23 jumper and isolated control setup were
powered, read-only checks found GPIO23 unused and configured as an input. The
input-only listener was run for 30 seconds against the `pinctrl-rp1` GPIO
chip. It saw **zero edges and zero complete PWM samples for the full 30.04
seconds**, including idle; no 1000 us or 1200 us pulse was observed. The
listener opened and released GPIO23 normally and sent no SPI or GPIO output
commands. No GUI control action was performed during the capture.

This does not prove C01 GP0 is electrically low: the jumper endpoint, Pico
GP0 header location, common ground, and C01 USB/control power remain
unverified. It does show that the expected C01 50 Hz idle PWM is absent at
the Pi input. Candidate fault domains are C01 power/firmware execution, a
wrong GP0 tap, or the temporary measurement jumper/ground. Power down before
checking those items. Do not reconnect propulsion or mass-reflash.

## Corrected Tap Capture Result

The operator corrected the measurement connection and requested a second
30-second input-only capture. GPIO23 then saw substantial malformed activity,
but it was not servo PWM: the final one-second report contained 1,042 samples
with a 6.00 us median pulse, approximately 14.15 kHz inferred frequency,
and 17,206 unpaired/out-of-order edges. Earlier intervals similarly showed
roughly 4-7 us pulses and approximately 10-15 kHz inferred rates. A valid
idle/command PWM should be approximately 1000/1200 us at 50 Hz.

This pattern is consistent with SPI/control-line pickup or the temporary tap
being on the wrong Pico/Pi endpoint; it is not evidence that C01 GP0 is
producing a valid ESC waveform. No propulsion power or motor command was
used. Power down before checking that the tap is physically Pico C01 GP0
(header pin 1) to Pi GPIO23 (physical pin 16), with a short common-ground
return, and that it is not touching Pi MOSI/SCLK/CE0/sync wiring. Do not
reconnect propulsion or mass-reflash.

The operator then confirmed the GUI is Emergency Stopped. Propulsion remains
disconnected. Leave C01 isolated and disarmed while checking direct CE0, sync,
and ground connections with power removed.

## Clean C01 Idle PWM Confirmation

A final 15-second GPIO23 input-only capture was run with the GUI closed after
the wiring correction. It saw clean C01 GP0 PWM for the entire capture:

```text
Pulse width: approximately 995.9-1001.0 us per report
Frequency:   50.0 Hz
Samples:     about 50 per second
Malformed:   0 edges
```

This proves C01 has control power, firmware is executing, GP0/header pin 1 is
the tapped output, and Pi GPIO23/physical pin 16 plus common ground are
correct. No above-idle command was sent; propulsion remained disconnected.
The next bounded test is a real GUI command at 1200 us while observing GP0.

## C01 Above-Idle Test Result

After the user manually confirmed the real GUI was running, an 8.01-second
input-only GPIO23 capture was taken. The GUI screenshot during the capture
showed `SYSTEM RUNNING`, 128/128 assigned motors, `Frames sent` 2329, and
F01/B01 displayed at 1250 us. C01 GP0 nevertheless measured only 992.9-996.8
us per report at 50 Hz, with zero malformed edges. Thus C01's actual PWM
remained idle while the host GUI displayed an above-idle command. This is the
first direct measurement separating host command generation from Pico output.

The result isolates the remaining fault to the direct Pi-to-C01 command path
or C01 frame latching, particularly Pi CE0 -> C01 GP17, Pi sync GPIO22 ->
C01 GP22, their ground reference, or C01 SPI reception. It does not justify
a firmware reflash: C01 produces correct idle PWM and the host-side frames
were previously verified. The operator was instructed to Emergency Stop with
propulsion disconnected. Keep the setup disarmed and do not reconnect
propulsion while only C01 remains on the bus.

The GUI was then closed and the input-only listener was run again for 15.02
seconds with C01 control power left on. It saw zero edges and zero PWM
samples throughout. This clean idle result confirms the earlier 4-7 us
activity was SPI/control-line pickup while the GUI was open; it was not C01
PWM. At this point no valid GP0 waveform is observable at Pi GPIO23 even
without host SPI traffic. Power down before checking C01 USB/control power,
the GP0 header pin, the GPIO23 endpoint, and the ground jumper. Do not
reconnect propulsion or mass-reflash.
