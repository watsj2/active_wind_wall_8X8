# Harness-Preserving Wiring Plan

This file replaces the older layer-first plane-split wiring draft. The current
goal is to reuse the original 8x8 harness wherever possible and add new Pico
controllers only for the missing middle positions.

The canonical generated mapping is:

```text
docs/MOTOR_CONTROLLER_MAPPING.md
config/motor_controller_mapping.csv
```

The PDF wiring manual has not been regenerated for this mapping yet.

## Motor Numbering

Wind-pixel labels are row-major from the operator/front view:

```text
P01-P08  -> R1, left to right
P09-P16  -> R2, left to right
P17-P24  -> R3, left to right
...
P57-P64  -> R8, left to right
```

Each wind pixel has two motor outputs:

```text
Fxx -> front motor / Pichler XQ-45 ESC
Bxx -> back motor / T-MOTOR AIR 40 ESC
```

Host frame order remains layer-first:

```text
0-63    -> F01-F64
64-127  -> B01-B64
```

## Controller Roles

`C01-C08` reuse the original 8x8 harness. Adjacent legacy outputs are treated
as one coaxial front/back pair.

`C09-C16` are new infill controllers for the middle positions that the old
harness does not cover cleanly.

Every controller still has eight local outputs:

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

## Old-Harness Controllers

```text
C01 -> P01, P04, P09, P12
C02 -> P17, P20, P25, P28
C03 -> P33, P36, P41, P44
C04 -> P49, P52, P57, P60
C05 -> P05, P08, P13, P16
C06 -> P21, P24, P29, P32
C07 -> P37, P40, P45, P48
C08 -> P53, P56, P61, P64
```

Example C01 channel order:

```text
C01 CH1 / GP0 -> F01
C01 CH2 / GP1 -> B01
C01 CH3 / GP2 -> F04
C01 CH4 / GP3 -> B04
C01 CH5 / GP4 -> F09
C01 CH6 / GP5 -> B09
C01 CH7 / GP6 -> F12
C01 CH8 / GP7 -> B12
```

## New-Infill Controllers

```text
C09 -> P02, P03, P10, P11
C10 -> P18, P19, P26, P27
C11 -> P34, P35, P42, P43
C12 -> P50, P51, P58, P59
C13 -> P06, P07, P14, P15
C14 -> P22, P23, P30, P31
C15 -> P38, P39, P46, P47
C16 -> P54, P55, P62, P63
```

Example C09 channel order:

```text
C09 CH1 / GP0 -> F02
C09 CH2 / GP1 -> B02
C09 CH3 / GP2 -> F03
C09 CH4 / GP3 -> B03
C09 CH5 / GP4 -> F10
C09 CH6 / GP5 -> B10
C09 CH7 / GP6 -> F11
C09 CH8 / GP7 -> B11
```

## Firmware Implication

The firmware must use the generated per-controller `HOST_INDICES` table. Do not
derive ownership from `controller_id * 8`.

Build all firmware:

```bash
cd /home/jwatson/coaxial_8x8x2_windwall_system
python3 pico/build_all_firmware.py
```

Bench-test C01 first with live ESC loads disconnected. Confirm the C01 channel
order above before flashing the remaining controllers.

## Wiring Safety

- ESC BEC/red wires remain disconnected and insulated.
- Pi/Pico/controller power remains separate from ESC BEC outputs.
- Control ground and ESC signal ground must share a deliberate common
  reference.
- Do not connect the full ESC load until one controller has proven frame
  validation, sync latch, watchdog idle, and channel ordering.
