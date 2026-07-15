#include "pico/stdlib.h"
#include "hardware/clocks.h"
#include "hardware/pwm.h"
#include <stdio.h>

#define LED_PIN 25
#define MOTOR_COUNT 8
#define WATCH_COUNT 7
#define PWM_DIVIDER 64.0f
#define PWM_FREQ_HZ 50.0f

static const uint MOTOR_PINS[MOTOR_COUNT] = {0, 1, 2, 3, 4, 5, 6, 7};
static const uint WATCH_PINS[WATCH_COUNT] = {16, 17, 18, 19, 20, 21, 22};

static volatile uint32_t rise_count[WATCH_COUNT];
static volatile uint32_t fall_count[WATCH_COUNT];

static uint slices[MOTOR_COUNT];
static uint channels[MOTOR_COUNT];
static float counts_per_us;
static uint16_t pwm_wrap_value;

static int watch_index_for_gpio(uint gpio) {
    for (uint i = 0; i < WATCH_COUNT; i++) {
        if (WATCH_PINS[i] == gpio) {
            return (int)i;
        }
    }
    return -1;
}

static void gpio_irq_handler(uint gpio, uint32_t events) {
    int idx = watch_index_for_gpio(gpio);
    if (idx < 0) {
        return;
    }
    if (events & GPIO_IRQ_EDGE_RISE) {
        rise_count[idx]++;
    }
    if (events & GPIO_IRQ_EDGE_FALL) {
        fall_count[idx]++;
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

    for (uint i = 0; i < WATCH_COUNT; i++) {
        gpio_init(WATCH_PINS[i]);
        gpio_set_dir(WATCH_PINS[i], GPIO_IN);
        gpio_pull_down(WATCH_PINS[i]);
        gpio_set_irq_enabled_with_callback(
            WATCH_PINS[i],
            GPIO_IRQ_EDGE_RISE | GPIO_IRQ_EDGE_FALL,
            true,
            &gpio_irq_handler
        );
    }

    sleep_ms(1500);
    printf("pico5_wire_report ready: watching GP16 GP17 GP18 GP19 GP20 GP21 GP22\n");

    uint32_t tick = 0;
    while (true) {
        printf("tick=%lu", (unsigned long)tick++);
        for (uint i = 0; i < WATCH_COUNT; i++) {
            printf(
                " GP%u=%d r%lu f%lu",
                WATCH_PINS[i],
                gpio_get(WATCH_PINS[i]),
                (unsigned long)rise_count[i],
                (unsigned long)fall_count[i]
            );
        }
        printf("\n");
        gpio_xor_mask(1u << LED_PIN);
        sleep_ms(500);
    }
}
