# Motor and Controller Mapping

This is the fixed software mapping for the Coaxial 8x8x2 wind wall.
Use this table for physical labels, wiring checks, host command frames,
and future 16-controller firmware generation.

## Mapping Decision

- Layout: proven 8x8 Pico-block numbering with harness-preserving controller grouping.
- Grid orientation: `R1` is top, `C1` is left, viewed from the operator/front side.
- Pair labels follow the original 8x8 Pico blocks; the top row is `P01-P04, P33-P36`.
- Motor labels: `F01-F64` are front-layer motors; `B01-B64` are back-layer motors.
- `FP` means the front plane and uses Pichler QX-45 ESCs.
- `BP` means the back plane and uses Pichler QX-45 ESCs.
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
| C01 | old harness | 0 | P01, P04, P05, P08 | R1C1, R1C4, R2C1, R2C4 | CH1/GP0=F01, CH2/GP1=B01, CH3/GP2=F04, CH4/GP3=B04, CH5/GP4=F05, CH6/GP5=B05, CH7/GP6=F08, CH8/GP7=B08 |
| C02 | old harness | 1 | P09, P12, P13, P16 | R3C1, R3C4, R4C1, R4C4 | CH1/GP0=F09, CH2/GP1=B09, CH3/GP2=F12, CH4/GP3=B12, CH5/GP4=F13, CH6/GP5=B13, CH7/GP6=F16, CH8/GP7=B16 |
| C03 | old harness | 2 | P17, P20, P21, P24 | R5C1, R5C4, R6C1, R6C4 | CH1/GP0=F17, CH2/GP1=B17, CH3/GP2=F20, CH4/GP3=B20, CH5/GP4=F21, CH6/GP5=B21, CH7/GP6=F24, CH8/GP7=B24 |
| C04 | old harness | 3 | P25, P28, P29, P32 | R7C1, R7C4, R8C1, R8C4 | CH1/GP0=F25, CH2/GP1=B25, CH3/GP2=F28, CH4/GP3=B28, CH5/GP4=F29, CH6/GP5=B29, CH7/GP6=F32, CH8/GP7=B32 |
| C05 | old harness | 4 | P33, P36, P37, P40 | R1C5, R1C8, R2C5, R2C8 | CH1/GP0=F33, CH2/GP1=B33, CH3/GP2=F36, CH4/GP3=B36, CH5/GP4=F37, CH6/GP5=B37, CH7/GP6=F40, CH8/GP7=B40 |
| C06 | old harness | 5 | P41, P44, P45, P48 | R3C5, R3C8, R4C5, R4C8 | CH1/GP0=F41, CH2/GP1=B41, CH3/GP2=F44, CH4/GP3=B44, CH5/GP4=F45, CH6/GP5=B45, CH7/GP6=F48, CH8/GP7=B48 |
| C07 | old harness | 6 | P49, P52, P53, P56 | R5C5, R5C8, R6C5, R6C8 | CH1/GP0=F49, CH2/GP1=B49, CH3/GP2=F52, CH4/GP3=B52, CH5/GP4=F53, CH6/GP5=B53, CH7/GP6=F56, CH8/GP7=B56 |
| C08 | old harness | 7 | P57, P60, P61, P64 | R7C5, R7C8, R8C5, R8C8 | CH1/GP0=F57, CH2/GP1=B57, CH3/GP2=F60, CH4/GP3=B60, CH5/GP4=F61, CH6/GP5=B61, CH7/GP6=F64, CH8/GP7=B64 |
| C09 | new infill | 8 | P02, P03, P06, P07 | R1C2, R1C3, R2C2, R2C3 | CH1/GP0=F02, CH2/GP1=B02, CH3/GP2=F03, CH4/GP3=B03, CH5/GP4=F06, CH6/GP5=B06, CH7/GP6=F07, CH8/GP7=B07 |
| C10 | new infill | 9 | P10, P11, P14, P15 | R3C2, R3C3, R4C2, R4C3 | CH1/GP0=F10, CH2/GP1=B10, CH3/GP2=F11, CH4/GP3=B11, CH5/GP4=F14, CH6/GP5=B14, CH7/GP6=F15, CH8/GP7=B15 |
| C11 | new infill | 10 | P18, P19, P22, P23 | R5C2, R5C3, R6C2, R6C3 | CH1/GP0=F18, CH2/GP1=B18, CH3/GP2=F19, CH4/GP3=B19, CH5/GP4=F22, CH6/GP5=B22, CH7/GP6=F23, CH8/GP7=B23 |
| C12 | new infill | 11 | P26, P27, P30, P31 | R7C2, R7C3, R8C2, R8C3 | CH1/GP0=F26, CH2/GP1=B26, CH3/GP2=F27, CH4/GP3=B27, CH5/GP4=F30, CH6/GP5=B30, CH7/GP6=F31, CH8/GP7=B31 |
| C13 | new infill | 12 | P34, P35, P38, P39 | R1C6, R1C7, R2C6, R2C7 | CH1/GP0=F34, CH2/GP1=B34, CH3/GP2=F35, CH4/GP3=B35, CH5/GP4=F38, CH6/GP5=B38, CH7/GP6=F39, CH8/GP7=B39 |
| C14 | new infill | 13 | P42, P43, P46, P47 | R3C6, R3C7, R4C6, R4C7 | CH1/GP0=F42, CH2/GP1=B42, CH3/GP2=F43, CH4/GP3=B43, CH5/GP4=F46, CH6/GP5=B46, CH7/GP6=F47, CH8/GP7=B47 |
| C15 | new infill | 14 | P50, P51, P54, P55 | R5C6, R5C7, R6C6, R6C7 | CH1/GP0=F50, CH2/GP1=B50, CH3/GP2=F51, CH4/GP3=B51, CH5/GP4=F54, CH6/GP5=B54, CH7/GP6=F55, CH8/GP7=B55 |
| C16 | new infill | 15 | P58, P59, P62, P63 | R7C6, R7C7, R8C6, R8C7 | CH1/GP0=F58, CH2/GP1=B58, CH3/GP2=F59, CH4/GP3=B59, CH5/GP4=F62, CH6/GP5=B62, CH7/GP6=F63, CH8/GP7=B63 |

## Wind-Pixel Pair Table

| Pair | Row | Col | Front Motor | Front Controller | Front Channel | Front Pin | Back Motor | Back Controller | Back Channel | Back Pin |
| --- | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| P01 | 1 | 1 | F01 | C01 | CH1 | GP0 | B01 | C01 | CH2 | GP1 |
| P02 | 1 | 2 | F02 | C09 | CH1 | GP0 | B02 | C09 | CH2 | GP1 |
| P03 | 1 | 3 | F03 | C09 | CH3 | GP2 | B03 | C09 | CH4 | GP3 |
| P04 | 1 | 4 | F04 | C01 | CH3 | GP2 | B04 | C01 | CH4 | GP3 |
| P33 | 1 | 5 | F33 | C05 | CH1 | GP0 | B33 | C05 | CH2 | GP1 |
| P34 | 1 | 6 | F34 | C13 | CH1 | GP0 | B34 | C13 | CH2 | GP1 |
| P35 | 1 | 7 | F35 | C13 | CH3 | GP2 | B35 | C13 | CH4 | GP3 |
| P36 | 1 | 8 | F36 | C05 | CH3 | GP2 | B36 | C05 | CH4 | GP3 |
| P05 | 2 | 1 | F05 | C01 | CH5 | GP4 | B05 | C01 | CH6 | GP5 |
| P06 | 2 | 2 | F06 | C09 | CH5 | GP4 | B06 | C09 | CH6 | GP5 |
| P07 | 2 | 3 | F07 | C09 | CH7 | GP6 | B07 | C09 | CH8 | GP7 |
| P08 | 2 | 4 | F08 | C01 | CH7 | GP6 | B08 | C01 | CH8 | GP7 |
| P37 | 2 | 5 | F37 | C05 | CH5 | GP4 | B37 | C05 | CH6 | GP5 |
| P38 | 2 | 6 | F38 | C13 | CH5 | GP4 | B38 | C13 | CH6 | GP5 |
| P39 | 2 | 7 | F39 | C13 | CH7 | GP6 | B39 | C13 | CH8 | GP7 |
| P40 | 2 | 8 | F40 | C05 | CH7 | GP6 | B40 | C05 | CH8 | GP7 |
| P09 | 3 | 1 | F09 | C02 | CH1 | GP0 | B09 | C02 | CH2 | GP1 |
| P10 | 3 | 2 | F10 | C10 | CH1 | GP0 | B10 | C10 | CH2 | GP1 |
| P11 | 3 | 3 | F11 | C10 | CH3 | GP2 | B11 | C10 | CH4 | GP3 |
| P12 | 3 | 4 | F12 | C02 | CH3 | GP2 | B12 | C02 | CH4 | GP3 |
| P41 | 3 | 5 | F41 | C06 | CH1 | GP0 | B41 | C06 | CH2 | GP1 |
| P42 | 3 | 6 | F42 | C14 | CH1 | GP0 | B42 | C14 | CH2 | GP1 |
| P43 | 3 | 7 | F43 | C14 | CH3 | GP2 | B43 | C14 | CH4 | GP3 |
| P44 | 3 | 8 | F44 | C06 | CH3 | GP2 | B44 | C06 | CH4 | GP3 |
| P13 | 4 | 1 | F13 | C02 | CH5 | GP4 | B13 | C02 | CH6 | GP5 |
| P14 | 4 | 2 | F14 | C10 | CH5 | GP4 | B14 | C10 | CH6 | GP5 |
| P15 | 4 | 3 | F15 | C10 | CH7 | GP6 | B15 | C10 | CH8 | GP7 |
| P16 | 4 | 4 | F16 | C02 | CH7 | GP6 | B16 | C02 | CH8 | GP7 |
| P45 | 4 | 5 | F45 | C06 | CH5 | GP4 | B45 | C06 | CH6 | GP5 |
| P46 | 4 | 6 | F46 | C14 | CH5 | GP4 | B46 | C14 | CH6 | GP5 |
| P47 | 4 | 7 | F47 | C14 | CH7 | GP6 | B47 | C14 | CH8 | GP7 |
| P48 | 4 | 8 | F48 | C06 | CH7 | GP6 | B48 | C06 | CH8 | GP7 |
| P17 | 5 | 1 | F17 | C03 | CH1 | GP0 | B17 | C03 | CH2 | GP1 |
| P18 | 5 | 2 | F18 | C11 | CH1 | GP0 | B18 | C11 | CH2 | GP1 |
| P19 | 5 | 3 | F19 | C11 | CH3 | GP2 | B19 | C11 | CH4 | GP3 |
| P20 | 5 | 4 | F20 | C03 | CH3 | GP2 | B20 | C03 | CH4 | GP3 |
| P49 | 5 | 5 | F49 | C07 | CH1 | GP0 | B49 | C07 | CH2 | GP1 |
| P50 | 5 | 6 | F50 | C15 | CH1 | GP0 | B50 | C15 | CH2 | GP1 |
| P51 | 5 | 7 | F51 | C15 | CH3 | GP2 | B51 | C15 | CH4 | GP3 |
| P52 | 5 | 8 | F52 | C07 | CH3 | GP2 | B52 | C07 | CH4 | GP3 |
| P21 | 6 | 1 | F21 | C03 | CH5 | GP4 | B21 | C03 | CH6 | GP5 |
| P22 | 6 | 2 | F22 | C11 | CH5 | GP4 | B22 | C11 | CH6 | GP5 |
| P23 | 6 | 3 | F23 | C11 | CH7 | GP6 | B23 | C11 | CH8 | GP7 |
| P24 | 6 | 4 | F24 | C03 | CH7 | GP6 | B24 | C03 | CH8 | GP7 |
| P53 | 6 | 5 | F53 | C07 | CH5 | GP4 | B53 | C07 | CH6 | GP5 |
| P54 | 6 | 6 | F54 | C15 | CH5 | GP4 | B54 | C15 | CH6 | GP5 |
| P55 | 6 | 7 | F55 | C15 | CH7 | GP6 | B55 | C15 | CH8 | GP7 |
| P56 | 6 | 8 | F56 | C07 | CH7 | GP6 | B56 | C07 | CH8 | GP7 |
| P25 | 7 | 1 | F25 | C04 | CH1 | GP0 | B25 | C04 | CH2 | GP1 |
| P26 | 7 | 2 | F26 | C12 | CH1 | GP0 | B26 | C12 | CH2 | GP1 |
| P27 | 7 | 3 | F27 | C12 | CH3 | GP2 | B27 | C12 | CH4 | GP3 |
| P28 | 7 | 4 | F28 | C04 | CH3 | GP2 | B28 | C04 | CH4 | GP3 |
| P57 | 7 | 5 | F57 | C08 | CH1 | GP0 | B57 | C08 | CH2 | GP1 |
| P58 | 7 | 6 | F58 | C16 | CH1 | GP0 | B58 | C16 | CH2 | GP1 |
| P59 | 7 | 7 | F59 | C16 | CH3 | GP2 | B59 | C16 | CH4 | GP3 |
| P60 | 7 | 8 | F60 | C08 | CH3 | GP2 | B60 | C08 | CH4 | GP3 |
| P29 | 8 | 1 | F29 | C04 | CH5 | GP4 | B29 | C04 | CH6 | GP5 |
| P30 | 8 | 2 | F30 | C12 | CH5 | GP4 | B30 | C12 | CH6 | GP5 |
| P31 | 8 | 3 | F31 | C12 | CH7 | GP6 | B31 | C12 | CH8 | GP7 |
| P32 | 8 | 4 | F32 | C04 | CH7 | GP6 | B32 | C04 | CH8 | GP7 |
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
