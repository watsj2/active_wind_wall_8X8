#include <assert.h>
#include <stdio.h>
#include "receiver.h"

static void frame(receiver_t *s, unsigned length, uint8_t raw, uint64_t now) {
    for (unsigned i = 0; i < length; ++i) receiver_byte(s, i ? 0 : raw);
    receiver_sync(s, now);
}
int main(void) {
    receiver_t s;
    receiver_init(&s);
    assert(s.pwm_us == IDLE_US && !s.armed);
    frame(&s, 36, TEST_RAW, 0);
    assert(s.valid == 1 && s.pwm_us == IDLE_US); // Boot cannot activate.

    receiver_arm(&s, 100, false);
    frame(&s, 36, TEST_RAW, 200);
    assert(s.pwm_us == ACTIVE_US);
    for (uint64_t t = 20200; t < 1000200; t += 20000) frame(&s, 36, TEST_RAW, t);
    receiver_tick(&s, 1000200);
    assert(s.pwm_us == IDLE_US && !s.armed && s.limits == 1);
    frame(&s, 36, TEST_RAW, 1000300);
    assert(s.pwm_us == IDLE_US); // Repeated active frames cannot extend/restart.

    receiver_arm(&s, 2000000, false);
    frame(&s, 36, TEST_RAW, 2000100);
    receiver_tick(&s, 2200100);
    assert(s.pwm_us == IDLE_US && s.timeouts == 1);

    const unsigned lengths[] = {0, 1, 35, 37, 266, 1000};
    for (unsigned i = 0; i < sizeof(lengths)/sizeof(lengths[0]); ++i) {
        receiver_arm(&s, 3000000, false);
        frame(&s, lengths[i], TEST_RAW, 3000100);
        assert(!s.armed && s.pwm_us == IDLE_US);
    }
    for (unsigned raw = 1; raw < 256; ++raw) {
        if (raw == TEST_RAW) continue;
        receiver_arm(&s, 4000000, false);
        frame(&s, 36, raw, 4000100);
        assert(s.pwm_us == IDLE_US && !s.armed);
    }
    for (unsigned bad = 1; bad < FRAME_BYTES; ++bad) {
        receiver_arm(&s, 5000000, false);
        for (unsigned i = 0; i < 36; ++i) receiver_byte(&s, i == 0 || i == bad ? TEST_RAW : 0);
        receiver_sync(&s, 5000100);
        assert(s.pwm_us == IDLE_US && !s.armed);
    }
    receiver_arm(&s, 6000000, false);
    frame(&s, 36, TEST_RAW, 6000100);
    frame(&s, 36, 0, 6000200);
    assert(s.pwm_us == IDLE_US);
    frame(&s, 36, TEST_RAW, 6000300);
    assert(s.pwm_us == IDLE_US); // Cannot restart inside spent lease.

    receiver_arm(&s, 7000000, true);
    assert(s.pwm_us == ACTIVE_US);
    receiver_tick(&s, 7300000);
    assert(s.pwm_us == ACTIVE_US); // USB test does not require SPI heartbeat.
    receiver_tick(&s, 8000000);
    assert(s.pwm_us == IDLE_US && !s.armed);
    receiver_arm(&s, 9000000, true);
    receiver_stop(&s);
    assert(s.pwm_us == IDLE_US && !s.armed);
    receiver_arm(&s, 10000000, false);
    for (uint64_t t=10000000; t<14000000; t+=20000) frame(&s,36,0,t);
    receiver_tick(&s, 14000000);
    assert(!s.armed && s.pwm_us == IDLE_US);
    puts("PASS: boot lock, exact frame, every forbidden byte/channel, overflow, idle/stop, watchdog, USB deadline, SPI deadline, lease expiry");
}
