## September 15 oscilloscope clock check underway

Operator connected FNIRSI 2C53P CH1 to Pi SCLK GPIO11/physical pin 23 with
instructed ground at physical pin 25. First idle-stream attempt aborted because
GUI had reopened. Subsequently terminated canonical GUI and started a bounded
30-second stream of disarmed 1000 us frames for scope inspection. No above-idle
command in this check. Await operator waveform observation before interpreting
Pi clock or C01 reception.

## September 15 measured C01 command-response failure

Operator observed no motion in the prior eight-motor pulse. Confirmed C01 GP0
to Pi GPIO23 jumper remains attached. Input-only baseline measured 150 pulses,
50 Hz, approximately 996-997 us median, no malformed edges. Under continuing
explicit real-test authorization, sent only F01/C01 GP0 1200 us for one second
(35 active frames), then disarmed idle. Concurrent seven-second capture measured
approximately 998 us throughout, 50 Hz, no malformed edges, maximum 1005.22 us:
no 1200 us response. GUI remained closed. This confirms C01 idle PWM but absent
command response; it does not distinguish physical bus reception from firmware
frame rejection/latching. Propulsion remains treated as connected. No firmware,
preset or mapping changes. Log: `logs/20260915_c01_pulse_capture.txt`.

# September 15 checkpoint

## 2026-09-15: cold-start no-motion diagnosis

Operator reports all motors worked the previous day; batteries were removed for
charging and all Pi/Pico power went out. After restart ESCs give connected tones,
but GUI RUNNING with increasing frames produces no observed motion. Canonical
GUI PID 1909 owned SPI0.0 and gpiochip15; SPI counters increased without reported
errors. Source mtimes remain September 11 or earlier. Saved preset assigns only
both layers of P16/P20/P45/P49 at 1200 us (eight motors).

At explicit operator authorization for a real spin attempt, terminated GUI PID
1909, waited for exit, and used canonical transport for a one-second 1200 us
pulse on those eight motors: 35 active frames, followed by successful disarmed
1000 us shutdown. GUI remains closed. Movement awaits operator observation;
host transmission is not proof of Pico reception. Propulsion is treated as
connected. No firmware, mapping, or preset changed. Result:
`logs/20260915_bounded_pulse.json`.

