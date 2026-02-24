"""
Global configuration constants for the Active Wind Wall Control System.
"""

# Hardware Configuration
NUM_MOTORS: int = 64
GRID_ROWS: int = 8
GRID_COLS: int = 8
NUM_PICOS: int = 8
MOTORS_PER_PICO: int = NUM_MOTORS // NUM_PICOS
UPDATE_RATE_HZ: int = 400
LOOP_TIME_MS: float = 1000.0 / UPDATE_RATE_HZ  # 2.5 ms

# PWM Signal Configuration
PWM_MIN: int = 1000  # Minimum PWM pulse width in microseconds
PWM_MAX: int = 2000  # Maximum PWM pulse width in microseconds
PWM_CENTER: int = (PWM_MIN + PWM_MAX) // 2  # 1500 µs neutral point

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
SHARED_MEM_SIZE: int = NUM_MOTORS * 8  # motors * PWM values * 8 bytes (float64)

# Pico Hardware Mapping
# Maps motors to Picos and their pin positions on each Pico.
# Default layout uses 8 Pico boards with 8 motors per board.

# Set True to test a single motor on Pico0 (motor 0 only).
SINGLE_MOTOR_TEST: bool = False

if NUM_MOTORS % NUM_PICOS != 0:
    raise ValueError("NUM_MOTORS must be divisible by NUM_PICOS")

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

# GPIO Sync Pin Configuration
SYNC_PIN: int = 22         # GPIO pin for synchronization trigger
SYNC_PULSE_WIDTH_US: int = 10  # Sync pulse width in microseconds
