cmake_minimum_required(VERSION 3.13)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

set(PICO_BOARD pico2 CACHE STRING "Board type")

include(pico_sdk_import.cmake)

project(firmware_pico7 C CXX ASM)

pico_sdk_init()

add_executable(firmware_pico7 firmware_pico7.c)

pico_set_program_name(firmware_pico7 "firmware_pico7")
pico_set_program_version(firmware_pico7 "1.0")

pico_enable_stdio_uart(firmware_pico7 0)
pico_enable_stdio_usb(firmware_pico7 0)

target_link_libraries(firmware_pico7
    pico_stdlib
    hardware_spi
    hardware_pwm
    hardware_dma
)

target_include_directories(firmware_pico7 PRIVATE
    ${CMAKE_CURRENT_LIST_DIR}
)

pico_add_extra_outputs(firmware_pico7)
