cmake_minimum_required(VERSION 3.13)
set(CMAKE_C_STANDARD 11)
set(PICO_BOARD pico2_w CACHE STRING "Board")
set(PICO_NO_PICOTOOL 1 CACHE BOOL "Offline build")
include(/home/jwatson/pico-sdk/external/pico_sdk_import.cmake)
project(german_one_motor C CXX ASM)
pico_sdk_init()
add_executable(german_one_motor firmware.c)
target_link_libraries(german_one_motor pico_stdlib pico_unique_id hardware_spi hardware_pwm hardware_clocks hardware_sync)
pico_enable_stdio_usb(german_one_motor 1)
pico_enable_stdio_uart(german_one_motor 0)
target_compile_definitions(german_one_motor PRIVATE
    PICO_STDIO_USB_CONNECT_WAIT_TIMEOUT_MS=0
    PICO_STDIO_USB_STDOUT_TIMEOUT_US=100000
    PICO_STDIO_DEADLOCK_TIMEOUT_MS=1
    PICO_STDIO_USB_ENABLE_RESET_VIA_BAUD_RATE=0
    PICO_STDIO_USB_ENABLE_RESET_VIA_VENDOR_INTERFACE=0)
target_compile_options(german_one_motor PRIVATE -Wall -Wextra)
pico_set_program_name(german_one_motor "german_one_motor_c01")
pico_set_program_version(german_one_motor "1.0")
pico_add_extra_outputs(german_one_motor)
