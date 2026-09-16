#!/usr/bin/env python3
"""Generate and validate the Coaxial 8x8x2 motor/controller map."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from io import StringIO
from pathlib import Path
from typing import Iterable

SCRIPT_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPT_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_PROJECT_ROOT))

from config import (
    COAXIAL_LAYERS,
    CONTROLLER_COUNT,
    GRID_COLS,
    GRID_ROWS,
    MOTORS_PER_CONTROLLER,
    NUM_MOTORS,
    PROJECT_ROOT,
)
from coaxial_windwall.model import CoaxialAddress, iter_addresses


CSV_PATH = PROJECT_ROOT / "config" / "motor_controller_mapping.csv"
MARKDOWN_PATH = PROJECT_ROOT / "docs" / "MOTOR_CONTROLLER_MAPPING.md"

PLANE_CODES = ("FP", "BP")
PLANE_NAMES = ("Front Plane", "Back Plane")
ESC_TYPE = "Pichler QX-45"

CSV_FIELDS = (
    "motor_id",
    "pair_id",
    "row",
    "col",
    "layer",
    "layer_code",
    "plane_code",
    "plane_name",
    "esc_type",
    "motor_index",
    "host_index",
    "controller",
    "controller_index",
    "channel",
    "channel_index",
    "pico_pwm_pin",
    "signed_alias",
    "location",
)


def mapping_rows() -> list[dict[str, str | int]]:
    rows: list[dict[str, str | int]] = []
    for address in sorted(iter_addresses(), key=lambda item: item.motor_index):
        rows.append(
            {
                "motor_id": address.label,
                "pair_id": address.pair_label,
                "row": address.row + 1,
                "col": address.col + 1,
                "layer": address.layer_name,
                "layer_code": address.layer_label,
                "plane_code": PLANE_CODES[address.layer],
                "plane_name": PLANE_NAMES[address.layer],
                "esc_type": ESC_TYPE,
                "motor_index": address.motor_index,
                "host_index": address.motor_index,
                "controller": address.controller_label,
                "controller_index": address.controller_index,
                "channel": address.controller_channel_label,
                "channel_index": address.controller_channel,
                "pico_pwm_pin": address.controller_pwm_pin,
                "signed_alias": address.signed_alias,
                "location": address.location_label,
            }
        )
    return rows


def csv_text(rows: Iterable[dict[str, str | int]]) -> str:
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def controller_groups(
    rows: Iterable[dict[str, str | int]],
) -> dict[str, list[dict[str, str | int]]]:
    grouped: dict[str, list[dict[str, str | int]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["controller"])].append(row)
    return dict(sorted(grouped.items()))


def pair_table_rows() -> list[tuple[str, int, int, CoaxialAddress, CoaxialAddress]]:
    rows: list[tuple[str, int, int, CoaxialAddress, CoaxialAddress]] = []
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            front = CoaxialAddress(row=row, col=col, layer=0)
            back = CoaxialAddress(row=row, col=col, layer=1)
            rows.append((front.pair_label, row + 1, col + 1, front, back))
    return rows


def channel_list(group: list[dict[str, str | int]]) -> str:
    parts = []
    for row in sorted(group, key=lambda item: int(item["channel_index"])):
        parts.append(
            f'{row["channel"]}/{row["pico_pwm_pin"]}={row["motor_id"]}'
        )
    return ", ".join(parts)


def markdown_text(rows: list[dict[str, str | int]]) -> str:
    grouped = controller_groups(rows)
    lines = [
        "# Motor and Controller Mapping",
        "",
        "This is the fixed software mapping for the Coaxial 8x8x2 wind wall.",
        "Use this table for physical labels, wiring checks, host command frames,",
        "and future 16-controller firmware generation.",
        "",
        "## Mapping Decision",
        "",
        "- Layout: proven 8x8 Pico-block numbering with harness-preserving controller grouping.",
        "- Grid orientation: `R1` is top, `C1` is left, viewed from the operator/front side.",
        "- Pair labels follow the original 8x8 Pico blocks; the top row is `P01-P04, P33-P36`.",
        "- Motor labels: `F01-F64` are front-layer motors; `B01-B64` are back-layer motors.",
        "- `FP` means the front plane and uses Pichler QX-45 ESCs.",
        "- `BP` means the back plane and uses Pichler QX-45 ESCs.",
        "- Controller labels: `C01-C16` are physical, one-based labels.",
        "- Controller channels: `CH1-CH8` are physical, one-based labels.",
        "- Host indices: `controller_index` is 0-15; `channel_index` and `host_index` are zero-based.",
        "- Host frame indices `0-63` are front-plane motors; indices `64-127` are back-plane motors.",
        "- Pico PWM pins: `CH1-CH8` map to `GP0-GP7` on each controller.",
        "",
        "`C01-C08` reuse the original 8x8 harness outputs. Adjacent legacy",
        "outputs now become one coaxial front/back pair. `C09-C16` are new",
        "infill controllers for the middle columns that are not covered by the",
        "old harness.",
        "",
        "## Controller Summary",
        "",
        "| Controller | Harness Role | Controller Index | Pixels | Locations | Channels |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]

    for controller, group in grouped.items():
        sorted_group = sorted(group, key=lambda item: int(item["channel_index"]))
        motor_ids = [str(item["motor_id"]) for item in sorted_group]
        pair_ids = list(dict.fromkeys(str(item["pair_id"]) for item in sorted_group))
        locations = list(
            dict.fromkeys(
                f'R{item["row"]}C{item["col"]}' for item in sorted_group
            )
        )
        controller_index = sorted_group[0]["controller_index"]
        harness_role = "old harness" if int(controller_index) < 8 else "new infill"
        lines.append(
            f"| {controller} | {harness_role} | {controller_index} | "
            f"{', '.join(pair_ids)} | {', '.join(locations)} | "
            f"{channel_list(sorted_group)} |"
        )

    lines.extend(
        [
            "",
            "## Wind-Pixel Pair Table",
            "",
            "| Pair | Row | Col | Front Motor | Front Controller | Front Channel | Front Pin | Back Motor | Back Controller | Back Channel | Back Pin |",
            "| --- | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )

    for pair, row, col, front, back in pair_table_rows():
        lines.append(
            f"| {pair} | {row} | {col} | {front.label} | "
            f"{front.controller_label} | {front.controller_channel_label} | "
            f"{front.controller_pwm_pin} | {back.label} | {back.controller_label} | "
            f"{back.controller_channel_label} | {back.controller_pwm_pin} |"
        )

    lines.extend(
        [
            "",
            "## Generated CSV",
            "",
            "The machine-readable table is generated at:",
            "",
            "```text",
            "config/motor_controller_mapping.csv",
            "```",
            "",
            "Regenerate or validate both files with:",
            "",
            "```bash",
            "python3 scripts/generate_motor_mapping.py --write",
            "python3 scripts/generate_motor_mapping.py --check",
            "```",
            "",
            "The mapping is generated from `coaxial_windwall/model.py`. If the",
            "physical wiring changes, update the address model first, regenerate",
            "these files, and re-check labels before enabling real hardware output.",
            "",
        ]
    )
    return "\n".join(lines)


def assert_model_shape() -> None:
    expected_motors = GRID_ROWS * GRID_COLS * COAXIAL_LAYERS
    expected_controllers = expected_motors // MOTORS_PER_CONTROLLER
    if NUM_MOTORS != expected_motors:
        raise SystemExit(
            f"NUM_MOTORS={NUM_MOTORS} does not match grid/layers={expected_motors}"
        )
    if CONTROLLER_COUNT != expected_controllers:
        raise SystemExit(
            "CONTROLLER_COUNT="
            f"{CONTROLLER_COUNT} does not match mapping={expected_controllers}"
        )


def write_files() -> None:
    rows = mapping_rows()
    CSV_PATH.write_text(csv_text(rows), encoding="utf-8")
    MARKDOWN_PATH.write_text(markdown_text(rows), encoding="utf-8")


def check_files() -> None:
    rows = mapping_rows()
    expected = {
        CSV_PATH: csv_text(rows),
        MARKDOWN_PATH: markdown_text(rows),
    }
    missing_or_stale = []
    for path, text in expected.items():
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            missing_or_stale.append(path)
    if missing_or_stale:
        paths = ", ".join(str(path.relative_to(PROJECT_ROOT)) for path in missing_or_stale)
        raise SystemExit(f"mapping files are missing or stale: {paths}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate or validate the 128-motor controller mapping."
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="write docs/MOTOR_CONTROLLER_MAPPING.md and config/motor_controller_mapping.csv",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if generated mapping files are missing or stale",
    )
    args = parser.parse_args()

    assert_model_shape()
    if args.write and args.check:
        parser.error("choose only one of --write or --check")
    if args.write:
        write_files()
    elif args.check:
        check_files()
    else:
        print(markdown_text(mapping_rows()), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
