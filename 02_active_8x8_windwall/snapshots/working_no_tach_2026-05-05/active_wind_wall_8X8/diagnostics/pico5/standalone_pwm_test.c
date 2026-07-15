#include "pico/stdlib.h"
#include "hardware/pwm.h"
#include "hardware/clocks.h"

#define LED_PIN 25
#define MOTOR_COUNT 8
#define PWM_DIVIDER 64.0f
#define PWM_FREQ_HZ 50.0f

static const uint MOTOR_PINS[MOTOR_COUNT] = {0, 1, 2, 3, 4, 5, 6, 7};

static uint slices[MOTOR_COUNT];
static uint channels[MOTOR_COUNT];
static uint16_t pwm_wrap_value;
static float counts_per_us;

static void set_motor_pwm_us(uint motor_index, uint16_t pulse_us) {
    uint16_t level = (uint16_t)(pulse_us * counts_per_us);
    if (level > pwm_wrap_value) level = pwm_wrap_value;
    pwm_set_chan_level(slices[motor_index], channels[motor_index], level);
}

int main(void) {
    const uint32_t sys_hz = clock_get_hz(clk_sys);
    counts_per_us = (float)sys_hz / PWM_DIVIDER / 1000000.0f;
    pwm_wrap_value = (uint16_t)((float)sys_hz / PWM_DIVIDER / PWM_FREQ_HZ) - 1;

    gpio_init(LED_PIN);
    gpio_set_dir(LED_PIN, GPIO_OUT);
    gpio_put(LED_PIN, 1);

    uint32_t slice_mask = 0;
    for (uint i = 0; i < MOTOR_COUNT; i++) {
        gpio_set_function(MOTOR_PINS[i], GPIO_FUNC_PWM);
        slices[i] = pwm_gpio_to_slice_num(MOTOR_PINS[i]);
        channels[i] = pwm_gpio_to_channel(MOTOR_PINS[i]);

        if (!(slice_mask & (1u << slices[i]))) {
            pwm_set_clkdiv(slices[i], PWM_DIVIDER);
            pwm_set_wrap(slices[i], pwm_wrap_value);
        }
        slice_mask |= (1u << slices[i]);
        set_motor_pwm_us(i, 1000);
    }
    pwm_set_mask_enabled(slice_mask);

    sleep_ms(5000);
    for (uint i = 0; i < MOTOR_COUNT; i++) {
        set_motor_pwm_us(i, 1600);
    }

    while (true) {
        gpio_xor_mask(1u << LED_PIN);
        sleep_ms(500);
    }
}
