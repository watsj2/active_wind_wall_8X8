# Coaxial 8x8x2 Design Notes

## Clean-Start Decisions

- Do not copy the old GUI into this project.
- Keep the first GUI focused on command construction and operator state.
- Keep the operator interface in dark mode for lab use.
- Paint the 8x8 pixel wall manually instead of using a child widget for every
  bar; this keeps visual updates cheap on the Raspberry Pi.
- Keep real hardware output disabled until the new 128-motor protocol exists.
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

## Initial Motor Mapping

The first mapping is row-major by wind pixel, with the two coaxial motors stored
next to each other:

```text
R1 C1 Front / F01 -> motor 0
R1 C1 Back  / B01 -> motor 1
R1 C2 Front / F02 -> motor 2
R1 C2 Back  / B02 -> motor 3
...
R8 C8 Front / F64 -> motor 126
R8 C8 Back  / B64 -> motor 127
```

The first controller assumption is 16 controllers with 8 motors each:

```text
controller = motor_index // 8
channel = motor_index % 8
```

If the physical wiring lands differently, update `coaxial_windwall/model.py`
or add a mapping table without changing the GUI.

## Feature Rebuild Order

1. 128-motor addressing and GUI preview
2. PWM ranges, timed tests, editable groups, and preset test frames
3. Pi-friendly painted grid display
4. Mock command loop and logging
5. Bench-tested hardware protocol
6. Firmware and controller flashing workflow
7. Telemetry transport with standalone readback test
8. Calibration/Testo import tools
9. Operator monitor views based on proven data
