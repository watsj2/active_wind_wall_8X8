# Host-to-Controller Protocol v1

This protocol defines the first bench-testable command path for the Coaxial
8x8x2 Windwall. It is for PWM commands only. Tach/readback should be added only
after one controller has been proven with this command frame.

Real wall output remains disabled in the GUI/hardware interface until the Pico
firmware and one-controller bench test are complete.

## Transport

Use a shared SPI command bus plus a separate sync line. The host sends a full
128-motor command frame, then sends one sync pulse. Every controller receives
the same frame and extracts the eight PWM values for its compiled controller
ID.

Host-side SPI writes must stay byte-paced. The older 64-motor system proved
that a fast multi-byte burst can overrun the Pico polling loop.

Recommended wiring:

```text
Pi GPIO10 / MOSI / physical pin 19 -> Pico GP16
Pi GPIO11 / SCLK / physical pin 23 -> Pico GP18
Pi GPIO8  / CE0  / physical pin 24 -> Pico GP17
Pi GPIO22 / sync / physical pin 15 -> Pico GP22
Pi GND                         -> Pico/controller/ESC signal ground reference
```

Reserved for future readback:

```text
Pi GPIO9 / MISO / physical pin 21 -> Pico GP19
```

All 16 controllers use the same local output pin map:

```text
CH1 -> GP0
CH2 -> GP1
CH3 -> GP2
CH4 -> GP3
CH5 -> GP4
CH6 -> GP5
CH7 -> GP6
CH8 -> GP7
```

## Controller IDs

Controller IDs in firmware are zero-based. Physical labels are one-based. The
controller map preserves the old 8x8 harness where possible, so each controller
uses an explicit eight-entry host-index list.

```text
C01 / controller_id 0  old harness  P01, P04, P09, P12
C02 / controller_id 1  old harness  P17, P20, P25, P28
C03 / controller_id 2  old harness  P33, P36, P41, P44
C04 / controller_id 3  old harness  P49, P52, P57, P60
C05 / controller_id 4  old harness  P05, P08, P13, P16
C06 / controller_id 5  old harness  P21, P24, P29, P32
C07 / controller_id 6  old harness  P37, P40, P45, P48
C08 / controller_id 7  old harness  P53, P56, P61, P64
C09 / controller_id 8  new infill   P02, P03, P10, P11
C10 / controller_id 9  new infill   P18, P19, P26, P27
C11 / controller_id 10 new infill   P34, P35, P42, P43
C12 / controller_id 11 new infill   P50, P51, P58, P59
C13 / controller_id 12 new infill   P06, P07, P14, P15
C14 / controller_id 13 new infill   P22, P23, P30, P31
C15 / controller_id 14 new infill   P38, P39, P46, P47
C16 / controller_id 15 new infill   P54, P55, P62, P63
```

For example, `C01` extracts these host indices:

```text
CH1 -> F01 host index 0
CH2 -> B01 host index 64
CH3 -> F04 host index 3
CH4 -> B04 host index 67
CH5 -> F09 host index 8
CH6 -> B09 host index 72
CH7 -> F12 host index 11
CH8 -> B12 host index 75
```

## Frame Format

All multi-byte fields are little-endian.

```text
byte 0       magic[0]      0x43  ASCII "C"
byte 1       magic[1]      0x57  ASCII "W"
byte 2       version       0x01
byte 3       message_type  0x01  PWM_US_BROADCAST
byte 4       flags         bit 0 = output armed
byte 5       sequence      uint8, wraps at 255
bytes 6-7    payload_len   0x0100 = 256 bytes
bytes 8-263  payload       128 x uint16 PWM pulse widths in microseconds
bytes 264-265 crc16        CRC-16/CCITT-FALSE over bytes 0-263
```

Total frame length is 266 bytes.

CRC parameters:

```text
name       CRC-16/CCITT-FALSE
poly       0x1021
init       0xFFFF
xorout     0x0000
reflection false
```

## Payload Order

Payload values are 16-bit PWM pulse widths in microseconds. Valid command range
is `1000-2000`.

The host order is layer-first and row-major within each layer:

```text
host indices 0-63    -> front plane F01-F64
host indices 64-127  -> back plane B01-B64
F01-F08 / B01-B08    -> R1 left-to-right
F09-F16 / B09-B16    -> R2 left-to-right
```

Examples:

```text
F01 -> host index 0   -> payload bytes 8-9
F64 -> host index 63  -> payload bytes 134-135
B01 -> host index 64  -> payload bytes 136-137
B64 -> host index 127 -> payload bytes 262-263
```

Controller extraction examples:

```text
C01 / controller_id 0 reads host indices 0,64,3,67,8,72,11,75
C09 / controller_id 8 reads host indices 1,65,2,66,9,73,10,74
```

## Firmware Latch Rules

Each controller should:

1. Receive bytes into a 266-byte buffer.
2. Wait for the sync rising edge.
3. On sync, validate exact byte count, magic, version, message type, payload
   length, and CRC.
4. If the frame is valid and `flags & 0x01` is set, copy its eight local
   `uint16` PWM values and clamp them to `1000-2000`.
5. If the frame is valid but the output-armed flag is clear, command all eight
   local outputs to idle `1000 us`.
6. If the frame is invalid, command all eight local outputs to idle `1000 us`.
7. Reset the receive buffer for the next frame.

The output PWM signal remains servo-style ESC PWM:

```text
frequency: 50 Hz
idle:     1000 us
maximum:  2000 us
```

The controller watchdog must set all eight local outputs to idle if no valid
frame is latched for `250 ms`.

## Firmware Programming

Every controller uses the same firmware source, with both the compiled
`controller_id` and that controller's eight host indices generated from
`coaxial_windwall/model.py`.

```text
C01 -> controller_id 0  old harness
C09 -> controller_id 8  first new infill controller
```

ESC-specific behavior belongs in calibration tables and operator presets, not
in the frame layout.

## Bench Bring-Up Order

1. Build one firmware image for `C01` and verify the reused old harness first.
2. Flash it with live ESC loads disconnected.
3. Send unarmed valid frames and confirm all local PWM outputs stay at
   `1000 us` on a scope or logic analyzer.
4. Send armed frames with seven channels idle and one channel at a low bench
   value.
5. Confirm byte order by moving the active channel from CH1 through CH8.
6. Repeat for the remaining old-harness controllers, then the new infill
   controllers.

Do not connect the full ESC load until the one-controller test has proven
framing, sync, watchdog idle, and channel ordering.
