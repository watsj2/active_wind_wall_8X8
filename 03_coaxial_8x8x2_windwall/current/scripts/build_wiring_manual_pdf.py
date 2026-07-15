#!/usr/bin/env python3
"""Build an assembly-style wiring manual PDF for the coaxial windwall."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from coaxial_windwall.model import PIXEL_NUMBER_GRID  # noqa: E402
from scripts.generate_motor_mapping import mapping_rows  # noqa: E402


DOCS_OUTPUT = PROJECT_ROOT / "docs" / "Coaxial_Windwall_Wiring_Assembly_Manual.pdf"
DESKTOP_OUTPUT = Path.home() / "Desktop" / "Coaxial_Windwall_Wiring_Assembly_Manual.pdf"

PAGE_W, PAGE_H = letter
MARGIN = 0.55 * inch
BLUE = colors.HexColor("#0b5cab")
YELLOW = colors.HexColor("#ffcc00")
INK = colors.HexColor("#171717")
MID = colors.HexColor("#5f6368")
LIGHT = colors.HexColor("#f4f6f8")
GRID = colors.HexColor("#d8dde3")
FRONT = colors.HexColor("#dbeafe")
BACK = colors.HexColor("#dcfce7")
WARN = colors.HexColor("#fff3bf")


def set_font(c: canvas.Canvas, name: str, size: int, color=INK) -> None:
    c.setFont(name, size)
    c.setFillColor(color)


def draw_wrapped(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    width: float,
    size: int = 9,
    leading: int = 12,
    font: str = "Helvetica",
    color=INK,
) -> float:
    words = text.split()
    lines: list[str] = []
    line = ""
    c.setFont(font, size)
    for word in words:
        candidate = f"{line} {word}".strip()
        if c.stringWidth(candidate, font, size) <= width:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)

    set_font(c, font, size, color)
    for item in lines:
        c.drawString(x, y, item)
        y -= leading
    return y


def hline(c: canvas.Canvas, y: float) -> None:
    c.setStrokeColor(GRID)
    c.setLineWidth(1)
    c.line(MARGIN, y, PAGE_W - MARGIN, y)


def draw_header(c: canvas.Canvas, step: str, title: str, subtitle: str = "") -> None:
    c.setFillColor(BLUE)
    c.rect(0, PAGE_H - 0.48 * inch, PAGE_W, 0.48 * inch, fill=1, stroke=0)
    c.setFillColor(YELLOW)
    c.rect(PAGE_W - 1.25 * inch, PAGE_H - 0.48 * inch, 0.7 * inch, 0.48 * inch, fill=1, stroke=0)
    if step:
        c.setFillColor(YELLOW)
        c.roundRect(MARGIN, PAGE_H - 1.08 * inch, 0.72 * inch, 0.72 * inch, 8, fill=1, stroke=0)
        set_font(c, "Helvetica-Bold", 24)
        c.drawCentredString(MARGIN + 0.36 * inch, PAGE_H - 0.86 * inch, step)
        x = MARGIN + 0.92 * inch
    else:
        x = MARGIN
    set_font(c, "Helvetica-Bold", 22)
    c.drawString(x, PAGE_H - 0.72 * inch, title)
    if subtitle:
        draw_wrapped(c, subtitle, x, PAGE_H - 0.95 * inch, PAGE_W - x - MARGIN, 9, 11, color=MID)
    hline(c, PAGE_H - 1.22 * inch)


def draw_footer(c: canvas.Canvas, page: int) -> None:
    hline(c, 0.45 * inch)
    set_font(c, "Helvetica", 7, MID)
    c.drawString(MARGIN, 0.27 * inch, "Coaxial 8x8x2 Windwall - wiring assembly manual")
    c.drawRightString(PAGE_W - MARGIN, 0.27 * inch, f"Page {page}")


def box(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    label: str,
    fill=LIGHT,
    stroke=INK,
    size: int = 10,
    bold: bool = True,
) -> None:
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(1.1)
    c.roundRect(x, y, w, h, 6, fill=1, stroke=1)
    set_font(c, "Helvetica-Bold" if bold else "Helvetica", size)
    c.drawCentredString(x + w / 2, y + h / 2 - size / 3, label)


def arrow(c: canvas.Canvas, x1: float, y1: float, x2: float, y2: float, label: str = "") -> None:
    c.setStrokeColor(INK)
    c.setFillColor(INK)
    c.setLineWidth(1.2)
    c.line(x1, y1, x2, y2)
    if abs(x2 - x1) >= abs(y2 - y1):
        direction = 1 if x2 > x1 else -1
        c.line(x2, y2, x2 - direction * 7, y2 + 4)
        c.line(x2, y2, x2 - direction * 7, y2 - 4)
    else:
        direction = 1 if y2 > y1 else -1
        c.line(x2, y2, x2 - 4, y2 - direction * 7)
        c.line(x2, y2, x2 + 4, y2 - direction * 7)
    if label:
        set_font(c, "Helvetica", 7, MID)
        c.drawCentredString((x1 + x2) / 2, (y1 + y2) / 2 + 6, label)


def warning_band(c: canvas.Canvas, x: float, y: float, w: float, text: str) -> None:
    c.setFillColor(WARN)
    c.setStrokeColor(colors.HexColor("#d19b00"))
    c.roundRect(x, y, w, 0.38 * inch, 6, fill=1, stroke=1)
    set_font(c, "Helvetica-Bold", 9)
    c.drawString(x + 0.16 * inch, y + 0.14 * inch, text)


def draw_grid(c: canvas.Canvas, x: float, y: float, w: float, h: float, prefix: str = "P") -> None:
    cell_w = w / 8
    cell_h = h / 8
    set_font(c, "Helvetica", 6, MID)
    for row in range(8):
        for col in range(8):
            px = x + col * cell_w
            py = y + (7 - row) * cell_h
            c.setFillColor(colors.white)
            c.setStrokeColor(GRID)
            c.rect(px, py, cell_w, cell_h, fill=1, stroke=1)
            n = PIXEL_NUMBER_GRID[row][col]
            set_font(c, "Helvetica-Bold", 6, INK)
            c.drawCentredString(px + cell_w / 2, py + cell_h / 2 - 2, f"{prefix}{n:02d}")
    set_font(c, "Helvetica-Bold", 8)
    c.drawString(x, y + h + 8, "Operator/front view")
    set_font(c, "Helvetica", 7, MID)
    c.drawString(x, y - 12, "Original 8x8 Pico-block numbering")


def controller_rows() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    rows = mapping_rows()
    groups: dict[str, list[dict[str, str | int]]] = {}
    for row in rows:
        groups.setdefault(str(row["controller"]), []).append(row)
    summary = []
    for controller in sorted(groups):
        group = sorted(groups[controller], key=lambda item: int(item["channel_index"]))
        pair_ids = list(dict.fromkeys(str(item["pair_id"]) for item in group))
        locations = list(dict.fromkeys(f'R{item["row"]}C{item["col"]}' for item in group))
        channels = ", ".join(
            f'{item["channel"]}/{item["pico_pwm_pin"]}={item["motor_id"]}'
            for item in group
        )
        controller_index = int(group[0]["controller_index"])
        summary.append(
            {
                "controller": controller,
                "role": "old harness" if controller_index < 8 else "new infill",
                "pairs": ", ".join(pair_ids),
                "locations": ", ".join(locations),
                "channels": channels,
            }
        )
    return summary[:8], summary[8:]


def controller_channel_rows(controller: str) -> list[dict[str, str | int]]:
    return sorted(
        (row for row in mapping_rows() if row["controller"] == controller),
        key=lambda row: int(row["channel_index"]),
    )


def page_cover(c: canvas.Canvas) -> None:
    c.setFillColor(colors.white)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(BLUE)
    c.rect(0, PAGE_H - 1.2 * inch, PAGE_W, 1.2 * inch, fill=1, stroke=0)
    c.setFillColor(YELLOW)
    c.rect(PAGE_W - 1.6 * inch, PAGE_H - 1.2 * inch, 1.05 * inch, 1.2 * inch, fill=1, stroke=0)
    set_font(c, "Helvetica-Bold", 26, colors.white)
    c.drawString(MARGIN, PAGE_H - 0.62 * inch, "COAXIAL WINDWALL")
    set_font(c, "Helvetica-Bold", 18, colors.white)
    c.drawString(MARGIN, PAGE_H - 0.96 * inch, "Wiring Assembly Manual")
    set_font(c, "Helvetica-Bold", 12, INK)
    c.drawString(MARGIN, PAGE_H - 1.72 * inch, "8x8x2 / 128 motors / two ESC planes")
    warning_band(c, MARGIN, PAGE_H - 2.22 * inch, PAGE_W - 2 * MARGIN, "KEEP REAL MOTOR OUTPUT DISABLED UNTIL BENCH TESTS PASS")

    y = PAGE_H - 3.3 * inch
    box(c, MARGIN + 0.1 * inch, y, 1.3 * inch, 0.55 * inch, "Pi", colors.white)
    box(c, MARGIN + 2.0 * inch, y + 0.42 * inch, 1.55 * inch, 0.55 * inch, "C01-C08", FRONT)
    box(c, MARGIN + 2.0 * inch, y - 0.42 * inch, 1.55 * inch, 0.55 * inch, "C09-C16", BACK)
    box(c, MARGIN + 4.1 * inch, y + 0.42 * inch, 1.35 * inch, 0.55 * inch, "old positions", FRONT)
    box(c, MARGIN + 4.1 * inch, y - 0.42 * inch, 1.35 * inch, 0.55 * inch, "infill positions", BACK)
    box(c, MARGIN + 5.95 * inch, y + 0.42 * inch, 1.0 * inch, 0.55 * inch, "F + B", FRONT)
    box(c, MARGIN + 5.95 * inch, y - 0.42 * inch, 1.0 * inch, 0.55 * inch, "F + B", BACK)
    arrow(c, MARGIN + 1.4 * inch, y + 0.27 * inch, MARGIN + 2.0 * inch, y + 0.7 * inch, "cmd")
    arrow(c, MARGIN + 1.4 * inch, y + 0.27 * inch, MARGIN + 2.0 * inch, y - 0.15 * inch, "cmd")
    arrow(c, MARGIN + 3.55 * inch, y + 0.7 * inch, MARGIN + 4.1 * inch, y + 0.7 * inch, "PWM")
    arrow(c, MARGIN + 3.55 * inch, y - 0.15 * inch, MARGIN + 4.1 * inch, y - 0.15 * inch, "PWM")
    arrow(c, MARGIN + 5.45 * inch, y + 0.7 * inch, MARGIN + 5.95 * inch, y + 0.7 * inch, "3 phase")
    arrow(c, MARGIN + 5.45 * inch, y - 0.15 * inch, MARGIN + 5.95 * inch, y - 0.15 * inch, "3 phase")

    draw_grid(c, MARGIN + 1.15 * inch, 1.25 * inch, 4.25 * inch, 4.25 * inch)
    set_font(c, "Helvetica-Bold", 10)
    c.drawString(MARGIN, 0.88 * inch, "Generated from the harness-preserving project mapping.")
    set_font(c, "Helvetica", 8, MID)
    c.drawString(MARGIN, 0.66 * inch, "C01-C08 reuse old wiring. C09-C16 fill the middle positions. Front/back motors use adjacent channels.")


def page_parts(c: canvas.Canvas) -> None:
    draw_header(c, "0", "Parts, Planes, and Labels", "Read the labels before cutting or crimping any harness.")
    y = PAGE_H - 1.85 * inch
    items = [
        ("P01-P64", "wind pixels", "physical 8x8 positions"),
        ("F01-F64", "front motors", "Pichler XQ-45 ESC plane"),
        ("B01-B64", "back motors", "T-MOTOR AIR 40 ESC plane"),
        ("C01-C08", "old harness", "reuse existing 8x8 cabling"),
        ("C09-C16", "new infill", "fill middle positions"),
        ("CH1-CH8", "outputs", "Pico GP0-GP7"),
        ("CTRL-GND", "ground", "shared signal reference"),
        ("BEC+", "unused", "red wire insulated"),
    ]
    col_w = (PAGE_W - 2 * MARGIN - 0.25 * inch) / 2
    for idx, (label, title, desc) in enumerate(items):
        col = idx % 2
        row = idx // 2
        x = MARGIN + col * (col_w + 0.25 * inch)
        yy = y - row * 0.75 * inch
        box(c, x, yy, 0.95 * inch, 0.42 * inch, label, YELLOW if idx == 7 else colors.white, size=8)
        set_font(c, "Helvetica-Bold", 10)
        c.drawString(x + 1.08 * inch, yy + 0.25 * inch, title)
        set_font(c, "Helvetica", 8, MID)
        c.drawString(x + 1.08 * inch, yy + 0.09 * inch, desc)

    warning_band(c, MARGIN, 1.55 * inch, PAGE_W - 2 * MARGIN, "BEC/red wires stay disconnected. Pi/Picos use a separate regulated supply.")
    draw_footer(c, 2)


def page_label_frame(c: canvas.Canvas) -> None:
    draw_header(c, "1", "Label the Frame", "Put pixel labels on the frame before unplugging or extending wiring.")
    draw_grid(c, MARGIN + 0.45 * inch, 1.15 * inch, 5.5 * inch, 5.5 * inch)
    x = MARGIN + 5.95 * inch
    y = 5.8 * inch
    box(c, x, y, 1.0 * inch, 0.42 * inch, "P01", colors.white)
    set_font(c, "Helvetica", 8)
    c.drawString(x, y - 0.22 * inch, "one wind pixel")
    arrow(c, x - 0.1 * inch, y + 0.2 * inch, MARGIN + 0.45 * inch + 0.34 * inch, 1.15 * inch + 5.5 * inch - 0.34 * inch)
    y -= 1.0 * inch
    box(c, x, y, 1.0 * inch, 0.42 * inch, "F01", FRONT)
    set_font(c, "Helvetica", 8)
    c.drawString(x, y - 0.22 * inch, "front motor")
    y -= 0.85 * inch
    box(c, x, y, 1.0 * inch, 0.42 * inch, "B01", BACK)
    set_font(c, "Helvetica", 8)
    c.drawString(x, y - 0.22 * inch, "back motor")
    warning_band(c, MARGIN, 0.62 * inch, PAGE_W - 2 * MARGIN, "Front/back are defined from the operator side. Do not swap this later.")
    draw_footer(c, 3)


def page_controller_banks(c: canvas.Canvas) -> None:
    draw_header(c, "2", "Mount Controller Banks", "C01-C08 reuse old harnesses. C09-C16 fill the middle positions.")
    old_rows, new_rows = controller_rows()
    x1 = MARGIN
    x2 = PAGE_W / 2 + 0.15 * inch
    set_font(c, "Helvetica-Bold", 12)
    c.drawString(x1, PAGE_H - 1.65 * inch, "Old harness / C01-C08")
    c.drawString(x2, PAGE_H - 1.65 * inch, "New infill / C09-C16")
    start_y = PAGE_H - 2.1 * inch
    for idx, row in enumerate(old_rows):
        yy = start_y - idx * 0.52 * inch
        box(c, x1, yy, 0.62 * inch, 0.34 * inch, str(row["controller"]), FRONT, size=8)
        set_font(c, "Helvetica", 8)
        c.drawString(x1 + 0.75 * inch, yy + 0.19 * inch, str(row["pairs"]))
        c.drawString(x1 + 0.75 * inch, yy + 0.05 * inch, str(row["locations"]))
    for idx, row in enumerate(new_rows):
        yy = start_y - idx * 0.52 * inch
        box(c, x2, yy, 0.62 * inch, 0.34 * inch, str(row["controller"]), BACK, size=8)
        set_font(c, "Helvetica", 8)
        c.drawString(x2 + 0.75 * inch, yy + 0.19 * inch, str(row["pairs"]))
        c.drawString(x2 + 0.75 * inch, yy + 0.05 * inch, str(row["locations"]))
    warning_band(c, MARGIN, 0.72 * inch, PAGE_W - 2 * MARGIN, "Mount labels must match docs/MOTOR_CONTROLLER_MAPPING.md before wiring.")
    draw_footer(c, 4)


def page_control_wiring(c: canvas.Canvas) -> None:
    draw_header(c, "3", "Wire Control and Ground", "The Pi controls both banks. Picos create the ESC PWM outputs.")
    y = PAGE_H - 2.0 * inch
    box(c, PAGE_W / 2 - 0.75 * inch, y, 1.5 * inch, 0.55 * inch, "Raspberry Pi", colors.white)
    box(c, MARGIN + 0.45 * inch, y - 1.3 * inch, 1.75 * inch, 0.52 * inch, "OLD-HARNESS BUS", FRONT)
    box(c, PAGE_W - MARGIN - 2.2 * inch, y - 1.3 * inch, 1.75 * inch, 0.52 * inch, "INFILL BUS", BACK)
    box(c, MARGIN + 0.45 * inch, y - 2.2 * inch, 1.75 * inch, 0.52 * inch, "C01-C08", FRONT)
    box(c, PAGE_W - MARGIN - 2.2 * inch, y - 2.2 * inch, 1.75 * inch, 0.52 * inch, "C09-C16", BACK)
    arrow(c, PAGE_W / 2 - 0.2 * inch, y, MARGIN + 1.35 * inch, y - 0.78 * inch, "cmd/sync")
    arrow(c, PAGE_W / 2 + 0.2 * inch, y, PAGE_W - MARGIN - 1.35 * inch, y - 0.78 * inch, "cmd/sync")
    arrow(c, MARGIN + 1.32 * inch, y - 1.3 * inch, MARGIN + 1.32 * inch, y - 1.68 * inch)
    arrow(c, PAGE_W - MARGIN - 1.32 * inch, y - 1.3 * inch, PAGE_W - MARGIN - 1.32 * inch, y - 1.68 * inch)
    c.setStrokeColor(MID)
    c.setLineWidth(2)
    ground_y = 1.55 * inch
    c.line(MARGIN + 0.55 * inch, ground_y, PAGE_W - MARGIN - 0.55 * inch, ground_y)
    set_font(c, "Helvetica-Bold", 9)
    c.drawCentredString(PAGE_W / 2, ground_y + 0.12 * inch, "CTRL-GND / common signal reference")
    arrow(c, MARGIN + 1.32 * inch, y - 2.2 * inch, MARGIN + 1.32 * inch, ground_y, "GND")
    arrow(c, PAGE_W - MARGIN - 1.32 * inch, y - 2.2 * inch, PAGE_W - MARGIN - 1.32 * inch, ground_y, "GND")
    warning_band(c, MARGIN, 0.75 * inch, PAGE_W - 2 * MARGIN, "Do not wire 128 ESC signals directly to Pi GPIO. Use the Pico controller outputs.")
    draw_footer(c, 5)


def page_signal_harness(c: canvas.Canvas) -> None:
    draw_header(c, "4", "Build the Signal Harness", "Every controller repeats the same CH1-CH8 to GP0-GP7 pattern.")
    x = MARGIN + 0.3 * inch
    top = PAGE_H - 1.75 * inch
    y = top - 3.15 * inch
    box(c, x, y, 1.25 * inch, 3.0 * inch, "Pico C01", FRONT)
    esc_x = x + 3.0 * inch
    c01_rows = controller_channel_rows("C01")
    labels = tuple(str(row["motor_id"]) for row in c01_rows)
    pair_ids = list(dict.fromkeys(str(row["pair_id"]) for row in c01_rows))
    for idx in range(8):
        yy = top - 0.45 * inch - idx * 0.34 * inch
        box(c, x + 1.55 * inch, yy, 0.78 * inch, 0.22 * inch, f"CH{idx + 1}/GP{idx}", colors.white, size=6)
        fill = FRONT if labels[idx].startswith("F") else BACK
        box(c, esc_x, yy, 0.9 * inch, 0.22 * inch, f"ESC-{labels[idx]}", fill, size=6)
        arrow(c, x + 2.33 * inch, yy + 0.11 * inch, esc_x, yy + 0.11 * inch, "SIG")
    set_font(c, "Helvetica-Bold", 10)
    c.drawString(esc_x + 1.25 * inch, top - 0.35 * inch, "Example:")
    draw_wrapped(
        c,
        f"C01 reuses old wiring. Adjacent outputs are front/back for {', '.join(pair_ids)}.",
        esc_x + 1.25 * inch,
        top - 0.62 * inch,
        1.85 * inch,
        8,
        11,
    )
    warning_band(c, MARGIN, 1.03 * inch, PAGE_W - 2 * MARGIN, "Each ESC gets its own signal channel. Do not join front and back pair signals.")
    draw_footer(c, 6)


def page_power(c: canvas.Canvas) -> None:
    draw_header(c, "5", "Wire Motor Power", "Fuse by practical harness/controller branch, then verify current per branch.")
    y = PAGE_H - 2.0 * inch
    box(c, MARGIN, y, 1.5 * inch, 0.5 * inch, "OLD-HARNESS PWR", FRONT)
    box(c, PAGE_W - MARGIN - 1.5 * inch, y, 1.5 * inch, 0.5 * inch, "INFILL PWR", BACK)
    for idx in range(4):
        yy = y - 0.75 * inch - idx * 0.6 * inch
        box(c, MARGIN + 1.95 * inch, yy, 1.25 * inch, 0.32 * inch, f"fuse C{idx + 1:02d}", colors.white, size=7)
        box(c, MARGIN + 3.45 * inch, yy, 1.25 * inch, 0.32 * inch, "4 coax pairs", FRONT, size=7)
        arrow(c, MARGIN + 1.5 * inch, y + 0.25 * inch, MARGIN + 1.95 * inch, yy + 0.16 * inch)
        arrow(c, MARGIN + 3.2 * inch, yy + 0.16 * inch, MARGIN + 3.45 * inch, yy + 0.16 * inch)
        box(c, PAGE_W - MARGIN - 4.7 * inch, yy, 1.25 * inch, 0.32 * inch, f"fuse C{idx + 9:02d}", colors.white, size=7)
        box(c, PAGE_W - MARGIN - 3.2 * inch, yy, 1.25 * inch, 0.32 * inch, "4 coax pairs", BACK, size=7)
        arrow(c, PAGE_W - MARGIN - 1.5 * inch, y + 0.25 * inch, PAGE_W - MARGIN - 3.45 * inch, yy + 0.16 * inch)
        arrow(c, PAGE_W - MARGIN - 3.45 * inch, yy + 0.16 * inch, PAGE_W - MARGIN - 3.2 * inch, yy + 0.16 * inch)
    set_font(c, "Helvetica", 8, MID)
    c.drawString(MARGIN + 1.95 * inch, 2.15 * inch, "Continue same pattern through C08 and C16.")
    warning_band(c, MARGIN, 0.85 * inch, PAGE_W - 2 * MARGIN, "Fuse from measured current, wire gauge, and connector rating. Do not size only from ESC max amps.")
    draw_footer(c, 7)


def page_pair(c: canvas.Canvas) -> None:
    draw_header(c, "6", "Wire One Coaxial Pair", "Front and back motors share a pixel label, but use separate ESCs and outputs.")
    y = PAGE_H - 2.0 * inch
    box(c, PAGE_W / 2 - 0.45 * inch, y, 0.9 * inch, 0.5 * inch, "P01", YELLOW)
    box(c, MARGIN + 0.5 * inch, y - 1.0 * inch, 1.0 * inch, 0.45 * inch, "C01 CH1", FRONT)
    box(c, MARGIN + 2.0 * inch, y - 1.0 * inch, 1.1 * inch, 0.45 * inch, "ESC-F01", FRONT)
    box(c, MARGIN + 3.55 * inch, y - 1.0 * inch, 0.9 * inch, 0.45 * inch, "F01", FRONT)
    box(c, PAGE_W - MARGIN - 4.45 * inch, y - 2.05 * inch, 1.0 * inch, 0.45 * inch, "C01 CH2", BACK)
    box(c, PAGE_W - MARGIN - 2.95 * inch, y - 2.05 * inch, 1.1 * inch, 0.45 * inch, "ESC-B01", BACK)
    box(c, PAGE_W - MARGIN - 1.4 * inch, y - 2.05 * inch, 0.9 * inch, 0.45 * inch, "B01", BACK)
    arrow(c, PAGE_W / 2 - 0.45 * inch, y, MARGIN + 4.0 * inch, y - 0.55 * inch)
    arrow(c, PAGE_W / 2 + 0.45 * inch, y, PAGE_W - MARGIN - 0.95 * inch, y - 1.6 * inch)
    arrow(c, MARGIN + 1.5 * inch, y - 0.78 * inch, MARGIN + 2.0 * inch, y - 0.78 * inch, "SIG")
    arrow(c, MARGIN + 3.1 * inch, y - 0.78 * inch, MARGIN + 3.55 * inch, y - 0.78 * inch, "U/V/W")
    arrow(c, PAGE_W - MARGIN - 3.45 * inch, y - 1.83 * inch, PAGE_W - MARGIN - 2.95 * inch, y - 1.83 * inch, "SIG")
    arrow(c, PAGE_W - MARGIN - 1.85 * inch, y - 1.83 * inch, PAGE_W - MARGIN - 1.4 * inch, y - 1.83 * inch, "U/V/W")
    draw_wrapped(c, "P01 is one air pixel at R1C1. F01 and B01 should be tested as one pair only after each ESC/motor works alone.", MARGIN, 1.75 * inch, PAGE_W - 2 * MARGIN, 9, 12)
    warning_band(c, MARGIN, 0.88 * inch, PAGE_W - 2 * MARGIN, "Separate signals let software offset Pichler and AIR throttle response.")
    draw_footer(c, 8)


def page_bringup(c: canvas.Canvas) -> None:
    draw_header(c, "7", "Bring Up Slowly", "No full-wall run until each lower-risk stage passes.")
    steps = [
        "Label P01-P64, F01-F64, B01-B64, C01-C16.",
        "Power Pi/Picos only. Confirm controllers boot.",
        "With ESC power off, confirm every channel idles.",
        "Bench-test C01 channel order with no live wall load.",
        "Bench-test one F motor and one B motor with no live wall load.",
        "Calibrate/program all ESCs consistently by type.",
        "Test one coaxial pair at low PWM.",
        "Test one old-harness controller.",
        "Test one new-infill controller.",
        "Expand carefully controller by controller.",
    ]
    y = PAGE_H - 1.75 * inch
    for idx, text in enumerate(steps):
        yy = y - idx * 0.43 * inch
        c.setStrokeColor(INK)
        c.rect(MARGIN, yy, 0.18 * inch, 0.18 * inch, fill=0, stroke=1)
        set_font(c, "Helvetica-Bold", 8)
        c.drawString(MARGIN + 0.3 * inch, yy + 0.03 * inch, f"{idx + 1}.")
        set_font(c, "Helvetica", 8)
        c.drawString(MARGIN + 0.55 * inch, yy + 0.03 * inch, text)
    warning_band(c, MARGIN, 0.78 * inch, PAGE_W - 2 * MARGIN, "Emergency stop, idle-on-exit, and idle-on-signal-loss must be proven before real operation.")
    draw_footer(c, 9)


def page_label_sheet(c: canvas.Canvas) -> None:
    draw_header(c, "8", "Print These Labels", "Use the same words on frame, ESCs, controller outputs, and power branches.")
    labels = [
        "P01",
        "F01 / ESC-F01 / FP / Pichler / C01-CH1 / GP0",
        "B01 / ESC-B01 / BP / AIR40 / C01-CH2 / GP1",
        "C01-PWR",
        "C09-PWR",
        "CTRL-GND",
        "SIG-GND",
        "BEC+ UNUSED",
        "C01-CH1 SIG -> ESC-F01 SIG",
        "C01-CH2 SIG -> ESC-B01 SIG",
    ]
    y = PAGE_H - 1.8 * inch
    for idx, label in enumerate(labels):
        yy = y - idx * 0.47 * inch
        box(c, MARGIN, yy, PAGE_W - 2 * MARGIN, 0.3 * inch, label, colors.white, size=8, bold=False)
    draw_footer(c, 10)


PAGES = [
    page_cover,
    page_parts,
    page_label_frame,
    page_controller_banks,
    page_control_wiring,
    page_signal_harness,
    page_power,
    page_pair,
    page_bringup,
    page_label_sheet,
]


def build_pdf(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(path), pagesize=letter)
    c.setTitle("Coaxial Windwall Wiring Assembly Manual")
    c.setAuthor("Coaxial Windwall Project")
    for page in PAGES:
        page(c)
        c.showPage()
    c.save()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the wiring assembly manual PDF.")
    parser.add_argument(
        "--output",
        type=Path,
        default=DOCS_OUTPUT,
        help="PDF output path",
    )
    parser.add_argument(
        "--desktop-copy",
        action="store_true",
        help=f"also write {DESKTOP_OUTPUT}",
    )
    args = parser.parse_args()

    build_pdf(args.output)
    if args.desktop_copy:
        build_pdf(DESKTOP_OUTPUT)
    print(args.output)
    if args.desktop_copy:
        print(DESKTOP_OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
