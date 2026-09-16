# Coaxial 8x8x2 Windwall Handoff - 2026-07-19

## Current Status

- The v1 host protocol remains the 266-byte full-wall `CW` broadcast defined
  in `docs/HOST_CONTROLLER_PROTOCOL.md`.
- The harness-preserving C01-C16 mapping and generated firmware images are
  unchanged from the 2026-07-14 handoff.
- Software verification on 2026-07-19 passed all 12 unit tests and the
  generated mapping check.
- A live attempt made before this handoff selected `P13` and `P17` on both
  layers. Those channels map to C02 and C03, not C01, and did not respond.
  Installed firmware on C02 and C03 is not known or queryable by protocol v1.

## C01 Flash Completed

Physical C01 was put into RP2350 BOOTSEL mode and flashed on 2026-07-19 with:

```text
pico/firmware_c01.uf2
SHA-256 bc75d1c1746c08ac0d424221fefe734af88f3008d888f30923839eaea899700c
RP2350 USB serial F68B8438147951D7
```

The compiled C01 identity and mapping were verified before copying:

```text
CONTROLLER_ID 0
HOST_INDICES 0, 64, 3, 67, 4, 68, 7, 71
CH1-CH8 F01, B01, F04, B04, F05, B05, F08, B08
```

The BOOTSEL mass-storage device disconnected immediately after the UF2 copy,
which is the expected flash/reboot behavior. Codex did not send any SPI motor
commands during the flash. Afterward, the user reported that "pico one
worked." This establishes a user-observed functional response from physical
C01, but the exact channels, PWM measurements, ESC/motor conditions, idle
behavior, and watchdog behavior were not reported. Do not treat this as an
instrumented verification of all eight C01 outputs.

## C02 Flash Completed

Physical C02 was put into RP2350 BOOTSEL mode and flashed on 2026-07-19 with:

```text
pico/firmware_c02.uf2
SHA-256 d60b4d377de78bc0df0f3fcb77601be0e5b42991cf6745791559bb936ed0c3a9
RP2350 USB serial 5D0AF10E890A0474
```

The compiled C02 identity and mapping were verified before copying:

```text
CONTROLLER_ID 1
HOST_INDICES 8, 72, 11, 75, 12, 76, 15, 79
CH1-CH8 F09, B09, F12, B12, F13, B13, F16, B16
```

The BOOTSEL device disconnected after the copy as expected. No SPI motor
command was sent and C02 has not yet been functionally tested.

## C03 Flash Completed With Kernel Warning

Physical C03 was put into RP2350 BOOTSEL mode and flashed on 2026-07-19 with:

```text
pico/firmware_c03.uf2
SHA-256 ec54e72b3892b07daf194ce4fcd989e07820314c5c18e860d07b0790a23f5a5a
RP2350 USB serial DD70280A88C6ED69
```

The compiled C03 identity and mapping were verified before copying:

```text
CONTROLLER_ID 2
HOST_INDICES 16, 80, 19, 83, 20, 84, 23, 87
CH1-CH8 F17, B17, F20, B20, F21, B21, F24, B24
```

The BOOTSEL device disconnected after consuming the UF2, which is the normal
flash/reboot behavior. Linux then reported one `lost async page write` for the
disappearing virtual FAT volume. This is consistent with delayed filesystem
bookkeeping after the RP2350 reboot, but C03 must be treated as provisionally
flashed until a low-output functional test confirms it. No SPI motor command
was sent during the flash.

The subsequent P17 test did not work. The saved GUI session was inspected and
confirmed that the host-side setup was correct:

```text
assigned motors 16 and 80 = F17 and B17
signal type Constant
constant_pwm_us 1400
controller C03 CH1/CH2
```

This rules out an incorrect grid selection or normalized-PWM conversion. It
does not yet distinguish a failed/incomplete C03 flash from missing C03 logic
power, local signal wiring, or a shared SPI/sync connection fault.

The user then reported that P20 worked. P20 is also owned by C03 (CH3/CH4), so
this functionally confirms that C03 flashed, booted, and receives the shared
host frame. Do not reflash C03. The remaining fault is local to P17/C03
CH1-CH2, layer/ESC behavior, or its wiring.

The latest saved GUI session was no longer an isolated test: Group 1 contained
32 motor indices spanning 16 front/back pairs and requested `1150 us`. Clear
the group before drawing conclusions from the next physical test.

The user later reported another unsuccessful P17 test. The saved session at
that point contained exactly motor indices `16` and `80` at `1400 us`, meaning
F17 and B17 were still commanded together. A front-only/back-only result was
not obtained. Because P20 works on the same C03 firmware, the next diagnostic
boundary is C03 CH1/CH2 and the local P17 wiring/ESC path versus known-working
C03 CH3/CH4; do not reflash C03 again.

## Exact Constant PWM Restored

The group signal panel once again provides a direct `Constant PWM` spin box in
microseconds when the signal type is `Constant`:

- accepted entry range: `1000-2000 us`;
- the selected Experiment output ceiling remains a hard cap;
- existing presets without the new field migrate their old constant fraction
  to the equivalent direct PWM value;
- the direct value is saved in group/session JSON as `constant_pwm_us`.

Verification completed after this GUI change:

```text
16 unit tests passed
mapping generation check passed
mock/offscreen GUI smoke test passed
```

## Next Safe Step

Before expanding beyond C01, retain the following verification targets:

1. With controller power only, verify all C01 outputs are `1000 us` at 50 Hz.
2. Verify unarmed/invalid/no-command behavior remains at `1000 us`.
3. Send a bench command with only one channel above idle and confirm the other
   seven remain at `1000 us`.
4. Confirm channel order:
   `F01`, `B01`, `F04`, `B04`, `F05`, `B05`, `F08`, `B08`.

C03 is functionally confirmed by the user's successful P20 observation. To
isolate P17 without commanding the current 32-motor group:

1. Disarm and clear Group 1.
2. Select `Front only`, assign only P17, and test F17/C03 CH1.
3. Stop/disarm and clear the group.
4. Select `Back only`, assign only P17, and test B17/C03 CH2.
5. If only the AIR 40 side fails, inspect that ESC's main power, signal ground,
   signal lead, arming tones/status, and throttle requirements.

Do not flash or test multiple additional controllers at once.
