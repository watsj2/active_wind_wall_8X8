# Physical Upgrade Checklist: 64 Motors to Coaxial 8x8x2 / 128 Motors

This checklist is for the physical upgrade from the existing 8x8 / 64-motor
wind wall to the new coaxial 8x8x2 / 128-motor system.

Assumptions:

- Keep the 8x8 wind-pixel layout.
- Add one coaxial motor behind or in front of each existing motor.
- Use `P01-P64` for wind-pixel pairs.
- Use `F01-F64` for front-layer motors and `B01-B64` for back-layer motors.
- Keep the current style of 8 motor outputs per Pico/controller unless a new
  controller architecture is chosen.

## 1. Lock Down Physical Naming

- Decide which physical side is `Front`.
  - Recommended: `Front` means the side the operator sees from the normal
    working position.
- Label the existing 64 motors as either `F01-F64` or `B01-B64`.
  - Do not mix this later.
- Label every wind pixel `P01-P64`.
- Define orientation permanently:
  - `R1` = top row from operator/front view.
  - `R8` = bottom row from operator/front view.
  - `C1` = left column from operator/front view.
  - `C8` = right column from operator/front view.
- Put durable labels on the frame, motor leads, ESC leads, and controller
  outputs before unplugging anything.

## 2. Decide Controller Count and Placement

Current controller architecture:

- Reuse the existing old 8x8 harness where practical.
- Add 8 additional Picos/controllers for the middle positions.
- New total: 16 Picos/controllers.
- Each controller handles 8 motors.
- Each controller handles 4 coaxial wind pixels, with front/back on adjacent
  channels.

Final software controller grouping for this baseline is harness-preserving:

```text
C01-C08  -> reused old 8x8 harness controllers
C09-C16  -> new infill controllers
```

Example old-harness controller:

```text
C01 CH1/GP0 -> F01
C01 CH2/GP1 -> B01
C01 CH3/GP2 -> F04
C01 CH4/GP3 -> B04
C01 CH5/GP4 -> F09
C01 CH6/GP5 -> B09
C01 CH7/GP6 -> F12
C01 CH8/GP7 -> B12
```

Use the generated mapping before labels or wiring are made permanent:

```text
docs/MOTOR_CONTROLLER_MAPPING.md
config/motor_controller_mapping.csv
docs/LAYER_FIRST_WIRING_PLAN.md
docs/Coaxial_Windwall_Wiring_Assembly_Manual.pdf  # not regenerated for this map yet
```

Do not wire from the older pair-first or layer-first plane-split drafts.

## 3. Inventory Parts

Add or verify:

- 64 additional motors.
- 64 additional ESCs or motor drivers.
- 8 additional Pico/controller boards if keeping 8 outputs per controller.
- Controller mounting hardware.
- Power distribution hardware rated for the doubled current.
- Fuses or breakers per supply branch.
- Main emergency stop rated for the new total current.
- Wire sized for the expected current and run length.
- Signal wire harnesses for 64 additional PWM outputs.
- Common ground wiring between Pi, Picos, ESC signal grounds, and power system.
- Extra USB cables or programming access for the added Picos.
- Cooling or airflow for the added ESCs and power distribution.
- Cable labels, heat shrink, ferrules, strain relief, and cable lacing.
- Motor guards or screen updates if the added layer exposes moving parts.

For power capacity, calculate from real motor/ESC data:

```text
required_current = 128 * max_expected_motor_current
supply_current_rating >= required_current * safety_margin
```

Use a safety margin appropriate for your motor startup behavior and test plan.

## 4. Mechanical Upgrade

- Power down and physically lock out the wall before mechanical work.
- Photograph the existing wiring and controller layout.
- Measure current motor spacing, depth clearance, and airflow path.
- Design second-layer mounts so each new motor aligns with its matching
  existing wind pixel.
- Keep enough spacing between coaxial motors for the selected prop/fan setup.
- Check that both motors in a pair move air in the intended wall direction.
- If using propellers, confirm front/back motor rotation and prop type:
  - Do not assume identical props and identical rotation will produce the
    desired coaxial flow.
  - Mark CW/CCW motors and props clearly.
- Add vibration isolation where needed.
- Add strain relief near every motor and ESC.
- Keep ESCs accessible for replacement.
- Keep power wiring physically separated from low-voltage signal wiring where
  practical.
- Confirm no motor, prop, or fan can contact wiring at full vibration.

## 5. Power System Upgrade

- Recalculate total current draw for 128 motors.
- Confirm the existing supply cannot be overloaded by the doubled system.
- Upgrade supplies or add supply banks as required.
- Add branch protection so a fault in one area does not take out the whole wall.
- Verify all grounds are common where signal references require it.
- Avoid ground loops where high-current motor return paths share fragile signal
  return paths.
- Confirm connector ratings for continuous current, not only peak current.
- Add clear power-bank labels:
  - Which motors/controllers each bank feeds.
  - Voltage.
  - Fuse/breaker rating.
- Test power distribution with motors disconnected first.
- Test ESC/controller power with motors disconnected or props removed where
  safe and practical.

## 6. Controller and Signal Wiring

For each Pico/controller in the current architecture:

- PWM outputs are Pico `GP0-GP7`.
- Current tach inputs, if used, are Pico `GP8-GP15`.
- SPI pins:
  - `GP16` = MOSI from Pi.
  - `GP17` = CE0 / chip select from Pi.
  - `GP18` = SCLK from Pi.
  - `GP19` = MISO to Pi if tach/readback is used.
  - `GP22` = sync input from Pi.

Physical tasks:

- Mount the added controllers.
- Route Pi SPI/sync wiring to all controllers according to the final protocol.
- Keep SPI wiring short and tidy; avoid long loose daisy chains.
- Make the added controllers easy to identify physically.
- Label each controller with its intended controller number and motor range.
- Wire each controller output to the intended motor/ESC signal input.
- Tie signal ground from each ESC/controller group back to the common reference.
- Do not connect added controller PWM outputs to live ESCs until firmware and
  host protocol have been verified with no-output automated tests and bench
  tests.

Important: the old firmware only knows 8 Picos and 64 motors. The physical
upgrade can be wired, but do not run the new 128-motor wall from old firmware or
old host code.

## 7. Tach / Telemetry Wiring, If Used

Telemetry was not reliable/useful enough in the old system, so treat this as
optional and staged.

If tach wiring is added:

- Add 64 more tach signal wires for the second layer.
- Confirm every tach signal is 3.3V-safe before connecting to Pico GPIO.
- Use Pico `GP8-GP15` for local tach inputs if keeping the old pin pattern.
- Keep tach wiring labeled by motor ID, not just by row/column.
- Do not rely on telemetry for safety until a standalone readback test proves
  it works.

Recommended staging:

1. Run 128-motor PWM control without tach.
2. Add tach to one controller.
3. Prove tach readback on the bench.
4. Expand tach wiring controller by controller.

## 8. Labeling Standard

Every physical item should have a human-readable label:

- Wind pixel: `P01-P64`.
- Front motor: `F01-F64`.
- Back motor: `B01-B64`.
- Controller: `C01-C16`.
- Controller output: `C03-CH5`, etc.
- ESC signal lead: matching motor ID.
- ESC power lead: matching motor ID or branch ID.
- Power branch: voltage and fuse/breaker rating.

Recommended example:

```text
P01
F01 -> C01-CH1
B01 -> C01-CH2
```

Use the final mapping table before committing labels permanently.

## 9. Bring-Up Order

Do not bring up 128 motors all at once.

Recommended physical bring-up:

1. Power off. Verify all labels and wiring against the map.
2. Power the Pi only.
3. Power the controllers only.
4. Confirm every controller boots and can be identified.
5. Flash only bench-safe firmware.
6. Test C01 with no motors connected.
7. Test one C01 ESC/motor pair at idle.
8. Test one coaxial pair at low PWM.
9. Test one full column or one controller group.
10. Test one layer only.
11. Test both layers at low PWM.
12. Test groups.
13. Test all 128 only after branch current, heat, vibration, and idle behavior
    are verified.

## 10. Safety Checks Before First Real Run

- Emergency stop works under load.
- All motors idle when software exits.
- All motors idle when sync/command signal is lost.
- Power branches are fused.
- No exposed moving parts.
- No loose wires near motors.
- ESCs are not overheating at idle or low PWM.
- Supply voltage does not sag dangerously during startup.
- All grounds are common where required.
- The GUI has no simulated-output mode. Treat every application launch as a
  real SPI/GPIO session and verify the physical safe state before opening it.

## 11. Things Not To Do

- Do not reuse old 64-motor firmware for the 128-motor wall.
- Do not use negative motor numbers as physical labels.
- Do not run all motors as the first test.
- Do not add tach telemetry to all 128 motors before proving one controller.
- Do not route high-current motor wiring and fragile signal wiring in the same
  loose bundle without planning.
- Do not trust GUI display values as proof of physical motor output.

## 12. Deliverables Needed Before Full 128-Motor Operation

- Final motor mapping table.
- Final controller mapping table.
- Updated 16-controller firmware plan.
- Updated host protocol for 128 motors.
- Bench test for one new controller.
- Single-pair physical test.
- Power/current test results.
- Emergency-stop verification.
- A fallback idle procedure.
