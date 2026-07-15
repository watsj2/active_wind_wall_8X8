"""
Shared memory management for inter-process communication.
Provides safe access to motor control state and telemetry data.
"""

import numpy as np
from multiprocessing import shared_memory
from typing import Tuple, Optional
from config import NUM_MOTORS, SHARED_MEM_CHANNELS, SHARED_MEM_NAME, SHARED_MEM_SIZE


PWM_CHANNEL = 0
TACH_HZ_CHANNEL = 1


class MotorStateBuffer:
    """
    Manages a shared memory buffer for motor commands and telemetry.
    
    Structure:
    - Shape: (SHARED_MEM_CHANNELS, NUM_MOTORS)
    - Channel 0: Target PWM values (1000-2000)
    - Channel 1: Tach frequency in Hz
    """
    
    def __init__(self, create: bool = True):
        """
        Initialize the shared memory buffer.
        
        Args:
            create: If True, create new buffer; if False, attach to existing
        """
        self.name = SHARED_MEM_NAME
        self.shape = (SHARED_MEM_CHANNELS, NUM_MOTORS)
        self.dtype = np.float64
        
        try:
            if create:
                # Try to unlink any existing buffer first
                try:
                    existing = shared_memory.SharedMemory(name=self.name)
                    existing.close()
                    existing.unlink()
                except (FileNotFoundError, ValueError):
                    pass
                
                # Create new shared memory block
                self.shm = shared_memory.SharedMemory(
                    name=self.name,
                    create=True,
                    size=SHARED_MEM_SIZE
                )
                self.array = np.ndarray(self.shape, dtype=self.dtype, buffer=self.shm.buf)
                self.array[PWM_CHANNEL, :] = 0.0
                self.array[TACH_HZ_CHANNEL, :] = np.nan
                print(f"[SharedMem] Created new buffer: {self.name}")
            else:
                # Attach to existing shared memory
                self.shm = shared_memory.SharedMemory(name=self.name)
                self.array = np.ndarray(self.shape, dtype=self.dtype, buffer=self.shm.buf)
                print(f"[SharedMem] Attached to existing buffer: {self.name}")
        
        except Exception as e:
            print(f"[SharedMem] ERROR: Failed to initialize buffer: {e}")
            raise
    
    def set_pwm(self, pwm_values: np.ndarray) -> None:
        """
        Update PWM values in shared memory.
        
        Args:
            pwm_values: numpy array of shape (NUM_MOTORS,) with PWM values
        """
        self.array[PWM_CHANNEL, :] = pwm_values

    def set_tach_hz(self, tach_hz: np.ndarray) -> None:
        """
        Update tach frequency values in shared memory.

        Args:
            tach_hz: numpy array of shape (NUM_MOTORS,) with tach frequencies in Hz
        """
        self.array[TACH_HZ_CHANNEL, :] = tach_hz

    def set_state(self, pwm_values: np.ndarray, tach_hz: np.ndarray) -> None:
        """
        Update PWM and tach values together.
        """
        self.array[PWM_CHANNEL, :] = pwm_values
        self.array[TACH_HZ_CHANNEL, :] = tach_hz
    
    def get_pwm(self) -> np.ndarray:
        """
        Read PWM values from shared memory.
        
        Returns:
            numpy array of shape (NUM_MOTORS,) with current PWM values
        """
        return self.array[PWM_CHANNEL, :].copy()

    def get_tach_hz(self) -> np.ndarray:
        """
        Read tach frequency values from shared memory.

        Returns:
            numpy array of shape (NUM_MOTORS,) with tach frequencies in Hz
        """
        return self.array[TACH_HZ_CHANNEL, :].copy()

    def get_state(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Read PWM and tach values from shared memory.

        Returns:
            tuple of (pwm_values, tach_hz)
        """
        return (
            self.array[PWM_CHANNEL, :].copy(),
            self.array[TACH_HZ_CHANNEL, :].copy(),
        )
    
    def close(self) -> None:
        """Close the shared memory buffer (does not unlink)."""
        if self.shm:
            self.shm.close()
            print(f"[SharedMem] Closed buffer: {self.name}")
    
    def unlink(self) -> None:
        """Unlink the shared memory buffer (cleanup)."""
        if self.shm:
            try:
                self.shm.unlink()
                print(f"[SharedMem] Unlinked buffer: {self.name}")
            except Exception as e:
                print(f"[SharedMem] Warning: Could not unlink buffer: {e}")
