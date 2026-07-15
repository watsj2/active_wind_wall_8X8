# Coaxial 8x8x2 Design Notes

## Clean-Start Decisions

- Do not copy the old GUI into this project.
- Keep the first GUI focused on command construction and operator state.
- Keep the operator interface in dark mode for lab use.
- Paint the 8x8 pixel wall manually instead of using a child widget for every
  bar; this keeps visual updates cheap on the Raspberry Pi.
- Keep real hardware output disabled until the new 128-motor protocol is
  implemented in firmware and bench-tested.
- Treat telemetry, Testo mapping, and monitor views as separate modules with
  standalone verification before putting them in the main control path.

## Initial Motor Naming

Operator-facing labels:

```text
P01-P64 -> wind-pixel pair numbers
F01-F64 -> front-layer motors
B01-B64 -> back-layer motors
```

Signed aliases such as `+01` and `-01` are available in the address model for
displays where the front/back symmetry is useful, but they should not be the
primary IDs in logs, command files, or hardware protocols.

## Final Motor Mapping

The fixed motor numbering is row-major. Front-plane motors occupy host frame
indices `0-63`; back-plane motors occupy indices `64-127`.

```text
R1 C1 Front / F01 -> motor 0
R1 C2 Front / F02 -> motor 1
...
R8 C8 Front / F64 -> motor 63
R1 C1 Back  / B01 -> motor 64
R1 C2 Back  / B02 -> motor 65
...
R8 C8 Back  / B64 -> motor 127
```

The controller layout is 16 controllers with 8 outputs each, but controllers do
not own contiguous host indices. `C01-C08` reuse the original 8x8 harness.
Adjacent old outputs become front/back channels for one coaxial pixel. `C09-C16`
fill the middle positions.

```text
C01 CH1-CH8 -> F01, B01, F04, B04, F09, B09, F12, B12
C09 CH1-CH8 -> F02, B02, F03, B03, F10, B10, F11, B11
```

The canonical controller lookup is `CONTROLLER_HOST_INDICES` in
`coaxial_windwall/model.py`; generated firmware must use that list rather than
deriving controller ownership from `controller_id * 8`.

The generated mapping deliverables are:

```text
docs/MOTOR_CONTROLLER_MAPPING.md
config/motor_controller_mapping.csv
docs/LAYER_FIRST_WIRING_PLAN.md
docs/Coaxial_Windwall_Wiring_Assembly_Manual.pdf
```

If the physical wiring lands differently, update `coaxial_windwall/model.py`,
then regenerate the mapping with `python3 scripts/generate_motor_mapping.py --write`
before changing firmware or enabling real hardware output.

## Feature Rebuild Order

1. 128-motor addressing and GUI preview
2. PWM ranges, timed tests, editable groups, and preset test frames
3. Pi-friendly painted grid display
4. Mock command loop and logging
5. Defined hardware protocol
6. Bench-tested Pico firmware and controller flashing workflow
7. Telemetry transport with standalone readback test
8. Calibration/Testo import tools
9. Operator monitor views based on proven data

The v1 host-to-controller protocol is defined in
`docs/HOST_CONTROLLER_PROTOCOL.md`. It is a shared-SPI, sync-latched full-wall
PWM command frame with 128 little-endian `uint16` pulse widths in microseconds.
