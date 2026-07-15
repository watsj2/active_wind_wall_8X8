cmake_minimum_required(VERSION 3.13)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

set(PICO_BOARD pico2 CACHE STRING "Board type")
include(pico_sdk_import.cmake)
project(esc_direct_test C CXX ASM)
pico_sdk_init()

add_executable(esc_direct_test esc_direct_test.c)
pico_set_program_name(esc_direct_test "esc_direct_test")
pico_set_program_version(esc_direct_test "1.0")
pico_enable_stdio_uart(esc_direct_test 0)
pico_enable_stdio_usb(esc_direct_test 0)

target_link_libraries(esc_direct_test pico_stdlib hardware_pwm hardware_gpio)
target_include_directories(esc_direct_test PRIVATE ${CMAKE_CURRENT_LIST_DIR})
pico_add_extra_outputs(esc_direct_test)
