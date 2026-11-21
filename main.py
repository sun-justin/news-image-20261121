#!/usr/bin/env python3
"""Sum up 21 November 2026's world news in one image.

Writes /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png): a 1024x1024
newspaper front page drawn procedurally from the day's verified stories.

Stories (checked 21 Nov 2026 against the One Turn daily digest, the
Horizon world-news page, the Michael Brunger daily brief and The Daily
Short, citing BBC, Reuters, The Guardian, FT, Al Jazeera, City AM):
  1. Russia launches its biggest attacks of the year on Ukraine: 400+
     drones and 110 missiles overnight; at least 8 killed in Kyiv;
     two missiles and a suspected drone come down in Poland, and
     Prime Minister Tusk calls it a deliberate provocation.
  2. AI stock sell-off: the S&P 500 falls 3.7% into correction, the
     Nasdaq falls 5.28% and erases all its 2026 gains, the Nikkei
     falls 5.06%; Anthropic slides after its record debut; the SEC
     opens a probe into Nvidia's accounting after Jensen Huang resigns.
  3. The UK and EU sign their biggest post-Brexit agreements: food
     trade, carbon markets and youth mobility for 100,000 young Britons.
  4. A magnitude 6.8 earthquake strikes the Junin region of the
     Peruvian Andes; tremors are felt in Lima, 320 km away.
  5. The FBI's criminal database is hacked for a second time as US
     computer outages continue; the USDA is also hit.
  6. A trial pill, daraxonrasib, makes pancreatic tumours
     undetectable on scans in 1 in 12 patients.
  7. Markets: S&P 500 -3.7%, Nasdaq -5.28%, Nikkei -5.06%,
     FTSE -1.02%, Brent $89.95, gold -4.62%.

Deterministic: no network, no clock, no randomness, no input files.
Pure standard library. Run twice, get the same bytes.
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- palette
# Fixed palette; indices are stable, so the output is deterministic.
PALETTE = [
    (247, 243, 232),  # 0 paper
    (20, 20, 20),     # 1 ink
    (179, 38, 30),    # 2 red
    (29, 78, 158),    # 3 blue
    (22, 54, 92),     # 4 dark blue
    (201, 162, 39),   # 5 gold
    (107, 107, 107),  # 6 grey
    (227, 221, 203),  # 7 light grey
    (255, 255, 255),  # 8 white
    (30, 122, 52),    # 9 green
    (122, 26, 20),    # 10 dark red
    (127, 179, 213),  # 11 sky
    (14, 107, 107),   # 12 teal
    (217, 108, 30),   # 13 orange
    (15, 42, 74),     # 14 navy
    (232, 196, 160),  # 15 sand
]
PAPER, INK, RED, BLUE, DBLUE, GOLD, GREY, LGREY = 0, 1, 2, 3, 4, 5, 6, 7
WHITE, GREEN, DRED, SKY, TEAL, ORANGE, NAVY, SAND = 8, 9, 10, 11, 12, 13, 14, 15

buf = bytearray([PAPER]) * (W * H)


def px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        buf[y * W + x] = c


def fill_rect(x, y, w, h, c):
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    for yy in range(y0, y1):
        row = yy * W
        buf[row + x0:row + x1] = bytes([c]) * (x1 - x0)


def hline(x0, x1, y, c, t=1):
    for t_ in range(t):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            px(x, y + t_, c)


def vline(x, y0, y1, c, t=1):
    for t_ in range(t):
        for y in range(min(y0, y1), max(y0, y1) + 1):
            px(x + t_, y, c)


def line(x0, y0, x1, y1, c, t=1):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    x, y = x0, y0
    while True:
        for a in range(t):
            for b in range(t):
                px(x + a, y + b, c)
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy


def rect(x, y, w, h, c, t=2):
    hline(x, x + w - 1, y, c, t)
    hline(x, x + w - 1, y + h - t, c, t)
    vline(x, y, y + h - 1, c, t)
    vline(x + w - t, y, y + h - 1, c, t)


def fill_circle(cx, cy, r, c):
    for yy in range(cy - r, cy + r + 1):
        dx = int((r * r - (yy - cy) ** 2) ** 0.5)
        for xx in range(cx - dx, cx + dx + 1):
            px(xx, yy, c)


def fill_poly(points, c):
    # Scanline polygon fill (even-odd), deterministic.
    ys = [p[1] for p in points]
    for y in range(min(ys), max(ys) + 1):
        xs = []
        n = len(points)
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            for x in range(int(xs[i]), int(xs[i + 1]) + 1):
                px(x, y, c)


def star(cx, cy, r_out, r_in, c, rot=-90):
    pts = []
    for i in range(10):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(rot + i * 36)
        pts.append((int(cx + r * math.cos(a)), int(cy + r * math.sin(a))))
    fill_poly(pts, c)


# ------------------------------------------------------------------- font
# 5x7 bitmap font, one glyph per character. '#' = on, '.' = off.
FONT = {}
def _g(ch, rows):
    FONT[ch] = rows

_g("A", ["01110", "10001", "10001", "11111", "10001", "10001", "10001"])
_g("B", ["11110", "10001", "10001", "11110", "10001", "10001", "11110"])
_g("C", ["01110", "10001", "10000", "10000", "10000", "10001", "01110"])
_g("D", ["11110", "10001", "10001", "10001", "10001", "10001", "11110"])
_g("E", ["11111", "10000", "10000", "11110", "10000", "10000", "11111"])
_g("F", ["11111", "10000", "10000", "11110", "10000", "10000", "10000"])
_g("G", ["01110", "10001", "10000", "10111", "10001", "10001", "01111"])
_g("H", ["10001", "10001", "10001", "11111", "10001", "10001", "10001"])
_g("I", ["01110", "00100", "00100", "00100", "00100", "00100", "01110"])
_g("J", ["00111", "00010", "00010", "00010", "00010", "10010", "01100"])
_g("K", ["10001", "10010", "10100", "11000", "10100", "10010", "10001"])
_g("L", ["10000", "10000", "10000", "10000", "10000", "10000", "11111"])
_g("M", ["10001", "11011", "10101", "10101", "10001", "10001", "10001"])
_g("N", ["10001", "11001", "10101", "10011", "10001", "10001", "10001"])
_g("O", ["01110", "10001", "10001", "10001", "10001", "10001", "01110"])
_g("P", ["11110", "10001", "10001", "11110", "10000", "10000", "10000"])
_g("Q", ["01110", "10001", "10001", "10001", "10101", "10010", "01101"])
_g("R", ["11110", "10001", "10001", "11110", "10100", "10010", "10001"])
_g("S", ["01111", "10000", "10000", "01110", "00001", "00001", "11110"])
_g("T", ["11111", "00100", "00100", "00100", "00100", "00100", "00100"])
_g("U", ["10001", "10001", "10001", "10001", "10001", "10001", "01110"])
_g("V", ["10001", "10001", "10001", "10001", "10001", "01010", "00100"])
_g("W", ["10001", "10001", "10001", "10101", "10101", "11011", "10001"])
_g("X", ["10001", "10001", "01010", "00100", "01010", "10001", "10001"])
_g("Y", ["10001", "10001", "01010", "00100", "00100", "00100", "00100"])
_g("Z", ["11111", "00001", "00010", "00100", "01000", "10000", "11111"])
_g("0", ["01110", "10001", "10011", "10101", "11001", "10001", "01110"])
_g("1", ["00100", "01100", "00100", "00100", "00100", "00100", "01110"])
_g("2", ["01110", "10001", "00001", "00110", "01000", "10000", "11111"])
_g("3", ["11111", "00010", "00100", "00010", "00001", "10001", "01110"])
_g("4", ["00010", "00110", "01010", "10010", "11111", "00010", "00010"])
_g("5", ["11111", "10000", "11110", "00001", "00001", "10001", "01110"])
_g("6", ["00110", "01000", "10000", "11110", "10001", "10001", "01110"])
_g("7", ["11111", "00001", "00010", "00100", "01000", "01000", "01000"])
_g("8", ["01110", "10001", "10001", "01110", "10001", "10001", "01110"])
_g("9", ["01110", "10001", "10001", "01111", "00001", "00010", "01100"])
_g(" ", ["00000", "00000", "00000", "00000", "00000", "00000", "00000"])
_g(".", ["00000", "00000", "00000", "00000", "00000", "01100", "01100"])
_g(",", ["00000", "00000", "00000", "00000", "01100", "00100", "01000"])
_g(":", ["00000", "01100", "01100", "00000", "01100", "01100", "00000"])
_g(";", ["00000", "01100", "01100", "00000", "01100", "00100", "01000"])
_g("!", ["00100", "00100", "00100", "00100", "00100", "00000", "00100"])
_g("?", ["01110", "10001", "00001", "00110", "00100", "00000", "00100"])
_g("'", ["00100", "00100", "01000", "00000", "00000", "00000", "00000"])
_g("-", ["00000", "00000", "00000", "01110", "00000", "00000", "00000"])
_g("(", ["00010", "00100", "01000", "01000", "01000", "00100", "00010"])
_g(")", ["01000", "00100", "00010", "00010", "00010", "00100", "01000"])
_g("%", ["11001", "11010", "00010", "00100", "01000", "01011", "10011"])
_g("+", ["00000", "00100", "00100", "01110", "00100", "00100", "00000"])
_g("/", ["00001", "00010", "00010", "00100", "01000", "01000", "10000"])
_g("$", ["00100", "01111", "10100", "01110", "00101", "11110", "00100"])
_g("&", ["01100", "10010", "10100", "01000", "10101", "10010", "01101"])
_g("*", ["00000", "10101", "01110", "10101", "00000", "00000", "00000"])
_g("=", ["00000", "00000", "01110", "00000", "01110", "00000", "00000"])
_g("<", ["00010", "00100", "01000", "10000", "01000", "00100", "00010"])
_g(">", ["01000", "00100", "00010", "00001", "00010", "00100", "01000"])
_g('"', ["01010", "01010", "00000", "00000", "00000", "00000", "00000"])
_g("#", ["01010", "01010", "11111", "01010", "11111", "01010", "01010"])
_g("@", ["01110", "10001", "10111", "10101", "10110", "10000", "01110"])
_g("_", ["00000", "00000", "00000", "00000", "00000", "00000", "11111"])

CHAR_W = 6  # 5 px glyph + 1 px gap, times scale


def text_width(text, scale):
    return len(text) * CHAR_W * scale - scale


def draw_text(x, y, text, scale, color):
    cx = x
    for ch in text:
        glyph = FONT.get(ch, FONT["?"])
        for r in range(7):
            row = glyph[r]
            for c_ in range(5):
                if row[c_] == "1":
                    fill_rect(cx + c_ * scale, y + r * scale, scale, scale, color)
        cx += CHAR_W * scale
    return cx


def draw_text_center(cx, y, text, scale, color):
    draw_text(cx - text_width(text, scale) // 2, y, text, scale, color)


def wrap_text(text, scale, max_w):
    words = text.split(" ")
    lines = []
    cur = ""
    for w in words:
        trial = (cur + " " + w).strip()
        if text_width(trial, scale) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_para(x, y, text, scale, color, max_w, leading=None):
    if leading is None:
        leading = 9 * scale
    for ln in wrap_text(text, scale, max_w):
        draw_text(x, y, ln, scale, color)
        y += leading
    return y


def kicker(x, y, text, scale=2, color=RED):
    return draw_text(x, y, text, scale, color)


# ------------------------------------------------------------------ layout
def draw():
    # ---- masthead ----
    fill_rect(0, 0, W, 10, INK)
    draw_text_center(W // 2, 26, "THE WORLD IN ONE IMAGE", 3, INK)
    draw_text_center(W // 2, 62, "SATURDAY 21 NOVEMBER 2026", 4, RED)
    hline(24, W - 24, 108, INK, 3)
    hline(24, W - 24, 116, INK, 1)

    # ---- lead story: Russia's attack on Ukraine, missiles in Poland ----
    y = 132
    kicker(24, y, "LEAD STORY - KYIV AND POLAND", 2, RED)
    draw_text(24, y + 22, "MISSILES RAIN ON", 5, INK)
    draw_text(24, y + 62, "KYIV - AND POLAND", 5, INK)
    draw_para(24, y + 112,
              "RUSSIA FIRES 400+ DRONES AND 110 MISSILES IN ITS "
              "BIGGEST ATTACKS OF THE YEAR. AT LEAST 8 KILLED IN "
              "KYIV. TWO MISSILES LAND IN POLAND - PM TUSK CALLS "
              "IT A DELIBERATE PROVOCATION.",
              2, INK, 600)
    # night sky over Kyiv, right of the lead story
    fx, fy = 660, y + 6
    fill_rect(fx, fy, 320, 132, NAVY)
    # skyline silhouettes
    for bx, bw, bh in ((0, 52, 58), (58, 40, 84), (104, 64, 48),
                       (174, 44, 96), (224, 52, 66), (282, 38, 78)):
        fill_rect(fx + bx, fy + 132 - bh, bw, bh, INK)
        for wy in range(0, bh - 12, 16):
            fill_rect(fx + bx + 8, fy + 132 - bh + 8 + wy, 8, 6, GOLD)
    # missile trails arcing down
    line(fx + 30, fy + 4, fx + 120, fy + 66, ORANGE, 2)
    line(fx + 300, fy + 2, fx + 210, fy + 58, ORANGE, 2)
    line(fx + 170, fy + 0, fx + 176, fy + 44, WHITE, 2)
    # explosions over the skyline
    star(fx + 122, fy + 66, 20, 8, ORANGE)
    star(fx + 122, fy + 66, 11, 5, GOLD)
    star(fx + 212, fy + 58, 16, 7, ORANGE)
    star(fx + 212, fy + 58, 9, 4, GOLD)
    star(fx + 178, fy + 44, 12, 5, ORANGE)
    draw_text(fx, fy + 140, "KYIV UNDER FIRE", 2, INK)
    draw_text(fx, fy + 162, "400+ DRONES, 110 MISSILES", 2, INK)
    draw_text(fx, fy + 184, "2 MISSILES LAND IN POLAND", 2, RED)
    draw_text(fx, fy + 206, "BIGGEST ATTACKS OF THE YEAR", 2, INK)

    hline(24, W - 24, 396, INK, 2)

    # ---- row 2: AI sell-off + UK-EU deal ----
    y = 414
    # left panel: markets plunge
    kicker(24, y, "ECONOMY - NEW YORK", 2, RED)
    draw_text(24, y + 22, "AI SELL-OFF:", 4, INK)
    draw_text(24, y + 58, "MARKETS PLUNGE", 4, RED)
    # falling bars: S&P -3.7%, Nasdaq -5.28%
    bx, by = 34, y + 210
    fill_rect(bx + 6, by - 52, 70, 52, RED)
    fill_rect(bx + 146, by - 74, 70, 74, DRED)
    draw_text(bx + 12, by - 72, "-3.7%", 2, RED)
    draw_text(bx + 152, by - 94, "-5.28%", 2, DRED)
    draw_text(bx + 6, by + 8, "S&P 500", 2, INK)
    draw_text(bx + 146, by + 8, "NASDAQ", 2, INK)
    draw_text(bx + 6, by + 26, "CORRECTION", 2, GREY)
    draw_text(bx + 146, by + 26, "GAINS ERASED", 2, GREY)
    draw_para(280, y + 104,
              "ANTHROPIC SLIDES AFTER ITS RECORD DEBUT. NVIDIA "
              "FACES AN SEC PROBE AS JENSEN HUANG RESIGNS.",
              2, INK, 220)
    # right panel: UK-EU deal
    rx = 524
    vline(rx - 12, y, y + 236, GREY, 1)
    kicker(rx, y, "POLITICS - BRUSSELS", 2, RED)
    draw_text(rx, y + 22, "UK AND EU SIGN", 4, INK)
    draw_text(rx, y + 58, "POST-BREXIT DEALS", 4, INK)
    # Union Jack (simplified) and EU flag
    ux, uy = rx, y + 100
    fill_rect(ux, uy, 150, 76, DBLUE)
    fill_rect(ux + 64, uy, 22, 76, WHITE)
    fill_rect(ux, uy + 27, 150, 22, WHITE)
    fill_rect(ux + 68, uy, 14, 76, RED)
    fill_rect(ux, uy + 31, 150, 14, RED)
    ex, ey = rx + 170, y + 100
    fill_rect(ex, ey, 150, 76, BLUE)
    for i in range(12):
        a = math.radians(i * 30)
        star(ex + 75 + int(28 * math.cos(a)),
             ey + 38 + int(24 * math.sin(a)), 5, 2, GOLD)
    draw_text(ux + 34, uy + 86, "BRITAIN", 2, INK)
    draw_text(ex + 40, ey + 86, "EUROPE", 2, INK)
    draw_para(rx, y + 206,
              "FOOD TRADE, CARBON MARKETS AND YOUTH MOBILITY FOR "
              "100,000 YOUNG BRITONS. BIGGEST STEP SINCE BREXIT.",
              2, INK, 448)
    hline(24, W - 24, 668, INK, 2)

    # ---- row 3: three panels ----
    y = 686
    pw = 320
    panels = [
        (24, "6.8 QUAKE SHAKES PERU",
         "ANDES REGION OF JUNIN HIT. TREMORS FELT IN LIMA, "
         "320 KM AWAY.",
         "quake"),
        (352, "FBI DATABASE HACKED",
         "SECOND CYBERATTACK ON THE CRIME DATABASE AS US "
         "OUTAGES CONTINUE. USDA ALSO HIT.",
         "fbi"),
        (680, "CANCER PILL HOPE",
         "TRIAL PILL DARAXONRASIB MAKES PANCREATIC TUMOURS "
         "UNDETECTABLE IN 1 IN 12 PATIENTS.",
         "pill"),
    ]
    for x, title, body, art in panels:
        kicker(x, y, title, 2, RED)
        ay = y + 26
        if art == "quake":
            # mountains and a jagged crack
            fill_poly([(x, ay + 66), (x + 60, ay + 10), (x + 120, ay + 66)],
                      DBLUE)
            fill_poly([(x + 90, ay + 66), (x + 170, ay + 2), (x + 250, ay + 66)],
                      NAVY)
            fill_poly([(x + 150, ay + 18), (x + 170, ay + 2), (x + 190, ay + 18)],
                      WHITE)
            line(x + 20, ay + 74, x + 90, ay + 66, RED, 3)
            line(x + 90, ay + 66, x + 150, ay + 78, RED, 3)
            line(x + 150, ay + 78, x + 210, ay + 68, RED, 3)
            line(x + 210, ay + 68, x + 280, ay + 76, RED, 3)
        elif art == "fbi":
            # monitor with warning, small padlock to the right
            fill_rect(x + 40, ay + 6, 200, 66, INK)
            fill_rect(x + 48, ay + 14, 184, 50, TEAL)
            draw_text(x + 60, ay + 26, "FBI", 4, WHITE)
            draw_text(x + 140, ay + 34, "HACKED", 2, GOLD)
            fill_rect(x + 252, ay + 26, 30, 26, GOLD)
            fill_rect(x + 262, ay + 36, 10, 10, INK)
            fill_rect(x + 258, ay + 16, 18, 12, INK)
            fill_rect(x + 262, ay + 20, 10, 8, PAPER)
        else:
            # capsule pill, half red half white
            fill_circle(x + 90, ay + 40, 26, RED)
            fill_circle(x + 206, ay + 40, 26, WHITE)
            fill_rect(x + 90, ay + 14, 116, 52, RED)
            fill_rect(x + 148, ay + 14, 58, 52, WHITE)
            rect(x + 64, ay + 14, 168, 52, INK, 2)
            vline(x + 148, ay + 14, ay + 66, INK, 2)
        draw_para(x, y + 108, body, 2, INK, pw - 24)
    hline(24, W - 24, 896, INK, 2)

    # ---- bottom: markets strip ----
    fill_rect(0, 912, W, 66, INK)
    draw_text_center(W // 2, 928,
                     "MARKETS: S&P 500 -3.7%  NASDAQ -5.28%  NIKKEI -5.06%",
                     3, WHITE)
    draw_text_center(W // 2, 954,
                     "BRENT $89.95  GOLD -4.62%  FTSE -1.02%",
                     3, GOLD)
    draw_text_center(W // 2, 992,
                     "21 NOVEMBER 2026 - SOURCES: BBC, REUTERS, GUARDIAN, FT, AL JAZEERA",
                     2, GREY)


# --------------------------------------------------------------------- png
def chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def write_png(path):
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 3, 0, 0, 0)
    plte = b"".join(bytes(c) for c in PALETTE)
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter: none
        raw += buf[y * W:(y + 1) * W]
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"PLTE", plte)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    draw()
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    size = write_png(path)
    print("wrote %s (%d bytes)" % (path, size))


if __name__ == "__main__":
    main()
