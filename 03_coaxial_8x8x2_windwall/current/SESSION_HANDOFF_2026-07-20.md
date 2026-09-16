# Coaxial 8x8x2 Windwall Handoff - 2026-07-20

## Current Hardware Result

The AIR 40 failure was isolated from the host software and C03 firmware and is
now resolved.

The user performed an ESC substitution on the known-working F20/C03 CH3 path:

```text
F20 with Pichler XQ-45 -> worked
F20 with T-MOTOR AIR 40 -> did not work
F20 restored to XQ-45 -> worked
```

The failure follows the AIR 40 ESC. The same Pico, host index, generated frame,
PWM channel, harness path, and motor position work with the XQ-45. Do not
reflash C03 or change the C03 host-index mapping for this symptom.

The user reported that the AIR 40 produces its main power-on tones but never
produces the ready/arming indication heard from the XQ-45. This proves main
power reaches the AIR 40 and the motor can generate tones, but strongly
indicates that the ESC is not recognizing a valid low-throttle signal.

The user then reversed the AIR 40 black/yellow terminals in its plug. The AIR
40 immediately worked. This functionally confirms that AIR 40 black is signal
ground and yellow is PWM signal, and that its original plug order was reversed
relative to the working XQ-45 harness. Preserve this repinning for every AIR 40
installed on an XQ-45-style wall connector.

The proven legacy wall was inspected for comparison. Its bench path held all
outputs at continuous `1000 us` for three seconds before applying a command,
and its first non-idle running value was `1200 us`. The current RP2350 firmware
also continuously generates `1000 us` at idle. Do not globally change the
idle endpoint based only on this AIR 40 symptom.

The F20 AIR 40 installation was a diagnostic substitution only. It does not
change the canonical mapping, which still assigns Pichler XQ-45 ESCs to the
front layer and AIR 40 ESCs to the back layer.

## AIR 40 Checks Required

The official AIR 40 product information identifies it as a 2-6S no-BEC ESC
with a twisted-pair throttle cable, but does not label the black/yellow wire
colors. The working hardware test establishes this project-specific wiring:

```text
AIR 40 black  -> controller/harness ground (XQ-45 black position)
AIR 40 yellow -> controller PWM output (XQ-45 white position)
```

For any untouched AIR 40 plug, work with all ESC and controller power removed:

1. Measure continuity/resistance from the AIR 40 thin black throttle wire to
   its heavy black battery-negative lead. Near-zero resistance/continuity
   identifies the thin black wire as signal ground; yellow is then PWM signal.
2. Put AIR 40 black in the harness position used by XQ-45 black, and AIR 40
   yellow in the position used by XQ-45 white. This terminal order has now
   passed a powered functional test.
3. Do not repin solely from wire color if the continuity result is absent or
   ambiguous; obtain the model-specific pinout or instrument the isolated ESC.
4. AIR 40 main red/black power leads receive the correct supply. The throttle
   connector does not power this no-BEC ESC.
5. Record the motor/ESC power-on tones or status indication while the
   controller is already producing idle PWM.
6. Measure the PWM at the AIR 40 connector between its confirmed signal and
   signal-ground wires. Expected current-controller output is a 3.3 V, 50 Hz
   waveform with a `1000 us` high pulse at idle.

Official product page:

```text
https://store.tmotor.com/product/air-40a-6s-esc.html
```

Do not change the global firmware idle pulse or add an AIR 40 calibration
sequence for this symptom; correcting the black/yellow plug order resolved it.

## Software and Controller State

- The 266-byte `CW` protocol and harness-preserving mapping remain unchanged.
- C01 was flashed and the user reported that it worked.
- C02 was flashed but has not been separately functionally recorded.
- C03 was flashed; P20 working confirms that C03 booted and receives commands.
  The earlier BOOTSEL virtual-volume warning did not prevent C03 operation.
- C04 was flashed on 2026-07-20 with `pico/firmware_c04.uf2`. Its SHA-256 is
  `e3ee3f1870d282c02f729706c136f242ea08340a3a9942a9382fc14db7cc40a9`.
  The RP2350 BOOTSEL volume automatically disconnected after the UF2 copy,
  indicating the expected reboot; C04 has not yet been functionally verified.
- C05 was flashed on 2026-07-20 with `pico/firmware_c05.uf2`. Its SHA-256 is
  `6d0465f74039f2d15387ade1a1de8dcdedcb4d2e90df9b18c7a6725134c069e6`.
  The RP2350 BOOTSEL volume automatically disconnected after the UF2 copy,
  indicating the expected reboot; C05 has not yet been functionally verified.
- C06 was flashed on 2026-07-20 with `pico/firmware_c06.uf2`. Its SHA-256 is
  `5ffaea6eec7cea34e8b70106ce9fbe4eb07ff618547a830cc39ac879e97cb5f5`.
  It was mounted at `/home/jwatson/rp2350_mount`; after the UF2 copy and
  `sync`, the RP2350 disappeared from USB as expected. C06 has not yet been
  functionally verified. Use this in-home mount for C07-C16 to avoid separate
  external-media copy approvals for every firmware filename.
- C07 was flashed on 2026-07-20 with `pico/firmware_c07.uf2`. Its SHA-256 is
  `c9ac3305719fe3783b593c7c43caba27bc0949a1e27526817e33de53cbbc8bc3`.
  After the UF2 copy and `sync`, the RP2350 disappeared from USB as expected;
  C07 has not yet been functionally verified.
- C08 was flashed on 2026-07-20 with `pico/firmware_c08.uf2`. Its SHA-256 is
  `a98dde8f77ef002bc6b7ccb01133129927571caee272d0742ea171fe790c0a93`.
  After the UF2 copy and `sync`, the RP2350 disappeared from USB as expected;
  C08 has not yet been functionally verified.
- C09 was flashed on 2026-07-20 with `pico/firmware_c09.uf2`. Its SHA-256 is
  `cec52021ebfd1911c70593115ff6e9c5ee1c3a4c471cb141d3cb1c0a0432546b`.
  After the UF2 copy and `sync`, the RP2350 disappeared from USB as expected;
  C09 has not yet been functionally verified.
- C10 was flashed on 2026-07-20 with `pico/firmware_c10.uf2`. Its SHA-256 is
  `27c7aa8166c2637649966d9e6d8029c40839e2bfcf34a54cb3f4935852065563`.
  After the UF2 copy and `sync`, the RP2350 disappeared from USB as expected;
  C10 has not yet been functionally verified.
- C11 initially failed to enumerate, then appeared correctly after the user
  repeated BOOTSEL. It was flashed on 2026-07-20 with
  `pico/firmware_c11.uf2`, SHA-256
  `cf564b2ced123f0927dcac42fd665be2b2166dbfb8b278e589d4b329895ccd38`.
  After the UF2 copy and `sync`, the RP2350 disappeared from USB as expected;
  C11 has not yet been functionally verified.
- C12 was flashed on 2026-07-20 with `pico/firmware_c12.uf2`. Its SHA-256 is
  `7eaef6594209642a77256c00ca2c8cfdf450d3013261dc4aa82bd6d4dc936a3d`.
  After the UF2 copy and `sync`, the RP2350 disappeared from USB as expected;
  C12 has not yet been functionally verified.
- The user's `11333` entry was interpreted as C13 because C13 was next and a
  new RP2350 BOOTSEL volume was present. C13 was flashed on 2026-07-20 with
  `pico/firmware_c13.uf2`, SHA-256
  `bf563330734c29f065214b62595636f9c1b7022cf2f3cd01b1c9a1eca1d0ba6d`.
  After the UF2 copy and `sync`, the RP2350 disappeared from USB as expected;
  C13 has not yet been functionally verified.
- C14 was flashed on 2026-07-20 with `pico/firmware_c14.uf2`. Its SHA-256 is
  `737ab81acee09adbbb0b3b0796383e42d03adc3a29698a424cac2941a01b83ee`.
  After the UF2 copy and `sync`, the RP2350 disappeared from USB as expected;
  C14 has not yet been functionally verified.
- C15 was flashed on 2026-07-20 with `pico/firmware_c15.uf2`. Its SHA-256 is
  `452949f63aaa0da5b0944bec8ef4a400de7c35e60edd66d9043d822076abc6fe`.
  After the UF2 copy and `sync`, the RP2350 disappeared from USB as expected;
  C15 has not yet been functionally verified.
- C16 was flashed on 2026-07-20 with `pico/firmware_c16.uf2`. Its SHA-256 is
  `940ea88cf29ecc1131fb278df9a5f0fbc99e84a4e5c2766694e365bb49f8aab5`.
  After the UF2 copy and `sync`, the RP2350 disappeared from USB as expected;
  C16 has not yet been functionally verified.
- The complete physical C01-C16 flashing pass is now finished. C01 was
  reported working and C03 is functionally confirmed by P20; C02 and C04-C16
  are flashed but still require controlled functional verification.
- Constant signal mode now has direct `1000-2000 us` PWM entry, capped by the
  selected Experiment output ceiling.
- The direct-PWM change passed 16 unit tests, mapping validation, and the mock
  GUI smoke test.

For the complete flash hashes, USB serials, and earlier test chronology, see
`SESSION_HANDOFF_2026-07-19.md`.

## Next Safe Step

Before bringing up additional AIR 40 channels, make moving parts safe and
inspect/repin each unverified throttle plug with power removed: black to the
XQ-45 black/ground harness position and yellow to the XQ-45 white/PWM harness
position. Bring up one channel at a time and confirm its ready/arming indication
before commanding motion. No C03 reflash or AIR 40-specific PWM change is
needed for the resolved F20 test.
