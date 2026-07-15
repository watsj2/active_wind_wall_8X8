# Codex Continue: Coaxial 8x8x2 Windwall

If this terminal/session is restarted, continue work from:

`/home/jwatson/coaxial_8x8x2_windwall_system`

Read:

`/home/jwatson/coaxial_8x8x2_windwall_system/SESSION_HANDOFF_2026-07-08.md`

Then read the latest handoff:

`/home/jwatson/coaxial_8x8x2_windwall_system/SESSION_HANDOFF_2026-07-14.md`

Current status:

- Old 64-motor system hard-saved.
- New Coaxial 8x8x2 / 128-motor project created.
- New GUI exists, dark mode, mock-safe only.
- Real hardware output is intentionally disabled.
- Row-major 128-motor physical numbering exists.
- Controller mapping preserves the original 8x8 harness where practical:
  `C01-C08` old harness, `C09-C16` new infill.
- Desktop PDF wiring assembly manual exists.
- V1 128-motor host-to-controller protocol is now defined.
- Firmware builder generates per-controller host-index tables.
- Next task should be a bench-safe C01 flash/output-order test before flashing
  the rest of the old-harness and infill controllers.
