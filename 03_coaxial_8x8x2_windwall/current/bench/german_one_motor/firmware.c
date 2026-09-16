/* Derived from the pinned German SPI/sync/PWM design; see SOURCE.json. */
#include <stdio.h>
#include <string.h>
#include "pico/stdlib.h"
#include "pico/stdio_usb.h"
#include "pico/unique_id.h"
#include "hardware/clocks.h"
#include "hardware/gpio.h"
#include "hardware/spi.h"
#include "hardware/pwm.h"
#include "hardware/sync.h"
#include "receiver.h"

#define SYNC_PIN 22
static receiver_t state;
static volatile uint32_t pending_sync;
static uint32_t sync_collisions, spi_overruns;
static uint slice, channel;
static uint16_t applied_us;
static float counts_per_us;
static char board_id[2 * PICO_UNIQUE_BOARD_ID_SIZE_BYTES + 1];

static void sync_irq(uint gpio, uint32_t events) {
    if (gpio == SYNC_PIN && (events & GPIO_IRQ_EDGE_RISE)) ++pending_sync;
}
static void apply_pwm(void) {
    if (applied_us != state.pwm_us) {
        pwm_set_chan_level(slice, channel, (uint16_t)(state.pwm_us * counts_per_us));
        applied_us = state.pwm_us;
    }
}
static void status(void) {
    printf("{\"firmware\":\"german-one-motor-v1\",\"board\":\"%s\","
           "\"pwm_us\":%u,\"armed\":%u,\"direct\":%u,\"bytes\":%lu,"
           "\"syncs\":%lu,\"valid\":%lu,\"invalid\":%lu,\"last_length\":%u,"
           "\"raw\":%u,\"overflow\":%lu,\"overrun\":%lu,\"collisions\":%lu,"
           "\"timeouts\":%lu,\"limits\":%lu,\"ce0\":%u,\"sync_level\":%u}\n",
           board_id, state.pwm_us, state.armed, state.direct,
           (unsigned long)state.bytes, (unsigned long)state.syncs,
           (unsigned long)state.valid, (unsigned long)state.invalid,
           state.last_length, state.last_raw, (unsigned long)state.overflows,
           (unsigned long)spi_overruns, (unsigned long)sync_collisions,
           (unsigned long)state.timeouts, (unsigned long)state.limits,
           gpio_get(17), gpio_get(SYNC_PIN));
}
static void usb_commands(void) {
    static char command[20];
    static unsigned length;
    static bool too_long;
    for (unsigned n = 0; n < 16; ++n) {
        int c = getchar_timeout_us(0);
        if (c == PICO_ERROR_TIMEOUT) break;
        if (c == '\r') continue;
        if (c == '\n') {
            command[length] = 0;
            if (!too_long && !strcmp(command, "STATUS")) status();
            else if (!too_long && !strcmp(command, "ARM SPI")) {
                receiver_arm(&state, time_us_64(), false);
                puts("OK ARM SPI");
            } else if (!too_long && !strcmp(command, "PULSE USB")) {
                receiver_arm(&state, time_us_64(), true);
                apply_pwm();
                puts("OK PULSE USB");
            } else {
                receiver_stop(&state);
                apply_pwm();
                puts(!too_long && !strcmp(command, "STOP") ? "OK STOP" : "ERROR stopped");
            }
            length = 0;
            too_long = false;
        } else if (length < sizeof(command) - 1) command[length++] = (char)c;
        else too_long = true;
    }
}
int main(void) {
    receiver_init(&state);
    // Only GP0 can output PWM. GP1-GP8 and unused MISO stay high impedance.
    for (uint pin = 1; pin <= 8; ++pin) {
        gpio_init(pin); gpio_set_dir(pin, GPIO_IN); gpio_disable_pulls(pin);
    }
    gpio_init(19); gpio_set_dir(19, GPIO_IN); gpio_disable_pulls(19);
    uint32_t hz = clock_get_hz(clk_sys);
    counts_per_us = (float)hz / 64.0f / 1000000.0f;
    slice = pwm_gpio_to_slice_num(0);
    channel = pwm_gpio_to_channel(0);
    gpio_set_function(0, GPIO_FUNC_PWM);
    pwm_config config = pwm_get_default_config();
    pwm_config_set_clkdiv(&config, 64.0f);
    pwm_config_set_wrap(&config, (uint16_t)((float)hz / 64.0f / 50.0f) - 1);
    pwm_init(slice, &config, false);
    apply_pwm();
    pwm_set_enabled(slice, true);

    spi_init(spi0, 1000000);
    spi_set_format(spi0, 8, SPI_CPOL_0, SPI_CPHA_0, SPI_MSB_FIRST);
    spi_set_slave(spi0, true);
    gpio_set_function(16, GPIO_FUNC_SPI);
    gpio_set_function(17, GPIO_FUNC_SPI);
    gpio_set_function(18, GPIO_FUNC_SPI);
    while (spi_is_readable(spi0)) (void)spi_get_hw(spi0)->dr;
    gpio_init(SYNC_PIN); gpio_set_dir(SYNC_PIN, GPIO_IN); gpio_pull_down(SYNC_PIN);
    gpio_set_irq_enabled_with_callback(SYNC_PIN, GPIO_IRQ_EDGE_RISE, true, sync_irq);
    pico_get_unique_board_id_string(board_id, sizeof(board_id));
    stdio_init_all(); // USB telemetry only; no UART or Pico 2 W GP25 LED write.
    while (true) {
        // Bound work per iteration so noise cannot starve the pulse deadline.
        for (unsigned n = 0; n < 64 && spi_is_readable(spi0); ++n)
            receiver_byte(&state, (uint8_t)spi_get_hw(spi0)->dr);
        if (spi_get_hw(spi0)->ris & SPI_SSPRIS_RORRIS_BITS) {
            ++spi_overruns;
            spi_get_hw(spi0)->icr = SPI_SSPICR_RORIC_BITS;
            state.overflow = true;
        }
        uint32_t irq_state = save_and_disable_interrupts();
        uint32_t pulses = pending_sync;
        pending_sync = 0;
        restore_interrupts(irq_state);
        if (pulses) {
            if (pulses > 1) { ++sync_collisions; state.overflow = true; }
            receiver_sync(&state, time_us_64());
        }
        if (!stdio_usb_connected()) receiver_stop(&state);
        receiver_tick(&state, time_us_64());
        apply_pwm();
        usb_commands();
    }
}
