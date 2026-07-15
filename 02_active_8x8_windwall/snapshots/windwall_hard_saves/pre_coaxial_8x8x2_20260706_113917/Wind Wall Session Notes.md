# Wind Wall Session Notes

## Current State

- Project path: `/home/jwatson/active_wind_wall_8X8`
- Latest detailed handoff: `/home/jwatson/active_wind_wall_8X8/SESSION_HANDOFF_2026-05-04.md`
- Working no-tach snapshot saved on `2026-05-05 15:56 CST`: `/home/jwatson/Desktop/working, no tach 2026-05-05/`
- Active project now contains the tach-return development path.
- Tach-capable UF2s rebuilt on `2026-05-05`: `pico/firmware_pico0.uf2` through `pico/firmware_pico7.uf2`.
- Active GUI now has `Tach Return` and `No Tach / Legacy` telemetry modes, live monitor choices for PWM/Tach Hz/Tach RPM, experiment PWM speed presets, and motor-test PWM presets.
- Latest check on `2026-05-04 14:22 CST`: Pico 5 CE0 rewire verified, normal firmware `pico/firmware_pico4.uf2` flashed, all-idle SPI/GPIO send completed in REAL mode, and Motor 34 test ran at `1200us` for `5s` with final idle command.
- Motor 34 stronger test on `2026-05-04 14:29 CST`: ran at `1600us` for `3s` with final idle command.
- User clarified on `2026-05-04 14:34 CST`: only Motors 33-40 are connected on Pico 5. GUI Run All produced commands but none of Motors 33-40 spun. Motor 1 test is invalid for this setup.
- Pico 5 comm-report diagnostic flashed on `2026-05-04 14:44 CST`; follow-up command/readback test was interrupted before it ran. Pico 5 is currently on `pico5_comm_report`, not normal motor firmware.
- Root cause found on `2026-05-04 14:48 CST`: one-shot 64-byte SPI transfers overran Pico polling; Pico saw syncs but not Motor 34 byte. Restored byte-paced SPI sends. Comm-report then showed Motor 34 byte `128` at `1600us` and `0` after idle.
- Normal Pico 5 firmware restored on `2026-05-04 14:52 CST`; normal-firmware Motor 34 test ran at `1600us` for `4s` with fixed byte-paced SPI and final idle command. User observed Motor 34 spun.
- GUI motor spin confirmed working on `2026-05-04 14:55 CST`.
- Pico 6 flashed on `2026-05-05 10:04 CST` with `pico/firmware_pico5.uf2`. Firmware was generated locally via `.bin` build plus UF2 wrapping because `picotool` was unavailable and network/DNS prevented fetching it.
- Pico 7 flashed on `2026-05-05 10:25 CST` with `pico/firmware_pico6.uf2`. Firmware was generated locally via `.bin` build plus UF2 wrapping.
- Pico 8 flashed on `2026-05-05 10:39 CST` with `pico/firmware_pico7.uf2`. Firmware was generated locally via `.bin` build plus UF2 wrapping.
- GUI launcher fixed on `2026-05-04 14:24 CST`: Desktop launcher now uses `python3`; launch test showed no startup errors.
- Desktop launcher for GUI: `Active Wind Wall GUI.desktop`
- GUI launches the current `gui_interface.py` from the project folder
- GUI display labels now show motors as `1-64`
- Pico 1 wiring and control path were verified working

## Verified Working

- `Pico 1`, `Motor 1`, `1200us`, `10s` from terminal
- GUI sine function works
- Desktop GUI launcher works

## Firmware

- Pico 1 was flashed with `pico/firmware_pico0.uf2`
- PWM timing fix was added to `pico/firmware_template.c`

## Saved Commit

- Commit: `6b4d4c8`
- Message: `Fix Pico PWM timing for ESC control`

## Important Wiring

- Pi `19` -> Pico `21` (`GP16`)
- Pi `24` -> Pico `22` (`GP17`)
- Pi `23` -> Pico `24` (`GP18`)
- Pi `15` -> Pico `29` (`GP22`)
- Pi `GND` -> Pico `GND`
- ESC signal for Motor 1 -> Pico `1` (`GP0`)
- ESC ground -> Pico `GND`

## Useful Commands

Launch GUI:

```bash
cd /home/jwatson/active_wind_wall_8X8
PYTHONPATH=/home/jwatson/active_wind_wall_8X8/venv/lib/python3.11/site-packages:/usr/lib/python3/dist-packages:/usr/lib/python3.11/dist-packages QT_QPA_PLATFORM=xcb python3 gui_interface.py
```

Run Pico 1 Motor 1 at 1200us for 10s:

```bash
cd /home/jwatson/active_wind_wall_8X8
python3 - <<'PY'
import time
import numpy as np
from src.hardware.interface import HardwareInterface
from config import NUM_MOTORS

pwm = np.full(NUM_MOTORS, 1000.0)
pwm[0] = 1200.0

hw = HardwareInterface(use_mock=False)
start = time.perf_counter()
try:
    while time.perf_counter() - start < 10.0:
        hw.send_pwm(pwm)
        time.sleep(0.0025)
finally:
    hw.send_pwm(np.full(NUM_MOTORS, 1000.0))
    hw.close()
PY
```
