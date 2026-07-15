# Windwall Kitronik Comms + Sync Pin Plan v1

## Purpose

This document defines the first concrete communication pin plan for the Windwall 8x8 controller architecture using Kitronik 3151 boards.

It exists because the German wall communication pin choices conflict with the Kitronik board's servo output pins.

---

## Constraints

### Reserved for ESC/PWM outputs

The Kitronik 3151 servo outputs already occupy:

| Local channel | Pico GPIO |
|---|---:|
| 0 | 15 |
| 1 | 14 |
| 2 | 13 |
| 3 | 12 |
| 4 | 19 |
| 5 | 18 |
| 6 | 17 |
| 7 | 16 |

These pins are reserved for Windwall ESC signal output and must **not** be reused for communications.

### German wall pins that no longer work here

The German wall firmware used:
- MOSI = GPIO 16
- SCK = GPIO 18
- CS = GPIO 17
- SYNC = GPIO 22

This is incompatible with Kitronik because GPIO 16, 17, and 18 are already needed for PWM outputs.

---

## Recommended architecture

Preserve the German wall control concept:

- one Raspberry Pi master
- all Pico boards receive the same full command stream
- each Pico keeps only its own 8-byte slice
- one separate sync/latch line triggers atomic output update across all boards
- watchdog returns all outputs to idle if sync is lost

Do **not** preserve the German wall GPIO assignment.

---

## Pin plan v1

### PWM outputs (fixed)

```c
static const uint MOTOR_PINS[8] = {15, 14, 13, 12, 19, 18, 17, 16};
```

### Sync line

Use:
- **GPIO 22** = global sync/latch input

Reason:
- matches prior design concept
- appears available on the Kitronik board breakout
- clean separation from PWM outputs

### Comms candidate pins

Use these as the initial safe communications pool:
- **GPIO 21**
- **GPIO 26**
- **GPIO 27**
- **GPIO 28**

These are preferred because they do not overlap with the Kitronik servo output bank.

---

## Preferred protocol shape

### Recommended protocol

Use a **shared receive bus + sync line**.

Meaning:
- Pi transmits one 64-byte command frame
- all Pico boards receive it
- each Pico extracts its own 8-byte byte range by firmware ID
- Pi then toggles the sync line
- all Picos update outputs simultaneously

This keeps the most valuable part of the German wall architecture while adapting it to the Kitronik hardware.

---

## Provisional board-side signal roles

### Required per board

Each Kitronik/Pico board should ultimately need:
- 8 PWM outputs (already fixed)
- 1 data input
- 1 clock input or serial receive line
- 1 sync input
- optional board identity mechanism if not compiled per-board

### Strong recommendation

Continue generating **separate per-board firmware images**:
- `firmware_pico0.uf2`
- `firmware_pico1.uf2`
- ...
- `firmware_pico7.uf2`

That avoids needing extra board-ID straps and simplifies the hardware.

---

## Two viable implementation options

## Option A - Broadcast SPI-style receive + sync (preferred)

Use a shared serial receive scheme similar to the German wall:
- one shared data line
- one shared clock line
- one shared sync line
- each board reads the full frame and keeps only its own slice

### Suggested starting pins
- data in: **GPIO 21**
- clock in: **GPIO 26**
- sync in: **GPIO 22**

### Notes
- exact hardware-SPI feasibility on those pins still needs validation against RP2040/RP2350 peripheral routing
- if hardware SPI slave on those exact pins is awkward, software receive or PIO-backed receive may be used instead

## Option B - Simpler serial framing + sync

Use:
- one shared serial receive line
- one sync line
- frame parsing in firmware

### Suggested starting pins
- serial RX / data in: **GPIO 21**
- sync in: **GPIO 22**

### Notes
- easier to reassign if SPI peripheral mapping becomes annoying
- less elegant than true broadcast SPI but still workable

---

## Current recommendation

### Use Option A as the architectural target
because it preserves the German wall timing model best.

### Use Option B if hardware pin muxing or slave-mode implementation becomes too annoying
because reliability matters more than ideological purity.

---

## What is decided now

- keep **8 motors per Pico**
- keep **8 Pico boards**
- keep **64-byte full-frame control**
- keep **global sync/latch**
- reserve GPIO **12-19** exclusively for ESC outputs
- reserve GPIO **22** for sync
- reserve GPIO **21/26/27/28** as communications candidates

---

## What still needs validation

1. Best exact receive method on the Pico:
   - hardware SPI slave
   - PIO-based serial receive
   - UART-style custom framing

2. Which of GPIO 21/26/27/28 are most convenient in the real wiring layout

3. Whether additional pull-ups/pull-downs or signal conditioning are needed for long wire runs

---

## Immediate next step

Write the first Windwall firmware template against this plan using:
- fixed PWM output array for Kitronik
- fixed sync pin on GPIO 22
- provisional communications abstraction that can be switched between SPI-like and simpler serial receive if needed
