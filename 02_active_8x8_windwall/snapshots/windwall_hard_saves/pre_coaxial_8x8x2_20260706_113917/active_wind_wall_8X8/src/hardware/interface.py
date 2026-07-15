"""
Hardware Abstraction Layer for SPI motor control.
Supports both real Raspberry Pi hardware and mock drivers for development.
"""

import platform
import time
from typing import List, Optional
import numpy as np
from config import (
    MOTORS_PER_PICO,
    NUM_MOTORS,
    NUM_PICOS,
    SPI_BUS,
    SPI_DEVICE,
    SPI_SPEED_HZ,
    SYNC_PIN,
    PWM_MIN,
    PWM_MIN_RUNNING,
    PWM_MAX,
    TACH_ENABLED,
    TACH_FRAME_FLAG_REQUEST,
    TACH_FRAME_HEADER_BYTES,
    TACH_FRAME_MAGIC,
    TACH_NO_TARGET,
    TACH_PROTOCOL_VERSION,
    TACH_RESPONSE_BYTES,
    TACH_RESPONSE_MAGIC,
)

# Physical motor-to-byte mapping based on wiring configuration.
# Default is identity mapping for NUM_MOTORS motors.
PHYSICAL_MOTOR_ORDER = list(range(NUM_MOTORS))

class MockSPI:
    """Mock SPI for development/testing on non-Pi systems."""
    
    def __init__(self):
        self.frame_count = 0
    
    def write_bytes(self, data: List[int]) -> None:
        """Simulate SPI write operation."""
        self.frame_count += 1

    def transfer_bytes(self, data: List[int]) -> List[int]:
        """Simulate full-duplex SPI transfer."""
        self.frame_count += 1
        return [0] * len(data)
    
    def close(self) -> None:
        pass

class MockGPIO:
    """Mock GPIO for development/testing on non-Pi systems."""
    
    def __init__(self):
        self.frame_count = 0
    
    def toggle_sync_pin(self) -> None:
        """Simulate GPIO sync pulse."""
        self.frame_count += 1
        if self.frame_count % 100 == 0:
            print(f"[GPIO] Sync pulse {self.frame_count}")

class RealSPI:
    """Hardware SPI driver for Raspberry Pi (SPI0)."""
    
    def __init__(self):
        import spidev # type: ignore
        self.spi = spidev.SpiDev()
        self.spi.open(SPI_BUS, SPI_DEVICE)
        self.spi.max_speed_hz = SPI_SPEED_HZ
        self.spi.mode = 0
        self.spi.bits_per_word = 8
        print(f"[SPI] Initialized SPI{SPI_BUS}, CE{SPI_DEVICE} (GPIO10=MOSI, GPIO11=SCLK)")
    
    def write_bytes(self, data: List[int]) -> None:
        """Send bytes with enough pacing for the Pico polling loop to drain RX FIFO."""
        for b in data:
            self.spi.xfer2([int(b) & 0xFF])

    def transfer_bytes(self, data: List[int]) -> List[int]:
        """Transfer bytes one at a time so the Pico slave can service each byte."""
        rx = []
        for b in data:
            rx.extend(self.spi.xfer2([int(b) & 0xFF]))
        return rx

    def close(self) -> None:
        self.spi.close()

class RealGPIO:
    """Hardware GPIO driver using gpiod (Raspberry Pi 5)."""
    
    def __init__(self, sync_pin: int = SYNC_PIN):
        import gpiod # type: ignore
        import time
        
        self.gpiod = gpiod
        self.time = time
        self.sync_pin = sync_pin
        self.gpio_chip = '/dev/gpiochip4'  # Pi 5 uses gpiochip4
        self.legacy_line = None
        self.line_request = None

        try:
            from gpiod.line import Direction, Value # type: ignore

            self.Value = Value
            config = {
                sync_pin: gpiod.LineSettings(direction=Direction.OUTPUT)
            }
            self.line_request = gpiod.request_lines(
                self.gpio_chip,
                consumer="wind-wall-control",
                config=config
            )
            self.line_request.set_value(self.sync_pin, Value.INACTIVE)
        except ImportError:
            chip = gpiod.Chip(self.gpio_chip)
            self.legacy_line = chip.get_line(sync_pin)
            self.legacy_line.request(
                consumer="wind-wall-control",
                type=gpiod.LINE_REQ_DIR_OUT,
                default_vals=[0],
            )

        print(f"[GPIO] Initialized GPIO {self.sync_pin} (sync pulse)")
    
    def toggle_sync_pin(self) -> None:
        """Send 10µs sync pulse to trigger PWM latch on all Picos."""
        if self.legacy_line is not None:
            self.legacy_line.set_value(1)
            self.time.sleep(0.00001)  # 10 microsecond pulse
            self.legacy_line.set_value(0)
        else:
            self.line_request.set_value(self.sync_pin, self.Value.ACTIVE)
            self.time.sleep(0.00001)  # 10 microsecond pulse
            self.line_request.set_value(self.sync_pin, self.Value.INACTIVE)

    def close(self) -> None:
        if self.legacy_line is not None:
            self.legacy_line.release()

class HardwareInterface:
    """
    Main hardware abstraction layer.
    
    Architecture:
    - SPI broadcast: sends NUM_MOTORS-byte frame to all Picos simultaneously
    - Sync pulse: triggers atomic PWM update on all Picos
    - Physical motor remapping: handles wiring configuration
    """
    
    def __init__(self, use_mock: Optional[bool] = None, enable_tach: bool = TACH_ENABLED):
        self.platform = platform.system()
        
        # Auto-detect mock mode on macOS, or use explicit setting
        if use_mock is None:
            self.use_mock = self.platform == "Darwin"
        else:
            self.use_mock = use_mock
            
        self.frames_sent = 0
        self.enable_tach = enable_tach
        self.tach_sequence = 0
        self.last_tach_hz = np.full(NUM_MOTORS, np.nan, dtype=np.float64)
        
        self._init_drivers()
        mode = "MOCK" if self.use_mock else "REAL"
        protocol = "tach-v1" if self.enable_tach else "legacy-no-tach"
        print(f"[HW] Ready. Mode: {mode}, Protocol: {protocol}")

    def _init_drivers(self) -> None:
        """Initialize SPI and GPIO drivers based on platform."""
        if self.use_mock:
            print(f"[HW] Using mock drivers ({self.platform})")
            self.spi = MockSPI()
            self.gpio = MockGPIO()
        else:
            print(f"[HW] Initializing hardware drivers...")
            try:
                self.spi = RealSPI()
                self.gpio = RealGPIO(sync_pin=SYNC_PIN)
            except Exception as e:
                print(f"[HW] Hardware init failed: {e}")
                print(f"[HW] Falling back to mock drivers")
                self.use_mock = True
                self.spi = MockSPI()
                self.gpio = MockGPIO()

    def send_pwm(self, pwm_values: np.ndarray) -> None:
        """
        Send PWM values to ALL Picos in one Broadcast Frame.
        
        The input pwm_values array is in logical motor order (0..NUM_MOTORS-1).
        We remap it to physical wiring order before sending.
        
        Packet structure: NUM_MOTORS bytes, one per motor in physical order.
        """
        self.frames_sent += 1
        
        packet = self._build_packet(pwm_values)

        try:
            self.spi.write_bytes(packet)
            self.gpio.toggle_sync_pin()
        except Exception as e:
            print(f"[HW] Send Error (frame {self.frames_sent}): {e}")
        
        if self.frames_sent % 400 == 0:
            print(f"[HW] Frame {self.frames_sent}: Broadcast sent, sync triggered")

    def _build_motor_bytes(self, pwm_values: np.ndarray) -> List[int]:
        """Convert logical PWM values into physical motor command bytes."""
        reordered_pwm = np.array([pwm_values[i] for i in PHYSICAL_MOTOR_ORDER])
        
        motor_bytes = []
        pwm_range = max(1, PWM_MAX - PWM_MIN_RUNNING)
        for pwm in reordered_pwm:
            if pwm < PWM_MIN_RUNNING or pwm <= PWM_MIN:
                byte_val = 0x00
            else:
                clipped = max(PWM_MIN_RUNNING, min(PWM_MAX, pwm))
                byte_val = 1 + int((clipped - PWM_MIN_RUNNING) * 254 / pwm_range)
                byte_val = max(1, min(255, byte_val))
            motor_bytes.append(byte_val)
        return motor_bytes

    def _build_packet(
        self,
        pwm_values: np.ndarray,
        tach_target: int = TACH_NO_TARGET,
        sequence: int = 0,
    ) -> List[int]:
        """Build either a legacy frame or a tach-v1 command frame."""
        motor_bytes = self._build_motor_bytes(pwm_values)
        if not self.enable_tach:
            return motor_bytes

        flags = TACH_FRAME_FLAG_REQUEST if tach_target != TACH_NO_TARGET else 0
        header = [
            TACH_FRAME_MAGIC,
            flags & 0xFF,
            tach_target & 0xFF,
            sequence & 0xFF,
        ]
        if len(header) != TACH_FRAME_HEADER_BYTES:
            raise RuntimeError("Tach frame header size mismatch")
        return header + motor_bytes

    def _send_packet_and_sync(self, packet: List[int]) -> None:
        """Send one command frame and latch it with the sync line."""
        self.spi.write_bytes(packet)
        self.gpio.toggle_sync_pin()

    def read_tach_all(self, pwm_values: np.ndarray) -> np.ndarray:
        """
        Poll tach data from all Picos.

        The current PWM frame is resent once per Pico with that Pico selected as
        the only MISO talker. Each selected Pico returns 8 local tach edge rates.
        """
        if not self.enable_tach:
            return self.last_tach_hz.copy()

        tach_hz = self.last_tach_hz.copy()
        for pico_id in range(NUM_PICOS):
            self.tach_sequence = (self.tach_sequence + 1) & 0xFF
            packet = self._build_packet(
                pwm_values,
                tach_target=pico_id,
                sequence=self.tach_sequence,
            )
            try:
                self._send_packet_and_sync(packet)
                time.sleep(0.00025)
                response = self.spi.transfer_bytes([0] * TACH_RESPONSE_BYTES)
                local_hz = self._parse_tach_response(response, pico_id, self.tach_sequence)
                if local_hz is not None:
                    start = pico_id * MOTORS_PER_PICO
                    tach_hz[start:start + MOTORS_PER_PICO] = local_hz
            except Exception as e:
                print(f"[HW] Tach read error on Pico {pico_id}: {e}")

        self.last_tach_hz = tach_hz
        return tach_hz.copy()

    def _parse_tach_response(
        self,
        response: List[int],
        expected_pico_id: int,
        expected_sequence: int,
    ) -> Optional[np.ndarray]:
        """Parse one 40-byte tach response into local Hz values."""
        if len(response) != TACH_RESPONSE_BYTES:
            return None
        if response[0] != TACH_RESPONSE_MAGIC:
            return None
        if response[1] != TACH_PROTOCOL_VERSION:
            return None
        if response[2] != expected_pico_id:
            return None
        if response[3] != (expected_sequence & 0xFF):
            return None

        dt_us = int.from_bytes(bytes(response[4:8]), byteorder="little", signed=False)
        if dt_us <= 0:
            return None

        local_hz = np.zeros(MOTORS_PER_PICO, dtype=np.float64)
        offset = 8
        for i in range(MOTORS_PER_PICO):
            count = int.from_bytes(
                bytes(response[offset:offset + 4]),
                byteorder="little",
                signed=False,
            )
            local_hz[i] = count * 1_000_000.0 / dt_us
            offset += 4
        return local_hz

    def close(self) -> None:
        """Cleanup hardware resources."""
        try:
            self.spi.close()
            print("[HW] SPI closed")
        except:
            pass
        try:
            self.gpio.close()
        except:
            pass
