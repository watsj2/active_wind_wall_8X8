# Windwall 8x8 Pico Firmware Plan v1

## Purpose

Adapt the German wall Pico firmware concept from:
- 4 boards
- 9 motors per board
- 36-byte frame

to the Windwall 8x8 architecture:
- 8 boards
- 8 motors per board
- 64-byte frame

## Preserve from German Wall

Keep these design ideas:
- one firmware template with per-board ID substitution
- Pi broadcasts the full command frame to all Picos
- each Pico extracts only its own byte range
- one sync pulse latches all outputs at once
- watchdog returns outputs to idle on communication loss
- simple byte-to-PWM conversion on the Pico side

## New Windwall firmware constants

Recommended constants for the 8x8 design:

- `MOTORS_PER_PICO = 8`
- `TOTAL_MOTORS = 64`
- `FRAME_BYTES = 64`
- `NUM_BOARDS = 8`

Per-board slice logic:
- `MY_START = PICO_ID * MOTORS_PER_PICO`
- `MY_END = MY_START + MOTORS_PER_PICO`

## Human board labels vs firmware IDs

Human labels:
- Pico 1-8

Firmware IDs:
- 0-7

Mapping:
- Pico 1 -> firmware ID 0
- Pico 2 -> firmware ID 1
- Pico 3 -> firmware ID 2
- Pico 4 -> firmware ID 3
- Pico 5 -> firmware ID 4
- Pico 6 -> firmware ID 5
- Pico 7 -> firmware ID 6
- Pico 8 -> firmware ID 7

## Local motor ownership per Pico

Each Pico controls 8 motors in a 2-row x 4-column block.

- Pico 1: Motors 1, 2, 3, 4, 9, 10, 11, 12
- Pico 2: Motors 17, 18, 19, 20, 25, 26, 27, 28
- Pico 3: Motors 33, 34, 35, 36, 41, 42, 43, 44
- Pico 4: Motors 49, 50, 51, 52, 57, 58, 59, 60
- Pico 5: Motors 5, 6, 7, 8, 13, 14, 15, 16
- Pico 6: Motors 21, 22, 23, 24, 29, 30, 31, 32
- Pico 7: Motors 37, 38, 39, 40, 45, 46, 47, 48
- Pico 8: Motors 53, 54, 55, 56, 61, 62, 63, 64

## Packet assumptions

The Pi should transmit a 64-byte frame using the packet order defined in `mapping-spec.md`.
That packet order groups bytes by Pico ownership so each Pico can read a contiguous 8-byte slice.

## Firmware behavior

### Startup
- initialize LED
- initialize 8 PWM outputs
- set all outputs to idle
- initialize SPI in slave mode
- initialize sync input pin with rising-edge interrupt

### Runtime loop
1. Read incoming SPI bytes continuously
2. Increment frame byte index
3. Store only bytes within this Pico's owned byte range
4. On sync pulse:
   - latch the latest 8 bytes into the active buffer
   - convert values to PWM pulse widths
   - update all 8 outputs atomically
   - reset byte index for next frame
5. If sync is missing beyond watchdog timeout:
   - set all outputs to idle
   - blink status LED in fault pattern

## PWM byte encoding

Carry forward the German wall encoding unless testing suggests otherwise:
- `0` -> idle / stop command -> 1000 us
- `1..255` -> active command range mapped to roughly 1200..2000 us

This is acceptable for initial bring-up because it keeps the protocol simple and already matches the upstream concept.

## Open implementation questions

These must be confirmed before final firmware generation:

1. **Confirmed Pico GPIO mapping for Kitronik 3151 output channels 0-7**
   - Channel 0 -> GPIO 15
   - Channel 1 -> GPIO 14
   - Channel 2 -> GPIO 13
   - Channel 3 -> GPIO 12
   - Channel 4 -> GPIO 19
   - Channel 5 -> GPIO 18
   - Channel 6 -> GPIO 17
   - Channel 7 -> GPIO 16
   - Source: local datasheet `/home/jwatson/Downloads/5348-simply-robotics-board-raspberry-pi-pico-datasheet.pdf`

2. **Is the SPI pinout the same on every board?**
   - MOSI
   - SCK
   - CS
   - sync input

3. **Is GPIO 22 still the intended sync pin for all boards?**

4. **Do you want identical firmware behavior on all 8 boards except board ID?**
   - This is preferred.

5. **Do you need any onboard telemetry or USB serial debugging enabled?**
   - Initial answer should probably be no.

## Build system adaptation

The German wall build script currently generates 4 firmware files.
For Windwall it should generate 8:

- `firmware_pico0.uf2`
- `firmware_pico1.uf2`
- `firmware_pico2.uf2`
- `firmware_pico3.uf2`
- `firmware_pico4.uf2`
- `firmware_pico5.uf2`
- `firmware_pico6.uf2`
- `firmware_pico7.uf2`

## Safe bring-up sequence

1. Build 8-board firmware set
2. Flash one test Pico only
3. Verify it boots and holds outputs at idle
4. Verify sync watchdog behavior
5. Verify one controlled byte slice drives the expected 8 channels
6. Only then replicate to the remaining boards

## Immediate next tasks

1. Verify Pi toolchain readiness for Pico builds
2. Confirm actual 8-pin output list for one Pico board
3. Draft Windwall-specific firmware template
4. Adapt build script from 4 boards to 8 boards
5. Build test UF2s locally
