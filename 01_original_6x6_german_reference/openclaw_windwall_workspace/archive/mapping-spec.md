# Windwall 8x8 Mapping Spec v1

## Purpose

This document defines the canonical motor, Pico, and packet mapping for the 8x8 Windwall.

Human-facing numbering uses **Motor 1-64**.
Internal software may use zero-based indexing, but that should stay behind the curtain unless implementation requires it.

## Wall Coordinates

- Rows: **1-8** from top to bottom
- Columns: **1-8** from left to right
- Motor 1 is the **top-left** motor at **Row 1, Column 1**
- Motor 64 is the **bottom-right** motor at **Row 8, Column 8**

## Canonical Motor Numbering

| Row | Motors |
|---|---|
| 1 | 1, 2, 3, 4, 5, 6, 7, 8 |
| 2 | 9, 10, 11, 12, 13, 14, 15, 16 |
| 3 | 17, 18, 19, 20, 21, 22, 23, 24 |
| 4 | 25, 26, 27, 28, 29, 30, 31, 32 |
| 5 | 33, 34, 35, 36, 37, 38, 39, 40 |
| 6 | 41, 42, 43, 44, 45, 46, 47, 48 |
| 7 | 49, 50, 51, 52, 53, 54, 55, 56 |
| 8 | 57, 58, 59, 60, 61, 62, 63, 64 |

## Pico Region Layout

Each Pico controls a 2-row x 4-column block.

| Pico | Rows | Columns |
|---|---:|---:|
| 1 | 1-2 | 1-4 |
| 2 | 3-4 | 1-4 |
| 3 | 5-6 | 1-4 |
| 4 | 7-8 | 1-4 |
| 5 | 1-2 | 5-8 |
| 6 | 3-4 | 5-8 |
| 7 | 5-6 | 5-8 |
| 8 | 7-8 | 5-8 |

## Pico to Motor Ownership

| Pico | Motors |
|---|---|
| 1 | 1, 2, 3, 4, 9, 10, 11, 12 |
| 2 | 17, 18, 19, 20, 25, 26, 27, 28 |
| 3 | 33, 34, 35, 36, 41, 42, 43, 44 |
| 4 | 49, 50, 51, 52, 57, 58, 59, 60 |
| 5 | 5, 6, 7, 8, 13, 14, 15, 16 |
| 6 | 21, 22, 23, 24, 29, 30, 31, 32 |
| 7 | 37, 38, 39, 40, 45, 46, 47, 48 |
| 8 | 53, 54, 55, 56, 61, 62, 63, 64 |

## Recommended 64-Byte Packet Order

To keep firmware simple, packet bytes should be grouped by Pico ownership rather than full-wall row-major order.

### Packet byte ranges

| Packet bytes | Pico | Motors |
|---|---:|---|
| 1-8 | 1 | 1, 2, 3, 4, 9, 10, 11, 12 |
| 9-16 | 2 | 17, 18, 19, 20, 25, 26, 27, 28 |
| 17-24 | 3 | 33, 34, 35, 36, 41, 42, 43, 44 |
| 25-32 | 4 | 49, 50, 51, 52, 57, 58, 59, 60 |
| 33-40 | 5 | 5, 6, 7, 8, 13, 14, 15, 16 |
| 41-48 | 6 | 21, 22, 23, 24, 29, 30, 31, 32 |
| 49-56 | 7 | 37, 38, 39, 40, 45, 46, 47, 48 |
| 57-64 | 8 | 53, 54, 55, 56, 61, 62, 63, 64 |

## Firmware Index Convention

For firmware and software implementation only:
- human Pico labels remain **1-8**
- internal firmware IDs may be **0-7**

Recommended mapping:
- human Pico 1 -> firmware ID 0
- human Pico 2 -> firmware ID 1
- human Pico 3 -> firmware ID 2
- human Pico 4 -> firmware ID 3
- human Pico 5 -> firmware ID 4
- human Pico 6 -> firmware ID 5
- human Pico 7 -> firmware ID 6
- human Pico 8 -> firmware ID 7

## Python Remap List (software internal, zero-based)

If internal code uses zero-based motor indices 0-63, the packet remap should be:

```python
PHYSICAL_MOTOR_ORDER = [
    0, 1, 2, 3, 8, 9, 10, 11,
    16, 17, 18, 19, 24, 25, 26, 27,
    32, 33, 34, 35, 40, 41, 42, 43,
    48, 49, 50, 51, 56, 57, 58, 59,
    4, 5, 6, 7, 12, 13, 14, 15,
    20, 21, 22, 23, 28, 29, 30, 31,
    36, 37, 38, 39, 44, 45, 46, 47,
    52, 53, 54, 55, 60, 61, 62, 63,
]
```

## Notes

- Human conversation, build notes, labels, and debugging should use **Motor 1-64**.
- Software should translate internally as needed.
- This mapping spec should be treated as canonical unless a deliberate wiring revision is made.
