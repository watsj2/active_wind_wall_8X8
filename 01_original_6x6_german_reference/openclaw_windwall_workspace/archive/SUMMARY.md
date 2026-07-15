# Pre-Pivot Windwall Summary

## Scope archived

This archive preserves all work completed before the decision to restart from the German wall 36-motor baseline and only expand after mastering that version.

Archived themes:
- 8x8 / 64-motor expansion planning
- Kitronik 3151 controller-board investigation
- Kitronik pin mapping and comms constraints
- Pico firmware skeletons and build scripts
- German wall repo snapshot under `upstream/`
- notes on Pi/Pico/motor bench testing and failed assumptions

## Important conclusions from archived work

1. The German wall architecture should be treated as the baseline, not merely inspiration.
2. The Kitronik 3151 boards complicated faithful expansion because their GPIO usage conflicted with the German comms pin layout.
3. Kitronik-based comms testing did not produce active motor response.
4. The project was re-based to a bare-Pico / German-pin-layout direction before the decision to fully pivot back to a 36-motor-first workflow.
5. UF2 firmware builds were successfully generated for the expansion firmware branch, but bench testing did not validate active command/control end-to-end.

## Archived files of note

- `mapping-spec.md`
- `german-wall-port-checklist.md`
- `pico-firmware-plan.md`
- `kitronik-3151-adaptation-note.md`
- `kitronik-3151-pinout.md`
- `kitronik-comms-pin-plan.md`
- `firmware-template-v1.md`
- `german-expansion-note.md`
- `pico/`
- `upstream/`

## Status at archive time

- firmware compiled for the expansion branch
- one Pico was flashed successfully
- direct active motor control testing did not produce motion
- the exact comms/output assumptions remained unresolved
- project direction changed to: copy the German 36-motor version exactly first, then expand only after mastery
