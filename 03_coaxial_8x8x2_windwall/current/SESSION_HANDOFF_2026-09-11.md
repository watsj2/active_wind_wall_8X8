# Coaxial 8x8x2 Windwall Handoff - 2026-09-11

## Latest: square grid, side shortcuts, signals on the right

Restored square cells using a dedicated Qt layout geometry pass; there is no
resizeEvent/setFixedSize feedback or deferred enlargement. The existing five
bottom buttons remain below the grid. Each side now has Both/Upstream/Downstream
half-assignment buttons and its correctly mapped Pico shortcuts: left C01-04,
C09-12; right C05-08, C13-16. Centered 2x2-7x7 patch buttons sit above the grid;
the adjacent layer picker applies to patch and Pico shortcuts.

Shortcuts add assignments to the selected group, move overlapping motor owners,
and preserve its name and waveform. Repeated presses do not toggle assignments
off. They are blocked during runs and send no motor command. New from template
remains an optional way to create a separate named group. Signal/PWM/waveform
controls now sit in the scrollable right panel above experiment controls; group
management stays left. The narrower group panel preserves 1366x900 fit.

All 51 hardware-free tests pass, including square sizing across three window
sizes, stable first paint, direct-button mappings and layer choice, repeated
assignment, running lockout, preserved signals/no-output, and control location.
Mapping validation, compilation, and offscreen visual review pass. Preview:
`docs/gui_side_shortcuts_20260911.png`. No live GUI launch, motor command,
firmware/mapping change, or operator-preset edit occurred.


## Native grid layout and graphite styling - latest

The operator correctly identified a visible startup resize. Removed the grid's
resizeEvent/setFixedSize feedback loop entirely. MotorCellGrid now uses native
QGridLayout equal row/column stretches and expanding PairCell widgets, with
the existing fixed central gutter. The launch path sets available-screen
geometry before showing maximized. No timer, delayed resize, hidden-window
workaround, or hardware action was introduced.

The visual direction now combines neutral graphite panels, pale olive accents,
soft corners, restrained group marks, and state-specific status badges. Long
group names elide with full tooltips instead of creating horizontal scrollbars.
Preview: `docs/gui_graphite_20260911.png`. The previous source is preserved in
`recovery_20260911_before_native_layout/`.

All 48 hardware-free tests, mapping validation and compilation pass, including
a first-paint test proving all 64 cell geometries remain stable across subsequent
offscreen event processing, plus resize/edge-fill tests. Actual desktop-window
manager startup has not been observed; no real GUI was launched for verification.
No motor command, firmware change, mapping change, or preset edit was made.
The operator's preset has changed since the earlier right-half snapshot; do not
infer current assignments from that older record.


## Grid fills the panel - latest update

The operator disliked the wide empty margins around the grid. Cells now size
their width and height independently, filling the panel rather than preserving
a square aspect ratio. Reduced panel padding/spacing; retained the central
left/right gap and UP/pair/DN hit targets. The visible startup resizing comes
from maximization/layout sizing, not motor state. All 47 hardware-free tests
pass, including edge-fill checks at 1366x900, 1600x1000, and 1920x1080.
The refreshed offscreen preview is `docs/gui_redesign_20260911.png`.
No real GUI was launched, no motor command was sent, and no preset was changed.


## Latest: interface redesign and premade groups

The operator requested a full visual redesign and premade spatial groups.
The GUI now uses slate panels, mint accents, a quieter tinted motor grid,
slim group-color markers, a visible left/right gap, a status badge, and clearer
experiment controls. Irrelevant signal controls are hidden in Constant mode.
Physical numbering and small optional Pico labels remain intact.

The **Premade groups** button opens a picker with Whole wall, Left half,
Right half, 2x2-7x7 patches, and Pico 01-16. It supports both/upstream/downstream
layers, editable patch origin, a miniature spatial preview, and an overlap
count before adding. Assigned motors move to the new group under the existing
one-owner rule. New groups start at Constant 1000 us and adding sends no
hardware frame; the picker is blocked during an experiment. The saved-group
limit is now 32 (colors cycle) so all 16 Picos can have separate groups.
No template has been applied to the operator's saved preset.

Verified all Pico templates against controller host-index tables, all square
positions and layers, left/right partition, overlap movement, idle defaults,
no-output creation, running lockout, 16-Pico session reload, and 1366x900 fit.
All 46 hardware-free tests, compilation, and generated mapping validation pass.
Offscreen main-window and picker previews were visually inspected. Artifacts:
`docs/gui_redesign_20260911.png`, `docs/group_library_20260911.png`.
The pre-redesign GUI, tests, README, and preset are preserved in
`recovery_20260911_before_redesign/`.
Mapping/model, transport/protocol, all 16 UF2 images, and the saved preset
remain unchanged. No real GUI launch or hardware command occurred.

## Subtle Pico overlay

The operator requested a quieter Pico grid with explicit Pico numbers.
Removed the saturated controller borders and center fills. The overlay now
uses neutral borders/centers, a prominent physical pair number, and a smaller
muted `Pico 01`-`Pico 16` label. Selection remains visible with the overlay on.
Controller identity still comes from the authoritative address model.
Inspected a 1600x1000 offscreen preview using injected no-output transports;
mapping validation and all 38 hardware-free tests pass. No real GUI launch,
motor command, firmware change, or preset change occurred.

## Left/right GUI numbering restored

At the operator's request, grid labels and the Selected Pixel readout now use
the existing physical pair number: 01-32 in the left four columns, 33-64 in
the right four columns. Tooltips and the optional Pico overlay inherit the
same labels. First row: `01 02 03 04 | 33 34 35 36`.

This supersedes the row-major display numbering in earlier handoffs. C01's
visible labels now match physical P01/P04/P05/P08: **01/04/05/08**.
The underlying motor addressing, controller mapping, protocol, transport,
all 16 UF2 files, and saved preset were verified byte-for-byte unchanged.
The saved `normal` group currently owns physical pairs 33-64 on both layers
(64 motors), at Constant 1200 us; other saved groups are empty.

Updated the existing GUI numbering test and README. All 38 hardware-free
tests, generated mapping validation, and GUI compilation pass. No real GUI
was launched, no hardware command sent, and no firmware flashed. The Desktop
launcher will load the updated labels on its next launch.

For the last hardware checkpoint, see `SESSION_HANDOFF_2026-09-09.md`: new Pi
and isolated C01 wiring passed bench diagnostics; C01 was restored to its
full-wall firmware, and C02-C16 were unchanged. Hardware power and wiring
state were not verified today.
