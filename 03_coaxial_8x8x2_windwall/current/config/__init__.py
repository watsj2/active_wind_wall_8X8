"""Configuration constants for the Coaxial 8x8x2 Windwall system."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "logs"
GUI_PRESETS_PATH = PROJECT_ROOT / "config" / "gui_presets.json"

GRID_ROWS = 8
GRID_COLS = 8
COAXIAL_LAYERS = 2
LAYER_LABELS = ("F", "B")
LAYER_NAMES = ("Front", "Back")

NUM_WIND_PIXELS = GRID_ROWS * GRID_COLS
NUM_MOTORS = NUM_WIND_PIXELS * COAXIAL_LAYERS

MOTORS_PER_CONTROLLER = 8
CONTROLLER_COUNT = NUM_MOTORS // MOTORS_PER_CONTROLLER

PWM_MIN = 1000
PWM_IDLE = 1000
PWM_SAFE_START = 1150
PWM_DEFAULT = 1300
PWM_UI_MAX = 1800
PWM_MAX = 2000

PWM_RANGE_PRESETS = (
    ("Safe 1000-1400", 1000, 1400),
    ("Test 1000-1800", 1000, 1800),
    ("Full 1000-2000", 1000, 2000),
)

PWM_PRESETS = (
    ("Idle", 1000),
    ("Safe Start", 1150),
    ("Low", 1200),
    ("Medium", 1300),
    ("Working", 1450),
    ("Strong", 1600),
    ("High", 1750),
)

COMMAND_RATE_HZ = 50
CONTROL_LOOP_RATE_HZ = 200
SLEW_LIMIT_US_PER_TICK = 25
GUI_REFRESH_HZ = 12

SPI_BUS = 0
SPI_DEVICE = 0
SPI_SPEED_HZ = 1_000_000
SYNC_PIN = 22
GPIO_CHIP_PATH = "/dev/gpiochip4"

DEFAULT_HARDWARE_MODE = "real"
