#include "pico/stdlib.h"
#include "hardware/pwm.h"
#include "hardware/spi.h"
#include "hardware/gpio.h"
#include "hardware/clocks.h"
#include <stdbool.h>
#include <stdint.h>

// Generated per physical controller. C01 uses controller_id 0; C16 uses 15.
#define CONTROLLER_ID {{CONTROLLER_ID}}

#define MOTORS_PER_CONTROLLER 8
static const uint MOTOR_PINS[MOTORS_PER_CONTROLLER] = {0, 1, 2, 3, 4, 5, 6, 7};
static const uint HOST_INDICES[MOTORS_PER_CONTROLLER] = {{HOST_INDICES}};

#define PWM_MIN_US 1000
#define PWM_IDLE_US 1000
#define PWM_MAX_US 2000

#define PWM_DIVIDER 64.0f
#define PWM_FREQ_HZ 50.0f

#define SPI_INST spi0
#define PIN_MISO 19
#define PIN_CS   17
#define PIN_SCK  18
#define PIN_MOSI 16

#define SYNC_PIN 22
#define LED_PIN 25

#define PROTOCOL_MAGIC0 0x43
#define PROTOCOL_MAGIC1 0x57
#define PROTOCOL_VERSION 1
#define MESSAGE_PWM_US_BROADCAST 0x01
#define FLAG_OUTPUT_ARMED 0x01

#define TOTAL_MOTORS 128
#define HEADER_BYTES 8
#define PWM_US_BYTES 2
#define PWM_PAYLOAD_BYTES (TOTAL_MOTORS * PWM_US_BYTES)
#define CRC_BYTES 2
#define FRAME_BYTES (HEADER_BYTES + PWM_PAYLOAD_BYTES + CRC_BYTES)

#define WATCHDOG_TIMEOUT_US 250000

#define CRC16_INIT 0xFFFF
#define CRC16_POLY 0x1021

uint slices[MOTORS_PER_CONTROLLER];
uint channels[MOTORS_PER_CONTROLLER];
uint16_t pwm_wrap_value = 0;
float counts_per_us = 0.0f;

volatile bool sync_pulse_detected = false;
volatile uint32_t sync_counter = 0;

uint8_t rx_frame[FRAME_BYTES];
uint16_t byte_index = 0;
bool frame_overflow = false;

static inline uint16_t get_u16_le(const uint8_t *src) {
    return (uint16_t)src[0] | ((uint16_t)src[1] << 8);
}

static uint16_t crc16_ccitt_false(const uint8_t *data, uint16_t length) {
    uint16_t crc = CRC16_INIT;
    for (uint16_t i = 0; i < length; i++) {
        crc ^= (uint16_t)data[i] << 8;
        for (uint8_t bit = 0; bit < 8; bit++) {
            if (crc & 0x8000) {
                crc = (uint16_t)((crc << 1) ^ CRC16_POLY);
            } else {
                crc = (uint16_t)(crc << 1);
            }
        }
    }
    return crc;
}

static void miso_tristate(void) {
    gpio_set_function(PIN_MISO, GPIO_FUNC_SIO);
    gpio_set_dir(PIN_MISO, GPIO_IN);
    gpio_disable_pulls(PIN_MISO);
}

static uint16_t clamp_pwm_us(uint16_t pulse_us) {
    if (pulse_us < PWM_MIN_US) return PWM_MIN_US;
    if (pulse_us > PWM_MAX_US) return PWM_MAX_US;
    return pulse_us;
}

static void set_motor_pwm_us(uint motor_index, uint16_t pulse_us) {
    pulse_us = clamp_pwm_us(pulse_us);
    uint16_t level = (uint16_t)(pulse_us * counts_per_us);
    if (level > pwm_wrap_value) level = pwm_wrap_value;
    pwm_set_chan_level(slices[motor_index], channels[motor_index], level);
}

static void set_all_idle(void) {
    for (uint i = 0; i < MOTORS_PER_CONTROLLER; i++) {
        set_motor_pwm_us(i, PWM_IDLE_US);
    }
}

static bool frame_is_valid(void) {
    if (frame_overflow || byte_index != FRAME_BYTES) return false;
    if (rx_frame[0] != PROTOCOL_MAGIC0 || rx_frame[1] != PROTOCOL_MAGIC1) return false;
    if (rx_frame[2] != PROTOCOL_VERSION) return false;
    if (rx_frame[3] != MESSAGE_PWM_US_BROADCAST) return false;
    if (get_u16_le(&rx_frame[6]) != PWM_PAYLOAD_BYTES) return false;

    uint16_t expected_crc = crc16_ccitt_false(rx_frame, FRAME_BYTES - CRC_BYTES);
    uint16_t received_crc = get_u16_le(&rx_frame[FRAME_BYTES - CRC_BYTES]);
    return received_crc == expected_crc;
}

static void apply_local_payload(void) {
    for (uint local = 0; local < MOTORS_PER_CONTROLLER; local++) {
        uint host_index = HOST_INDICES[local];
        uint offset = HEADER_BYTES + host_index * PWM_US_BYTES;
        set_motor_pwm_us(local, get_u16_le(&rx_frame[offset]));
    }
}

static bool process_received_frame(void) {
    bool valid = frame_is_valid();

    if (valid && (rx_frame[4] & FLAG_OUTPUT_ARMED)) {
        apply_local_payload();
    } else {
        set_all_idle();
    }

    byte_index = 0;
    frame_overflow = false;
    return valid;
}

void gpio_irq_handler(uint gpio, uint32_t events) {
    if (gpio == SYNC_PIN && (events & GPIO_IRQ_EDGE_RISE)) {
        sync_pulse_detected = true;
        sync_counter++;
        if (sync_counter >= 20) {
            gpio_xor_mask(1u << LED_PIN);
            sync_counter = 0;
        }
    }
}

int main(void) {
    stdio_init_all();

    const uint32_t sys_hz = clock_get_hz(clk_sys);
    counts_per_us = (float)sys_hz / PWM_DIVIDER / 1000000.0f;
    pwm_wrap_value = (uint16_t)((float)sys_hz / PWM_DIVIDER / PWM_FREQ_HZ) - 1;

    gpio_init(LED_PIN);
    gpio_set_dir(LED_PIN, GPIO_OUT);
    gpio_put(LED_PIN, 1);

    for (uint i = 0; i < MOTORS_PER_CONTROLLER; i++) {
        gpio_set_function(MOTOR_PINS[i], GPIO_FUNC_PWM);
        slices[i] = pwm_gpio_to_slice_num(MOTOR_PINS[i]);
        channels[i] = pwm_gpio_to_channel(MOTOR_PINS[i]);

        pwm_set_clkdiv(slices[i], PWM_DIVIDER);
        pwm_set_wrap(slices[i], pwm_wrap_value);
        pwm_set_enabled(slices[i], true);
        set_motor_pwm_us(i, PWM_IDLE_US);
    }

    spi_init(SPI_INST, 1000000);
    spi_set_slave(SPI_INST, true);

    miso_tristate();
    gpio_set_function(PIN_CS, GPIO_FUNC_SPI);
    gpio_set_function(PIN_SCK, GPIO_FUNC_SPI);
    gpio_set_function(PIN_MOSI, GPIO_FUNC_SPI);

    while (spi_is_readable(SPI_INST)) {
        (void)spi_get_hw(SPI_INST)->dr;
    }

    gpio_init(SYNC_PIN);
    gpio_set_dir(SYNC_PIN, GPIO_IN);
    gpio_pull_down(SYNC_PIN);
    gpio_set_irq_enabled_with_callback(SYNC_PIN, GPIO_IRQ_EDGE_RISE, true, &gpio_irq_handler);

    absolute_time_t last_valid_frame_time = get_absolute_time();

    while (true) {
        while (spi_is_readable(SPI_INST)) {
            uint8_t rx = (uint8_t)spi_get_hw(SPI_INST)->dr;
            if (byte_index < FRAME_BYTES) {
                rx_frame[byte_index++] = rx;
            } else {
                frame_overflow = true;
            }
        }

        if (sync_pulse_detected) {
            sync_pulse_detected = false;
            if (process_received_frame()) {
                last_valid_frame_time = get_absolute_time();
            }
        }

        if (absolute_time_diff_us(last_valid_frame_time, get_absolute_time()) > WATCHDOG_TIMEOUT_US) {
            set_all_idle();
            gpio_put(LED_PIN, (to_ms_since_boot(get_absolute_time()) % 200) < 100);
        }
    }
}
