# Coaxial 8x8x2 Windwall System

Clean-start control system for a coaxial 8x8 wind wall with two motors per
wind pixel.

## System Shape

- Grid: 8 rows x 8 columns
- Coaxial layers: 2
- Wind pixels: 64
- Motors: 128
- Initial controller assumption: 16 controllers x 8 motor outputs

The project is intentionally separate from the older `active_wind_wall_8X8`
system. The old system was hard-saved before this project was created.

## Current Status

This is the first clean baseline:

- New project files
- New 128-motor addressing model
- New mock-safe hardware interface
- New PyQt6 GUI for the coaxial grid
- Dark-mode operator interface
- Explicit PWM range and preset controls
- Timed test runner with entered PWM speed and duration
- Editable wind-pixel groups with front/back/both layer scope
- Saved preset tests as reusable 128-motor PWM frames
- Lightweight painted pixel bars tuned for Raspberry Pi use
- No inherited telemetry, Testo map, or monitor complexity

Real motor output is disabled in this baseline until the 128-motor hardware
protocol is designed and verified.

## GUI Tools

- `Command`: build direct PWM commands from profiles, PWM ranges, presets, and
  selected pixels.
- `Groups`: create named pixel groups, choose whether they target front, back,
  or both coaxial layers, then apply the current PWM to that group.
- `Tests`: apply built-in tests or save the current 128-motor frame as a named
  preset test. Enter `Test Speed PWM` and `Duration`, then run a timed test that
  idles automatically when the timer expires.

User-created groups and saved tests are stored in `config/gui_presets.json`.

## Display Performance

The GUI does not use 128 live progress-bar widgets for the pixel wall. Each
pixel is a lightweight painted cell with two drawn bars. Motor commands can run
at the configured command rate, while the visual grid is throttled by
`GUI_REFRESH_HZ` in `config/__init__.py`. This is intended to keep the Pi 5 UI
responsive even while speeds change.

## Run

```bash
cd /home/jwatson/coaxial_8x8x2_windwall_system
python3 main.py
```

or:

```bash
./scripts/launch_gui.sh
```

## Verification

```bash
python3 -m py_compile main.py config/__init__.py coaxial_windwall/*.py coaxial_windwall/*/*.py
python3 main.py --smoke-test
```

## Design Rule

Core motor control comes first. Telemetry, Testo mapping, and advanced monitor
views should only move into the main GUI after each has a small standalone test
that proves the data path is accurate and useful.
