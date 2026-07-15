#include "pico/stdlib.h"
#include "hardware/pwm.h"
#include "hardware/clocks.h"

#define LED_PIN 25
#define MOTOR_COUNT 8
#define PWM_DIVIDER 64.0f
#define PWM_FREQ_HZ 50.0f

static const uint MOTOR_PINS[MOTOR_COUNT] = {0, 1, 2, 3, 4, 5, 6, 7};

int main(void) {
    const uint32_t sys_hz = clock_get_hz(clk_sys);
    const float counts_per_us = (float)sys_hz / PWM_DIVIDER / 1000000.0f;
    const uint16_t pwm_wrap_value = (uint16_t)((float)sys_hz / PWM_DIVIDER / PWM_FREQ_HZ) - 1;
    const uint16_t idle_level = (uint16_t)(1000.0f * counts_per_us);

    gpio_init(LED_PIN);
    gpio_set_dir(LED_PIN, GPIO_OUT);
    gpio_put(LED_PIN, 0);

    uint32_t slice_mask = 0;
    for (uint i = 0; i < MOTOR_COUNT; i++) {
        gpio_set_function(MOTOR_PINS[i], GPIO_FUNC_PWM);
        uint slice = pwm_gpio_to_slice_num(MOTOR_PINS[i]);
        uint channel = pwm_gpio_to_channel(MOTOR_PINS[i]);
        if (!(slice_mask & (1u << slice))) {
            pwm_set_clkdiv(slice, PWM_DIVIDER);
            pwm_set_wrap(slice, pwm_wrap_value);
        }
        slice_mask |= (1u << slice);
        pwm_set_chan_level(slice, channel, idle_level);
    }
    pwm_set_mask_enabled(slice_mask);

    while (true) {
        tight_loop_contents();
    }
}
