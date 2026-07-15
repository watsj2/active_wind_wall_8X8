#include "pico/stdlib.h"
#include "hardware/clocks.h"
#include "hardware/pwm.h"
#include "hardware/spi.h"
#include <stdio.h>

#define LED_PIN 25
#define MOTOR_COUNT 8
#define MOTOR34_LOCAL_INDEX 1

#define PWM_DIVIDER 64.0f
#define PWM_FREQ_HZ 50.0f

#define SPI_INST spi0
#define PIN_MISO 19
#define PIN_CS   17
#define PIN_SCK  18
#define PIN_MOSI 16
#define SYNC_PIN 22

#define FRAME_BYTES 64
#define MOTOR34_FRAME_INDEX 33
#define SAFETY_TIMEOUT_US 250000

static const uint MOTOR_PINS[MOTOR_COUNT] = {0, 1, 2, 3, 4, 5, 6, 7};

static uint slices[MOTOR_COUNT];
static uint channels[MOTOR_COUNT];
static float counts_per_us;
static uint16_t pwm_wrap_value;

static volatile uint32_t sync_count;

static void sync_irq_handler(uint gpio, uint32_t events) {
    if (gpio == SYNC_PIN && (events & GPIO_IRQ_EDGE_RISE)) {
        sync_count++;
    }
}

static void set_motor_us(uint motor_index, uint16_t pulse_us) {
    if (pulse_us < 1000) {
        pulse_us = 1000;
    }
    if (pulse_us > 2000) {
        pulse_us = 2000;
    }

    uint16_t level = (uint16_t)(pulse_us * counts_per_us);
    if (level > pwm_wrap_value) {
        level = pwm_wrap_value;
    }
    pwm_set_chan_level(slices[motor_index], channels[motor_index], level);
}

static void set_all_idle(void) {
    for (uint i = 0; i < MOTOR_COUNT; i++) {
        set_motor_us(i, 1000);
    }
}

static uint16_t byte_to_pwm_us(uint8_t raw_val) {
    if (raw_val == 0) {
        return 1000;
    }
    return (uint16_t)(1200 + ((uint32_t)raw_val * 800) / 255);
}

int main(void) {
    stdio_init_all();

    const uint32_t sys_hz = clock_get_hz(clk_sys);
    counts_per_us = (float)sys_hz / PWM_DIVIDER / 1000000.0f;
    pwm_wrap_value = (uint16_t)((float)sys_hz / PWM_DIVIDER / PWM_FREQ_HZ) - 1;

    gpio_init(LED_PIN);
    gpio_set_dir(LED_PIN, GPIO_OUT);
    gpio_put(LED_PIN, 0);

    uint32_t slice_mask = 0;
    for (uint i = 0; i < MOTOR_COUNT; i++) {
        gpio_set_function(MOTOR_PINS[i], GPIO_FUNC_PWM);
        slices[i] = pwm_gpio_to_slice_num(MOTOR_PINS[i]);
        channels[i] = pwm_gpio_to_channel(MOTOR_PINS[i]);
        if ((slice_mask & (1u << slices[i])) == 0) {
            pwm_set_clkdiv(slices[i], PWM_DIVIDER);
            pwm_set_wrap(slices[i], pwm_wrap_value);
        }
        slice_mask |= 1u << slices[i];
        set_motor_us(i, 1000);
    }
    pwm_set_mask_enabled(slice_mask);

    spi_init(SPI_INST, 1000000);
    spi_set_slave(SPI_INST, true);
    gpio_set_function(PIN_MISO, GPIO_FUNC_SPI);
    gpio_set_function(PIN_CS, GPIO_FUNC_SPI);
    gpio_set_function(PIN_SCK, GPIO_FUNC_SPI);
    gpio_set_function(PIN_MOSI, GPIO_FUNC_SPI);

    gpio_init(SYNC_PIN);
    gpio_set_dir(SYNC_PIN, GPIO_IN);
    gpio_pull_down(SYNC_PIN);
    gpio_set_irq_enabled_with_callback(SYNC_PIN, GPIO_IRQ_EDGE_RISE, true, &sync_irq_handler);

    uint8_t frame[FRAME_BYTES] = {0};
    uint8_t byte_index = 0;
    uint8_t last_motor34_byte = 0;
    uint32_t bytes_total = 0;
    uint32_t frames_total = 0;
    absolute_time_t last_byte_time = get_absolute_time();
    absolute_time_t last_frame_time = get_absolute_time();
    absolute_time_t last_print_time = get_absolute_time();

    sleep_ms(1500);
    printf("pico5_comm_report ready: SPI0 RX=GP16 CS=GP17 SCK=GP18 TX=GP19 SYNC=GP22 MOTOR34=GP1\n");

    while (true) {
        absolute_time_t now = get_absolute_time();

        if (byte_index != 0 && absolute_time_diff_us(last_byte_time, now) > 5000) {
            byte_index = 0;
        }

        while (spi_is_readable(SPI_INST)) {
            uint8_t rx = (uint8_t)spi_get_hw(SPI_INST)->dr;
            last_byte_time = get_absolute_time();
            bytes_total++;

            frame[byte_index] = rx;
            byte_index++;

            if (byte_index >= FRAME_BYTES) {
                last_motor34_byte = frame[MOTOR34_FRAME_INDEX];
                set_all_idle();
                set_motor_us(MOTOR34_LOCAL_INDEX, byte_to_pwm_us(last_motor34_byte));
                frames_total++;
                last_frame_time = get_absolute_time();
                gpio_put(LED_PIN, frames_total & 1u);
                byte_index = 0;
            }
        }

        now = get_absolute_time();
        if (absolute_time_diff_us(last_frame_time, now) > SAFETY_TIMEOUT_US) {
            set_all_idle();
        }

        if (absolute_time_diff_us(last_print_time, now) > 500000) {
            last_print_time = now;
            printf(
                "bytes=%lu frames=%lu idx=%u m34_byte=%u sync=%lu cs=%d sck=%d mosi=%d\n",
                (unsigned long)bytes_total,
                (unsigned long)frames_total,
                byte_index,
                last_motor34_byte,
                (unsigned long)sync_count,
                gpio_get(PIN_CS),
                gpio_get(PIN_SCK),
                gpio_get(PIN_MOSI)
            );
        }
    }
}
