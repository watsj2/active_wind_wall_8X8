# Coaxial 8x8x2 Windwall System

Clean-start control system for a coaxial 8x8 wind wall with two motors per
wind pixel.

## System Shape

- Grid: 8 rows x 8 columns
- Coaxial planes: upstream and downstream
- Wind pixels: 64
- Motors: 128
- ESCs: 128 Pichler QX-45 units across both upstream and downstream planes
- Initial controller assumption: 16 controllers x 8 motor outputs

The project is intentionally separate from the older `active_wind_wall_8X8`
system. The old system was hard-saved before this project was created.

## Current Status

The control interface is a direct 8x8x2 extrapolation of the original German
6x6 group-and-signal workflow:

- New project files
- New 128-motor addressing model
- Real shared-SPI/GPIO transport as the only application runtime path
- German-derived PyQt6 experiment GUI for the coaxial grid
- Dark-mode operator interface
- Rival Lab-branded application header with a bundled official logo for
  offline, publication-ready screenshots
- Graphite instrument-panel styling with pale olive accents, a quiet motor grid,
  explicit status, and compact stacked safety controls
- Premade group library: whole wall, left/right halves, adjustable 2x2-7x7
  patches, and Pico 01-16, with a spatial preview and layer selection
- Per-group sine, square, constant, and custom Fourier signals
- Direct per-group constant PWM entry across the full 1000-2000 us range
- Direct upstream, downstream, or paired motor-group assignment within each
  grid cell: click `UP`, `DN`, or the center number respectively, or
  drag a desktop-style selection box across multiple cells, while preserving
  the fixed F/B hardware motor identifiers
- Timed experiments with explicit arm, stop, auto-disarm, and emergency stop
- Live selected-motor, selected-group, and wall-average PWM monitor
- Compact-by-default live monitor with an expandable signal plot
- JSON group/signal preset save and load
- Selected-pixel controller/channel inspector
- Optional `Show Pico grid` overlay with subtle `Pico 01`-`Pico 16` labels
  beside the physical pair numbers, without affecting selection or output
- Lightweight painted pixel cells that fill the available grid area
- Prominent physical pair labels: `01-32` on the left, `33-64` on the right
- Original 8x8 Pico-block motor numbering with harness-preserving controller mapping
- Color-coded 8x8x2 Pico/controller mapping image
- Defined v1 host-to-controller PWM protocol
- Built C01-C16 Pico UF2 firmware images for the current mapping
- No inherited Testo or unverified telemetry path

The controller positions and channels preserve the approved coaxial layout.
The motor numbers follow the proven 8x8 Pi/Pico wall and `Book.xlsx`.

The GUI labels match the physical pair identities: `01-32` occupy the left
four columns and `33-64` occupy the right four columns. The first row reads
`01 02 03 04 | 33 34 35 36`; the second reads
`05 06 07 08 | 37 38 39 40`. The Selected Pixel readout uses the same pair
number alongside the exact `F##`/`B##`, controller, and channel mapping.
This restores the left/right display split without changing motor addressing,
controller firmware, or saved group assignments.

## Motor Mapping

The fixed motor numbering follows the original 8x8 Pico blocks:

```text
R1 -> P01, P02, P03, P04, P33, P34, P35, P36
R2 -> P05, P06, P07, P08, P37, P38, P39, P40
R3 -> P09, P10, P11, P12, P41, P42, P43, P44
R4 -> P13, P14, P15, P16, P45, P46, P47, P48
R5 -> P17, P18, P19, P20, P49, P50, P51, P52
R6 -> P21, P22, P23, P24, P53, P54, P55, P56
R7 -> P25, P26, P27, P28, P57, P58, P59, P60
R8 -> P29, P30, P31, P32, P61, P62, P63, P64
```

The controller mapping preserves the old 8x8 harness where practical:

- `C01-C08` reuse the original 8x8 wiring.
- Adjacent old outputs become one coaxial pair: old outputs 1 and 2 are now
  `F01` and `B01`.
- `C09-C16` are new infill controllers for the middle positions.

Example: `C01` drives `P01`, `P04`, `P05`, and `P08`, with
upstream/downstream motors on adjacent channels. Their fixed hardware IDs
remain `F##`/`B##`.

Human-readable mapping:

```text
docs/MOTOR_CONTROLLER_MAPPING.md
```

Machine-readable mapping:

```text
config/motor_controller_mapping.csv
```

Color-coded 8x8x2 Pico/controller mapping image:

```text
docs/coaxial_8x8x2_pico_mapping.png
```

Host-to-controller PWM protocol:

```text
docs/HOST_CONTROLLER_PROTOCOL.md
```

Built Pico firmware:

```text
pico/firmware_c01.uf2
...
pico/firmware_c16.uf2
```

The approved motor-number change alters the compiled `HOST_INDICES` table in
all 16 firmware images. Keep every Pico in its existing physical `C01-C16`
position and keep `CH1-CH8` wiring unchanged, but reflash each controller with
its matching `firmware_cNN.uf2` before powered operation.

## GUI Tools

Click **Premade groups** in the left panel to add **Whole wall**, **Left half**,
**Right half**, a **2 × 2** through **7 × 7 patch**, or **Pico 01–16**.
Whole wall is the 8 × 8 selection. Choose both layers, upstream only, or
downstream only. Patch row/column fields set its top-left corner on the visible
grid; patches initially sit centrally (odd sizes use the upper-left of the
two possible central positions). The miniature map previews the selection.

Each motor belongs to one group. The picker reports how many assigned motors
will move to the new group; other motors stay in their existing groups.
New template groups start at **Constant 1000 µs**, ready for signal editing.
Adding a group sends no motor command and is disabled during an experiment.
Up to 32 groups can be saved, allowing all 16 Picos to have separate groups;
the eight group colors repeat. Existing saved sessions remain compatible.

The grid keeps physical left/right numbering, a visible gap between the halves,
and small optional Pico labels. Group colors appear as light tints and slim
markers. Constant mode shows its direct PWM field; waveform and harmonic
controls appear when relevant. The top bar displays DISARMED, ARMED, or RUNNING.

Hardware-free previews: [main interface](docs/gui_redesign_20260911.png) and
[premade group picker](docs/group_library_20260911.png).

The GUI follows the German wall's operating sequence:

1. Create or select a motor group.
2. Assign wind pixels directly on the grid: click a cell's `UP` section for
   its upstream motor, `DN` for its downstream motor, or the center number for
   both. To assign a rectangular region, press in one of those three sections,
   drag a selection box around the pixels, and release. The section where the
   drag began determines which plane is assigned across the box. The three
   `All` buttons provide the same choices for the full wall.
3. Configure that group's waveform, amplitude limits, period, phase, and any
   custom Fourier harmonics. For `Constant`, enter the exact PWM command in
   the `Constant PWM` field.
4. Set the experiment duration. Signal fractions use the full 1000-2000 us
   range; arming alone keeps every output at 1000 us idle until the experiment
   is started.
5. Arm the wall and start the timed experiment.
6. Observe the PWM trace; stop normally or use `EMERGENCY STOP` / `Esc`.

Enable `Show Pico grid` above the motor grid to show a small, muted `Pico 01`
through `Pico 16` label beside each prominent physical pair number. Neutral
borders and center strips keep group colors and selection easy to see.
The Pico numbers use the authoritative C01-C16 mapping. This is a display-only
diagnostic overlay; `UP`, `DN`, group assignments, and output are unchanged.

Runtime session state is stored locally in `config/gui_presets.json` and is
ignored by Git. Named presets can be saved to or loaded from any JSON file.
The derivation and frozen-interface rules are documented in
`docs/GERMAN_GUI_EXTRAPOLATION.md`.

## Display Performance

The GUI does not use 128 live progress-bar widgets for the pixel wall. Each
pixel is a lightweight painted cell with two drawn motor regions. The
byte-paced SPI transport runs through a bounded latest-frame worker instead of
blocking the Qt event loop; stale queued frames are replaced rather than
replayed. Motor commands are produced at the configured command rate, while
the visual grid is independently throttled by `GUI_REFRESH_HZ` in
`config/__init__.py`. Stop, disarm, and emergency-stop paths discard queued
runtime frames, wait for any active transfer to finish, and then send their
idle safety frame synchronously. The app opens maximized and keeps the live
plot collapsed until requested so the grid receives the available
screen height.

## Run

```bash
cd /home/jwatson/coaxial_8x8x2_windwall_system
python3 main.py
```

or:

```bash
./scripts/launch_gui.sh
```

The application has no mock or simulated-output mode. Every launch opens the
real SPI0/GPIO22 transport and sends a disarmed `1000 us` idle frame during
initialization. Verify the physical safe state before opening it; above-idle
output still requires explicit Arm and Start actions.

## Verification

```bash
python3 -m py_compile main.py config/__init__.py coaxial_windwall/*.py coaxial_windwall/*/*.py
python3 scripts/generate_motor_mapping.py --check
python3 -m unittest discover -s tests -v
```

Automated GUI and transport tests inject no-output test transports directly;
the application itself has no mock mode or simulated-output command-line path.

## Design Rule

Core motor control comes first. Telemetry, Testo mapping, and advanced monitor
views should only move into the main GUI after each has a small standalone test
that proves the data path is accurate and useful.

## Direct assignment layout

Square pixels sit between left/right shortcut columns. Each side has Both,
Upstream, and Downstream buttons plus its eight Pico buttons. Centered
2x2-7x7 patch buttons sit above the grid; choose their layers (also used by Pico
buttons) with the adjacent picker. Shortcuts assign motors to the currently
selected group and preserve its signal. Pressing again keeps them assigned.
Overlapping motors move from their former group, matching the bottom All buttons.
The original bottom buttons remain in place. Signal type, PWM and waveform
controls are on the right above experiment controls; group management stays left.

Square geometry is allocated directly by a Qt layout before paint, without
resize-event fixed-size changes. Startup and resized geometry are tested offline.
