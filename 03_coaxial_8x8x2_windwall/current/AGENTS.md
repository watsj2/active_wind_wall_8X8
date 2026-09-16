# 8x8x2 Project Instructions

This folder is the 8x8 pixel, two-layer coaxial wall with 128 motors and 16
RP2350 controllers. When the user says `open 8x8x2`, `continue 8x8x2`, `back
to the 8x8x2`, `large coaxial wall`, or `128 motor wall`, read
`SESSION_HANDOFF.md` and `README.md` before acting.

- Do not confuse this project with the dedicated 2x2x2 X-501 experiment or
  the legacy single-layer `/home/jwatson/active_wind_wall_8X8` project.
- Preserve the approved harness mapping and generated `HOST_INDICES`; never
  infer controller ownership as a contiguous `controller_id * 8` block.
- Do not flash all controllers before the documented no-live-load C01 bench
  test succeeds.
- After material changes, run the relevant mapping/protocol/GUI verification
  and update the dated handoff plus `SESSION_HANDOFF.md` pointer.
