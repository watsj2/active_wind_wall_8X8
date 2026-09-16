## September 16 GitHub archive update

Prepared the canonical 8x8x2 source, GUI, controller images, mapping, bench
sources, documentation, and diagnostic logs for the existing GitHub archive
branch `complete-windwall-archive-2026-07-15`. Hardware-free verification:
51 unit tests passed and generated motor mapping check passed.
September 15 remains the latest hardware checkpoint: C01 produced approximately
1000 us idle PWM but did not respond to the bounded 1200 us command. The SCLK
oscilloscope observation remains pending. No hardware command or flash was
performed during this archive update. Machine-local presets, build products,
and recovery copies are excluded from this published current snapshot.

## September 15 oscilloscope clock check underway

Operator connected FNIRSI 2C53P CH1 to Pi SCLK GPIO11/physical pin 23 with
instructed ground at physical pin 25. First idle-stream attempt aborted because
GUI had reopened. Subsequently terminated canonical GUI and started a bounded
30-second stream of disarmed 1000 us frames for scope inspection. No above-idle
command in this check. Await operator waveform observation before interpreting
Pi clock or C01 reception.

## September 15 measured C01 command-response failure

Operator observed no motion in the prior eight-motor pulse. Confirmed C01 GP0
to Pi GPIO23 jumper remains attached. Input-only baseline measured 150 pulses,
50 Hz, approximately 996-997 us median, no malformed edges. Under continuing
explicit real-test authorization, sent only F01/C01 GP0 1200 us for one second
(35 active frames), then disarmed idle. Concurrent seven-second capture measured
approximately 998 us throughout, 50 Hz, no malformed edges, maximum 1005.22 us:
no 1200 us response. GUI remained closed. This confirms C01 idle PWM but absent
command response; it does not distinguish physical bus reception from firmware
frame rejection/latching. Propulsion remains treated as connected. No firmware,
preset or mapping changes. Log: `logs/20260915_c01_pulse_capture.txt`.

## 2026-09-15: cold-start no-motion diagnosis

Operator reports all motors worked the previous day; batteries were removed for
charging and all Pi/Pico power went out. After restart ESCs give connected tones,
but GUI RUNNING with increasing frames produces no observed motion. Canonical
GUI PID 1909 owned SPI0.0 and gpiochip15; SPI counters increased without reported
errors. Source mtimes remain September 11 or earlier. Saved preset assigns only
both layers of P16/P20/P45/P49 at 1200 us (eight motors).

At explicit operator authorization for a real spin attempt, terminated GUI PID
1909, waited for exit, and used canonical transport for a one-second 1200 us
pulse on those eight motors: 35 active frames, followed by successful disarmed
1000 us shutdown. GUI remains closed. Movement awaits operator observation;
host transmission is not proof of Pico reception. Propulsion is treated as
connected. No firmware, mapping, or preset changed. Result:
`logs/20260915_bounded_pulse.json`.

# Coaxial 8x8x2 Stable Handoff Entry

## Latest: square grid, side shortcuts, signals on the right

Restored square cells using a dedicated Qt layout geometry pass; there is no
resizeEvent/setFixedSize feedback or deferred enlargement. The existing five
bottom buttons remain below the grid. Each side now has Both/Upstream/Downstream
half-assignment buttons and its correctly mapped Pico shortcuts: left C01-04,
C09-12; right C05-08, C13-16. Centered 2x2-7x7 patch buttons sit above the grid;
the adjacent layer picker applies to patch and Pico shortcuts.

Shortcuts add assignments to the selected group, move overlapping motor owners,
and preserve its name and waveform. Repeated presses do not toggle assignments
off. They are blocked during runs and send no motor command. New from template
remains an optional way to create a separate named group. Signal/PWM/waveform
controls now sit in the scrollable right panel above experiment controls; group
management stays left. The narrower group panel preserves 1366x900 fit.

All 51 hardware-free tests pass, including square sizing across three window
sizes, stable first paint, direct-button mappings and layer choice, repeated
assignment, running lockout, preserved signals/no-output, and control location.
Mapping validation, compilation, and offscreen visual review pass. Preview:
`docs/gui_side_shortcuts_20260911.png`. No live GUI launch, motor command,
firmware/mapping change, or operator-preset edit occurred.


## Native grid layout and graphite styling - latest

The operator correctly identified a visible startup resize. Removed the grid's
resizeEvent/setFixedSize feedback loop entirely. MotorCellGrid now uses native
QGridLayout equal row/column stretches and expanding PairCell widgets, with
the existing fixed central gutter. The launch path sets available-screen
geometry before showing maximized. No timer, delayed resize, hidden-window
workaround, or hardware action was introduced.

The visual direction now combines neutral graphite panels, pale olive accents,
soft corners, restrained group marks, and state-specific status badges. Long
group names elide with full tooltips instead of creating horizontal scrollbars.
Preview: `docs/gui_graphite_20260911.png`. The previous source is preserved in
`recovery_20260911_before_native_layout/`.

All 48 hardware-free tests, mapping validation and compilation pass, including
a first-paint test proving all 64 cell geometries remain stable across subsequent
offscreen event processing, plus resize/edge-fill tests. Actual desktop-window
manager startup has not been observed; no real GUI was launched for verification.
No motor command, firmware change, mapping change, or preset edit was made.
The operator's preset has changed since the earlier right-half snapshot; do not
infer current assignments from that older record.


## Grid fills the panel - latest update

The operator disliked the wide empty margins around the grid. Cells now size
their width and height independently, filling the panel rather than preserving
a square aspect ratio. Reduced panel padding/spacing; retained the central
left/right gap and UP/pair/DN hit targets. The visible startup resizing comes
from maximization/layout sizing, not motor state. All 47 hardware-free tests
pass, including edge-fill checks at 1366x900, 1600x1000, and 1920x1080.
The refreshed offscreen preview is `docs/gui_redesign_20260911.png`.
No real GUI was launched, no motor command was sent, and no preset was changed.


## Latest checkpoint - 2026-09-11

Latest update: complete GUI visual redesign with slate panels, mint accents,
subtle group tints, a left/right gap, explicit status, and a **Premade groups**
picker. Templates cover whole/left/right wall, positioned 2x2-7x7 patches, and
Pico 01-16, with layer selection and a preview. New groups start at 1000 us;
the saved-group limit is 32. All 46 hardware-free tests pass. Saved assignments,
motor mapping, firmware, and transport are unchanged; no hardware was opened.

The Pico overlay is now subtle: neutral borders and center strips, prominent
physical pair numbers, and smaller muted `Pico 01`-`Pico 16` labels. This
supersedes the earlier colorful overlay. Offscreen visual review, mapping
validation, and all 38 hardware-free tests pass; no hardware command was sent.

Read `SESSION_HANDOFF_2026-09-11.md` for the current GUI state and
`SESSION_HANDOFF_2026-09-09.md` for the last hardware checkpoint.
The operator requested restoring left/right numbering: visible grid labels,
tooltips, Pico overlay labels, and Selected Pixel now match physical pairs
01-32 on the left and 33-64 on the right. C01 now displays 01/04/05/08.
Earlier row-major display references below are historical. Motor addressing,
firmware, transport, and saved assignments are unchanged; all 38 hardware-free
tests pass. Current saved `normal` group selects physical pairs 33-64 on both
layers at 1200 us. No real GUI launch or hardware command occurred.

## New Pi and new C01 five-wire path - 2026-09-09

The operator reports that the cloned Raspberry Pi SD card is now running on a
new Raspberry Pi, with a new five-wire path connected directly to C01 and
motor 1 attached. The previous Pi and its September 9 zero-byte SPI result are
stale hardware evidence and must not be treated as a result from this setup.

Read-only inspection of the new Pi reports Raspberry Pi OS/Debian 12 on a Pi 5
with `dtparam=spi=on` and the SPI kernel modules loaded. The current session
does not expose `/dev/spidev0.0`, `/dev/gpiochip*`, or a C01 `/dev/ttyACM*`
device, although `spidev0.0` and GPIO chips appear under sysfs. `bench.py
status` therefore cannot yet identify C01 and no SPI, GPIO, or motor command
has been sent from this Pi. First restore device-node/USB visibility, then run
the read-only C01 status check before any bounded output test.

The device nodes were restored with udev refresh. C01 status then identified
the expected serial and firmware, but showed retained/recent 266-byte wall
traffic (`bytes=152152`, `syncs=578`, `invalid=578`, `last_length=266`). The
bounded USB test stopped at its required boot-idle PWM capture because GPIO23
received zero samples; it did not issue the 1200 us pulse. C01 remained at
1000 us and disarmed. The SPI test was not run because it uses the same GPIO23
capture precheck. Connect C01 GP0 to Pi GPIO23 with a short common-ground
return, keep the motor battery disconnected, and rerun the precheck before
testing the new five-wire SPI path.

After the existing GP0-to-GPIO23 jumper was confirmed, the standalone
input-only capture measured clean 50 Hz idle PWM at approximately 995 us. The
bench diagnostic initially still failed because its capture window used
wall-clock timestamps while new-Pi GPIO events use the monotonic clock. The
bench was corrected to use `time.monotonic_ns()` consistently. Compilation
passed, and the bounded USB and SPI tests then passed. USB measured idle and
1200 us PWM cleanly; SPI received all 30 idle 36-byte frames (1080 bytes),
all 30 syncs, and all 30 valid frames, then passed the SPI 1200 us output,
stop, watchdog, and malformed-frame checks. C01 finished at 1000 us,
disarmed. Reports: `logs/20260909-132320-usb.json` and
`logs/20260909-132328-spi.json`. No propulsion battery was connected.

At the operator's request, C01 was placed in BOOTSEL and flashed with the
matching full-wall `pico/firmware_c01.uf2`. The verified SHA-256 was
`bc75d1c1746c08ac0d424221fefe734af88f3008d888f30923839eaea899700c`.
Copy and `sync` completed; the `/media/jwatson/RP2350` mount disappeared and
the RP2350 BOOTSEL USB device left enumeration, confirming reboot. The
full-wall firmware has no USB CDC status console, so no `/dev/ttyACM*` is
expected afterward. Motor battery remained disconnected during flashing.
The remaining C01-C16 controllers still require their matching full-wall
images before full-wall operation.

The recorded September 4 GUI/runtime source was then restored from
`recovery_20260908_sep3/source_september4/` for the GUI, transport, signals,
config constants, matching tests, and README. Python compilation, generated
mapping validation, and all 38 hardware-free tests pass. This is the exact
recoverable September 4 source checkpoint; no independent filesystem snapshot
timestamped exactly 16:00 exists. The mutable `config/gui_presets.json` was
left untouched because its exact 16:00 contents are not preserved separately.
C01's full-wall image remains the verified image above. Its mapping is
physical P01/P04/P05/P08, displayed by the revised GUI as visible pairs
01/04/09/12, with front/back host indices `0,64,3,67,4,68,7,71`.

Current detailed handoff:

```text
/home/jwatson/coaxial_8x8x2_windwall_system/SESSION_HANDOFF_2026-09-09.md
```

Read that file and `README.md` before continuing work. Current state:

- At the operator's request, a real above-idle five-wire test was run through
  the standalone C01 bench: `ARM SPI`, 50 complete active 36-byte frames at
  1 MHz, and 50 GPIO22 sync pulses for one second, followed by `STOP`. C01
  received 0 SPI bytes, syncs rose 198 -> 248, valid remained 0, invalid rose
  198 -> 248, and its no-frame watchdog timed out safely. Final status is
  1000 us, disarmed. No movement occurred because MOSI/SCLK/CE0 still do not
  reach C01. Raw summary: `logs/german_one_motor_20260909_spi_active.json`;
- The operator requested a real movement test. The standalone German-reference
  bench sent `PULSE USB` to serial-matched C01 GP0, commanding 1200 us for its
  one-second lease, then sent `STOP`; both USB acknowledgements returned. The
  operator observed that the isolated motor spun. Final C01 status is PWM
  1000 us, armed=0, direct=0. This confirms C01 GP0 output, the attached ESC,
  motor, and the new bench firmware are functional. SPI remains isolated as
  the separate fault: C01 still reports bytes=0 despite sync pulses. Raw
  result: `logs/german_one_motor_20260909_usb_spin.json`;
- The idle-only SPI test was repeated after the operator requested another try.
  The host sent 20 more complete 36-byte frames and 20 more sync pulses.
  C01 changed from `bytes=0, syncs=21, invalid=21, last_length=0` to
  `bytes=0, syncs=41, invalid=41, last_length=0`. The stable repeat confirms
  sync reaches C01 while SPI bytes remain absent. No above-idle output was
  sent. Raw summary: `logs/german_one_motor_20260909_spi_idle_repeat.json`;
- The corrected bench UF2 was flashed to serial-matched C01 after motor-battery
  disconnected confirmation. USB `STATUS` now works and identifies
  `german-one-motor-v1`, C01 serial, PWM idle 1000 us, and clean counters.
  The bounded USB pulse command was accepted and expired its one-second lease,
  but the Pi GPIO23 tap saw zero edges; a direct passive idle capture also saw
  zero edges, so the GP0 measurement jumper or GP0 electrical output must be
  rechecked before interpreting PWM. A direct idle SPI test then sent 20
  complete 36-byte frames and 20 GPIO22 sync pulses. C01 reported **0 bytes,
  20 syncs, 0 valid, 20 invalid, last frame length 0**. This is decisive
  isolation: sync reaches C01, while SPI data/clock/chip-select reception does
  not. Raw summary: `logs/german_one_motor_20260909_spi_idle.json`. GUI is
  closed; no above-idle SPI frame was sent and motor battery remains
  disconnected as last confirmed;
- A clean-room C01 bench test was created from the pinned original German
  reference revision `0280f876e587c41cd54a499913e4e208465c6d3e`, isolated under
  `bench/german_one_motor/`. It uses the original 36-byte byte-paced SPI0
  frame and GPIO22 latch, but only enables GP0 PWM. It adds serial-matched C01
  USB status, a one-second 1200 us USB pulse, SPI receive counters, strict
  malformed-frame rejection, a 200 ms SPI watchdog, and a one-shot lease so
  tests cannot continuously restart the motor. The exact C01 serial is
  required. The old GUI was closed before preparation.
  Firmware compiled for `pico2_w`; its 32,476-byte BIN was wrapped into a
  127-block RP2350 UF2 and payload-verified. Host/receiver software tests pass
  with `-Wall -Wextra -Werror`: boot lock, exact frame, every forbidden channel,
  overflow, idle/stop, watchdog, USB deadline, SPI deadline, and lease expiry.
  No firmware was flashed and no motor command was sent with the new test.
  Awaiting the serial-matched C01 in BOOTSEL before copying
  `bench/german_one_motor/german_one_motor.uf2`;
- At the operator's explicit request, C01 was reflashed after fresh confirmation
  that the motor battery was physically disconnected. BOOTSEL serial
  `F68B8438147951D7` matched recorded C01; no Python GUI process was running.
  Verified `pico/firmware_c01.uf2` retained SHA-256
  `bc75d1c1746c08ac0d424221fefe734af88f3008d888f30923839eaea899700c`;
  its 45 application blocks match the compiled BIN and mapping validation
  passed. Copy and sync succeeded, and the device exited BOOTSEL. A subsequent
  eight-second input-only GPIO23 capture measured 400 idle pulses at 50 Hz,
  report medians 996.55-1003.10 us, and zero malformed edges. C01 firmware
  execution and idle output are confirmed after flashing; command response
  has not been retested. GUI remains closed and propulsion is disconnected
  as last confirmed. No motor command was sent during this flash or check;
- The operator explicitly authorized spinning the isolated motor and stated
  the setup was safe. A bounded test closed GUI PID 19495 normally, then used
  the canonical transport to command only F01/C01 GP0 at 1200 us for one
  second, with all other channels idle. Disarmed idle was sent immediately
  afterward and again before transport release. Concurrent GPIO23 capture
  showed only approximately 997-999 us median at 50 Hz, no sustained 1200 us
  pulse, and seven malformed edges plus short-width outliers. This reproduces
  the lack of PWM response without the GUI command loop; it does not establish
  an electrically valid command at C01 or a root cause. No higher-throttle
  attempt, reflash, or wiring change followed. GUI is closed; final commanded
  state is disarmed idle, with idle still measured after transport release.
  Propulsion must be treated as connected until newly confirmed otherwise.
  Raw capture: `logs/c01_single_motor_20260908_one_second.txt`;
- The operator confirms the single C01 ESC goes quiet after normal startup
  tones, is on GP0, and GP0 is tapped to Pi GPIO23. A new eight-second
  input-only capture measured 400 pulses at about 50 Hz, per-report median
  996.08-997.64 us, and zero malformed edges. C01 is generating idle PWM in
  this isolated direct-USB setup. GUI run state during capture and current
  propulsion power are not confirmed, so this alone does not demonstrate
  failed command reception. Before a bounded above-idle diagnostic, obtain
  current confirmation that propulsion is disconnected and control USB stays
  powered. No SPI or GPIO output command was sent;
- After the corrected GUI recovery, the operator reports the failure persists
  with the full wall removed: only C01 and one motor/ESC remain, with all five
  Pi command links and USB directly from the Pi, bypassing the hubs. The ESC
  output pin, beep behavior, current propulsion power state, and whether the
  GPIO23 PWM measurement tap remains connected are not yet confirmed.
  Read-only host inspection found canonical GUI PID 19495 owning SPI0.0 and
  GPIO22's sync handle on `/dev/gpiochip15`, consistent pin modes, and
  7,156,464 transmitted bytes
  since boot with zero SPI errors/timeouts. This is not electrical reception
  evidence or a measurement of the present run. No hardware command was sent;
- The operator clarified that the July 15 rollback was not the GUI used on
  September 3. That rollback is now superseded. Reconstructed and installed
  the pre-September-4 version by reversing 41 recorded file patches across
  eight files from the September-4 backup and matching tests/README. Forward
  replay reproduced every source byte exactly. The GUI retains Rival Lab
  styling, row-major labels, the plane dropdown, full bottom plot, real-only
  runtime, and stable GPIO discovery. All 28 hardware-free tests (26 recovered
  plus two discovery regressions), mapping validation, compilation, and an
  offscreen visual check pass. The Desktop icon uses this version on its next
  launch. Current files were backed up in
  `rollback_backup_20260908_before_sep3_recovery/`; recovery evidence, original
  source baselines, reconstructed files, hashes, and preview are in
  `recovery_20260908_sep3/`. No preset, firmware, mapping, or Desktop launcher
  edits and no hardware output occurred. This is an exact reconstruction of
  the recorded pre-redesign source, not an independently dated September-3
  snapshot. The C01 command-response fault remains unresolved;
- Desktop startup repaired after the GUI rollback: `.xsession-errors` showed
  `RealSync` failing on the restored hardcoded `/dev/gpiochip4`. Restored
  stable `pinctrl-rp1` label discovery in the older synchronous transport;
  a read-only hardware check resolves `/dev/gpiochip15`. The older GUI and
  Desktop launcher remain in place. GPIO discovery tests for gpiod 1.x/2.x
  and missing-device behavior, compilation, mapping validation, and an
  offscreen no-output GUI launch passed. No hardware output or preset write
  occurred; an actual Desktop launch has not yet been verified. The broader
  September GUI/worker tests still target the newer API removed by rollback;
- after the confirmed host-side trace, the operator replaced all five
  Pi-to-Pico MOSI/SCLK/CE0/sync/ground conductors and reports no change.
  Whether other Pico signal branches were isolated remains unconfirmed.
  A passive measurement tool, `scripts/passive_pwm_capture.py`, is now ready
  to measure C01 GP0 on unused Pi GPIO23 (physical pin 16), with common ground
  at physical pin 14. It is input-only and passed compilation and synthetic
  50 Hz / 1000/1200 us / malformed-edge checks. The measurement jumper has
  not been confirmed connected and no capture or further motor command was
  performed. Add wiring with propulsion disconnected and Pi/Pico power off;
  restore control power only before measuring. Application, mapping, firmware,
  and preset are unchanged. See the dated handoff for the exact procedure;
- after that diagnostic preparation, physical C01/Pico 0 was isolated from
  C02-C16. The five Pi conductors now go directly to C01: MOSI->GP16,
  CE0->GP17, SCLK->GP18, sync->GP22, and ground->Pico GND. GP19/MISO and
  RUN remain unconnected. C01 GP0/F01 motor signal remains attached to its
  ESC; the optional Pi GPIO23 measurement tap was not added because Pi header
  access would require disassembly. The GUI's last controlled state was
  disarmed at 1000 us; propulsion remained disconnected during the prior
  diagnostic. Prepare shutdown by closing the GUI, then removing Pi/Pico
  control power; do not restore propulsion with the bus partially connected.
  No further command was sent and application/firmware/mapping/preset remain
  unchanged;
- on 2026-09-08, the operator reports that the GUI looks normal but no motors
  spin. The canonical live GUI holds SPI0/CE0 and the GPIO sync handle;
  static Pi pin configuration is consistent with the project. Mapping
  validation and all 36 hardware-free tests pass. The saved all-128 `normal`
  group changed from Constant 1200 us to 1500 us during diagnosis; offline
  generation/decoding of the latter produces a valid armed frame. The operator
  confirms normal ESC startup beeps followed by silence and `SYSTEM RUNNING`
  on Start. There is no real/mock label in this GUI; earlier requests to look
  for `RUNNING / REAL` were obsolete. The operator clarifies Average PWM is
  1200 us during the run; the earlier 1000 us report must not be treated as
  evidence of running at idle. The saved preset is back at 1200 us. Kernel
  SPI0.0 counters show 1,558,760 one-byte transfers since boot (equivalent to
  5,860 wall frames), zero errors/timeouts, and no change on a subsequent
  read. After the operator confirmed propulsion batteries disconnected and
  Pico USB still powered, Codex performed a short control-only GUI run.
  It displayed SYSTEM RUNNING / 1200 us, and the capture verified exactly
  30,324 successful one-byte SPI transfers, 114 complete 266-transfer frames,
  and 114 matching GPIO22 high/low sync pairs. The GUI frame counter rose
  from 5,396 to 5,510. The final Emergency Stop left the existing GUI open,
  disarmed, and at 1000 us. Strace did not decode payload bytes and cannot
  prove electrical Pico reception. The next check is the physical shared
  command harness with all power removed; no root cause is established.
  No application, mapping, firmware, or preset changes were made. See the
  dated handoff for artifacts and limitations;
- an optional `Show Pico grid` diagnostic overlay is now available in the
  Motor Grid header. It color-codes and labels every visible pixel with its
  authoritative `C01-C16` controller while keeping the row-major pixel number,
  `UP`/`DN`, clicking, and rubber-band selection intact. It is display-only
  and off by default. The fixed controller pattern and assignment behavior
  while enabled are covered by tests, and a 1600x1000 offscreen rendering was
  inspected; all 36 hardware-free tests pass. No real GUI launch or motor
  command occurred;
- the operator reports a brief motor pulse or sag at startup followed by
  recovery. Splitting the listed column loads across independent bus bars and
  batteries did not alter it. Assuming the listed values are fixed pair IDs,
  they span seven controllers, so neither one propulsion branch nor one Pico
  explains the common behavior. The operator further reports 2x2 through 4x4
  groups start cleanly and the problem appears only with more motors. The
  running saved group is Constant `1200 us` on 16 upstream plus 16 downstream
  motors. A trial `2.0 s` linear ramp made the live startup symptom roughly
  ten times worse, pointing away from pure battery inrush and toward prolonged
  operation in the ESC/motor startup-threshold region. The ramp has been
  removed on disk and direct start restored; the trial GUI process was later
  observed to have exited, so the next launch will use the rollback. A future
  software test should stagger direct starts in small batches rather than use a slow PWM
  sweep. All 36 hardware-free tests, compilation, and mapping validation pass.
  No command was sent by Codex;
- on 2026-09-04, the sluggish grid and plane-selection workflow were
  redesigned. Each enlarged square pixel now has direct `UP`, center-number
  (both), and `DN` click targets; the plane dropdown is gone, the application
  opens maximized, and the live plot is compact/collapsed by default to give
  the grid more space. A desktop-style rubber-band drag selects rectangular
  groups of cells, with the initial `UP` / number / `DN` zone determining the
  plane target for the whole box. A real-event propagation bug that overwrote
  `UP` and `DN` drag origins with the both-plane fallback was subsequently
  fixed and covered by an actual press/move/release regression test. Runtime
  byte-paced SPI frames now use a bounded
  latest-frame worker so they do not block Qt input/painting, while the grid is
  independently refreshed at `GUI_REFRESH_HZ` instead of on every 50 Hz
  command tick. Stop/disarm/emergency paths quiesce queued work before a
  synchronous idle frame. Compilation, mapping validation, all 36 tests, and a
  1600x1000 no-output visual inspection passed. The real GUI was not launched
  and no command was sent;
- mock mode has been completely removed from the operator/runtime application.
  There is no `--mock`, `DEFAULT_HARDWARE_MODE`, `use_mock`, or transport branch
  that suppresses real writes. `python3 main.py --mock` is explicitly rejected.
  Hardware-free tests use paired no-output transports through test-only
  dependency injection. After the real-only launch exposed a stale hardcoded
  `/dev/gpiochip4`, GPIO22 discovery was changed to locate the stable
  `pinctrl-rp1` label; on 2026-08-12 this resolved `/dev/gpiochip15`. The real
  GUI then opened successfully, owned SPI0/CE0 and GPIO22, and displayed the
  `Windwall` window. Startup sent only disarmed `1000 us` idle. Compilation,
  mapping validation, and all 26 tests passed;
- after the user confirmed propulsion batteries were disconnected, a
  control-only trace of a confirmed Arm/Start/Stop run recorded exactly 94,164
  successful SPI byte transfers: 354 complete 266-byte frames. It also recorded
  708 successful GPIO22 set-line calls: 354 matching high/low sync pulses. The
  active `1400 us` group spanned C05, C11, and C12. This proves the real GUI,
  protocol send loop, SPI device, and GPIO sync calls execute; the current
  no-response fault is downstream in the shared physical
  MOSI/SCLK/CE0/sync/ground path or Pico frame reception. Keep propulsion
  disconnected and check common-bus continuity to known-working C05 with all
  control power removed before changing mapping or firmware;
- the GUI now uses a graphite/steel/muted-olive tactical instrument-panel
  theme. In the top-right safety stack, compact Emergency Stop is above the
  `ARM SYSTEM` / `DISARM SYSTEM` control;
  Arm no longer uses orange. Operator-facing layer wording is now Upstream
  plane and Downstream plane, while authoritative `F##`/`B##` motor IDs remain
  unchanged. The controller-filter dropdown and highlighting path were
  removed; controller/channel identity remains in Selected Pixel. The final
  offscreen layout was visually verified;
- the visible 8x8 grid now uses prominent row-major two-digit labels without a
  `P` prefix: row 1 is `01-08`, row 2 is `09-16`, through row 8 `57-64`.
  This is display-only; hardware `F##`/`B##` IDs, inherited physical pair
  numbering, motor indices, mapping, protocol, and firmware are unchanged.
  `Selected Pixel` uses the same visible number while retaining exact motor,
  controller, and channel details. Compilation, mapping validation, all 23
  tests, no-output offscreen verification, and a visual inspection passed;
- the GUI was cleaned up for publication screenshots on 2026-07-27. Its
  window and top-bar title are now `Windwall`; the old coaxial-wall
  development title and German-model subtitle were removed. The official
  white Rival Lab logo from `rival-lab.com` is bundled locally in
  `assets/branding/rival_lab_logo_white.png`. An offscreen full-window render
  verified the final layout;
- on 2026-07-27, the separate Start and Stop controls were combined into one
  large rounded muted-olive/dark-red toggle button, and Arm/Disarm was moved
  into the top-right safety stack. The Output ceiling selector was
  removed, so GUI signals always have the full `1000-2000 us` range available.
  Arming alone still sends `1000 us` idle; output above idle begins only after
  Start. The emergency-stop button and `Esc` behavior are unchanged. Python
  compilation, mapping validation, all 22 tests, an offscreen no-output test,
  and an offscreen visual inspection passed. No real command was sent;
- the user reports a new mechanical-strike event: the propeller/blade came off
  `B08` (`C01 CH8/GP7`), struck `B28` (`C04 CH4/GP3`), and afterward `B08`
  plus all eight C04 outputs stopped working. The C04 bank is
  `F25/B25`, `F28/B28`, `F29/B29`, and `F32/B32`. The real GUI was not
  running during the read-only host check. At the user's request, physical C04
  was positively identified in BOOTSEL by recorded serial
  `755F04F32D54ABCA`. After the user explicitly confirmed that the propulsion
  batteries were disconnected, verified `firmware_c04.uf2` (SHA-256
  `e3ee3f1870d282c02f729706c136f242ea08340a3a9942a9382fc14db7cc40a9`)
  was copied and synced; C04 exited BOOTSEL and rebooted normally. No motor
  command was sent. The reflash does not clear the strike hazard: inspect the
  impacted rotors/mounts and the B28/C04 wiring, Pico USB power, ground,
  controller connector, and local SPI/sync harness with all power removed,
  and do not resume live testing until the damage is found and corrected;
- the user subsequently reports that the B08/B28 strike damage has been fixed,
  but C04 still seems nonresponsive. No GUI process was running during the
  read-only host check. C04 not appearing as a normal USB serial device and
  showing no onboard-LED activity do not prove it is dead: runtime USB stdio is
  disabled, and the installed Pico 2 W LED is not driven by the current
  GP25-based `pico2` firmware. The serial-matched BOOTSEL enumeration, UF2
  acceptance, and reboot prove that its boot ROM/USB/flash path responded.
  With propulsion disconnected, verify C04 USB power, the eight-channel
  connector, signal ground, and local harness before another flash;
- the user later clarified that the propeller release itself was an
  installation error and is resolved. Do not surface it as an ongoing design
  concern or in unrelated work unless specifically asked about installation
  or retention;
- on 2026-07-23, the user requested a C01 code check and reflash. Python
  compilation, generated-mapping validation, all 16 unit/GUI/signal/transport
  tests, and the offscreen no-output test passed. The C01 UF2 application
  payload matches its compiled BIN and retains the exact previously working
  SHA-256
  `bc75d1c1746c08ac0d424221fefe734af88f3008d888f30923839eaea899700c`.
  Physical C01 was positively identified by its previously recorded BOOTSEL
  serial `F68B8438147951D7`. After the user explicitly confirmed that all
  propulsion batteries were physically disconnected and with the GUI stopped,
  the verified C01 image was copied and synced; the board exited BOOTSEL
  normally. No motor command was sent and post-flash functional testing has
  not yet been reported;
- the user has now reported that no motor will run; read-only host inspection
  found the GUI process running in real mode and owning SPI0/CE0 and GPIO22,
  but the visible GUI was `ARMED / REAL`, not `RUNNING / REAL`, with every
  channel at the intentional `1000 us` idle value after the run. The user
  confirmed that the attempted run had shown `RUNNING / REAL` and `1200 us`,
  all 16 Pico power indicators were on, and expected-working ESCs did not give
  their no-signal alarm. The canonical process and Pi pin functions are
  correct, and executable control files are unchanged from the 121-of-128
  result. With propulsion physically disconnected, command only formerly
  working F01/C01 GP0 and measure whether it changes from 1000 to 1200 us; if
  it does not, trace the common MOSI/SCLK/CE0/sync/ground path. Do not start
  the saved all-128 group. The user has no scope or logic analyzer, but the
  existing Pico onboard-LED diagnostic can split the fault: during
  `RUNNING / REAL`, valid 50 Hz frames produce a slow state change about every
  0.4 s, while the no-valid-frame watchdog changes about every 0.1 s. Observe
  only during an active run. This onboard-LED test is not usable on the
  installed controllers: the user confirmed all are Pico 2 W boards, while
  current firmware is built for `pico2` and drives GP25. The Pico 2 W onboard
  LED is `WL_GPIO0` behind the CYW43, so no visible blink is expected. The
  external SPI/motor pins are unchanged and these images previously ran 121
  motors, so do not attribute the new total failure to this mismatch or
  mass-reflash; use a power-off continuity test or one bench-tested Pico 2 W
  diagnostic image;
- 121 of 128 motors now work; the remaining failures are `B02`, `F06`, `F07`,
  `B11`, `B14`, `B15`, and `F27`;
- all 128 ESCs are Pichler QX-45 units; every AIR 40 has been removed, so the
  older AIR 40 substitution and repinning notes are historical only;
- no ESC BEC output is used anywhere on the wall. Every QX-45 red/BEC lead is
  disconnected and individually insulated; Pico/controller power comes only
  from the separate USB hub power system;
- the initially reported failures covered `GP0-GP7` exactly once, but the
  fast-beeping F02 Pichler QX-45 ESC was faulty; F02 now works and proves C09
  CH1/GP0, while the remaining seven cover `GP1-GP7` exactly once;
- this supersedes earlier whole-controller results and moves diagnosis to
  individual connectors, signal grounds, ESC paths, and harness topology;
- the fast/loud-beeping F02 ESC was confirmed faulty and must not be reused;
  B02 remains a separate unresolved channel;
- all seven remaining QX-45 ESCs stop their no-signal beep with the GPIO lead
  connected and resume it when the lead is removed, proving recognized idle
  PWM and signal ground reach each ESC; measure whether each pulse rises above
  idle when commanded before diagnosing further;
- C13, C15, and C16 were subsequently reported nonworking; BOOTSEL serial
  `9215A5CE8E496A38`, initially unidentified and therefore left untouched, was
  later physically identified by the user as C15;
- the BOOTSEL target later changed to serial `00FD8CDB8C792B84`; the user
  confirmed it as physical C13 with propulsion batteries disconnected, and it
  was flashed with verified `firmware_c13.uf2` for P34/P35/P38/P39 on both
  layers; copy and sync completed and the board exited BOOTSEL normally;
- Pico 16, BOOTSEL serial `57471CD1D7E2E6C2`, was physically identified by the
  user and flashed on 2026-07-23, with propulsion batteries disconnected and
  the GUI stopped, using verified `firmware_c16.uf2` for P58/P59/P62/P63 on
  both layers; copy and sync completed and the board exited BOOTSEL normally;
  no motor command was sent;
- Pico 15, BOOTSEL serial `9215A5CE8E496A38`, was then physically identified
  by the user and flashed on 2026-07-23, with propulsion batteries disconnected
  and the GUI stopped, using verified `firmware_c15.uf2` for P50/P51/P54/P55
  on both layers; copy and sync completed and the board exited BOOTSEL
  normally; no motor command was sent;
- the 266-byte v1 full-wall SPI/sync protocol is defined;
- the approved harness-preserving C01-C16 mapping is generated;
- matching C01-C16 firmware images are built and were copied to their physical
  controllers during the completed flashing pass;
- a loose `GP16` / SPI MOSI wire feeding the P33-P64 side was corrected, after
  which C05-C08 began working;
- all C01-C08 hardware paths are functionally confirmed working;
- C13-C16 are also functionally confirmed working; the later exact fault list
  leaves individual outputs on C09, C10, and C12 unresolved;
- the user corrected the physical wiring so Pico 2 owns P09/P12/P13/P16 and
  Pico 4 owns P25/P28/P29/P32;
- Pico 2, BOOTSEL serial `5D0AF10E890A0474`, was flashed on 2026-07-22 with
  `firmware_c02.uf2` and rebooted after copy and `sync`;
- Pico 4, BOOTSEL serial `755F04F32D54ABCA`, should retain
  `firmware_c04.uf2`; it was not touched during the final Pico 2 correction;
- C02 and C04 are confirmed working separately after the correction;
- Pico 9, BOOTSEL serial `BA0F8CD9D7DB68F7`, was reflashed on 2026-07-22 with
  verified `firmware_c09.uf2` for P02/P03/P06/P07 on both layers; it accepted
  the image and rebooted; after later BOOTSEL troubleshooting it received the
  same verified C09 image again with the GUI closed and rebooted normally;
- Pico 10, BOOTSEL serial `04AD9C1382F0E250`, was reflashed on 2026-07-22 with
  verified `firmware_c10.uf2` for P10/P11/P14/P15 on both layers; it accepted
  the image and rebooted; after later BOOTSEL troubleshooting it received the
  same verified C10 image again with the GUI closed and rebooted normally;
- Pico 11, BOOTSEL serial `19D7ABD191DD6213`, was reflashed on 2026-07-22 with
  verified `firmware_c11.uf2` for P18/P19/P22/P23 on both layers; it accepted
  the image and rebooted; after later BOOTSEL troubleshooting it received the
  same verified C11 image again with the GUI closed and rebooted normally;
- Pico 12, BOOTSEL serial `8BD9571726565DC8`, was reflashed on 2026-07-22 with
  verified `firmware_c12.uf2` for P26/P27/P30/P31 on both layers; it accepted
  the image and rebooted, then received the same verified image a second time
  after the C09-C11 pass and a third time after BOOTSEL troubleshooting, with
  the GUI closed and a normal reboot each time; in the earlier live test C12
  tried to start a couple of times but appeared to stall;
- bring-up is moving through C09-C12 one controller at a time; test C12 alone
  after its reflash and check the common infill-bus feed if it does not respond;
- after the C09-C12 flashes, a `RUNNING / REAL` test with all 128 motors saved
  at `1200 us` produced no motor output, including the proven banks; the GUI
  process held SPI0/CE0 and GPIO22 correctly, so inspect the common physical
  MOSI/SCLK/CE0/sync/ground entry with power removed before further flashing;
- all ESCs subsequently gave their connected chime and stopped no-signal
  beeping, confirming valid Pico-generated idle PWM and local Pico-to-ESC
  paths; this does not yet prove that Pi SPI/sync commands reach the Picos;
- all Picos and propulsion batteries had remained connected during the C09-C12
  BOOTSEL flashes, explaining temporary no-signal/arming behavior; no damage is
  indicated, but future flashes must be done with propulsion batteries
  disconnected and the GUI stopped/disarmed;
- a clean ESC power cycle did not restore output to one known-good motor;
  read-only checks confirmed the Pi's SPI/CE/sync pin modes, so isolate the
  C09-C12 signal-bus taps with all power removed and retest C01 before checking
  common-bus continuity or reconnecting branches one at a time;
- CRITICAL: unplugging C09-C12 USB power while propulsion batteries remained
  connected caused erratic/random full-speed motor operation; keep batteries
  disconnected and do no further live testing until controller-power-loss and
  ESC fail-safe behavior are made safe with an independent physical cutoff;
- BOOTSEL became difficult while the real GUI still drove the shared bus;
  combined with the earlier harness-dependent BOOTSEL behavior, this indicates
  GPIO backfeeding can prevent a true USB power-cycle—close the GUI and isolate
  the target harness with all power off before a USB-only BOOTSEL attempt;
- the isolated target still did not appear in either `lsusb` or `lsblk`, so it
  is not entering ROM USB mode; use the known-good data cable/port and hold
  BOOTSEL before and throughout a true USB power-on/reset before testing the
  physical BOOTSEL/RUN controls;
- after rewiring C09-C12, C09 works with the rest of the wall, proving the
  common SPI/sync path; C10-C12 ESCs report no signal, which isolates the
  remaining fault to local Pico power, GP0-GP7 PWM wiring, or ESC signal ground;
  compare GP0 idle PWM against C09 with batteries disconnected before reflashing;
- a full code/artifact audit found C01-C04 and C09-C12 behavior identical except
  for intended `HOST_INDICES`; paired BINs differ only in eight mapping bytes
  and embedded name digits, all UF2 payloads match their BINs, mapping/tests/
  no-output test pass, and no code difference explains C10-C12 no-signal beeping;
- known-working C04 spins C12's motors on C12's motor/ESC leads, proving the
  downstream C12 leads/ESCs/motors; the remaining fault is C12's Pico board,
  USB supply, local connector/ground, or firmware execution—compare idle PWM
  directly at C12 GP0 with batteries disconnected;
- the 2026-07-23 exact eight-motor result supersedes the earlier C09-C12
  controller-level findings; C09, C10, and C12 have mixed working/nonworking
  channels, while no C11 failure appears in the exact list;
- `docs/LAYER_FIRST_WIRING_PLAN.md` has one stale C09 GP4-GP7 example showing
  P10/P11 instead of authoritative P06/P07; executable mapping is correct;
- the current wall uses Pichler QX-45 ESCs exclusively on both layers;
- Constant mode exposes exact PWM entry across the full `1000-2000 us` range;
- the operator edited the saved GUI session on 2026-07-27, so it no longer
  matches the historical all-128 group. Inspect the current assignment and
  waveform before every run rather than inferring them from an older handoff.
- the four Waveshare `USB3.2-Gen1-HUB-2IN-4OUT` hubs power four Picos each;
  normal wall commands do not travel over USB—they travel from the Pi over the
  shared GPIO/SPI plus sync wiring, and each Pico generates `GP0-GP7` PWM;
- the Pi remains on its own USB-C supply. A separate 5 V USB-A charger can
  power one hub through a selected USB-A host input; use one charger per hub
  and prefer a dependable 5 V/2 A-or-greater unit. Do not put 5 V into the
  hub's 7-36 V DC terminal;
- a charger-powered selected input does not provide a USB data path to the Pi,
  although normal GPIO/SPI wall control still works. Reconnect/select Pi USB
  for BOOTSEL only with propulsion batteries disconnected;
- never switch hub inputs or controller power while propulsion is connected;
  a hub/Pico brownout is safety-critical because prior controller-power loss
  caused random full-speed operation. A separately fused 24 V/5 A control
  supply for all four hub DC inputs is optional, not required.

Do not infer contiguous controller ownership; preserve the generated
`HOST_INDICES`. USB/controller power must never be removed while propulsion
batteries are connected. Do not resume live testing, mass-reflash, or command
motors until the critical fail-unsafe incident is resolved.

When a newer verified dated handoff is created, update this stable pointer and
`/home/jwatson/WINDWALL_PROJECT_INDEX.md`.

- a final 15-second GUI-closed capture measured clean C01 GP0 idle PWM:
  approximately 996-1001 us at exactly 50 Hz, about 50 samples/second, and
  zero malformed edges. This proves C01 control power/firmware, GP0 pin 1,
  GPIO23 pin 16, and common ground are functioning at idle. No above-idle
  command was sent; propulsion remained disconnected. The next bounded test
  is a 1200 us control-only GUI run while observing GP0;
- during a confirmed manual `SYSTEM RUNNING` GUI state, an 8.01-second
  GPIO23 capture measured C01 GP0 at only 992.9-996.8 us, 50 Hz, and zero
  malformed edges while the GUI displayed F01/B01 at 1250 us, 128/128 assigned,
  and frame count 2329. C01 stayed idle despite the host above-idle command.
  This isolates the remaining fault to direct Pi-to-C01 CE0/GP17, sync/GP22,
  ground, or C01 SPI frame latching. Do not reflash or reconnect propulsion;
  Emergency Stop was requested;

- with the GUI closed and C01 control power left on, a further 15.02-second
  input-only idle capture saw zero edges and zero PWM samples. This confirms
  the earlier high-frequency activity was host SPI pickup. No valid C01 GP0
  waveform is observable without host SPI traffic. Power down and check C01
  control power, GP0 pin 1, GPIO23 pin 16, and the ground jumper; keep
  propulsion disconnected and do not mass-reflash;
- the operator confirmed Emergency Stop after the above-idle capture;
  propulsion remains disconnected. Leave C01 isolated and disarmed while
  checking direct CE0, sync, and ground with power removed;

- the 30-second input-only C01 GP0 -> Pi GPIO23 capture saw zero edges and
  zero PWM samples, including idle. GPIO23 opened as an input and no output
  command was sent. Verify C01 control power, the Pico GP0 header point,
  jumper endpoint, and common ground after power-down; do not reconnect
  propulsion or mass-reflash from this result;
- after the operator corrected the tap, a second 30-second input-only capture
  saw malformed high-frequency activity rather than PWM: final report 1,042
  samples, 6.00 us median, about 14.15 kHz, and 17,206 unpaired edges.
  Valid ESC PWM is about 1000/1200 us at 50 Hz. Treat this as SPI/control-line
  pickup or a wrong endpoint, not valid C01 GP0 output. Power down and verify
  Pico GP0 header pin 1 -> Pi GPIO23 physical pin 16 and a short ground return;
  keep propulsion disconnected and do not mass-reflash;
# 2026-09-08 GUI rollback

- Restored the 8x8x2 GUI to the latest locally saved pre-September-4 version
  from `windwall_complete_github_20260715/03_coaxial_8x8x2_windwall/current`.
- The restored GUI has no `Show Pico grid` option and uses the matching older
  synchronous transport/config/signal files.
- The September-4 versions were preserved at
  `rollback_backup_20260908_pre_pico_grid/` for recovery.
- Mock launch passed. The current September-4 GUI tests are intentionally not
  compatible with this older API and fail during collection; no hardware was
  opened or energized.
