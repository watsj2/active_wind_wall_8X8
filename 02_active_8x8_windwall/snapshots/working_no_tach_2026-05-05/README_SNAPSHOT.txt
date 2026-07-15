Working, no tach snapshot
Date: 2026-05-05

This folder preserves the active wind wall state before tach-return development.

Included:
- active_wind_wall_8X8: full project copy, including GUI, firmware, diagnostics, logs, and notes.
- Active Wind Wall GUI.desktop: Desktop launcher copy.
- Resume Wind Wall Notes.desktop: Desktop notes launcher copy.
- Wind Wall Session Notes.md: Desktop session notes copy.

Known working state:
- GUI motor command path works with the current no-tach SPI broadcast firmware.
- Pico 5 / firmware_pico4.uf2 was verified with Motor 34.
- Picos 6-8 were flashed with firmware_pico5.uf2, firmware_pico6.uf2, and firmware_pico7.uf2.
- Tach return is not integrated in this snapshot.
