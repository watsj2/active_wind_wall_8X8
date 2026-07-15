# Coaxial 8x8x2 Windwall Handoff - 2026-07-14

## Current Status

- The v1 host-to-controller protocol is defined.
- Motor/pixel order follows the approved original 8x8 Pico-block numbering:
  the top row is `P01-P04, P33-P36`.
- Controller mapping now preserves the original 8x8 harness where practical:
  `C01-C08` are old-harness controllers and `C09-C16` are new infill
  controllers.
- Firmware must use each controller's generated `HOST_INDICES`; controllers do
  not own contiguous `controller_id * 8` host values.
- The wiring manual PDF has been regenerated for the harness-preserving map in
  both `docs/` and on the Desktop.
- New `C01-C16` UF2 files have been built, but no hardware was flashed during
  this work. All 16 physical Picos require their matching new image.
- The GUI defaults to the real SPI/GPIO transport; `--mock` is available for
  simulation and smoke tests.

## Protocol

Canonical spec:

```text
docs/HOST_CONTROLLER_PROTOCOL.md
```

Python protocol helpers:

```text
coaxial_windwall/protocol.py
```

Protocol summary:

- Shared SPI command bus plus sync pulse.
- Host sends one full-wall frame to all 16 controllers.
- Frame is 266 bytes:
  - 8-byte header
  - 128 x little-endian `uint16` PWM pulse widths in microseconds
  - CRC-16/CCITT-FALSE
- Payload order is layer-first and numeric by the original Pico-block motor
  number inside each layer:
  - host indices `0-63` = front plane `F01-F64`
  - host indices `64-127` = back plane `B01-B64`
- Controller ownership is explicit:
  - `C01` channels: `F01`, `B01`, `F04`, `B04`, `F05`, `B05`, `F08`, `B08`
  - `C09` channels: `F02`, `B02`, `F03`, `B03`, `F06`, `B06`, `F07`, `B07`
- Firmware must require valid magic/version/type/length/CRC.
- Firmware must idle at `1000 us` if the output-armed flag is clear, the frame
  is invalid, or no valid frame has been received for `250 ms`.

## Firmware

Firmware template:

```text
pico/firmware_controller_template.c
```

Build script:

```text
pico/build_all_firmware.py
```

Controller roles:

```text
C01-C08 -> reused old 8x8 harness
C09-C16 -> new infill controllers
```

Rebuild all firmware:

```bash
cd /home/jwatson/coaxial_8x8x2_windwall_system
python3 pico/build_all_firmware.py
```

## Verification Completed

```bash
python3 -m py_compile main.py config/__init__.py coaxial_windwall/*.py coaxial_windwall/*/*.py pico/build_all_firmware.py
python3 scripts/generate_motor_mapping.py --check
timeout 5 env QT_QPA_PLATFORM=offscreen python3 main.py --mock --smoke-test
python3 scripts/build_wiring_manual_pdf.py --desktop-copy
```

The GUI smoke test printed the normal Qt offscreen warning:

```text
This plugin does not support propagateSizeHints()
```

## Next Safe Step

Bench-test `C01` first because it uses the reused old harness:

1. Put the physical C01 Pico in BOOTSEL mode.
2. Copy `pico/firmware_c01.uf2` to the RP2350 drive.
3. With live ESC loads disconnected, verify outputs stay at `1000 us` for
   unarmed valid frames.
4. Verify one armed channel at a low value while the other seven stay idle.
5. Confirm channel order:
   `F01`, `B01`, `F04`, `B04`, `F05`, `B05`, `F08`, `B08`.

Only after C01 is correct should the rest of the old-harness controllers and
then the new infill controllers be flashed.
