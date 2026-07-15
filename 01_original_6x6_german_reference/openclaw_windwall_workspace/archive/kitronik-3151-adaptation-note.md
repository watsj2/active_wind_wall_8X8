# Kitronik 3151 Adaptation Note

## Purpose

This note records the current hardware baseline for the Windwall controller boards and supersedes earlier uncertainty about whether each board exposed 4, 6, or 8 usable control channels.

## Confirmed board identity

The controller board in use is:

- **Kitronik 3151**
- **Simply Robotics Motor Driver Board for Raspberry Pi Pico**

Photos provided by the user show a Pico mounted on the Kitronik board and an 8-channel servo-style output bank labeled:

- `0`
- `1`
- `2`
- `3`
- `4`
- `5`
- `6`
- `7`

Each channel exposes:
- `SIG`
- `V+`
- `GND`

## Current working conclusion

For Windwall planning purposes, treat each Kitronik 3151 board as providing:

- **8 usable PWM/servo-style output channels**
- one channel per ESC signal input
- one board per 8-motor controller region

This restores the earlier 8-board architecture as the most likely correct implementation path:

- **8 boards**
- **8 signal outputs per board**
- **64 total motors**

## Windwall controller topology

The intended board-to-wall mapping remains:

| Board / Pico | Rows | Columns | Motors |
|---|---:|---:|---|
| Pico 1 | 1-2 | 1-4 | 1, 2, 3, 4, 9, 10, 11, 12 |
| Pico 2 | 3-4 | 1-4 | 17, 18, 19, 20, 25, 26, 27, 28 |
| Pico 3 | 5-6 | 1-4 | 33, 34, 35, 36, 41, 42, 43, 44 |
| Pico 4 | 7-8 | 1-4 | 49, 50, 51, 52, 57, 58, 59, 60 |
| Pico 5 | 1-2 | 5-8 | 5, 6, 7, 8, 13, 14, 15, 16 |
| Pico 6 | 3-4 | 5-8 | 21, 22, 23, 24, 29, 30, 31, 32 |
| Pico 7 | 5-6 | 5-8 | 37, 38, 39, 40, 45, 46, 47, 48 |
| Pico 8 | 7-8 | 5-8 | 53, 54, 55, 56, 61, 62, 63, 64 |

## Confirmed Kitronik servo-channel GPIO mapping

The datasheet saved locally in Downloads confirms the 8 servo outputs are mapped as follows:

| Kitronik channel | Pico GPIO |
|---|---:|
| 0 | 15 |
| 1 | 14 |
| 2 | 13 |
| 3 | 12 |
| 4 | 19 |
| 5 | 18 |
| 6 | 17 |
| 7 | 16 |

Source used: `/home/jwatson/Downloads/5348-simply-robotics-board-raspberry-pi-pico-datasheet.pdf`

## Important follow-up detail

The board also uses Pico GPIO for the built-in brushed motor outputs:

- Motor 1: GPIO 2 + GPIO 5
- Motor 2: GPIO 4 + GPIO 3
- Motor 3: GPIO 6 + GPIO 9
- Motor 4: GPIO 8 + GPIO 7

For Windwall purposes, the important part is the confirmed servo/ESC signal mapping above.

## Why this matters

The German wall firmware assumes a simple hardcoded direct pin array for output channels.
The Windwall firmware should instead target the **real Kitronik 3151 pin routing**, not guess or inherit the upstream 6x6 pin assumptions.

## Practical development rule

Until official documentation or a verified pin map is obtained:

- proceed with protocol, mapping, and architecture work assuming **8 channels per board**
- do **not** finalize production firmware pin assignments
- keep the output pin list as an explicit configurable array in the firmware template

## Immediate next tasks

1. Obtain official Kitronik 3151 documentation or pin map
2. Confirm channel `0..7` to Pico GPIO mapping
3. Confirm any conflicts with SPI or sync pin usage
4. Draft Windwall-specific firmware template for 8 boards x 8 channels
5. Build test UF2 images only after pin mapping is verified

## Notes

The board identity and 8-channel output bank are now considered the strongest hardware evidence available and should guide the next implementation steps.
