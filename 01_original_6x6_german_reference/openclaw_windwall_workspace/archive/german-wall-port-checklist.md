# German Wall (6x6) -> Windwall (8x8) Port Checklist

## Purpose

This document describes how to adapt the German wall upstream repository:
- Upstream: https://github.com/kowshiksri/active_wind_wall
- From: 6x6 / 36 motors / 4 Picos / 9 motors each
- To: 8x8 / 64 motors / 8 Picos / 8 motors each

The upstream repository should be treated as a useful architecture reference, not a drop-in implementation.

## High-Level Strategy

Preserve:
- central Pi orchestration
- real-time flight loop structure
- precomputed signal generation
- broadcast SPI + sync-pulse update model
- safety watchdog ideas
- GUI grouping concepts
- logging architecture

Rewrite:
- all topology-specific mapping
- motor count assumptions
- Pico count assumptions
- firmware frame sizing
- 6x6 GUI geometry assumptions
- 3x3 quadrant ownership assumptions

---

## 1. Configuration Layer

### File
- `config/__init__.py`

### Required changes
- Change motor count from `36` to `64`
- Add explicit geometry constants:
  - `NUM_ROWS = 8`
  - `NUM_COLS = 8`
  - `NUM_MOTORS = 64`
  - `NUM_PICOS = 8`
  - `MOTORS_PER_PICO = 8`
- Recalculate shared memory size for 64 channels
- Disable or remove any single-motor test default for production work
- Replace old quadrant map with the 8-block Pico map from `mapping-spec.md`
- Keep update rate and PWM defaults initially unless testing proves otherwise

### Notes
- Use one canonical mapping source in config rather than duplicating ordering logic in multiple files.

---

## 2. Hardware Interface Layer

### File
- `src/hardware/interface.py`

### Required changes
- Replace the 36-motor `PHYSICAL_MOTOR_ORDER` with the 64-motor remap from `mapping-spec.md`
- Update all comments and packet documentation from 36-byte frame to 64-byte frame
- Update code paths that assume 4 Picos to support 8 Picos
- Preserve the existing byte encoding model unless testing suggests a better one:
  - 0 -> idle/stop
  - 1..255 -> active PWM range

### Validation tasks
- Verify packet ordering with a dry-run test vector
- Verify each packet byte range maps to the intended Pico block
- Confirm left-half and right-half block ordering matches actual wiring

---

## 3. Flight Loop

### File
- `src/core/flight_loop.py`

### Required changes
- Ensure all arrays and log outputs scale to 64 motors
- Confirm shared memory and logging headers use `NUM_MOTORS`
- Keep safety clamp and slew limiting intact
- Validate 400 Hz timing with 64 outputs and real hardware enabled

### Validation tasks
- Measure loop timing jitter on the Pi 5
- Confirm the 64-byte transmit + sync model stays well inside the loop period
- Confirm logging overhead does not destabilize timing

---

## 4. Signal Generation

### Files
- `src/physics/signal_designer.py`
- any signal reconstruction helper classes

### Required changes
- Mostly parameter scaling only
- Ensure all APIs accept `n_motors=64`
- Keep group-based pattern generation flexible for 8x8 selectors

### Opportunity improvements
- Add convenience generators for:
  - row sweep
  - column sweep
  - quadrant pulse
  - left/right half
  - traveling wave across rows or columns

---

## 5. GUI Layer

### Files
- `gui_interface.py`
- any GUI helper modules if later split out

### Required changes
- Expand grid visualization from 6x6 to 8x8
- Replace quadrant assumptions with 8 block-aware grouping tools
- Ensure display labels use human-facing Motor 1-64
- Add quick-select controls for:
  - row
  - column
  - left half
  - right half
  - quadrant
  - Pico block

### Validation tasks
- Confirm clicked cells map to the correct motor labels
- Confirm group assignment exports the right motor sets
- Confirm GUI remains readable with 64 motors

---

## 6. Main Entry / Programmatic Use

### File
- `main.py`

### Required changes
- Replace default examples using 36 motors with 64-motor examples
- Confirm default waveform generation uses `NUM_MOTORS`
- Keep mock mode support for offline development and testing

---

## 7. Pico Firmware

### Files
- `pico/firmware_template.c`
- `pico/build_all_firmware.py`
- `pico/README.md`

### Required changes
- Change from 4 firmware images to 8 firmware images
- Change constants:
  - `MOTORS_PER_PICO = 8`
  - `TOTAL_MOTORS = 64`
  - `FRAME_BYTES = 64`
- Update `MY_START` / `MY_END` slicing for 8-motor windows
- Update pin map to the real pin allocation used for 8 ESC signals per Pico
- Preserve sync interrupt + watchdog structure
- Update comments and docs to reflect 8-Pico architecture

### Validation tasks
- Flash and test one Pico first
- Verify packet slice and PWM output mapping on each firmware image
- Confirm watchdog drops outputs safely on lost sync

---

## 8. Logging and Analysis

### Files
- logging in `src/core/flight_loop.py`
- `tests/` utilities

### Required changes
- Expand CSV columns to 64 motors
- Review analysis scripts for fixed 36-channel assumptions
- Update any plotting code to support 64 channels or grouped plotting

### Opportunity improvements
- Add per-Pico summary views
- Add row/column average traces
- Add left-half / right-half comparison plots

---

## 9. Test Plan for Port Bring-Up

### Stage A - Software only
- Run mock hardware mode
- Verify 8x8 GUI behavior
- Verify packet remap with known test values
- Verify logs align with expected motor ordering

### Stage B - Single Pico block
- Connect one Pico only
- Drive an 8-motor local pattern
- Verify all 8 motors map correctly
- Verify idle behavior and watchdog behavior

### Stage C - Left-half bring-up
- Connect Picos 1-4
- Test uniform and stepped patterns
- Verify block boundaries

### Stage D - Full wall bring-up
- Connect all 8 Picos
- Start at low throttle
- Run uniform, row sweep, column sweep, and block tests
- Confirm synchronization across the wall

### Stage E - Experimental validation
- Compare commanded PWM vs measured RPM
- Measure airflow uniformity and repeatability
- Tune slew limits if needed

---

## 10. Upstream Sync Process

When the German wall repo updates:

1. Pull latest upstream snapshot
2. Review commit diffs
3. Classify changes as:
   - portable directly
   - portable with adaptation
   - irrelevant to 8x8 topology
4. Port only the changes that improve:
   - timing
   - safety
   - protocol robustness
   - signal generation
   - GUI ergonomics
   - telemetry/logging
5. Re-test in mock mode before hardware deployment

## Recommended rule
Do not merge topology-specific upstream changes blindly.
The 8x8 branch should track useful ideas, not inherit 6x6 assumptions by accident.

---

## Immediate Next Tasks

1. Finalize the mapping spec as canonical
2. Build an 8x8 config module
3. Adapt the hardware remap layer
4. Rewrite Pico firmware constants and build process for 8 boards
5. Update GUI to 8x8
6. Run packet-order dry tests
7. Bring up one Pico block before scaling out
