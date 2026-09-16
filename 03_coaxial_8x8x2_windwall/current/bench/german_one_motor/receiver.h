#ifndef ONE_MOTOR_RECEIVER_H
#define ONE_MOTOR_RECEIVER_H
#include <stdbool.h>
#include <stdint.h>
#include <string.h>

// Original German main: 36 bytes, raw 51 -> 1000 + 51*1000/255 = 1200 us.
#define FRAME_BYTES 36
#define TEST_RAW 51
#define IDLE_US 1000
#define ACTIVE_US 1200
#define LEASE_US 4000000ULL
#define PULSE_US 1000000ULL
#define WATCHDOG_US 200000ULL

typedef struct {
    uint8_t frame[FRAME_BYTES];
    uint16_t count, last_length, pwm_us;
    uint8_t last_raw;
    uint32_t bytes, syncs, valid, invalid, overflows, timeouts, limits;
    bool overflow, armed, direct, spent;
    uint64_t lease_until, pulse_until, last_valid;
} receiver_t;

static inline void receiver_stop(receiver_t *s) {
    s->armed = s->direct = false;
    s->pwm_us = IDLE_US;
    s->pulse_until = 0;
}
static inline void receiver_init(receiver_t *s) {
    memset(s, 0, sizeof(*s));
    receiver_stop(s);
}
static inline void receiver_arm(receiver_t *s, uint64_t now, bool direct) {
    receiver_stop(s);
    s->spent = false;
    s->armed = true;
    s->direct = direct;
    s->lease_until = now + LEASE_US;
    s->last_valid = now;
    s->count = 0;
    s->overflow = false;
    if (direct) {
        s->pwm_us = ACTIVE_US;
        s->pulse_until = now + PULSE_US;
        s->spent = true;
    }
}
static inline void receiver_tick(receiver_t *s, uint64_t now) {
    if (!s->armed) return;
    if (now >= s->lease_until || (s->pulse_until && now >= s->pulse_until)) {
        ++s->limits;
        receiver_stop(s);
    } else if (!s->direct && now - s->last_valid >= WATCHDOG_US) {
        ++s->timeouts;
        receiver_stop(s);
    }
}
static inline void receiver_byte(receiver_t *s, uint8_t byte) {
    ++s->bytes;
    if (s->count < FRAME_BYTES) s->frame[s->count] = byte;
    else if (!s->overflow) { s->overflow = true; ++s->overflows; }
    if (s->count < UINT16_MAX) ++s->count;
}
static inline void receiver_sync(receiver_t *s, uint64_t now) {
    ++s->syncs;
    s->last_length = s->count;
    s->last_raw = s->count ? s->frame[0] : 0;
    bool good = s->count == FRAME_BYTES && !s->overflow;
    if (good) {
        good = s->frame[0] == 0 || s->frame[0] == TEST_RAW;
        for (unsigned i = 1; i < FRAME_BYTES; ++i) good &= s->frame[i] == 0;
    }
    s->count = 0;
    s->overflow = false;
    receiver_tick(s, now);
    if (!good) {
        ++s->invalid;
        receiver_stop(s);
        return;
    }
    ++s->valid;
    s->last_valid = now;
    if (s->direct) return; // USB-only stage; SPI cannot extend its one-second pulse.
    if (!s->last_raw) {
        s->pwm_us = IDLE_US;
        return;
    }
    if (s->armed && !s->spent) {
        s->pwm_us = ACTIVE_US;
        s->pulse_until = now + PULSE_US;
        s->spent = true;
    }
    // Once stopped by idle, this lease cannot start a second pulse.
}
#endif
