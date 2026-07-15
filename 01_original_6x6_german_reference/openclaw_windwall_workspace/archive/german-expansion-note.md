# German Expansion Note

The Windwall control path is now re-baselined to expand the German wall directly.

## Active assumptions
- Kitronik controller boards are abandoned for control-path purposes.
- Control architecture should now track the German wall as closely as possible.
- Expansion only:
  - 4 boards -> 8 boards
  - 36 motors -> 64 motors
  - 9 motors per board -> 8 motors per board

## Preserved German comms layout
- MOSI = GPIO 16
- CS = GPIO 17
- SCK = GPIO 18
- SYNC = GPIO 22

## Preserved German firmware behavior
- full-frame receive
- per-board frame slicing
- sync latch
- watchdog timeout to PWM off
- same byte-to-PWM mapping model

## Current bare Pico motor output assumption
For the direct bare-Pico expansion path, the first-pass output mapping is:
- motor outputs on GPIO 0..7

This mirrors the German direct-drive style much more closely than the abandoned Kitronik path.
