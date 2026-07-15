# Coaxial 8x8x2 Windwall Handoff - 2026-07-06

Saved at: 2026-07-06 14:43 CST

## What Happened This Session

- Created a hard save of the old 64-motor Active Wind Wall system.
- Started a clean new project for the Coaxial 8x8x2 / 128-motor system.
- Built a new mock-safe PyQt6 GUI.
- Added dark mode.
- Added front/back motor naming:
  - `P01-P64` = wind-pixel pairs
  - `F01-F64` = front-layer motors
  - `B01-B64` = back-layer motors
- Added PWM range and preset controls.
- Added editable groups.
- Added saved preset tests.
- Added timed tests with:
  - `Test Speed PWM`
  - `Duration`
  - visible run timer
  - automatic idle at timer expiry
- Replaced per-pixel progress widgets with lightweight painted pixel cells for
  Raspberry Pi performance.
- Added a desktop launcher and representative SVG icon.
- Added a physical upgrade checklist for moving from 64 to 128 motors.

## Important Paths

Old system hard save:

`/home/jwatson/windwall_hard_saves/pre_coaxial_8x8x2_20260706_113917`

Old active 64-motor project:

`/home/jwatson/active_wind_wall_8X8`

New Coaxial project:

`/home/jwatson/coaxial_8x8x2_windwall_system`

New GUI launcher:

`/home/jwatson/Desktop/Coaxial Windwall GUI.desktop`

New icon:

`/home/jwatson/coaxial_8x8x2_windwall_system/assets/icons/coaxial-windwall.svg`

Physical upgrade checklist:

`/home/jwatson/coaxial_8x8x2_windwall_system/docs/PHYSICAL_UPGRADE_CHECKLIST.md`

## Current Safety State

- Real 128-motor hardware output is intentionally disabled.
- The new hardware interface is mock-only.
- Do not run the 128-motor wall from the old 64-motor firmware or old host
  protocol.
- The old Active Wind Wall repo was clean when checked.

## Verification Already Run

From `/home/jwatson/coaxial_8x8x2_windwall_system`:

```bash
python3 -m compileall -q .
timeout 5 env QT_QPA_PLATFORM=offscreen python3 main.py --smoke-test
```

Also checked:

- Timed test starts motors active in mock state, expires, and returns to idle.
- Group creation and group PWM application work in offscreen GUI checks.
- Desktop launcher points to the new icon.
- SVG icon parses as valid XML.

## Known Git Note

The new Coaxial project is a filesystem baseline, not a git repo. Git metadata
creation failed earlier in this environment with read-only filesystem errors.
The files are saved normally on disk.

## Next Good Tasks

1. Build a final 128-motor mapping table:
   - `P01-P64`
   - `F01-F64`
   - `B01-B64`
   - controller number
   - controller channel
2. Decide physical controller layout:
   - layer-first: old 8 controllers for one layer, new 8 controllers for the
     second layer
   - pair-first: each controller owns four coaxial pairs
3. Define the new 128-motor host-to-controller protocol.
4. Create 16-controller firmware generation.
5. Bench-test one added controller with no live motor load.
6. Only after bench testing, enable real hardware output in the new project.

## Resume Prompt

When Codex resumes, continue from:

`/home/jwatson/coaxial_8x8x2_windwall_system`

Read this file first, then inspect:

- `README.md`
- `docs/DESIGN_NOTES.md`
- `docs/PHYSICAL_UPGRADE_CHECKLIST.md`
- `coaxial_windwall/gui/app.py`
- `coaxial_windwall/model.py`
- `coaxial_windwall/hardware/interface.py`
