# Coaxial 8x8x2 Windwall Handoff - 2026-07-21

## Latest Hardware Result

The user initially reported that only C01, C03, and C04 were working. A loose
`GP16` / SPI MOSI wire feeding the P33-P64 side was then found and corrected.
After that correction, these physical controllers were reported working before
the subsequent mistaken C02 reflash:

```text
C01
C03
C04
C05
C06
C07
C08
```

C02 and C09-C16 remained reported not working after the wiring correction. The
Pico presented as physical C02 was subsequently flashed with
`firmware_c02.uf2`, but the functional test proved that this USB/BOOTSEL board
actually drives the physical C04 output harness. The same board, physically
labeled 02 and identified in BOOTSEL as serial `5D0AF10E890A0474`, was then
restored with `firmware_c04.uf2`; its post-restore functional result is pending.
Do not count physical C02 as reflashed. The C05-C08 recovery proves that their
earlier failure was caused by the loose MOSI feed rather than their firmware
images or host-index mappings.

Latest result: the user now reports that all controllers C01-C08 are working,
but C02 and C04 remain mixed up. This supersedes the earlier "C02 not working"
status. The previously observed label-02-to-C04-harness relationship remains
consistent with a crossed C02/C04 label, harness, or firmware identity.

All C01-C16 controllers had previously completed their matching UF2 copy and
reboot sequence. The latest functional result supersedes the verification
status in `SESSION_HANDOFF_2026-07-20.md`, but does not change the approved
controller mapping, compiled `HOST_INDICES`, or firmware images.

## Known Working Evidence

- C01 was previously reported working.
- C03 was previously confirmed by the successful P20 test.
- C04 was reported working on 2026-07-21 before its controller was mistakenly
  reflashed with the C02 image. The same board was restored with
  `pico/firmware_c04.uf2`, SHA-256
  `e3ee3f1870d282c02f729706c136f242ea08340a3a9942a9382fc14db7cc40a9`.
  Its RP2350 BOOTSEL volume disappeared after the copy, indicating the expected
  reboot. The later report that C01-C08 all work confirms that the restored C04
  path is functional, although C02/C04 identity remains crossed.
- C05-C08 began working after a loose `GP16` / SPI MOSI wire feeding the
  P33-P64 side was found and corrected on 2026-07-21.
- A board believed to be C02 was flashed on 2026-07-21 with
  `pico/firmware_c02.uf2`. The transfer/reboot succeeded, but the saved GUI
  selection and physical response prove this was the board driving C04:

  ```text
  selected P09  -> physical P25 ran (CH1/CH2)
  selected P12  -> physical P28 ran (CH3/CH4)
  selected P13  -> physical P29 ran (CH5/CH6)
  selected P16  -> physical P32 ran (CH7/CH8)
  ```

  The exact channel-preserving correspondence proves C02 firmware is currently
  on the C04-connected board, or equivalently that the board/USB label is wrong.
  Because C04 worked before this flash, mistaken board identification is the
  leading explanation. The user's latest report says both C02 and C04 now
  function but remain mixed up.
- BOOTSEL identity notes:

  ```text
  physical label 02 / drives C04 harness -> serial 5D0AF10E890A0474
  physical label 04 / harness role unknown -> serial 755F04F32D54ABCA
  ```

  The board labeled 04 was accidentally placed in BOOTSEL but no file was
  copied to it during that event. The latest report is consistent with labels
  02 and 04 being crossed, but a two-command test must distinguish swapped
  stickers from swapped logical responses before another flash.
- C09-C16 remain reported not working; their precise symptoms have not yet
  been separated into the common infill-bus feed, ESC arming, or power-path
  categories.

## AIR 40 Wiring Result

The resolved AIR 40 throttle-plug result remains valid:

```text
AIR 40 black  -> controller/harness ground (XQ-45 black position)
AIR 40 yellow -> controller PWM output (XQ-45 white position)
```

The prior F20 substitution test showed that the channel worked with an XQ-45,
failed with an incorrectly pinned AIR 40, and worked again with the XQ-45.
Reversing the AIR 40 black/yellow terminals made that AIR 40 work. Do not
change C03 mapping or global PWM endpoints for that resolved symptom.

## Software State

- The 266-byte `CW` full-wall protocol is unchanged.
- The approved harness-preserving C01-C16 mapping is unchanged.
- Matching C01-C16 firmware images remain built.
- Constant mode exposes direct PWM entry in microseconds, capped by the
  selected Experiment output ceiling.
- The saved GUI runtime preset was modified on 2026-07-21 and currently assigns
  both layers of P09, P12, P13, and P16 to one Constant group at `1200 us`.
  This saved state corroborates the mistaken C02-on-C04 result above.

## Next Safe Step

Resolve C02/C04 identity before another flash. In a controlled test, command
only P09 and record the physical output, then command only P25 and record the
physical output. If each correct motor runs, only the board stickers are
crossed and they should be relabeled without reflashing. If the two physical
outputs exchange commands, the firmware/harness identities are crossed and
must be corrected deliberately. Because all C09-C16 remain out, check the
common infill-bus MOSI feed first, then clock, CE0, sync, and ground, comparing
against a working controller with no live load. Do not mass-reflash or command
all 128 motors based on the current evidence.
