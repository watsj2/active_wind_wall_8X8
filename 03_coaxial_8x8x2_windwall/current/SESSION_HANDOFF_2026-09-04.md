# Coaxial 8x8x2 Windwall Handoff - 2026-09-04

## Responsive GUI and Direct Grid Selection

The motor grid was redesigned after the operator reported that the GUI felt
sluggish and that the plane-selection dropdown made assignments awkward.

- The Upstream / Downstream / Both assignment dropdown was removed.
- Every wind-pixel cell is now square and contains three direct click zones:
  `UP` assigns or removes the upstream motor, the center `01-64` number assigns
  or removes both motors, and `DN` assigns or removes the downstream motor.
- Hover feedback identifies the click target before it is selected.
- Desktop-style rubber-band selection works in every drag direction and
  includes each cell touched by the selection rectangle. Starting the drag on
  `UP`, the center number, or `DN` applies upstream, both, or downstream to the
  entire boxed region in one assignment/save/refresh operation. A short press
  and release remains a normal single-cell click.
- A post-test operator report exposed real Qt mouse-event propagation that
  reset cell-origin `UP` and `DN` drags to the grid fallback of both planes.
  The grid now preserves an already-recorded cell drag origin. A QTest
  regression exercises actual upstream and downstream press/move/release
  sequences rather than calling the drag helper directly.
- Full-wall shortcuts are explicit buttons: `All upstream`, `All pairs`, and
  `All downstream`.
- Cells have a 74 px minimum side, a 90 px preferred side, and grow together
  while remaining square. The normal application opens maximized.
- The full-width live plot is collapsed into a compact monitor bar by default.
  `Show plot` restores it when needed, allowing the grid to use substantially
  more vertical space during normal operation.

The visible row-major `01-64` labels remain display-only. The authoritative
`F##` / `B##` identities, motor indices, controller/channel mapping,
`HOST_INDICES`, protocol, firmware, and saved assignments were not changed.

## Pico Grid Diagnostic Overlay

After the startup symptom appeared to follow Pico-grid structure, an optional
`Show Pico grid` checkbox was added to the Motor Grid header. It is off by
default. When enabled, every square keeps its visible row-major number and adds
the authoritative `C01-C16` controller label in the center, with a distinct
controller color on the center and cell border. For example, the first visible
row reads `01 C01`, `02 C09`, `03 C09`, `04 C01`, `05 C05`, `06 C13`,
`07 C13`, and `08 C05`.

The overlay is paint-only. It does not change motor ownership, group
assignment, `UP`/`DN` targets, box-drag behavior, the physical mapping,
protocol frames, or firmware. The controller ID also appears in each cell's
tooltip. An actual assignment made with the overlay enabled is covered by the
GUI regression test.

## Responsiveness Changes

The physical SPI transport intentionally issues one transfer for each of the
266 bytes in a full-wall frame. Those byte-paced transfers previously ran in
the Qt GUI thread at the 50 Hz command rate, and every command tick also walked
and repainted the complete 64-cell grid.

- Runtime frames now go through a dedicated bounded latest-frame dispatcher.
  The Qt event loop queues a frame and returns immediately; if the transport is
  slower than the producer, the single pending frame is replaced so stale
  motor commands are never replayed.
- The 50 Hz command-production interval is unchanged.
- Grid painting is no longer triggered by the command timer. It is refreshed
  independently at `GUI_REFRESH_HZ` (currently 12 Hz).
- Each cell caches its upstream and downstream motor indices, eliminating
  repeated address construction during visual refreshes.
- The live plot is not repainted while it is collapsed.
- Stop, disarm, and emergency stop discard any queued runtime frame, wait for
  an active transfer to finish, and then send their idle safety frame
  synchronously. The initial running frame is also synchronous.
- A worker transport error stops the command timer, marks the GUI disarmed,
  and presents an operator error instead of silently continuing.

## Reported Startup Pulse / Sag

The operator subsequently reported that motors briefly pulse or sag at startup
and then recover. Splitting the listed column loads across separate bus bars
and separate batteries did not noticeably change the behavior. Interpreting
`P17`, `P19`, `P25`, `P33`, `P41`, `P49`, and `P57` as the fixed pair IDs,
they span C03, C04, C05, C06, C07, C08, and C11 rather than one controller.

Initial read-only inspection found the running GUI's saved active group set to
Constant `1200 us`, with 16 upstream and 16 downstream motors assigned. That
version changed every assigned motor from `1000 us` idle directly to its
requested PWM in the first frame. The operator noted that 2x2 through 4x4
groups start cleanly and the symptom appears only after more motors are added,
which points toward a shared startup threshold rather than one motor or ESC.

At the operator's request, a fixed `2.0 s` linear software ramp was briefly
implemented and hardware-free verified. In the subsequent live test the
operator reported that it made the startup problem roughly ten times worse.
The ramp held the direct-drive sensorless motors in the low-PWM starting region
instead of crossing it quickly, producing a result more consistent with
startup-threshold/commutation difficulty than with a pure battery-inrush
problem. The ramp was therefore removed from the code and tests, restoring the
previous direct start on the next application launch.

A startup-induced disturbance on the shared SPI/sync/signal-ground network is
still plausible because an invalid controller frame deliberately returns its
local outputs to `1000 us` until a valid frame is received. Separate propulsion
batteries do not isolate that shared control network. Power distribution is
not fully ruled out without capturing minimum voltage at the ESC input during
the event. The next software experiment, if authorized, should stagger clean
direct starts in small batches rather than sweep slowly through the unstable
region. Before that, record the duration and grouping, compare one guarded
motor and one plane, and inspect one isolated ESC's startup mode, governor
mode, timing, and throttle calibration before changing every controller.

No command was sent by Codex. At the time of the adverse report, the restarted
real GUI process still had the ramp loaded in memory, but it was subsequently
observed to have exited. The next application launch will use the on-disk
direct-start rollback.

## Verification

Hardware-free verification used only injected no-output transports:

```text
Python compilation                         PASS
generated motor mapping --check            PASS
36 unit/GUI/signal/transport tests          PASS
Pico overlay fixed C01-C16 pattern          PASS
direct UP / number / DN mouse targeting     PASS
real mouse-event rubber-band selection      PASS
real UP / DN drag-start plane propagation   PASS
square-cell resize behavior                 PASS
non-blocking slow-transport dispatch        PASS
stale pending-frame replacement             PASS
1600x1000 offscreen visual inspection       PASS
1600x1000 Pico-overlay visual inspection    PASS
```

The real application was not launched, SPI/GPIO was not opened, and no motor
command was sent during this work.

## Safety Continuity

The controller-power-loss incident remains controlling: never remove or
switch Pico/controller USB power while propulsion batteries are connected.
The required order remains:

```text
Power-up:   Pico/control USB first -> verify idle PWM -> propulsion battery last
Power-down: propulsion battery first -> verify motors stopped -> Pico USB last
```

The exact latest channel result remains 121 of 128 motors working, with `B02`,
`F06`, `F07`, `B11`, `B14`, `B15`, and `F27` unresolved. This GUI work does
not resolve or alter those physical faults. Treat every normal application
launch as real bus activity and do not launch it until the physical safe state
has been verified.
