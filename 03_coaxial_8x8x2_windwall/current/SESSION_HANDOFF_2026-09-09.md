# Coaxial 8x8x2 Windwall Handoff - 2026-09-09

## Current saved state

The cloned SD image is running on the new Raspberry Pi 5. The new direct
five-wire path to C01 passed the isolated bench diagnostics. The GP0 to Pi
GPIO23 input tap is present and measured clean 50 Hz idle PWM at about 995 us.

C01 was flashed back from the one-motor diagnostic firmware to the matching
full-wall image:

```text
pico/firmware_c01.uf2
SHA-256 bc75d1c1746c08ac0d424221fefe734af88f3008d888f30923839eaea899700c
```

C02-C16 were not changed; they remain on their known-working full-wall
firmware. The recorded September 4 GUI/runtime source was restored.
Compilation, generated mapping validation, and all 38 hardware-free tests
pass.

The exact September 4 16:00 mutable preset was not separately preserved, so
`config/gui_presets.json` was left as-is. The C01 layout is:

```text
C01 physical P01/P04/P05/P08 -> visible GUI pairs 01/04/09/12
C01 channels CH1-CH8         -> F01/B01/F04/B04/F05/B05/F08/B08
```

The application and diagnostic bench are stopped. C01 is idle/disarmed.

## Restart after reconnecting the wall

1. With propulsion batteries disconnected, reconnect the complete C01-C16
   five-wire harness and all ESC signal wiring. Keep Pi and controller USB
   power off while making connections.
2. Restore Pi/controller USB power first. Confirm the boards remain in their
   existing C01-C16 positions and no BOOTSEL drive is present.
3. Confirm ESC outputs are idle before connecting propulsion power.
4. Connect propulsion batteries last, with the mechanical area clear.
5. Launch the restored application:

```bash
cd /home/jwatson/coaxial_8x8x2_windwall_system
./scripts/launch_gui.sh
```

6. Verify the GUI starts disarmed at 1000 us. Test a small known group before
   expanding. To target all four C01 pixel pairs, use visible GUI pairs 01,
   04, 09, and 12 and select each pair center for both motors.

Do not use `bench/german_one_motor/bench.py` after C01 has the full-wall
image; that diagnostic expects the one-motor firmware and 36-byte protocol.
The operator GUI uses the full-wall 266-byte protocol.
