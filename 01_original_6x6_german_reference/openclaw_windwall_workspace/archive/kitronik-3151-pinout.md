# Kitronik 3151 / 5348 Pinout Notes for Windwall

## Board identity

- Product family referenced by user: **Kitronik 3151**
- Local datasheet filename: `5348-simply-robotics-board-raspberry-pi-pico-datasheet.pdf`
- Board shown in photos: **Kitronik Simply Robotics Motor Driver Board for Raspberry Pi Pico**

## Servo output mapping

The local datasheet confirms the servo outputs map to Pico GPIO as follows:

| Servo channel | Pico GPIO |
|---|---:|
| 0 | 15 |
| 1 | 14 |
| 2 | 13 |
| 3 | 12 |
| 4 | 19 |
| 5 | 18 |
| 6 | 17 |
| 7 | 16 |

This is the key mapping for Windwall ESC signal control.

Recommended firmware output pin array:

```c
static const uint MOTOR_PINS[8] = {15, 14, 13, 12, 19, 18, 17, 16};
```

## Built-in brushed motor driver mapping

The datasheet also lists the onboard H-bridge motor outputs:

- Motor 1: GPIO 2 + GPIO 5
- Motor 2: GPIO 4 + GPIO 3
- Motor 3: GPIO 6 + GPIO 9
- Motor 4: GPIO 8 + GPIO 7

These are less important for Windwall if ESC control is done through the 8 servo outputs.

## Board characteristics relevant to Windwall

- 8 servo outputs with SIG / V+ / GND
- 4 terminal-block motor outputs for brushed motor drive
- extra GPIO breakout pads
- power input via terminal block
- onboard regulation supplying the Pico

## Windwall firmware implication

For Windwall's 8-board / 64-motor architecture, the Kitronik servo outputs should be treated as the ESC signal channels.

Per-board channel order should be:
- local channel 0 -> first motor in that board's 2x4 block
- local channel 1 -> second motor
- ...
- local channel 7 -> eighth motor

## Source

Extracted from:
- `/home/jwatson/Downloads/5348-simply-robotics-board-raspberry-pi-pico-datasheet.pdf`

Relevant text from datasheet:
- `GPIO Pins: 15,14,13,12,19,18,17,16 for Servo 0 to Servo 7 in order`
