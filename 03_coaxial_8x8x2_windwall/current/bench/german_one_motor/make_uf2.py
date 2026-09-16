#!/usr/bin/env python3
"""Wrap the bench BIN in an RP2350 UF2 using the project's verified family ID."""
from pathlib import Path
import math
import struct

MAGIC0, MAGIC1, MAGIC_END = 0x0A324655, 0x9E5D5157, 0x0AB16F30
FLAG_FAMILY = 0x00002000
FAMILY_RP2350 = 0xE48BFF59
BASE, PAYLOAD = 0x10000000, 256

root = Path(__file__).resolve().parent
binary = (root / "build" / "german_one_motor.bin").read_bytes()
count = math.ceil(len(binary) / PAYLOAD)
blocks = []
for index in range(count):
    block = bytearray(512)
    struct.pack_into("<8I", block, 0, MAGIC0, MAGIC1, FLAG_FAMILY,
                     BASE + index * PAYLOAD, PAYLOAD, index, count, FAMILY_RP2350)
    part = binary[index * PAYLOAD:(index + 1) * PAYLOAD]
    block[32:32 + len(part)] = part
    struct.pack_into("<I", block, 508, MAGIC_END)
    blocks.append(block)
(root / "german_one_motor.uf2").write_bytes(b"".join(blocks))
print(f"wrote {root / 'german_one_motor.uf2'} ({len(blocks)} blocks, {len(binary)} BIN bytes)")
