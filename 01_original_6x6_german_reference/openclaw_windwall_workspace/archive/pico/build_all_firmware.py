#!/usr/bin/env python3
"""
Windwall Pico Firmware Builder

Builds firmware for all 8 Windwall Pico boards from a single template file.
This is adapted from the German wall 4-board build script.
"""

import shutil
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.absolute()
PICO_DIR = SCRIPT_DIR
TEMPLATE_FILE = PICO_DIR / "firmware_template.c"
NUM_BOARDS = 8


def generate_firmware_source(pico_id: int) -> Path:
    output_file = PICO_DIR / f"firmware_pico{pico_id}.c"
    template_content = TEMPLATE_FILE.read_text()
    firmware_content = template_content.replace('{{PICO_ID}}', str(pico_id))
    output_file.write_text(firmware_content)
    return output_file


def generate_cmake_file(pico_id: int) -> None:
    project_name = f"firmware_pico{pico_id}"
    source_file = f"firmware_pico{pico_id}.c"
    cmake_content = f"""# Auto-generated for Windwall Pico {pico_id}
cmake_minimum_required(VERSION 3.13)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

set(PICO_BOARD pico2 CACHE STRING \"Board type\")
include(pico_sdk_import.cmake)
project({project_name} C CXX ASM)
pico_sdk_init()

add_executable({project_name} {source_file})
pico_set_program_name({project_name} \"{project_name}\")
pico_set_program_version({project_name} \"1.0\")
pico_enable_stdio_uart({project_name} 0)
pico_enable_stdio_usb({project_name} 0)

target_link_libraries({project_name}
        pico_stdlib
        hardware_pwm
        hardware_gpio
        hardware_spi)

target_include_directories({project_name} PRIVATE
        ${{CMAKE_CURRENT_LIST_DIR}})

pico_add_extra_outputs({project_name})
"""
    (PICO_DIR / "CMakeLists.txt").write_text(cmake_content)


def build_firmware(pico_id: int) -> bool:
    project_name = f"firmware_pico{pico_id}"
    build_dir = PICO_DIR / "build"
    uf2_source = build_dir / f"{project_name}.uf2"
    uf2_dest = PICO_DIR / f"{project_name}.uf2"

    generate_firmware_source(pico_id)
    generate_cmake_file(pico_id)

    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(exist_ok=True)

    cmake_result = subprocess.run(["cmake", ".."], cwd=build_dir, capture_output=True, text=True)
    if cmake_result.returncode != 0:
        print(cmake_result.stderr)
        return False

    make_result = subprocess.run(["make", "-j4"], cwd=build_dir, capture_output=True, text=True)
    if make_result.returncode != 0:
        print(make_result.stderr)
        return False

    if not uf2_source.exists():
        print(f"UF2 not found: {uf2_source}")
        return False

    shutil.copy2(uf2_source, uf2_dest)
    shutil.rmtree(build_dir)

    source_file = PICO_DIR / f"firmware_pico{pico_id}.c"
    if source_file.exists():
        source_file.unlink()

    return True


def main() -> None:
    if not TEMPLATE_FILE.exists():
        raise SystemExit(f"Template not found: {TEMPLATE_FILE}")

    failures = []
    for pico_id in range(NUM_BOARDS):
        print(f"Building Pico {pico_id}...")
        ok = build_firmware(pico_id)
        if not ok:
            failures.append(pico_id)

    cmake_file = PICO_DIR / "CMakeLists.txt"
    if cmake_file.exists():
        cmake_file.unlink()

    if failures:
        raise SystemExit(f"Failed boards: {failures}")

    print("Built all Windwall Pico firmware files successfully.")


if __name__ == "__main__":
    main()
