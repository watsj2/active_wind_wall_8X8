"""
Global configuration constants for the Active Wind Wall Control System.
"""

# Hardware Configuration
NUM_MOTORS: int = 64
GRID_ROWS: int = 8
GRID_COLS: int = 8
NUM_PICOS: int = 8
MOTORS_PER_PICO: int = NUM_MOTORS // NUM_PICOS
QUADRANT_ROWS: int = 2
QUADRANT_COLS: int = 2
QUADRANT_SIZE: int = 4
MOTORS_PER_QUADRANT: int = QUADRANT_SIZE * QUADRANT_SIZE
QUADRANT_GRID_ORDER: tuple[tuple[int, ...], ...] = (
    (0, 2),
    (1, 3),
)
UPDATE_RATE_HZ: int = 400
LOOP_TIME_MS: float = 1000.0 / UPDATE_RATE_HZ  # 2.5 ms

# PWM Signal Configuration
PWM_MIN: int = 1000  # Minimum PWM pulse width in microseconds
PWM_MIN_RUNNING: int = 1200  # First non-idle PWM command; tune for the motor/ESC pair
PWM_MAX: int = 2000  # Maximum PWM pulse width in microseconds
PWM_CENTER: int = (PWM_MIN + PWM_MAX) // 2  # 1500 µs neutral point
PWM_SPEED_PRESETS: dict[str, tuple[int, int]] = {
    "Full Range": (1000, 2000),
    "Cautious": (1000, 1600),
    "Active Mid": (1200, 1600),
    "Strong": (1400, 1800),
    "Upper Range": (1500, 2000),
}
PWM_TEST_PRESETS: dict[str, int] = {
    "1200 us": 1200,
    "1300 us": 1300,
    "1400 us": 1400,
    "1500 us": 1500,
    "1600 us": 1600,
    "1750 us": 1750,
    "2000 us": 2000,
}

# Anemometer / tach based uniform-flow calibration presets.
# The calibration run records raw per-motor telemetry, writes an Excel workbook,
# and estimates per-motor PWM offsets that flatten the measured flow field.
ANEMOMETER_CALIBRATION_PRESETS: dict[str, dict[str, float]] = {
    "Uniform Flow Calibration": {
        "pwm_us": 1600.0,
        "duration_s": 15.0,
        "warmup_s": 3.0,
    },
}
ANEMOMETER_CALIBRATION_DIR: str = "logs/anemometer"

# Safety Parameters
SLEW_LIMIT: int = 50  # Maximum PWM change per loop tick (units/tick)

# Signal Synthesis
FOURIER_TERMS: int = 7  # Number of Fourier coefficients per motor
BASE_FREQUENCY: float = 1.0  # Hz (base frequency for periodic signals)
# Optional per-experiment defaults
EXPERIMENT_DURATION_S: float = 10.0  # Default run length; can be overridden per run
# Normalized signal bounds (can be narrowed per experiment; never remapped)
SIGNAL_MIN_DEFAULT: float = 0.0
SIGNAL_MAX_DEFAULT: float = 1.0

# Visualization Parameters
GUI_UPDATE_RATE_FPS: int = 60
LOG_INTERVAL_MS: int = 100

# Shared Memory
SHARED_MEM_NAME: str = "aww_control_buffer"
SHARED_MEM_CHANNELS: int = 2  # PWM command and tach Hz per motor
SHARED_MEM_SIZE: int = SHARED_MEM_CHANNELS * NUM_MOTORS * 8

# Pico Hardware Mapping
# Maps motors to Picos and their pin positions on each Pico.
# Default layout uses 8 Pico boards with 8 motors per board.

# Set True to test a single motor on Pico0 (motor 0 only).
SINGLE_MOTOR_TEST: bool = False

if NUM_MOTORS % NUM_PICOS != 0:
    raise ValueError("NUM_MOTORS must be divisible by NUM_PICOS")

if GRID_ROWS != QUADRANT_ROWS * QUADRANT_SIZE or GRID_COLS != QUADRANT_COLS * QUADRANT_SIZE:
    raise ValueError("GRID_ROWS and GRID_COLS must match the configured quadrant layout")


QUADRANT_INDEX_TO_GRID_POSITION: dict[int, tuple[int, int]] = {
    quadrant_index: (grid_row, grid_col)
    for grid_row, row in enumerate(QUADRANT_GRID_ORDER)
    for grid_col, quadrant_index in enumerate(row)
}


def grid_position_to_motor_id(row: int, col: int) -> int:
    quadrant_grid_row = row // QUADRANT_SIZE
    quadrant_grid_col = col // QUADRANT_SIZE
    local_row = row % QUADRANT_SIZE
    local_col = col % QUADRANT_SIZE
    quadrant_index = QUADRANT_GRID_ORDER[quadrant_grid_row][quadrant_grid_col]
    local_index = local_row * QUADRANT_SIZE + local_col
    return quadrant_index * MOTORS_PER_QUADRANT + local_index


WALL_MOTOR_GRID: list[list[int]] = [
    [grid_position_to_motor_id(row, col) for col in range(GRID_COLS)]
    for row in range(GRID_ROWS)
]

FULL_PICO_MOTOR_MAP: dict = {
    f"pico_{pico_id}": {
        "pico_id": pico_id,
        "motors": list(range(pico_id * MOTORS_PER_PICO, (pico_id + 1) * MOTORS_PER_PICO)),
        "pin_offset": 0,
        "description": f"Pico {pico_id} motor block"
    }
    for pico_id in range(NUM_PICOS)
}

PICO_MOTOR_MAP: dict = (
    {
        'single_motor_test': {
            'pico_id': 0,
            'motors': [0],
            'pin_offset': 0,
            'description': 'Single Motor Test (Motor 0 on Pico0)'
        }
    }
    if SINGLE_MOTOR_TEST
    else FULL_PICO_MOTOR_MAP
)

# Derived motor-to-Pico lookup (auto-generated from PICO_MOTOR_MAP)
# Maps motor_id → (pico_id, pin_position_on_pico)
def _build_motor_pico_lookup() -> dict:
    """Build reverse lookup: motor_id → (pico_id, pin_on_pico)"""
    lookup = {}
    for quadrant_name, config in PICO_MOTOR_MAP.items():
        pico_id = config['pico_id']
        pin_offset = config['pin_offset']
        for pin_index, motor_id in enumerate(config['motors']):
            pin_on_pico = pin_offset + pin_index
            lookup[motor_id] = (pico_id, pin_on_pico)
    return lookup

MOTOR_TO_PICO_LOOKUP: dict = _build_motor_pico_lookup()

# SPI Configuration
SPI_BUS: int = 0           # SPI bus number (0 for default)
SPI_DEVICE: int = 0        # SPI device number (0 for default)
SPI_SPEED_HZ: int = 1000000  # 1 MHz SPI speed

# Tach return protocol configuration
TACH_ENABLED: bool = False
TACH_PROTOCOL_VERSION: int = 1
TACH_FRAME_MAGIC: int = 0xA5
TACH_RESPONSE_MAGIC: int = 0x5A
TACH_FRAME_HEADER_BYTES: int = 4
TACH_FRAME_FLAG_REQUEST: int = 0x01
TACH_NO_TARGET: int = 0xFF
TACH_RESPONSE_BYTES: int = 40
TACH_POLL_HZ: int = 20
TACH_PULSES_PER_REV: float = 1.0

# Pico tach input pins are local tach 1..8.
TACH_INPUT_PINS: tuple[int, ...] = (8, 9, 10, 11, 12, 13, 14, 15)

# GPIO Sync Pin Configuration
SYNC_PIN: int = 22         # GPIO pin for synchronization trigger
SYNC_PULSE_WIDTH_US: int = 10  # Sync pulse width in microseconds
