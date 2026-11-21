#!/usr/bin/env python3
"""Sum up the world news of Saturday 21 November 2026 in one image.

Draws a one-page newspaper front page, procedurally, with the Python
standard library only. No network, no clock, no randomness: every run
writes the exact same PNG bytes to $MAKEFUN_OUTPUT_DIR/entry.png
(or /output/entry.png).

Stories (as reported on 21 November 2026):
  * Russia's largest air assault of the month on Kyiv: 400+ drones and
    110+ missiles overnight; at least 9 killed; bridges over the Dnipro
    hit; two missiles and a drone come down in Poland.
  * US stocks fall into correction in an AI-led sell-off.
  * The International Court of Justice finds Myanmar committed
    genocide against the Rohingya.
  * COP31 climate talks in Antalya run past their deadline.
  * The UK and the EU sign their biggest post-Brexit agreements.
  * A 6.9 earthquake shakes the Peruvian Andes; a power-plant fire in
    Basra kills at least four; a pancreatic-cancer pill trial reports
    tumours undetectable in one in twelve patients.
"""

import os
import struct
import sys
import zlib

WIDTH = 1024
HEIGHT = 1024

PAPER = (246, 241, 227)
INK = (22, 22, 22)
SOFT = (74, 70, 60)
RED = (163, 18, 18)
NAVY = (24, 42, 74)
NAVY_DARK = (16, 28, 52)
SKYLINE = (10, 18, 36)
GOLD = (214, 164, 48)
ORANGE = (224, 110, 30)
WHITE = (245, 244, 238)

# ---------------------------------------------------------------- font
# A 5x7 bitmap font, drawn by hand for this program. Each glyph is seven
# rows of five cells; "#" is ink, "." is blank. Only the characters the
# page uses are defined; anything else renders as a blank cell.

FONT = {
    "A": (" .###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "&": (".##..", "#..#.", "#..#.", ".#...", "#.#.#", "#..#.", ".##.#"),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    "*": (".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", "....."),
    "_": (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
    "<": ("....#", "...#.", "..#..", ".#...", "..#..", "...#.", "....#"),
    ">": ("#....", ".#...", "..#..", "...#.", "..#..", ".#...", "#...."),
    "[": (".###.", ".#...", ".#...", ".#...", ".#...", ".#...", ".###."),
    "]": (".###.", "...#.", "...#.", "...#.", "...#.", "...#.", ".###."),
}


def glyph_rows(ch):
    return FONT.get(ch, FONT[" "])


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, width, height, colour):
        self.w = width
        self.h = height
        self.px = bytearray(width * height * 3)
        r, g, b = colour
        for i in range(0, len(self.px), 3):
            self.px[i] = r
            self.px[i + 1] = g
            self.px[i + 2] = b

    def set(self, x, y, colour):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = colour

    def fill(self, x, y, w, h, colour):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        r, g, b = colour
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i] = r
                self.px[i + 1] = g
                self.px[i + 2] = b

    def outline(self, x, y, w, h, colour, t=1):
        self.fill(x, y, w, t, colour)
        self.fill(x, y + h - t, w, t, colour)
        self.fill(x, y, t, h, colour)
        self.fill(x + w - t, y, t, h, colour)

    def hline(self, x, y, w, colour, t=1):
        self.fill(x, y, w, t, colour)

    def line(self, x0, y0, x1, y1, colour):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            self.set(x, y, colour)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def disc(self, cx, cy, r, colour):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, colour)

    def burst(self, cx, cy, r, colour, core):
        for k in range(12):
            # Twelve fixed rays; angles step by 30 degrees.
            ang = k * 30
            ex = cx + int(r * _cos(ang))
            ey = cy + int(r * _sin(ang))
            self.line(cx, cy, ex, ey, colour)
        self.disc(cx, cy, max(2, r // 4), core)
        self.disc(cx, cy, max(1, r // 8), WHITE)


# Fixed-point cosine/sine for the twelve 30-degree steps (x1000).
_COS = (1000, 866, 500, 0, -500, -866, -1000, -866, -500, 0, 500, 866)
_SIN = (0, 500, 866, 1000, 866, 500, 0, -500, -866, -1000, -866, -500)


def _cos(deg):
    return _COS[(deg // 30) % 12] / 1000.0


def _sin(deg):
    return _SIN[(deg // 30) % 12] / 1000.0


# ---------------------------------------------------------------- text
def text_width(text, scale):
    return len(text) * 6 * scale


def draw_text(cv, x, y, text, scale, colour):
    for ch in text:
        rows = glyph_rows(ch)
        for r in range(7):
            row = rows[r]
            for c in range(5):
                if row[c] == "#":
                    cv.fill(x + c * scale, y + r * scale, scale, scale, colour)
        x += 6 * scale
    return x


def draw_text_centred(cv, cx, y, text, scale, colour):
    draw_text(cv, cx - text_width(text, scale) // 2, y, text, scale, colour)


def wrap(text, max_chars):
    """Greedy word wrap; returns a list of lines, each <= max_chars."""
    lines = []
    for para in text.split("\n"):
        words = para.split(" ")
        cur = ""
        for word in words:
            if not cur:
                cur = word
            elif len(cur) + 1 + len(word) <= max_chars:
                cur += " " + word
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
    return lines


def draw_block(cv, x, y, width, text, scale, colour, leading=None):
    """Draw wrapped text; returns the y just below the last line."""
    if leading is None:
        leading = 7 * scale + 4
    max_chars = max(1, width // (6 * scale))
    for line in wrap(text, max_chars):
        draw_text(cv, x, y, line, scale, colour)
        y += leading
    return y


# ---------------------------------------------------------------- pieces
def draw_masthead(cv):
    cv.hline(28, 20, 968, INK, 3)
    cv.hline(28, 26, 968, INK, 1)
    draw_text_centred(cv, WIDTH // 2, 36, "THE WORLD TODAY", 9, INK)
    cv.hline(28, 108, 968, INK, 1)
    draw_text(cv, 28, 118, "ONE PAGE", 2, SOFT)
    draw_text_centred(cv, WIDTH // 2, 118, "SATURDAY, 21 NOVEMBER 2026", 3, INK)
    draw_text(cv, 1024 - 28 - text_width("LATE EDITION", 2), 118, "LATE EDITION", 2, SOFT)
    cv.hline(28, 142, 968, INK, 3)


def draw_lead_art(cv, x, y, w, h):
    """Night sky over Kyiv: skyline, missile arcs, explosion bursts."""
    cv.fill(x, y, w, h, NAVY)
    # Fixed star field: positions from a plain arithmetic pattern.
    for i in range(46):
        sx = x + 12 + (i * 173) % (w - 24)
        sy = y + 8 + (i * 97) % 58
        cv.set(sx, sy, WHITE)
        if i % 5 == 0:
            cv.set(sx + 1, sy, WHITE)
    # Distant fires on the horizon.
    cv.fill(x + 60, y + h - 58, 90, 6, ORANGE)
    cv.fill(x + 700, y + h - 52, 120, 6, ORANGE)
    # Missile arcs across the sky.
    cv.line(x + 90, y + h - 40, x + 430, y + 42, GOLD)
    cv.line(x + 92, y + h - 38, x + 432, y + 44, GOLD)
    cv.line(x + 860, y + h - 44, x + 560, y + 30, GOLD)
    cv.line(x + 862, y + h - 42, x + 562, y + 32, GOLD)
    # Explosion bursts.
    cv.burst(x + 430, y + 46, 34, ORANGE, GOLD)
    cv.burst(x + 560, y + 34, 28, ORANGE, GOLD)
    cv.burst(x + 250, y + 78, 20, GOLD, ORANGE)
    # Skyline silhouette with a few lit windows.
    heights = (64, 92, 58, 110, 76, 48, 100, 70, 88, 54, 96, 62,
               104, 72, 58, 90, 66, 118, 80, 56)
    bx = x + 8
    step = (w - 16) // len(heights)
    for i, bh in enumerate(heights):
        bw = step - 6
        cv.fill(bx, y + h - bh, bw, bh, SKYLINE)
        for wy in range(y + h - bh + 8, y + h - 10, 16):
            for wx in (bx + 5, bx + bw - 9):
                if (wx * 7 + wy * 13) % 5 < 2:
                    cv.fill(wx, wy, 4, 5, GOLD)
        bx += step
    cv.fill(x, y + h - 6, w, 6, NAVY_DARK)


def draw_story_box(cv, x, y, w, h, kicker, headline, deck, accent=RED,
                   headline_scale=3, deck_leading=17):
    cv.outline(x, y, w, h, INK, 2)
    pad = 16
    inner = w - 2 * pad
    draw_text(cv, x + pad, y + 12, kicker, 2, accent)
    cy = draw_block(cv, x + pad, y + 36, inner, headline,
                    headline_scale, INK, 7 * headline_scale + 5)
    cy += 4
    return draw_block(cv, x + pad, cy, inner, deck, 2, SOFT, deck_leading)


def draw_market_rows(cv, x, y, w, rows):
    cy = y
    for name, value, move in rows:
        draw_text(cv, x, cy, name, 2, INK)
        mv = text_width(move, 2)
        draw_text(cv, x + w - mv, cy, move, 2, RED)
        vw = text_width(value, 2)
        draw_text(cv, x + w - mv - 10 - vw, cy, value, 2, SOFT)
        cy += 20
        cv.hline(x, cy - 4, w, (210, 204, 188), 1)
    return cy


def build_image():
    cv = Canvas(WIDTH, HEIGHT, PAPER)

    draw_masthead(cv)

    # ---- lead story
    draw_text(cv, 28, 154, "WAR IN UKRAINE - LEAD STORY", 2, RED)
    draw_text(cv, 28, 176, "RUSSIA'S BIGGEST AIR", 5, INK)
    draw_text(cv, 28, 216, "ASSAULT HITS KYIV", 5, INK)
    draw_text(cv, 28, 256, "MISSILES FALL IN POLAND AS NATO ALLIES DRILL NEARBY", 2, SOFT)
    draw_lead_art(cv, 28, 278, 968, 156)
    draw_block(
        cv, 28, 444, 968,
        "MORE THAN 400 DRONES AND 110 MISSILES STRUCK OVERNIGHT. AT LEAST 9 PEOPLE "
        "WERE KILLED AND THREE BRIDGES OVER THE DNIPRO WERE HIT. POLAND SAYS TWO "
        "MISSILES AND A DRONE CAME DOWN ON ITS SOIL. PM TUSK CALLS IT A DELIBERATE "
        "PROVOCATION.",
        2, INK, 19)

    cv.hline(28, 512, 968, INK, 2)

    # ---- middle row: justice and markets
    draw_story_box(
        cv, 28, 524, 474, 200, "JUSTICE - THE HAGUE",
        "WORLD COURT: MYANMAR COMMITTED GENOCIDE",
        "BY 9 VOTES TO 6, THE COURT FOUND THE 2017 CAMPAIGN AGAINST THE ROHINGYA "
        "WAS GENOCIDE - THE FIRST TIME IT HAS HELD A STATE RESPONSIBLE. MYANMAR "
        "MUST ALLOW RETURNS AND PAY REPARATIONS.")
    end = draw_story_box(
        cv, 522, 524, 474, 200, "MARKETS - WALL STREET",
        "AI SELL-OFF DRAGS STOCKS INTO CORRECTION",
        "THE S&P 500 FELL 3.70% AND THE NASDAQ 5.28% AS CHIP STOCKS SLID.")
    draw_market_rows(
        cv, 538, end + 6, 442,
        [("S&P 500", "6,910.39", "-3.70%"),
         ("NASDAQ", "22,617.73", "-5.28%"),
         ("ANTHROPIC", "$2 TRILLION", "DEBUT")])

    cv.hline(28, 736, 968, INK, 2)

    # ---- bottom row: climate, Europe, in brief
    draw_story_box(
        cv, 28, 748, 312, 180, "CLIMATE - ANTALYA",
        "CLIMATE TALKS MISS DEADLINE",
        "COP31 RUNS INTO OVERTIME. NEARLY 200 NATIONS FAIL TO AGREE ON FOSSIL FUELS.")
    draw_story_box(
        cv, 356, 748, 312, 180, "EUROPE - BRUSSELS",
        "UK AND EU SEAL BIG POST-BREXIT DEAL",
        "THREE PACTS: FOOD, CARBON, YOUTH MOBILITY.")
    draw_story_box(
        cv, 684, 748, 312, 180, "IN BRIEF",
        "QUAKE, FIRE AND HOPE",
        "PERU: 6.9 QUAKE SHAKES THE ANDES. BASRA: POWER PLANT FIRE KILLS 4. "
        "CANCER PILL: TUMOURS GONE IN 1 IN 12.",
        deck_leading=16)

    cv.hline(28, 940, 968, INK, 1)
    draw_text_centred(
        cv, WIDTH // 2, 952,
        "SOURCES: REUTERS, BBC, AP, THE GUARDIAN, NYT - 21 NOVEMBER 2026", 2, SOFT)
    cv.hline(28, 984, 968, INK, 3)
    return cv


# ---------------------------------------------------------------- png
def chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png(cv):
    raw = bytearray()
    for yy in range(cv.h):
        raw.append(0)
        base = yy * cv.w * 3
        raw += cv.px[base:base + cv.w * 3]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    return png


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    data = encode_png(build_image())
    with open(path, "wb") as fh:
        fh.write(data)
    print("wrote %s (%d bytes)" % (path, len(data)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
