# Motor and Controller Mapping

This is the fixed software mapping for the Coaxial 8x8x2 wind wall.
Use this table for physical labels, wiring checks, host command frames,
and future 16-controller firmware generation.

## Mapping Decision

- Layout: row-major pixel numbering with harness-preserving controller grouping.
- Grid orientation: `R1` is top, `C1` is left, viewed from the operator/front side.
- Pair labels: `P01-P64` are row-major from `R1C1` through `R8C8`.
- Motor labels: `F01-F64` are front-layer motors; `B01-B64` are back-layer motors.
- `FP` means the front plane and uses Pichler XQ-45 ESCs in this plan.
- `BP` means the back plane and uses T-MOTOR AIR 40 ESCs in this plan.
- Controller labels: `C01-C16` are physical, one-based labels.
- Controller channels: `CH1-CH8` are physical, one-based labels.
- Host indices: `controller_index` is 0-15; `channel_index` and `host_index` are zero-based.
- Host frame indices `0-63` are front-plane motors; indices `64-127` are back-plane motors.
- Pico PWM pins: `CH1-CH8` map to `GP0-GP7` on each controller.

`C01-C08` reuse the original 8x8 harness outputs. Adjacent legacy
outputs now become one coaxial front/back pair. `C09-C16` are new
infill controllers for the middle columns that are not covered by the
old harness.

## Controller Summary

| Controller | Harness Role | Controller Index | Pixels | Locations | Channels |
| --- | --- | ---: | --- | --- | --- |
| C01 | old harness | 0 | P01, P04, P09, P12 | R1C1, R1C4, R2C1, R2C4 | CH1/GP0=F01, CH2/GP1=B01, CH3/GP2=F04, CH4/GP3=B04, CH5/GP4=F09, CH6/GP5=B09, CH7/GP6=F12, CH8/GP7=B12 |
| C02 | old harness | 1 | P17, P20, P25, P28 | R3C1, R3C4, R4C1, R4C4 | CH1/GP0=F17, CH2/GP1=B17, CH3/GP2=F20, CH4/GP3=B20, CH5/GP4=F25, CH6/GP5=B25, CH7/GP6=F28, CH8/GP7=B28 |
| C03 | old harness | 2 | P33, P36, P41, P44 | R5C1, R5C4, R6C1, R6C4 | CH1/GP0=F33, CH2/GP1=B33, CH3/GP2=F36, CH4/GP3=B36, CH5/GP4=F41, CH6/GP5=B41, CH7/GP6=F44, CH8/GP7=B44 |
| C04 | old harness | 3 | P49, P52, P57, P60 | R7C1, R7C4, R8C1, R8C4 | CH1/GP0=F49, CH2/GP1=B49, CH3/GP2=F52, CH4/GP3=B52, CH5/GP4=F57, CH6/GP5=B57, CH7/GP6=F60, CH8/GP7=B60 |
| C05 | old harness | 4 | P05, P08, P13, P16 | R1C5, R1C8, R2C5, R2C8 | CH1/GP0=F05, CH2/GP1=B05, CH3/GP2=F08, CH4/GP3=B08, CH5/GP4=F13, CH6/GP5=B13, CH7/GP6=F16, CH8/GP7=B16 |
| C06 | old harness | 5 | P21, P24, P29, P32 | R3C5, R3C8, R4C5, R4C8 | CH1/GP0=F21, CH2/GP1=B21, CH3/GP2=F24, CH4/GP3=B24, CH5/GP4=F29, CH6/GP5=B29, CH7/GP6=F32, CH8/GP7=B32 |
| C07 | old harness | 6 | P37, P40, P45, P48 | R5C5, R5C8, R6C5, R6C8 | CH1/GP0=F37, CH2/GP1=B37, CH3/GP2=F40, CH4/GP3=B40, CH5/GP4=F45, CH6/GP5=B45, CH7/GP6=F48, CH8/GP7=B48 |
| C08 | old harness | 7 | P53, P56, P61, P64 | R7C5, R7C8, R8C5, R8C8 | CH1/GP0=F53, CH2/GP1=B53, CH3/GP2=F56, CH4/GP3=B56, CH5/GP4=F61, CH6/GP5=B61, CH7/GP6=F64, CH8/GP7=B64 |
| C09 | new infill | 8 | P02, P03, P10, P11 | R1C2, R1C3, R2C2, R2C3 | CH1/GP0=F02, CH2/GP1=B02, CH3/GP2=F03, CH4/GP3=B03, CH5/GP4=F10, CH6/GP5=B10, CH7/GP6=F11, CH8/GP7=B11 |
| C10 | new infill | 9 | P18, P19, P26, P27 | R3C2, R3C3, R4C2, R4C3 | CH1/GP0=F18, CH2/GP1=B18, CH3/GP2=F19, CH4/GP3=B19, CH5/GP4=F26, CH6/GP5=B26, CH7/GP6=F27, CH8/GP7=B27 |
| C11 | new infill | 10 | P34, P35, P42, P43 | R5C2, R5C3, R6C2, R6C3 | CH1/GP0=F34, CH2/GP1=B34, CH3/GP2=F35, CH4/GP3=B35, CH5/GP4=F42, CH6/GP5=B42, CH7/GP6=F43, CH8/GP7=B43 |
| C12 | new infill | 11 | P50, P51, P58, P59 | R7C2, R7C3, R8C2, R8C3 | CH1/GP0=F50, CH2/GP1=B50, CH3/GP2=F51, CH4/GP3=B51, CH5/GP4=F58, CH6/GP5=B58, CH7/GP6=F59, CH8/GP7=B59 |
| C13 | new infill | 12 | P06, P07, P14, P15 | R1C6, R1C7, R2C6, R2C7 | CH1/GP0=F06, CH2/GP1=B06, CH3/GP2=F07, CH4/GP3=B07, CH5/GP4=F14, CH6/GP5=B14, CH7/GP6=F15, CH8/GP7=B15 |
| C14 | new infill | 13 | P22, P23, P30, P31 | R3C6, R3C7, R4C6, R4C7 | CH1/GP0=F22, CH2/GP1=B22, CH3/GP2=F23, CH4/GP3=B23, CH5/GP4=F30, CH6/GP5=B30, CH7/GP6=F31, CH8/GP7=B31 |
| C15 | new infill | 14 | P38, P39, P46, P47 | R5C6, R5C7, R6C6, R6C7 | CH1/GP0=F38, CH2/GP1=B38, CH3/GP2=F39, CH4/GP3=B39, CH5/GP4=F46, CH6/GP5=B46, CH7/GP6=F47, CH8/GP7=B47 |
| C16 | new infill | 15 | P54, P55, P62, P63 | R7C6, R7C7, R8C6, R8C7 | CH1/GP0=F54, CH2/GP1=B54, CH3/GP2=F55, CH4/GP3=B55, CH5/GP4=F62, CH6/GP5=B62, CH7/GP6=F63, CH8/GP7=B63 |

## Wind-Pixel Pair Table

| Pair | Row | Col | Front Motor | Front Controller | Front Channel | Front Pin | Back Motor | Back Controller | Back Channel | Back Pin |
| --- | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| P01 | 1 | 1 | F01 | C01 | CH1 | GP0 | B01 | C01 | CH2 | GP1 |
| P02 | 1 | 2 | F02 | C09 | CH1 | GP0 | B02 | C09 | CH2 | GP1 |
| P03 | 1 | 3 | F03 | C09 | CH3 | GP2 | B03 | C09 | CH4 | GP3 |
| P04 | 1 | 4 | F04 | C01 | CH3 | GP2 | B04 | C01 | CH4 | GP3 |
| P05 | 1 | 5 | F05 | C05 | CH1 | GP0 | B05 | C05 | CH2 | GP1 |
| P06 | 1 | 6 | F06 | C13 | CH1 | GP0 | B06 | C13 | CH2 | GP1 |
| P07 | 1 | 7 | F07 | C13 | CH3 | GP2 | B07 | C13 | CH4 | GP3 |
| P08 | 1 | 8 | F08 | C05 | CH3 | GP2 | B08 | C05 | CH4 | GP3 |
| P09 | 2 | 1 | F09 | C01 | CH5 | GP4 | B09 | C01 | CH6 | GP5 |
| P10 | 2 | 2 | F10 | C09 | CH5 | GP4 | B10 | C09 | CH6 | GP5 |
| P11 | 2 | 3 | F11 | C09 | CH7 | GP6 | B11 | C09 | CH8 | GP7 |
| P12 | 2 | 4 | F12 | C01 | CH7 | GP6 | B12 | C01 | CH8 | GP7 |
| P13 | 2 | 5 | F13 | C05 | CH5 | GP4 | B13 | C05 | CH6 | GP5 |
| P14 | 2 | 6 | F14 | C13 | CH5 | GP4 | B14 | C13 | CH6 | GP5 |
| P15 | 2 | 7 | F15 | C13 | CH7 | GP6 | B15 | C13 | CH8 | GP7 |
| P16 | 2 | 8 | F16 | C05 | CH7 | GP6 | B16 | C05 | CH8 | GP7 |
| P17 | 3 | 1 | F17 | C02 | CH1 | GP0 | B17 | C02 | CH2 | GP1 |
| P18 | 3 | 2 | F18 | C10 | CH1 | GP0 | B18 | C10 | CH2 | GP1 |
| P19 | 3 | 3 | F19 | C10 | CH3 | GP2 | B19 | C10 | CH4 | GP3 |
| P20 | 3 | 4 | F20 | C02 | CH3 | GP2 | B20 | C02 | CH4 | GP3 |
| P21 | 3 | 5 | F21 | C06 | CH1 | GP0 | B21 | C06 | CH2 | GP1 |
| P22 | 3 | 6 | F22 | C14 | CH1 | GP0 | B22 | C14 | CH2 | GP1 |
| P23 | 3 | 7 | F23 | C14 | CH3 | GP2 | B23 | C14 | CH4 | GP3 |
| P24 | 3 | 8 | F24 | C06 | CH3 | GP2 | B24 | C06 | CH4 | GP3 |
| P25 | 4 | 1 | F25 | C02 | CH5 | GP4 | B25 | C02 | CH6 | GP5 |
| P26 | 4 | 2 | F26 | C10 | CH5 | GP4 | B26 | C10 | CH6 | GP5 |
| P27 | 4 | 3 | F27 | C10 | CH7 | GP6 | B27 | C10 | CH8 | GP7 |
| P28 | 4 | 4 | F28 | C02 | CH7 | GP6 | B28 | C02 | CH8 | GP7 |
| P29 | 4 | 5 | F29 | C06 | CH5 | GP4 | B29 | C06 | CH6 | GP5 |
| P30 | 4 | 6 | F30 | C14 | CH5 | GP4 | B30 | C14 | CH6 | GP5 |
| P31 | 4 | 7 | F31 | C14 | CH7 | GP6 | B31 | C14 | CH8 | GP7 |
| P32 | 4 | 8 | F32 | C06 | CH7 | GP6 | B32 | C06 | CH8 | GP7 |
| P33 | 5 | 1 | F33 | C03 | CH1 | GP0 | B33 | C03 | CH2 | GP1 |
| P34 | 5 | 2 | F34 | C11 | CH1 | GP0 | B34 | C11 | CH2 | GP1 |
| P35 | 5 | 3 | F35 | C11 | CH3 | GP2 | B35 | C11 | CH4 | GP3 |
| P36 | 5 | 4 | F36 | C03 | CH3 | GP2 | B36 | C03 | CH4 | GP3 |
| P37 | 5 | 5 | F37 | C07 | CH1 | GP0 | B37 | C07 | CH2 | GP1 |
| P38 | 5 | 6 | F38 | C15 | CH1 | GP0 | B38 | C15 | CH2 | GP1 |
| P39 | 5 | 7 | F39 | C15 | CH3 | GP2 | B39 | C15 | CH4 | GP3 |
| P40 | 5 | 8 | F40 | C07 | CH3 | GP2 | B40 | C07 | CH4 | GP3 |
| P41 | 6 | 1 | F41 | C03 | CH5 | GP4 | B41 | C03 | CH6 | GP5 |
| P42 | 6 | 2 | F42 | C11 | CH5 | GP4 | B42 | C11 | CH6 | GP5 |
| P43 | 6 | 3 | F43 | C11 | CH7 | GP6 | B43 | C11 | CH8 | GP7 |
| P44 | 6 | 4 | F44 | C03 | CH7 | GP6 | B44 | C03 | CH8 | GP7 |
| P45 | 6 | 5 | F45 | C07 | CH5 | GP4 | B45 | C07 | CH6 | GP5 |
| P46 | 6 | 6 | F46 | C15 | CH5 | GP4 | B46 | C15 | CH6 | GP5 |
| P47 | 6 | 7 | F47 | C15 | CH7 | GP6 | B47 | C15 | CH8 | GP7 |
| P48 | 6 | 8 | F48 | C07 | CH7 | GP6 | B48 | C07 | CH8 | GP7 |
| P49 | 7 | 1 | F49 | C04 | CH1 | GP0 | B49 | C04 | CH2 | GP1 |
| P50 | 7 | 2 | F50 | C12 | CH1 | GP0 | B50 | C12 | CH2 | GP1 |
| P51 | 7 | 3 | F51 | C12 | CH3 | GP2 | B51 | C12 | CH4 | GP3 |
| P52 | 7 | 4 | F52 | C04 | CH3 | GP2 | B52 | C04 | CH4 | GP3 |
| P53 | 7 | 5 | F53 | C08 | CH1 | GP0 | B53 | C08 | CH2 | GP1 |
| P54 | 7 | 6 | F54 | C16 | CH1 | GP0 | B54 | C16 | CH2 | GP1 |
| P55 | 7 | 7 | F55 | C16 | CH3 | GP2 | B55 | C16 | CH4 | GP3 |
| P56 | 7 | 8 | F56 | C08 | CH3 | GP2 | B56 | C08 | CH4 | GP3 |
| P57 | 8 | 1 | F57 | C04 | CH5 | GP4 | B57 | C04 | CH6 | GP5 |
| P58 | 8 | 2 | F58 | C12 | CH5 | GP4 | B58 | C12 | CH6 | GP5 |
| P59 | 8 | 3 | F59 | C12 | CH7 | GP6 | B59 | C12 | CH8 | GP7 |
| P60 | 8 | 4 | F60 | C04 | CH7 | GP6 | B60 | C04 | CH8 | GP7 |
| P61 | 8 | 5 | F61 | C08 | CH5 | GP4 | B61 | C08 | CH6 | GP5 |
| P62 | 8 | 6 | F62 | C16 | CH5 | GP4 | B62 | C16 | CH6 | GP5 |
| P63 | 8 | 7 | F63 | C16 | CH7 | GP6 | B63 | C16 | CH8 | GP7 |
| P64 | 8 | 8 | F64 | C08 | CH7 | GP6 | B64 | C08 | CH8 | GP7 |

## Generated CSV

The machine-readable table is generated at:

```text
config/motor_controller_mapping.csv
```

Regenerate or validate both files with:

```bash
python3 scripts/generate_motor_mapping.py --write
python3 scripts/generate_motor_mapping.py --check
```

The mapping is generated from `coaxial_windwall/model.py`. If the
physical wiring changes, update the address model first, regenerate
these files, and re-check labels before enabling real hardware output.
