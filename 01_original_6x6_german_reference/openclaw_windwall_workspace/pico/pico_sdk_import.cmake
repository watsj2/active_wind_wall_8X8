# Windwall Pico SDK import shim.
# Force the local Pico SDK path available on this Pi.

set(PICO_SDK_PATH "/home/jwatson/pico-sdk")
include("/home/jwatson/pico-sdk/external/pico_sdk_import.cmake")
