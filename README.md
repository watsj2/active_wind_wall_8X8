# Windwall Complete Project Archive

This repository is a shareable archive of the windwall work from the original
6x6 German wall reference through the active 8x8 wall and the coaxial 8x8x2
work completed on July 14-15, 2026.

## Folder Map

```text
01_original_6x6_german_reference/
  Original German-wall reference notes, upstream-derived files, Pico firmware
  notes, mapping specs, and inertial windwall PDFs.

02_active_8x8_windwall/
  current/
    Current active 8x8 windwall project, including source, GUI, config,
    Pico firmware, diagnostics, and current CSV logs.

  snapshots/
    Saved source snapshots from earlier working states, including the
    pre-coaxial hard save and the "working, no tach 2026-05-05" snapshot.

03_coaxial_8x8x2_windwall/
  current/
    Current clean coaxial 8x8x2 project, including the 128-motor model,
    row-major/harness-preserving controller mapping, color Pico mapping image,
    C01-C16 UF2 firmware, host protocol docs, GUI, and scripts.

04_session_notes/
  Desktop notes, launchers, handoff files, and a copy of the latest color
  Pico/controller mapping image.

git_bundles/
  Git bundle exports for preserving source history when available.
```

## Current Coaxial Mapping

The latest 8x8x2 mapping uses row-major pixel numbering:

```text
P01-P08  -> row 1, left to right
P09-P16  -> row 2, left to right
...
P57-P64  -> row 8, left to right
```

Controller mapping preserves the original 8x8 harness where practical:

- `C01-C08` reuse the old 8x8 harness controllers.
- `C09-C16` are new infill controllers.
- Each controller has 8 PWM channels.
- Channel-to-Pico pin mapping is `CH1=GP0`, `CH2=GP1`, through `CH8=GP7`.
- The firmware images `firmware_c01.uf2` through `firmware_c16.uf2` match this
  mapping and were flashed to Picos 1-16.

Primary mapping files:

```text
03_coaxial_8x8x2_windwall/current/docs/coaxial_8x8x2_pico_mapping.png
03_coaxial_8x8x2_windwall/current/docs/MOTOR_CONTROLLER_MAPPING.md
03_coaxial_8x8x2_windwall/current/config/motor_controller_mapping.csv
```

## What Was Excluded

This archive intentionally excludes machine-local or rebuildable files:

- Python virtual environments
- `.git` internals from nested projects
- `.agents` and `.codex` runtime metadata
- Python caches
- CMake/Pico build directories
- compiled intermediate files such as `.elf`, `.bin`, `.hex`, `.map`, `.dis`

The current 8x8 CSV logs are included because they are part of the experimental
record and are below GitHub's single-file size limit.

## Existing Upstream Reference

The German 6x6 reference notes identify the upstream source as:

```text
https://github.com/kowshiksri/active_wind_wall
```

The active 8x8 project also had its own Git remote:

```text
git@github.com:watsj2/active_wind_wall_8X8.git
```

This archive is separate so one GitHub link can contain the 6x6 reference
material, the 8x8 work, and the 8x8x2 coaxial work together.
