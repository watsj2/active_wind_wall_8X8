#include "pico/stdlib.h"
#include "hardware/pwm.h"

#define LED_PIN 25
#define ESC_PIN 0

static void set_pwm_us(uint gpio, uint16_t pulse_us) {
    uint slice = pwm_gpio_to_slice_num(gpio);
    uint channel = pwm_gpio_to_channel(gpio);

    if (pulse_us == 0) {
        pwm_set_chan_level(slice, channel, 0);
        return;
    }

    if (pulse_us < 1000) pulse_us = 1000;
    if (pulse_us > 2000) pulse_us = 2000;

    uint16_t level = (uint16_t)(pulse_us * 2.34375f);
    if (level > 31250) level = 31250;
    pwm_set_chan_level(slice, channel, level);
}

int main() {
    stdio_init_all();

    gpio_init(LED_PIN);
    gpio_set_dir(LED_PIN, GPIO_OUT);

    gpio_set_function(ESC_PIN, GPIO_FUNC_PWM);
    uint slice = pwm_gpio_to_slice_num(ESC_PIN);
    pwm_set_clkdiv(slice, 64.0f);
    pwm_set_wrap(slice, 31250);
    pwm_set_enabled(slice, true);

    // Boot with no PWM for 3 seconds
    set_pwm_us(ESC_PIN, 0);
    sleep_ms(3000);

    // Hold 1000 us for 5 seconds
    gpio_put(LED_PIN, 1);
    set_pwm_us(ESC_PIN, 1000);
    sleep_ms(5000);

    // Hold 1200 us for 5 seconds
    gpio_put(LED_PIN, 0);
    set_pwm_us(ESC_PIN, 1200);
    sleep_ms(5000);

    // Back to off
    set_pwm_us(ESC_PIN, 0);

    while (true) {
        gpio_xor_mask(1u << LED_PIN);
        sleep_ms(250);
    }
}
