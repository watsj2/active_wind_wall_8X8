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

Wind-pixel labels follow the original 8x8 Pico blocks from the operator/front
view:

```text
R1 -> P01, P02, P03, P04, P33, P34, P35, P36
R2 -> P05, P06, P07, P08, P37, P38, P39, P40
R3 -> P09, P10, P11, P12, P41, P42, P43, P44
R4 -> P13, P14, P15, P16, P45, P46, P47, P48
R5 -> P17, P18, P19, P20, P49, P50, P51, P52
R6 -> P21, P22, P23, P24, P53, P54, P55, P56
R7 -> P25, P26, P27, P28, P57, P58, P59, P60
R8 -> P29, P30, P31, P32, P61, P62, P63, P64
```

Each wind pixel has two motor outputs:

```text
Fxx -> front motor / Pichler QX-45 ESC
Bxx -> back motor / Pichler QX-45 ESC
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
C01 -> P01, P04, P05, P08
C02 -> P09, P12, P13, P16
C03 -> P17, P20, P21, P24
C04 -> P25, P28, P29, P32
C05 -> P33, P36, P37, P40
C06 -> P41, P44, P45, P48
C07 -> P49, P52, P53, P56
C08 -> P57, P60, P61, P64
```

Example C01 channel order:

```text
C01 CH1 / GP0 -> F01
C01 CH2 / GP1 -> B01
C01 CH3 / GP2 -> F04
C01 CH4 / GP3 -> B04
C01 CH5 / GP4 -> F05
C01 CH6 / GP5 -> B05
C01 CH7 / GP6 -> F08
C01 CH8 / GP7 -> B08
```

## New-Infill Controllers

```text
C09 -> P02, P03, P06, P07
C10 -> P10, P11, P14, P15
C11 -> P18, P19, P22, P23
C12 -> P26, P27, P30, P31
C13 -> P34, P35, P38, P39
C14 -> P42, P43, P46, P47
C15 -> P50, P51, P54, P55
C16 -> P58, P59, P62, P63
```

Example C09 channel order:

```text
C09 CH1 / GP0 -> F02
C09 CH2 / GP1 -> B02
C09 CH3 / GP2 -> F03
C09 CH4 / GP3 -> B03
C09 CH5 / GP4 -> F06
C09 CH6 / GP5 -> B06
C09 CH7 / GP6 -> F07
C09 CH8 / GP7 -> B07
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
