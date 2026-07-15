# Coaxial 8x8x2 Windwall Handoff - 2026-07-08

Saved at: 2026-07-08 CST

## What Changed

- Changed the canonical 128-motor mapping from pair-first to layer-first.
- Front plane (`FP`) is now treated as one 8x8 wall:
  - `C01-C08`
  - `F01-F64`
  - Pichler XQ-45 ESCs
- Back plane (`BP`) is now treated as one 8x8 wall:
  - `C09-C16`
  - `B01-B64`
  - T-MOTOR AIR 40 ESCs
- Updated `coaxial_windwall/model.py` so host indices are layer-first:
  - `0-63` = front-plane motors
  - `64-127` = back-plane motors
- Updated the mapping generator and regenerated:
  - `docs/MOTOR_CONTROLLER_MAPPING.md`
  - `config/motor_controller_mapping.csv`
- Added detailed wiring documentation:
  - `docs/LAYER_FIRST_WIRING_PLAN.md`
- Added an assembly-style PDF wiring manual:
  - `docs/Coaxial_Windwall_Wiring_Assembly_Manual.pdf`
  - `/home/jwatson/Desktop/Coaxial_Windwall_Wiring_Assembly_Manual.pdf`
- Added repeatable PDF generation script:
  - `scripts/build_wiring_manual_pdf.py`

## Final Mapping Decision

The software baseline is layer-first:

```text
C01-C08  -> FP / front plane / F01-F64 / Pichler XQ-45 ESCs
C09-C16  -> BP / back plane  / B01-B64 / T-MOTOR AIR 40 ESCs
```

Each controller owns one row of one plane:

```text
C03 CH1-CH8 -> F17-F24
C11 CH1-CH8 -> B17-B24
```

Physical labels are one-based (`C01-C16`, `CH1-CH8`). Host protocol fields
should stay zero-based (`controller_index` 0-15, `channel_index` 0-7).

## Current Safety State

- Real 128-motor hardware output is still intentionally disabled.
- The hardware interface is still mock-only.
- Do not run the 128-motor wall from the old 64-motor firmware or old host
  protocol.
- Do not wire from the older pair-first draft. Use the layer-first mapping and
  the PDF/manual files listed above.
- ESC BEC/red wires are unused and should be disconnected/insulated.
- Pi/Pico/controller power remains separate from ESC BEC outputs.
- Control ground and ESC signal ground must share a deliberate common
  reference.

## Verification Run

From `/home/jwatson/coaxial_8x8x2_windwall_system`:

```bash
python3 scripts/generate_motor_mapping.py --check
python3 scripts/build_wiring_manual_pdf.py --desktop-copy
python3 -m compileall -q .
timeout 5 env QT_QPA_PLATFORM=offscreen python3 main.py --smoke-test
```

The PDF was visually spot-checked by rendering the cover and signal-harness
page with `pdftoppm`. The smoke test printed
`This plugin does not support propagateSizeHints()`, which is the normal Qt
offscreen-platform warning.

## Next Good Tasks

1. Define the 128-motor host-to-controller protocol using the layer-first map.
2. Create the 16-controller firmware generation plan.
3. Add a bench-safe one-controller firmware/protocol test with no live motor
   load.
4. Add a calibration table for Pichler-vs-AIR layer PWM offsets.
5. Only after bench testing, add a deliberately gated real hardware interface.

## Resume Prompt

Continue from:

`/home/jwatson/coaxial_8x8x2_windwall_system`

Read this file first, then inspect:

- `docs/Coaxial_Windwall_Wiring_Assembly_Manual.pdf`
- `docs/LAYER_FIRST_WIRING_PLAN.md`
- `docs/MOTOR_CONTROLLER_MAPPING.md`
- `config/motor_controller_mapping.csv`
- `scripts/generate_motor_mapping.py`
- `scripts/build_wiring_manual_pdf.py`
- `coaxial_windwall/model.py`
- `coaxial_windwall/hardware/interface.py`
