# German 6x6 GUI Extrapolation

## Source Foundation

The GUI is derived from the original `kowshiksri/active_wind_wall` source
preserved in the archive Git bundle. The reference revision is available as
`refs/remotes/kowshiksri/main` in that bundle (`0280f876e587c41cd54a499913e4e208465c6d3e`).

The new GUI preserves the original operator model:

- motors belong to named, color-coded groups;
- each group owns one independently configurable signal;
- supported signals include sine, square, constant, and custom Fourier;
- experiments have explicit arm, start, timed run, stop, and disarm states;
- group/signal configurations can be saved and loaded;
- an oscilloscope-style plot shows preview and live PWM values.

## 8x8x2 Extrapolation

The original 36 single motors become 64 coaxial wind pixels and 128 motors.
Each grid cell therefore exposes independent front and back assignment colors.
An operator can assign both motors in a pair together or target only one layer.

Group membership stores canonical host motor indices:

```text
0-63    front F01-F64, row-major
64-127  back  B01-B64, row-major
```

Signal generation produces a complete 128-value host frame in that order. The
existing address model remains the only authority for translating a selected
pixel to controller and channel labels.

## Frozen Hardware Boundary

The GUI rewrite does not alter:

- `coaxial_windwall/model.py` or `CONTROLLER_HOST_INDICES`;
- `config/motor_controller_mapping.csv`;
- the C01-C16 physical controller/channel layout;
- `coaxial_windwall/protocol.py` or the 266-byte v1 frame format;
- `pico/firmware_controller_template.c`;
- `pico/build_all_firmware.py`;
- any `pico/firmware_c01.uf2` through `pico/firmware_c16.uf2` image.

The host interface now passes the GUI's arm state into the already-defined v1
`FLAG_OUTPUT_ARMED` field. This uses the existing protocol as intended; it does
not change the protocol or firmware.

Real host transport remains disabled until the one-controller bench procedure
has validated C01, watchdog idle behavior, arm-flag behavior, channel order,
and output slew requirements.
