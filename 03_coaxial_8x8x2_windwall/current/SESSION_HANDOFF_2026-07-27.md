# Coaxial 8x8x2 Windwall Handoff - 2026-07-27

## Row-Major GUI Pixel Labels

At the user's request, the operator-facing numbers in the 8x8 motor grid now
run sequentially by visible row:

```text
Row 1: 01 02 03 04 05 06 07 08
Row 2: 09 10 11 12 13 14 15 16
...
Row 8: 57 58 59 60 61 62 63 64
```

The `P` prefix and the small competing `R#C#` text were removed from each
painted grid tile. The two-digit number is now a prominent 13-point bold,
centred label. The detail heading now reads `Selected Pixel`, and its first
line uses the same two-digit display number without a `P` prefix. It continues
to show the authoritative upstream/downstream `F##`/`B##` motor IDs plus the
fixed controller and channel assignments.

This is deliberately a display-only numbering layer. The inherited physical
pair numbers, `PIXEL_NUMBER_GRID`, motor indices, harness mapping,
`HOST_INDICES`, saved assignments, protocol, firmware, and physical wiring are
unchanged. For example, visible grid tile `05` at R1C5 still targets hardware
motors F33/B33 on their existing controller channels. Python compilation,
mapping validation, all 23 tests, the offscreen mock smoke test, and a full
1480x920 visual inspection passed. No real command was sent.

## Publication Branding Cleanup

The GUI header was cleaned up for screenshots and documents at the user's
request:

- the visible `Coaxial 8x8x2 Windwall` development title was removed;
- the `German 6x6 control model / 64 wind pixels / 128 motors` subtitle was
  removed;
- the application/window title is now `Windwall`;
- the top bar now uses the official white vertical Rival Lab logo published by
  `https://rival-lab.com/home`, bundled locally at
  `assets/branding/rival_lab_logo_white.png` so normal GUI startup does not
  require internet access;
- the bundled original is a 2560x2000 RGBA PNG with SHA-256
  `53ce3a58b7c7226096d6ba2ff65775d7735bbdab5d7491bf3c9bb6ab90dba59b`.

An offscreen full-window render confirmed that the logo, title, Arm/Disarm,
timer, and Emergency Stop fit cleanly in the top bar at the normal 1480x920
window size.

## Tactical UI and Plane-Terminology Cleanup

The screenshot-oriented cleanup continued at the user's request:

- the top-bar safety controls are now a vertical stack at the far right, with
  the compact `EMERGENCY STOP` control above `ARM SYSTEM`;
- the system button reads only `ARM SYSTEM`, `DISARM SYSTEM`, or
  `SYSTEM RUNNING` according to state; the `REAL` / `MOCK` suffix was removed
  from this control at the user's request;
- Arm no longer uses orange. The GUI now uses a restrained graphite, steel,
  and muted-olive instrument-panel palette with tighter corner radii;
- Emergency Stop uses a compact dark-red treatment rather than a large bright
  red block;
- the large rounded experiment Start/Stop toggle remains in the Experiment
  Control panel, with muted olive for Start and dark red for Stop;
- operator-facing `front layer` / `back layer` wording was replaced with
  `Upstream plane` / `Downstream plane` in assignment scope, summary counts,
  the selected-pair readout, grid-bar labels (`U` / `D`), and monitor choices;
- fixed hardware motor identifiers such as `F01` and `B01` were deliberately
  preserved because they are authoritative mapping and wiring identities;
- the controller-filter dropdown and its visual highlighting path were
  removed. Controller and channel identity remains available in the Selected
  Pixel readout.

The final 1480x920 offscreen render was visually inspected. The safety stack,
plane selector, motor grid, experiment controls, and live monitor fit without
clipping.

## GUI Control Update

The experiment controls were simplified at the user's request:

- the separate `START EXPERIMENT` and `STOP EXPERIMENT` buttons are now one
  large rounded toggle button;
- while stopped, the button is muted olive and reads `START EXPERIMENT`;
- while running, the same button is red and reads `STOP EXPERIMENT`;
- normal Stop retains the existing behavior: it immediately sends `1000 us`
  idle to every channel and follows the `Auto-disarm after experiment` choice;
- the Arm/Disarm button now occupies the former top-bar status-badge position;
- its text includes the hardware mode (`REAL` or `MOCK`), and it is disabled
  during a running experiment so Stop or Emergency Stop must be used;
- the separate red `EMERGENCY STOP` button and the `Esc` shortcut are
  unchanged and still stop, send idle, and disarm.

The `Output ceiling` selector was also removed. GUI-generated signals now
always use the full configured `1000-2000 us` range. Fractional signals map
`0.0` to `1000 us` and `1.0` to `2000 us`; Constant mode accepts an exact
value through `2000 us`. Arming alone still sends `1000 us` idle to all 128
channels. A configured above-idle value is sent only after the experiment is
started.

No controller mapping, host protocol, transport, firmware, saved motor
assignment, or physical hardware was changed by this work. No real motor
command was sent.

## Verification

Verification completed in mock/no-output mode:

- Python compilation passed;
- generated motor-mapping validation passed;
- all 22 unit, GUI-workflow, signal, and mocked transport tests passed;
- the offscreen mock smoke test passed;
- an offscreen rendered-window inspection confirmed the top-bar Arm/Disarm
  placement, large rounded Start/Stop control, and removal of the Output
  ceiling field;
- a GUI workflow test confirms that Arm sends only `1000 us`, while Start can
  send a selected `2000 us` Constant command;
- a branding test confirms the new window/header title, verifies that the
  bundled logo loads, and rejects both removed development-header phrases;
- GUI tests confirm Emergency Stop is stacked above Arm, the Arm state styling
  changes correctly, upstream/downstream terminology is present, and the
  controller-filter dropdown is absent.

## Hardware and Safety Continuity

The detailed hardware history and the latest confirmed channel diagnosis
remain in `SESSION_HANDOFF_2026-07-23.md`. The latest recorded result is 121 of
128 motors working, with `B02`, `F06`, `F07`, `B11`, `B14`, `B15`, and `F27`
unresolved.

The user clarified that the earlier propeller-release event was an installation
error and is resolved. Do not raise it as an ongoing design fault or in
unrelated work unless the user asks specifically about installation or
retention.

The controller-power-loss incident remains controlling: removing or switching
Pico/controller USB power while propulsion batteries were connected caused
erratic/random full-speed motor operation. Keep propulsion batteries
physically disconnected for controller-power or signal-wiring work. Required
order remains:

```text
Power-up:   Pico/control USB first -> verify idle PWM -> propulsion battery last
Power-down: propulsion battery first -> verify motors stopped -> Pico USB last
```

The saved GUI session was edited by the operator on 2026-07-27 and is no
longer the historical all-128-motor group described in the July 23 handoff.
Always inspect the currently assigned group and commanded waveform before a
run; do not infer saved selection from an older handoff.
