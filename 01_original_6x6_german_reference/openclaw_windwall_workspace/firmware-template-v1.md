# Windwall Firmware Template v1 Plan

## Goal

Create the first Windwall-specific Pico firmware template for:
- 8 Pico boards
- 8 ESC outputs per board
- Kitronik 3151 servo-channel GPIO mapping
- 64-byte command frame
- synchronized updates via a dedicated sync pin

This is the first practical firmware target after the design/spec stage.

---

## What this firmware must do

Each Pico should:
1. initialize 8 PWM outputs on Kitronik servo GPIOs
2. receive a full wall command frame from the Pi
3. keep only its own 8-byte slice
4. wait for a sync pulse
5. latch and apply all 8 outputs at once
6. idle all outputs if sync disappears for too long

---

## Fixed hardware assumptions

### Board identity
- one firmware image per board
- firmware IDs: `0..7`
- human Pico labels: `1..8`

### PWM output pins
```c
static const uint MOTOR_PINS[8] = {15, 14, 13, 12, 19, 18, 17, 16};
```

### Frame sizing
- `MOTORS_PER_PICO = 8`
- `TOTAL_MOTORS = 64`
- `FRAME_BYTES = 64`

### Byte slicing
```c
#define MY_START (PICO_ID * MOTORS_PER_PICO)
#define MY_END   (MY_START + MOTORS_PER_PICO)
```

### Sync line
- `SYNC_PIN = 22`

### Watchdog
- if sync is absent for >200 ms, set all outputs to idle

---

## Open technical choice for v1

The only unresolved implementation detail is the receive mechanism.

### Candidate A
**SPI-like shared receive + sync**
- preferred architectural target
- closest to German wall

### Candidate B
**Simpler shared serial/custom receive + sync**
- acceptable fallback if SPI slave pin/routing becomes ugly

To avoid blocking implementation, the firmware template should isolate receive logic behind a small interface.

---

## Proposed firmware structure

### 1. Configuration block
Contains:
- board ID
- motor pin array
- frame constants
- sync pin
- receive pin definitions
- watchdog timeout

### 2. Output control block
Functions:
- `set_motor_pwm_us()`
- `set_all_idle()`
- `apply_active_frame()`

### 3. Receive buffer block
Buffers:
- `incoming_values[8]`
- `active_frame_buffer[8]`
- `byte_index`
- receive state flags

### 4. Sync interrupt block
Responsibilities:
- mark sync pulse received
- update watchdog timer
- trigger atomic application of latest buffered commands
- optionally blink status LED

### 5. Main loop
Responsibilities:
- continuously ingest incoming frame bytes
- store only bytes in this board's slice
- on sync, latch values and update PWM outputs
- if watchdog timeout occurs, idle all outputs

---

## PWM command mapping

Carry over the German wall byte encoding:
- `0` -> idle -> `1000 us`
- `1..255` -> active command range -> approximately `1200..2000 us`

Reason:
- simple
- already validated conceptually upstream
- easy to generate from the Pi side

---

## Local channel order

Per board, local output channel order should follow Kitronik channel order directly:

| Local output | GPIO |
|---|---:|
| 0 | 15 |
| 1 | 14 |
| 2 | 13 |
| 3 | 12 |
| 4 | 19 |
| 5 | 18 |
| 6 | 17 |
| 7 | 16 |

This should map to the board's assigned 8 motors in the packet order already defined in `mapping-spec.md`.

---

## First implementation target

For v1, the first code draft should:
- compile for all 8 board IDs
- set up PWM outputs correctly for Kitronik
- preserve the sync/watchdog model
- leave receive backend implementation replaceable

That means we can write the firmware skeleton now even before the final receive backend is fully chosen.

---

## Build outputs expected

The adapted build script should generate:
- `firmware_pico0.uf2`
- `firmware_pico1.uf2`
- `firmware_pico2.uf2`
- `firmware_pico3.uf2`
- `firmware_pico4.uf2`
- `firmware_pico5.uf2`
- `firmware_pico6.uf2`
- `firmware_pico7.uf2`

---

## Immediate next coding tasks

1. Create Windwall `firmware_template.c`
2. Update build script from 4 boards to 8 boards
3. Replace German motor pins with Kitronik motor pins
4. Replace 36-byte assumptions with 64-byte assumptions
5. Keep sync + watchdog logic
6. Add a provisional receive abstraction so backend can be swapped if needed
