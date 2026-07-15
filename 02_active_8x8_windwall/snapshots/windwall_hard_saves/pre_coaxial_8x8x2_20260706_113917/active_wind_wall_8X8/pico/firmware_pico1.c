#include "pico/stdlib.h"
#include "hardware/pwm.h"
#include "hardware/spi.h"
#include "hardware/gpio.h"
#include "hardware/clocks.h"
#include "hardware/sync.h"
#include <stdbool.h>
#include <stdint.h>
#include <limits.h>

// ==========================================
// CONFIGURATION
// ==========================================

// Board identifier - generated for each Pico board (0..7).
#define PICO_ID 1

// Motor configuration
#define MOTORS_PER_PICO 8
static const uint MOTOR_PINS[MOTORS_PER_PICO] = {0, 1, 2, 3, 4, 5, 6, 7};

// PWM limits - injected from config/__init__.py by build_all_firmware.py.
#define PWM_MIN_US         1000
#define PWM_MIN_RUNNING_US 1200
#define PWM_MAX_US         2000
#define PWM_RANGE_US       800

// Tach input configuration: local tach 1..8 map to GP8..GP15.
static const uint TACH_PINS[MOTORS_PER_PICO] = {8, 9, 10, 11, 12, 13, 14, 15};

// Status LED
#define LED_PIN 25

// Servo-style PWM output configuration for ESC control
#define PWM_DIVIDER 64.0f
#define PWM_FREQ_HZ 50.0f

// SPI Configuration (Slave mode)
#define SPI_INST spi0
#define PIN_MISO 19   // SPI0 TX (to Pi MISO) - enabled only during addressed tach response
#define PIN_CS   17   // SPI0 CSn (from Pi CE0)
#define PIN_SCK  18   // SPI0 SCK (clock)
#define PIN_MOSI 16   // SPI0 RX (from Pi MOSI)

// Synchronization pulse input
#define SYNC_PIN 22

// Frame structure
#define TOTAL_MOTORS       64
#define LEGACY_FRAME_BYTES TOTAL_MOTORS
#define FRAME_MAGIC        0xA5
#define FRAME_VERSION      1
#define FRAME_FLAG_TACH    0x01
#define FRAME_HEADER_BYTES 4
#define TACH_NO_TARGET     0xFF
#define FRAME_BYTES        (FRAME_HEADER_BYTES + TOTAL_MOTORS)

// Tach response: magic, version, pico_id, seq, dt_us, 8 x uint32 edge deltas.
#define RESPONSE_MAGIC 0x5A
#define RESPONSE_BYTES 40

// Calculate which bytes in the motor array belong to this Pico.
#define MY_START (PICO_ID * MOTORS_PER_PICO)
#define MY_END   (MY_START + MOTORS_PER_PICO)

// ==========================================
// GLOBAL STATE
// ==========================================

// PWM hardware configuration for each motor
uint slices[MOTORS_PER_PICO];
uint channels[MOTORS_PER_PICO];
uint16_t pwm_wrap_value = 0;
float counts_per_us = 0.0f;

// Motor control buffers
volatile uint8_t motor_values[MOTORS_PER_PICO];
volatile uint8_t active_frame_buffer[MOTORS_PER_PICO];

// Tach counters
volatile uint32_t tach_edges[MOTORS_PER_PICO];
uint32_t tach_last_edges[MOTORS_PER_PICO];
uint64_t tach_last_report_us = 0;

// Synchronization state
volatile bool sync_pulse_detected = false;
volatile uint32_t sync_counter = 0;

// SPI command frame tracking
volatile uint8_t byte_index = 0;
volatile bool frame_overflow = false;
volatile uint8_t rx_frame[FRAME_BYTES];

// Tach response tracking
uint8_t response_buf[RESPONSE_BYTES];
volatile uint8_t response_tx_index = 0;
volatile uint8_t response_rx_count = 0;
volatile bool readback_active = false;

// ==========================================
// HELPERS
// ==========================================

static inline void put_u32_le(uint8_t *dst, uint32_t value) {
    dst[0] = (uint8_t)(value & 0xFF);
    dst[1] = (uint8_t)((value >> 8) & 0xFF);
    dst[2] = (uint8_t)((value >> 16) & 0xFF);
    dst[3] = (uint8_t)((value >> 24) & 0xFF);
}

static inline void miso_tristate(void) {
    gpio_set_function(PIN_MISO, GPIO_FUNC_SIO);
    gpio_set_dir(PIN_MISO, GPIO_IN);
    gpio_disable_pulls(PIN_MISO);
}

static inline void miso_spi_output(void) {
    gpio_set_function(PIN_MISO, GPIO_FUNC_SPI);
}

// ==========================================
// PWM CONTROL
// ==========================================

void set_motor_pwm_us(uint motor_index, uint16_t pulse_us) {
    if (pulse_us < PWM_MIN_US) pulse_us = PWM_MIN_US;
    if (pulse_us > PWM_MAX_US) pulse_us = PWM_MAX_US;

    uint16_t level = (uint16_t)(pulse_us * counts_per_us);
    if (level > pwm_wrap_value) level = pwm_wrap_value;

    pwm_set_chan_level(slices[motor_index], channels[motor_index], level);
}

// ==========================================
// TACH RESPONSE
// ==========================================

void prime_response_tx(void) {
    while (readback_active && response_tx_index < RESPONSE_BYTES && spi_is_writable(SPI_INST)) {
        spi_get_hw(SPI_INST)->dr = response_buf[response_tx_index++];
    }
}

void finish_response(void) {
    readback_active = false;
    response_tx_index = 0;
    response_rx_count = 0;
    miso_tristate();
}

void ignore_tach_response_window(void) {
    response_tx_index = RESPONSE_BYTES;
    response_rx_count = 0;
    readback_active = true;
    miso_tristate();
}

void prepare_tach_response(uint8_t sequence) {
    uint32_t deltas[MOTORS_PER_PICO];
    uint64_t now_us = to_us_since_boot(get_absolute_time());
    uint64_t previous_us;

    uint32_t irq_state = save_and_disable_interrupts();
    previous_us = tach_last_report_us;
    tach_last_report_us = now_us;
    for (uint i = 0; i < MOTORS_PER_PICO; i++) {
        uint32_t current = tach_edges[i];
        deltas[i] = current - tach_last_edges[i];
        tach_last_edges[i] = current;
    }
    restore_interrupts(irq_state);

    uint64_t dt64 = now_us > previous_us ? now_us - previous_us : 1;
    uint32_t dt_us = dt64 > UINT32_MAX ? UINT32_MAX : (uint32_t)dt64;
    if (dt_us == 0) dt_us = 1;

    response_buf[0] = RESPONSE_MAGIC;
    response_buf[1] = FRAME_VERSION;
    response_buf[2] = PICO_ID;
    response_buf[3] = sequence;
    put_u32_le(&response_buf[4], dt_us);

    uint offset = 8;
    for (uint i = 0; i < MOTORS_PER_PICO; i++) {
        put_u32_le(&response_buf[offset], deltas[i]);
        offset += 4;
    }

    response_tx_index = 0;
    response_rx_count = 0;
    readback_active = true;
    miso_spi_output();
    prime_response_tx();
}

// ==========================================
// GPIO INTERRUPT HANDLER
// ==========================================

void gpio_irq_handler(uint gpio, uint32_t events) {
    if (gpio == SYNC_PIN && (events & GPIO_IRQ_EDGE_RISE)) {
        sync_pulse_detected = true;
        sync_counter++;

        if (sync_counter >= 20) {
            gpio_xor_mask(1u << LED_PIN);
            sync_counter = 0;
        }
        return;
    }

    if (events & GPIO_IRQ_EDGE_RISE) {
        for (uint i = 0; i < MOTORS_PER_PICO; i++) {
            if (gpio == TACH_PINS[i]) {
                tach_edges[i]++;
                return;
            }
        }
    }
}

// ==========================================
// FRAME PROCESSING
// ==========================================

void process_received_frame(void) {
    bool tach_frame = !frame_overflow && byte_index == FRAME_BYTES && rx_frame[0] == FRAME_MAGIC;
    bool legacy_frame = !frame_overflow && !tach_frame && byte_index == LEGACY_FRAME_BYTES;
    bool accepted_frame = false;

    if (tach_frame) {
        for (uint i = 0; i < MOTORS_PER_PICO; i++) {
            motor_values[i] = rx_frame[FRAME_HEADER_BYTES + MY_START + i];
        }
        accepted_frame = true;

        uint8_t flags = rx_frame[1];
        uint8_t target = rx_frame[2];
        uint8_t sequence = rx_frame[3];
        if (flags & FRAME_FLAG_TACH) {
            if (target == PICO_ID) {
                prepare_tach_response(sequence);
            } else {
                ignore_tach_response_window();
            }
        } else {
            finish_response();
        }
    } else if (legacy_frame) {
        for (uint i = 0; i < MOTORS_PER_PICO; i++) {
            motor_values[i] = rx_frame[MY_START + i];
        }
        accepted_frame = true;
        finish_response();
    } else {
        finish_response();
    }

    if (accepted_frame) {
        for (uint i = 0; i < MOTORS_PER_PICO; i++) {
            active_frame_buffer[i] = motor_values[i];
            motor_values[i] = 0;
        }

        for (uint i = 0; i < MOTORS_PER_PICO; i++) {
            uint8_t raw_val = active_frame_buffer[i];
            uint16_t target_pwm;

            if (raw_val == 0) {
                target_pwm = PWM_MIN_US;
            } else {
                target_pwm = PWM_MIN_RUNNING_US + ((uint32_t)raw_val * PWM_RANGE_US) / 255;
            }
            if (target_pwm > PWM_MAX_US) target_pwm = PWM_MAX_US;

            set_motor_pwm_us(i, target_pwm);
        }
    }

    byte_index = 0;
    frame_overflow = false;
}

// ==========================================
// MAIN PROGRAM
// ==========================================

int main() {
    stdio_init_all();

    const uint32_t sys_hz = clock_get_hz(clk_sys);
    counts_per_us = (float)sys_hz / PWM_DIVIDER / 1000000.0f;
    pwm_wrap_value = (uint16_t)((float)sys_hz / PWM_DIVIDER / PWM_FREQ_HZ) - 1;

    gpio_init(LED_PIN);
    gpio_set_dir(LED_PIN, GPIO_OUT);
    gpio_put(LED_PIN, 1);

    for (uint i = 0; i < MOTORS_PER_PICO; i++) {
        gpio_set_function(MOTOR_PINS[i], GPIO_FUNC_PWM);
        slices[i] = pwm_gpio_to_slice_num(MOTOR_PINS[i]);
        channels[i] = pwm_gpio_to_channel(MOTOR_PINS[i]);

        pwm_set_clkdiv(slices[i], PWM_DIVIDER);
        pwm_set_wrap(slices[i], pwm_wrap_value);
        pwm_set_enabled(slices[i], true);

        motor_values[i] = 0;
        active_frame_buffer[i] = 0;
        tach_edges[i] = 0;
        tach_last_edges[i] = 0;

        set_motor_pwm_us(i, 1000);
    }

    for (uint i = 0; i < MOTORS_PER_PICO; i++) {
        gpio_init(TACH_PINS[i]);
        gpio_set_dir(TACH_PINS[i], GPIO_IN);
        gpio_pull_up(TACH_PINS[i]);
    }

    tach_last_report_us = to_us_since_boot(get_absolute_time());

    spi_init(SPI_INST, 1000000);
    spi_set_slave(SPI_INST, true);

    miso_tristate();
    gpio_set_function(PIN_CS,   GPIO_FUNC_SPI);
    gpio_set_function(PIN_SCK,  GPIO_FUNC_SPI);
    gpio_set_function(PIN_MOSI, GPIO_FUNC_SPI);

    while (spi_is_readable(SPI_INST)) {
        (void)spi_get_hw(SPI_INST)->dr;
    }

    gpio_init(SYNC_PIN);
    gpio_set_dir(SYNC_PIN, GPIO_IN);
    gpio_pull_down(SYNC_PIN);

    gpio_set_irq_enabled_with_callback(SYNC_PIN, GPIO_IRQ_EDGE_RISE, true, &gpio_irq_handler);
    for (uint i = 0; i < MOTORS_PER_PICO; i++) {
        gpio_set_irq_enabled(TACH_PINS[i], GPIO_IRQ_EDGE_RISE, true);
    }

    absolute_time_t last_sync_time = get_absolute_time();
    const uint64_t SAFETY_TIMEOUT_US = 200000;

    while (true) {
        prime_response_tx();

        while (spi_is_readable(SPI_INST)) {
            uint8_t rx = (uint8_t)spi_get_hw(SPI_INST)->dr;

            if (readback_active) {
                response_rx_count++;
                if (response_rx_count >= RESPONSE_BYTES) {
                    finish_response();
                } else {
                    prime_response_tx();
                }
            } else {
                if (byte_index < FRAME_BYTES) {
                    rx_frame[byte_index] = rx;
                    byte_index++;
                } else {
                    frame_overflow = true;
                }
            }
        }

        if (sync_pulse_detected) {
            sync_pulse_detected = false;
            last_sync_time = get_absolute_time();
            process_received_frame();
        }

        if (absolute_time_diff_us(last_sync_time, get_absolute_time()) > SAFETY_TIMEOUT_US) {
            for (uint i = 0; i < MOTORS_PER_PICO; i++) {
                set_motor_pwm_us(i, PWM_MIN_US);
            }
            gpio_put(LED_PIN, (to_ms_since_boot(get_absolute_time()) % 200) < 100);
        }
    }
}
