#!/usr/bin/env python3
"""Build RP2350 firmware for the 16 coaxial windwall controllers."""

from __future__ import annotations

import argparse
import math
import shutil
import struct
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import CONTROLLER_COUNT  # noqa: E402
from coaxial_windwall.model import controller_host_indices  # noqa: E402


TEMPLATE_FILE = SCRIPT_DIR / "firmware_controller_template.c"
PICO_SDK_IMPORT = SCRIPT_DIR / "pico_sdk_import.cmake"

REFERENCE_UF2_CANDIDATES = (
    SCRIPT_DIR / "reference_rp2350.uf2",
    Path("/home/jwatson/active_wind_wall_8X8/pico/firmware_pico0.uf2"),
    Path("/home/jwatson/Desktop/working, no tach 2026-05-05/active_wind_wall_8X8/pico/firmware_pico0.uf2"),
)

UF2_MAGIC_START0 = 0x0A324655
UF2_MAGIC_START1 = 0x9E5D5157
UF2_MAGIC_END = 0x0AB16F30
UF2_FLAG_FAMILY_ID = 0x00002000
UF2_APP_FAMILY_ID = 0xE48BFF59
UF2_FLASH_BASE = 0x10000000
UF2_PAYLOAD_SIZE = 256


def controller_label(controller_id: int) -> str:
    return f"C{controller_id + 1:02d}"


def parse_controller_token(token: str) -> int:
    normalized = token.strip().upper()
    if not normalized:
        raise ValueError("empty controller token")
    if normalized.startswith("C"):
        physical = int(normalized[1:])
        controller_id = physical - 1
    else:
        controller_id = int(normalized)
    if not 0 <= controller_id < CONTROLLER_COUNT:
        raise ValueError(f"controller out of range: {token}")
    return controller_id


def selected_controllers(args: argparse.Namespace) -> list[int]:
    if args.new_infill or args.back_plane:
        return list(range(8, 16))
    if args.old_harness or args.front_plane:
        return list(range(0, 8))
    if args.controllers:
        selected: list[int] = []
        for raw in args.controllers:
            for part in raw.split(","):
                selected.append(parse_controller_token(part))
        return sorted(set(selected))
    return list(range(CONTROLLER_COUNT))


def render_firmware_source(controller_id: int) -> str:
    template = TEMPLATE_FILE.read_text(encoding="utf-8")
    host_indices = ", ".join(str(index) for index in controller_host_indices(controller_id))
    return (
        template
        .replace("{{CONTROLLER_ID}}", str(controller_id))
        .replace("{{HOST_INDICES}}", "{" + host_indices + "}")
    )


def render_cmake(project_name: str, source_name: str) -> str:
    return f"""cmake_minimum_required(VERSION 3.13)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
set(PICO_BOARD pico2 CACHE STRING "Board type")
set(PICO_NO_PICOTOOL 1 CACHE BOOL "Build without fetching picotool")

include("{PICO_SDK_IMPORT}")

project({project_name} C CXX ASM)

pico_sdk_init()

add_executable({project_name} {source_name})

pico_set_program_name({project_name} "{project_name}")
pico_set_program_version({project_name} "1.0")

pico_enable_stdio_uart({project_name} 0)
pico_enable_stdio_usb({project_name} 0)

target_link_libraries({project_name}
    pico_stdlib
    hardware_spi
    hardware_pwm
    hardware_gpio
    hardware_clocks
)

target_include_directories({project_name} PRIVATE
    ${{CMAKE_CURRENT_LIST_DIR}}
)

pico_add_extra_outputs({project_name})
"""


def reference_uf2_path() -> Path | None:
    for candidate in REFERENCE_UF2_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def wrap_bin_as_uf2(bin_source: Path, uf2_dest: Path) -> bool:
    reference_path = reference_uf2_path()
    if reference_path is None:
        print("    ERROR: no RP2350 reference UF2 found for wrapping .bin output")
        return False

    app = bin_source.read_bytes()
    app_blocks = math.ceil(len(app) / UF2_PAYLOAD_SIZE)

    reference = bytearray(reference_path.read_bytes()[:512])
    if len(reference) != 512:
        print(f"    ERROR: invalid reference UF2: {reference_path}")
        return False

    magic0, magic1 = struct.unpack_from("<II", reference, 0)
    magic_end = struct.unpack_from("<I", reference, 508)[0]
    if magic0 != UF2_MAGIC_START0 or magic1 != UF2_MAGIC_START1 or magic_end != UF2_MAGIC_END:
        print(f"    ERROR: reference UF2 magic mismatch: {reference_path}")
        return False

    struct.pack_into("<I", reference, 20, 0)
    struct.pack_into("<I", reference, 24, 2)

    blocks = [bytes(reference)]
    for block_index in range(app_blocks):
        block = bytearray(512)
        payload = app[
            block_index * UF2_PAYLOAD_SIZE:(block_index + 1) * UF2_PAYLOAD_SIZE
        ]
        struct.pack_into(
            "<IIIIIIII",
            block,
            0,
            UF2_MAGIC_START0,
            UF2_MAGIC_START1,
            UF2_FLAG_FAMILY_ID,
            UF2_FLASH_BASE + block_index * UF2_PAYLOAD_SIZE,
            UF2_PAYLOAD_SIZE,
            block_index,
            app_blocks,
            UF2_APP_FAMILY_ID,
        )
        block[32:32 + len(payload)] = payload
        struct.pack_into("<I", block, 508, UF2_MAGIC_END)
        blocks.append(bytes(block))

    uf2_dest.write_bytes(b"".join(blocks))
    return True


def run_command(command: list[str], cwd: Path) -> bool:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    if result.returncode == 0:
        return True
    print(result.stdout)
    print(result.stderr)
    return False


def build_controller(controller_id: int) -> bool:
    label = controller_label(controller_id).lower()
    project_name = f"firmware_{label}"
    build_dir = SCRIPT_DIR / f"build_{label}"
    source_name = f"{project_name}.c"

    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir()

    (build_dir / source_name).write_text(
        render_firmware_source(controller_id),
        encoding="utf-8",
    )
    (build_dir / "CMakeLists.txt").write_text(
        render_cmake(project_name, source_name),
        encoding="utf-8",
    )

    print(f"Building {controller_label(controller_id)} -> {project_name}.uf2")
    if not run_command(["cmake", ".", "-DPICO_NO_PICOTOOL=1"], build_dir):
        print(f"  FAILED: CMake for {controller_label(controller_id)}")
        return False
    if not run_command(["make", "-j4"], build_dir):
        print(f"  FAILED: make for {controller_label(controller_id)}")
        return False

    uf2_source = build_dir / f"{project_name}.uf2"
    bin_source = build_dir / f"{project_name}.bin"
    uf2_dest = SCRIPT_DIR / f"{project_name}.uf2"

    if uf2_source.exists():
        shutil.copy2(uf2_source, uf2_dest)
    elif bin_source.exists():
        if not wrap_bin_as_uf2(bin_source, uf2_dest):
            return False
    else:
        print(f"  FAILED: no UF2 or BIN output for {controller_label(controller_id)}")
        return False

    size_kb = uf2_dest.stat().st_size / 1024
    print(f"  Wrote {uf2_dest.name} ({size_kb:.1f} KB)")
    return True


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--new-infill",
        action="store_true",
        help="Build C09-C16 only.",
    )
    group.add_argument(
        "--old-harness",
        action="store_true",
        help="Build C01-C08 only.",
    )
    group.add_argument("--back-plane", action="store_true", help=argparse.SUPPRESS)
    group.add_argument("--front-plane", action="store_true", help=argparse.SUPPRESS)
    group.add_argument(
        "--controllers",
        nargs="+",
        help="Specific controllers, using zero-based ids or labels like C09.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if not TEMPLATE_FILE.exists():
        print(f"Missing template: {TEMPLATE_FILE}")
        return 1

    controllers = selected_controllers(args)
    print("Selected controllers: " + ", ".join(controller_label(i) for i in controllers))

    failures = []
    for controller_id in controllers:
        if not build_controller(controller_id):
            failures.append(controller_id)

    if failures:
        print("Failed: " + ", ".join(controller_label(i) for i in failures))
        return 1

    print("Firmware build complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
