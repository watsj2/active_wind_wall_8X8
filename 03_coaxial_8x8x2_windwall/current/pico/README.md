# Pico Firmware

Firmware for the Coaxial 8x8x2 system should implement the v1 protocol in:

```text
docs/HOST_CONTROLLER_PROTOCOL.md
```

The protocol is a shared-SPI, sync-latched, 266-byte full-wall PWM frame:

```text
8-byte header + 128 x uint16 PWM microseconds + uint16 CRC
```

The firmware plan should use the controller map generated from the Python
address model:

```text
docs/MOTOR_CONTROLLER_MAPPING.md
config/motor_controller_mapping.csv
docs/LAYER_FIRST_WIRING_PLAN.md
```

Physical labels are one-based (`C01-C16`, `CH1-CH8`). Host protocol fields stay
zero-based (`controller_index` 0-15, `channel_index` 0-7).

Harness roles:

```text
C01-C08  -> reused old 8x8 harness controllers
C09-C16  -> new infill controllers
```

The build script generates both `CONTROLLER_ID` and each controller's
`HOST_INDICES` list. Do not derive host ownership from `controller_id * 8`.

## Required Reflash For Approved Numbering

The `Book.xlsx` numbering changes every controller's compiled `HOST_INDICES`
table. The Pico positions and local output wiring do not move: leave each Pico
at `C01-C16` and leave `CH1-CH8` on `GP0-GP7`. Before powered operation, flash
every controller with the correspondingly named firmware file generated here.

Do not swap firmware between controller positions. For example, the physical
`C05` Pico must receive `firmware_c05.uf2`.

Every controller should use the same local PWM pin map:

```text
CH1 -> GP0
CH2 -> GP1
CH3 -> GP2
CH4 -> GP3
CH5 -> GP4
CH6 -> GP5
CH7 -> GP6
CH8 -> GP7
```

The firmware must idle all eight outputs at `1000 us` when a frame is invalid,
when the output-armed flag is clear, or when no valid frame has been received
for `250 ms`.

Build all controller firmware files:

```bash
cd /home/jwatson/coaxial_8x8x2_windwall_system
python3 pico/build_all_firmware.py
```

Expected outputs:

```text
pico/firmware_c01.uf2
pico/firmware_c02.uf2
...
pico/firmware_c09.uf2
pico/firmware_c16.uf2
```

For the first old-harness bench test, build only C01:

```bash
python3 pico/build_all_firmware.py --controllers C01
```
