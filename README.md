# Windwall Complete Project Archive

This repository is a shareable archive of the windwall work from the original
6x6 German wall reference through the active 8x8 wall and the coaxial 8x8x2
work initially archived on July 14-15, 2026, with the coaxial project updated
through September 16, 2026.

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

## Current Coaxial Snapshot — September 16, 2026

The current 8x8x2 source, GUI, C01–C16 firmware images, bench diagnostics,
mapping, and session handoffs are in [the coaxial project](03_coaxial_8x8x2_windwall/current/README.md).
Physical pair labels are 01–32 on the left and 33–64 on the right, with two
motors per pair. C01 owns pairs 01/04/05/08. The generated controller mapping
is authoritative; controller ownership is not contiguous.

All 51 hardware-free tests and the generated mapping check pass. The latest
hardware diagnosis is September 15: C01 idle PWM works, but its response to a
1200 us command remains unresolved. The oscilloscope SCLK observation is pending.
See the [latest handoff](03_coaxial_8x8x2_windwall/current/SESSION_HANDOFF.md).
The GUI opens real hardware transport; these software checks used injected
no-output transports. No hardware was operated for this archive update.

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
