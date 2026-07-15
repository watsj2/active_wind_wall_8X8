# Active Wind Wall Handoff - 2026-05-04

## Current Situation

Physical Pico 5 is connected and was being used to test Motor 34.

The motors are safe/idle. Pico 5 is now flashed with normal motor-control firmware from `pico/firmware_pico4.uf2`. The CE0 wiring fix was verified before flashing, and a short all-idle SPI/GPIO command test completed in REAL hardware mode after flashing.

As of `2026-05-07`, physical Picos 1-8 have been flashed with the corrected tach-capable firmware. The GUI still defaults to `No Tach / Legacy`, so it continues to send the working 64-byte motor frames unless `Tach Return` is selected.

## Main Finding

The motor path works, but the Pi-to-Pico SPI command path failed because the SPI chip-select wire is on the wrong Pico pin.

Evidence from the wire-map diagnostic:

- Pi SCLK reaches Pico `GP18`.
- Pi MOSI reaches Pico `GP16`.
- Pi CE0 is not reaching Pico `GP17`.
- CE0 activity appears on Pico `GP19` instead.
- Pi GPIO22 sync reaches Pico `GP22`.

Conclusion: move the CE0 wire from Pico `GP19` to Pico `GP17`.

## Latest Resume Check

Checked again on `2026-05-04 14:05 CST` with the `pico5_wire_report` diagnostic still flashed.

Result from coordinated serial/SPI test:

- SPI test sent `1907` transfers.
- `GP16` showed MOSI activity.
- `GP18` showed SCLK activity.
- `GP17` stayed at `0` edges.
- `GP19` still showed CE0-like activity.

Conclusion: the CE0 wire has not been corrected yet, or it is still electrically connected to Pico `GP19`. Do not flash normal motor-control firmware until CE0 activity appears on `GP17` and no longer appears on `GP19`.

## CE0 Rewire Verified

Checked again on `2026-05-04 14:15 CST` after moving CE0.

Result from coordinated serial/SPI test:

- SPI test sent `1899` transfers.
- `GP16` showed MOSI activity.
- `GP18` showed SCLK activity.
- `GP17` showed CE0 activity, ending at about `1901` rising / `1900` falling edges.
- `GP19` retained its previous cumulative count but did not increase during the test.

Conclusion: the CE0 wire is now on Pico `GP17` as expected. It is OK to flash normal Pico 5 motor-control firmware next.

## Pico 5 Normal Firmware Flashed

Flashed at `2026-05-04 14:20 CST`:

- Copied `pico/firmware_pico4.uf2` to `/media/jwatson/RP2350/`.
- Ran `sync`.
- RP2350 bootloader drive disconnected afterward, as expected.
- Ran a short all-idle SPI/GPIO verification with `python3`.
- `HardwareInterface(use_mock=False)` initialized in `REAL` mode and sent idle frames without errors.

Normal Pico 5 motor-control firmware is now flashed. Next step is a cautious Motor 34 spin test when the physical setup is clear.

## Motor 34 Cautious Spin Test

Tested at `2026-05-04 14:22 CST`:

- Used Motor 34, zero-based index `33`.
- Armed all motors at idle / `1000us` for `3s`.
- Ran Motor 34 at `1200us` for `5s`.
- Sent all motors idle afterward.
- `HardwareInterface(use_mock=False)` initialized in `REAL` mode and completed without software errors.
- Physical observation: Motor 34 did not spin.

## Motor 34 Stronger Spin Test

Tested at `2026-05-04 14:29 CST`:

- Used Motor 34, zero-based index `33`.
- Armed all motors at idle / `1000us` for `3s`.
- Ran Motor 34 at `1600us` for `3s`.
- Sent all motors idle afterward.
- `HardwareInterface(use_mock=False)` initialized in `REAL` mode and completed without software errors.
- Physical observation: Motor 34 did not spin.

## Pico 5 Output Scan / GUI Run All

Checked at `2026-05-04 14:34 CST`:

- User clarified that only Motors 33-40 are connected, all on Pico 5.
- A previous Motor 1 control test is invalid for this physical setup because Motor 1 is not connected.
- GUI "Run All" created a log commanding all 64 motors around `1575-1750us`.
- User observed that none of the connected Motors 33-40 spun.
- A terminal scan of GUI Motors 33-40 / Pico 5 local GP0-GP7 at `1600us` completed with no software errors and final idle command.

Next diagnostic should prove the Pico 5 output side directly. Preferred: flash `diagnostics/pico5/pico5_comm_report.uf2`, command Motor 34, and read USB serial to confirm received frame byte and sync count. If the diagnostic reports Motor 34 commands but the motor still does not spin, focus on ESC power/arming, signal-wire placement/orientation, common ground, or the ESC/motor itself.

## Pico 5 Comm Report Diagnostic Flashed

Flashed at `2026-05-04 14:44 CST`:

- Copied `diagnostics/pico5/pico5_comm_report.uf2` to the RP2350 bootloader drive.
- Ran `sync`.
- RP2350 bootloader drive disconnected afterward, as expected.
- `/dev/ttyACM0` appeared afterward, indicating the diagnostic USB serial is available.
- The follow-up Motor 34 command/readback test was interrupted before it ran.
- Current firmware on Pico 5 is `pico5_comm_report`, not normal `firmware_pico4.uf2`.
- GUI was still running as `python3 gui_interface.py` when checked.

## Root Cause Found: SPI Frame Overrun

Found at `2026-05-04 14:48 CST` with Pico 5 running `pico5_comm_report`:

- With the newer host code that sent one 64-byte SPI transfer per frame, Pico 5 saw sync pulses but only about one SPI byte per sync.
- During Motor 34 active command, the diagnostic kept reporting `m34_byte=0`.
- This means Pico 5 was not receiving the Motor 34 byte; the Pico polling loop was likely losing most bytes from the SPI RX FIFO during the fast 64-byte burst.
- Restored `src/hardware/interface.py` to send SPI one byte at a time with pacing, matching the earlier bench-test behavior.
- Retested Motor 34 at `1600us`.
- Comm-report then showed `m34_byte=128` during the active period and `m34_byte=0` after idle.

Conclusion: the no-spin issue from Pi/GUI commands was caused by the host SPI frame-transfer change. The fix is to keep byte-paced SPI sends unless the Pico firmware is rewritten to use IRQ/DMA or a larger receive strategy.

## Normal Firmware Restored After SPI Fix

Completed at `2026-05-04 14:52 CST`:

- User observed that Motor 34 ran during the `pico5_comm_report` retest after the SPI pacing fix.
- Flashed normal Pico 5 firmware `pico/firmware_pico4.uf2` again.
- RP2350 bootloader drive disconnected afterward, as expected.
- Ran normal-firmware Motor 34 test with fixed byte-paced host SPI:
  - Armed all motors at `1000us` for `3s`.
  - Ran Motor 34 at `1600us` for `4s`.
  - Sent final all-idle frames.
- `HardwareInterface(use_mock=False)` initialized in `REAL` mode and completed without software errors.
- User observed Motor 34 spun during the normal-firmware test.
- `python3 -m py_compile src/hardware/interface.py gui_interface.py config/__init__.py` passed afterward.
- User then confirmed the GUI path is working to spin motors at `2026-05-04 14:55 CST`.

## Pico 6 Firmware Flashed

Completed at `2026-05-05 10:04 CST`:

- User put Pico 6 into BOOTSEL mode.
- RP2350 bootloader drive mounted at `/media/jwatson/RP2350`.
- Expected firmware for physical Pico 6 is `pico/firmware_pico5.uf2` (`PICO_ID=5`).
- `firmware_pico5.uf2` was missing, so it was built locally from `firmware_pico5.c`.
- Full all-board build failed because the SDK tried to fetch `picotool` from GitHub and DNS/network was unavailable.
- Workaround used: build `firmware_pico5.bin` with `PICO_NO_PICOTOOL=1`, then wrap it into UF2 using the same RP2350 UF2 layout/family IDs from the working `firmware_pico4.uf2`.
- Copied `pico/firmware_pico5.uf2` to `/media/jwatson/RP2350/` and ran `sync`.
- RP2350 bootloader drive disconnected afterward, as expected.

## Pico 7 Firmware Flashed

Completed at `2026-05-05 10:25 CST`:

- User put Pico 7 into BOOTSEL mode.
- RP2350 bootloader drive mounted at `/media/jwatson/RP2350`.
- Expected firmware for physical Pico 7 is `pico/firmware_pico6.uf2` (`PICO_ID=6`).
- `firmware_pico6.uf2` was missing, so it was built locally from `firmware_pico6.c`.
- Workaround used: build `firmware_pico6.bin` with `PICO_NO_PICOTOOL=1`, then wrap it into UF2 using the same RP2350 UF2 layout/family IDs from the working `firmware_pico4.uf2`.
- Copied `pico/firmware_pico6.uf2` to `/media/jwatson/RP2350/` and ran `sync`.
- RP2350 bootloader drive disconnected afterward, as expected.

## Pico 8 Firmware Flashed

Completed at `2026-05-05 10:39 CST`:

- User put Pico 8 into BOOTSEL mode.
- RP2350 bootloader drive mounted at `/media/jwatson/RP2350`.
- Expected firmware for physical Pico 8 is `pico/firmware_pico7.uf2` (`PICO_ID=7`).
- `firmware_pico7.uf2` was missing, so it was built locally from `firmware_pico7.c`.
- Workaround used: build `firmware_pico7.bin` with `PICO_NO_PICOTOOL=1`, then wrap it into UF2 using the same RP2350 UF2 layout/family IDs from the working `firmware_pico4.uf2`.
- Copied `pico/firmware_pico7.uf2` to `/media/jwatson/RP2350/` and ran `sync`.
- RP2350 bootloader drive disconnected afterward, as expected.

## Working No-Tach Snapshot

Completed at `2026-05-05 15:56 CST`:

- Saved the current working no-tach setup to `/home/jwatson/Desktop/working, no tach 2026-05-05/`.
- The snapshot includes a full copy of `active_wind_wall_8X8`, the Desktop GUI launcher, the Desktop notes launcher, and `Wind Wall Session Notes.md`.
- The snapshot represents the last known working GUI/SPI motor-control path before tach-return development.

## Tach-Return Development Path

Completed at `2026-05-05 16:00 CST`:

- Added tach-return protocol constants to `config/__init__.py`.
- Expanded shared memory so the control process publishes both PWM commands and tach Hz.
- Added Pi-side tach polling in `src/hardware/interface.py`.
- Added tach logging in `src/core/flight_loop.py`.
- Updated `gui_interface.py` with:
  - Tach Return / No Tach Legacy telemetry mode.
  - PWM speed-range presets for full experiments.
  - PWM preset choices for single-motor tests.
  - Live monitor signal selection: PWM, Tach Hz, Tach RPM.
- Rebuilt all eight tach-capable Pico UF2 files:
  - `pico/firmware_pico0.uf2`
  - `pico/firmware_pico1.uf2`
  - `pico/firmware_pico2.uf2`
  - `pico/firmware_pico3.uf2`
  - `pico/firmware_pico4.uf2`
  - `pico/firmware_pico5.uf2`
  - `pico/firmware_pico6.uf2`
  - `pico/firmware_pico7.uf2`
- Python compile check passed for config, GUI, hardware interface, control loop, and builder.
- Short GUI launch smoke test produced no startup errors before timeout.

New tach firmware behavior:

- PWM outputs remain on Pico `GP0-GP7`.
- Tach inputs are Pico `GP8-GP15`, one tach input per local motor.
- Pico `GP19` / physical pin `25` is now SPI MISO for tach readback.
- MISO is tri-stated by default. Only the addressed Pico enables MISO during its tach response.
- The host sends 68-byte tach-v1 frames: 4-byte header plus 64 motor bytes.
- Tach response is 40 bytes: magic, version, Pico ID, sequence, sample time, and 8 edge-count deltas.
- All non-addressed Picos ignore the 40-byte response clock window so the next command frame stays aligned.

Tach wiring plan per Pico:

- Local tach 1 -> Pico `GP8` / physical pin `11`
- Local tach 2 -> Pico `GP9` / physical pin `12`
- Local tach 3 -> Pico `GP10` / physical pin `14`
- Local tach 4 -> Pico `GP11` / physical pin `15`
- Local tach 5 -> Pico `GP12` / physical pin `16`
- Local tach 6 -> Pico `GP13` / physical pin `17`
- Local tach 7 -> Pico `GP14` / physical pin `19`
- Local tach 8 -> Pico `GP15` / physical pin `20`
- Pi `GPIO9` / physical pin `21` MISO -> Pico `GP19` / physical pin `25` on each Pico
- Keep Pi/Pico/ESC grounds common.
- Tach inputs must be 3.3V-safe. The firmware enables Pico internal pullups on tach pins, which suits open-collector/open-drain tach outputs if the voltage level is safe.

Important transition note:

- The active project now defaults the GUI telemetry mode to `Tach Return`.
- Motors require the new tach-capable Pico firmware when the GUI is in Tach Return mode.
- To run the old motor-only firmware from the active code, choose `No Tach / Legacy` in the GUI.
- The saved Desktop snapshot remains the clean working no-tach fallback.

## GUI Visual Refresh

Completed at `2026-05-05 16:20 CST`:

- Refreshed `gui_interface.py` toward the WindShape/WindControl style:
  - Cleaner top command bar.
  - Central `Wind Pixel Wall` view.
  - PWM legend beside the motor grid.
  - Modern card, input, button, and status styling.
  - Updated live plot styling and color-coded PWM/Tach display modes.
- Hardware control paths were not changed by this visual pass.
- `python3 -m py_compile gui_interface.py` passed.
- Short GUI launch smoke test produced no startup errors before timeout.

Expanded at `2026-05-05 16:30 CST`:

- Added dashboard metric cards for wind-pixel count, active pixels, PWM range, and telemetry mode.
- Added live heatmap rendering on the wind-pixel wall for PWM, Tach Hz, and Tach RPM modes.
- Group list entries now show pixel counts and signal type.
- Tightened the profile editor into a property-panel layout.
- Added subtle card shadows and refined dashboard spacing.
- `python3 -m py_compile gui_interface.py` passed.
- Short GUI launch smoke test produced no startup errors before timeout.

Corrected at `2026-05-06` after field test:

- The GUI default telemetry mode is now `No Tach / Legacy`.
- `config.TACH_ENABLED` is now `False` so the default host packet is the known-working 64-byte motor frame.
- `Tach Return` remains selectable, but should only be used after tach-capable firmware is flashed.
- Disabled expensive Qt drop-shadow effects.
- Disabled continuous 64-button live heatmap repainting during runs.
- Reduced GUI monitor update rate from 40 Hz to 10 Hz; the hardware control loop remains 400 Hz.
- Verified default `HardwareInterface(use_mock=True)` builds a 64-byte packet.
- `python3 -m py_compile config/__init__.py gui_interface.py src/hardware/interface.py src/core/flight_loop.py` passed.
- Short GUI launch smoke test produced no startup errors before timeout.

Layout corrected at `2026-05-06`:

- Reduced default window geometry to `1280x760`.
- Moved the right-side `Run`, `Motor Test`, and `Calibrate` controls into tabs so the control panel fits on one page.
- Kept status and Start/Stop buttons visible outside the tabs.
- `python3 -m py_compile gui_interface.py` passed.
- Short GUI launch smoke test produced no startup errors before timeout.

Dark mode applied at `2026-05-06`:

- Converted the active GUI stylesheet to a dark palette.
- Darkened motor-grid idle cells, tabs, lists, tables, inputs, checkboxes, status labels, and live plot background/axes.
- Kept `No Tach / Legacy` as the default telemetry mode.
- Verified default host packet remains 64 bytes.
- `python3 -m py_compile gui_interface.py` passed.
- Short GUI launch smoke test produced no startup errors before timeout.

## Pico 1 Tach Firmware Flashed

Completed at `2026-05-06`:

- User put physical Pico 1 into BOOTSEL.
- Initially copied active tach `pico/firmware_pico0.uf2`, but the bootloader stayed mounted; inspection showed the UF2 wrapper had app blocks numbered as one combined sequence instead of the RP2350 boot-block/app-block layout used by known-good UF2s.
- Fixed `pico/build_all_firmware.py` so wrapped UF2s preserve a separate RP2350 boot/picobin block and number app-family blocks from zero.
- Rebuilt all eight tach-capable UF2 files.
- Verified `pico/firmware_pico0.uf2` now has:
  - boot block family `0xe48bff57`, block `0/2`
  - app family `0xe48bff59`, blocks `0..48/49`
- Copied corrected tach-capable `pico/firmware_pico0.uf2` to Pico 1 bootloader drive and ran `sync`.
- RP2350 disappeared from `lsblk` afterward, indicating the Pico accepted the UF2 and rebooted.
- Cleared stale mount entry with `sudo umount /home/jwatson/rp2350_mount`.

Pico 1 now has tach-capable firmware. The firmware still accepts the GUI's default `No Tach / Legacy` 64-byte motor frames, and also supports `Tach Return` mode when the MISO/tach wiring is present.

## Pico 2 Tach Firmware Flashed

Completed at `2026-05-07`:

- User put physical Pico 2 into BOOTSEL.
- Flashed corrected tach-capable `pico/firmware_pico1.uf2`.
- RP2350 disappeared from `lsblk` after copy and `sync`, indicating the Pico accepted the UF2 and rebooted.
- Physical Pico 2 maps to GUI motors 9-16.

## Pico 3 Tach Firmware Flashed

Completed at `2026-05-07`:

- User put physical Pico 3 into BOOTSEL.
- Flashed corrected tach-capable `pico/firmware_pico2.uf2`.
- RP2350 disappeared from `lsblk` after copy and `sync`, indicating the Pico accepted the UF2 and rebooted.
- Physical Pico 3 maps to GUI motors 17-24.

## Pico 4 Tach Firmware Flashed

Completed at `2026-05-07`:

- User put physical Pico 4 into BOOTSEL.
- Flashed corrected tach-capable `pico/firmware_pico3.uf2`.
- RP2350 disappeared from `lsblk` after copy and `sync`, indicating the Pico accepted the UF2 and rebooted.
- Physical Pico 4 maps to GUI motors 25-32.

## Pico 5 Tach Firmware Flashed

Completed at `2026-05-07`:

- User put physical Pico 5 into BOOTSEL.
- Flashed corrected tach-capable `pico/firmware_pico4.uf2`.
- RP2350 disappeared from `lsblk` after copy and `sync`, indicating the Pico accepted the UF2 and rebooted.
- Physical Pico 5 maps to GUI motors 33-40.

## Pico 6 Tach Firmware Flashed

Completed at `2026-05-07`:

- User put physical Pico 6 into BOOTSEL.
- Flashed corrected tach-capable `pico/firmware_pico5.uf2`.
- RP2350 disappeared from `lsblk` after copy and `sync`, indicating the Pico accepted the UF2 and rebooted.
- Physical Pico 6 maps to GUI motors 41-48.

## Pico 7 Tach Firmware Flashed

Completed at `2026-05-07`:

- User put physical Pico 7 into BOOTSEL.
- Flashed corrected tach-capable `pico/firmware_pico6.uf2`.
- RP2350 disappeared from `lsblk` after copy and `sync`, indicating the Pico accepted the UF2 and rebooted.
- Physical Pico 7 maps to GUI motors 49-56.

## Pico 8 Tach Firmware Flashed

Completed at `2026-05-07`:

- User put physical Pico 8 into BOOTSEL.
- Flashed corrected tach-capable `pico/firmware_pico7.uf2`.
- RP2350 disappeared from `lsblk` after copy and `sync`, indicating the Pico accepted the UF2 and rebooted.
- Physical Pico 8 maps to GUI motors 57-64.

## GUI Status

Checked at `2026-05-04 14:24 CST`:

- `python3` has the required GUI and hardware modules.
- `gui_interface.py`, `src/hardware/interface.py`, and `config/__init__.py` compile cleanly.
- The Desktop launcher previously pointed at missing `./venv/bin/python`.
- Updated `Active Wind Wall GUI.desktop` to launch with `python3`.
- A 4-second GUI launch test produced no startup errors and exited only because of the timeout.

## Correct Wiring For Pico 5

Use these physical pins:

- `Pi physical 19 / GPIO10 / MOSI` -> `Pico physical 21 / GP16`
- `Pi physical 23 / GPIO11 / SCLK` -> `Pico physical 24 / GP18`
- `Pi physical 24 / GPIO8 / CE0` -> `Pico physical 22 / GP17`
- `Pi physical 15 / GPIO22 / sync` -> `Pico physical 29 / GP22`
- Common ground connected

Do not connect Pi CE0 to `Pico physical 25 / GP19`. GP19 is MISO/TX and is unused.

## Next Step After Reboot

1. Move the Pi CE0 wire to Pico physical pin `22` / `GP17`.
2. Start Codex again in `/home/jwatson/active_wind_wall_8X8`.
3. Tell Codex: "continue from SESSION_HANDOFF_2026-05-04.md".
4. Rerun the wire-map diagnostic before flashing normal firmware.

Expected after the CE0 fix:

- During SPI traffic, `GP17` should show edge counts.
- `GP16` and `GP18` should still show edge counts.
- `GP19` should no longer show CE0-like activity.

## Important Files Preserved

Diagnostic files were copied out of `/tmp` into:

`/home/jwatson/active_wind_wall_8X8/diagnostics/pico5/`

Preserved UF2s:

- `pico5_wire_report.uf2`
- `pico5_comm_report.uf2`
- `pico5_spi_nosync_diag.uf2`
- `pico5_pwm_idle.uf2`
- `pico5_pwm_diag.uf2`

Preserved sources:

- `wire_report.c`
- `comm_report.c`
- `spi_nosync_diag.c`
- `idle_pwm.c`
- `standalone_pwm_test.c`

## Repo State

Repo was reset earlier to commit `6b4d4c8` from Apr 8, then these local changes were intentionally re-added:

- `config/__init__.py`: restored quadrant GUI motor layout.
- `gui_interface.py`: restored Motor Test section, 1-based labels, GUI XCB launch fix.
- `src/hardware/interface.py`: restored legacy `gpiod` support and changed SPI sending to one 64-byte frame per transfer.

Current uncommitted/generated files include:

- Modified `config/__init__.py`
- Modified `gui_interface.py`
- Modified `src/hardware/interface.py`
- Generated `pico/firmware_pico4.uf2`
- Generated `pico/CMakeLists.txt`
- New `diagnostics/pico5/` diagnostic archive

## Useful Commands

Read wire diagnostic serial:

```bash
python3 -c "import os, time, select; fd=os.open('/dev/ttyACM0', os.O_RDWR|os.O_NOCTTY|os.O_NONBLOCK); end=time.time()+12; buf=b''; print('reading'); \
while time.time()<end: \
    r,_,_=select.select([fd], [], [], 0.25); \
    data=os.read(fd,4096) if fd in r else b''; \
    print(data.decode('utf-8','replace'), end='') if data else None; \
os.close(fd)"
```

Send SPI edge-test pattern:

```bash
python3 -c "import time, spidev; spi=spidev.SpiDev(); spi.open(0,0); spi.max_speed_hz=1000000; spi.mode=0; pattern=[0xAA,0x55]*32; end=time.time()+4; \
while time.time()<end: spi.xfer2(pattern); time.sleep(0.0025); \
spi.close()"
```

Flash normal firmware to physical Pico 5 after wiring is fixed:

```bash
sudo mount -o remount,rw /media/jwatson/RP2350
cp /home/jwatson/active_wind_wall_8X8/pico/firmware_pico4.uf2 /media/jwatson/RP2350/
sync
```

Motor 34 mapping:

- GUI Motor 34 is zero-based motor index `33`.
- Physical Pico 5 uses firmware file `firmware_pico4.uf2`.
- Motor 34 is Pico local GP1, physical Pico pin `2`.
