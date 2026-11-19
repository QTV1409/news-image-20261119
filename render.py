#!/usr/bin/env python3
"""Draw the front page for 19 November 2026 as a 1024x1024 PNG.

Self-contained: Pillow + DejaVu only, no network, no timestamps in the
output, so two runs write byte-identical files.
"""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

W = 1024
H = 1024
MARGIN = 36
GUTTER = 24

PAPER = (253, 251, 244)
INK = (26, 26, 26)
RED = (178, 34, 34)
GREY = (110, 108, 100)
RULE = (26, 26, 26)
FAINT = (200, 198, 188)

SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(draw, text, fnt, max_w):
    """Greedy word wrap measured with textlength; returns a list of lines."""
    words = text.split()
    if not words:
        return []
    lines = []
    cur = words[0]
    for word in words[1:]:
        trial = cur + " " + word
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


def para(draw, x, y, text, fnt, max_w, leading, max_lines=None, fill=INK):
    """Draw wrapped text; trim with an ellipsis past max_lines. Returns lines."""
    lines = wrap(draw, text, fnt, max_w)
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        while lines and draw.textlength(lines[-1] + " ...", font=fnt) > max_w:
            lines[-1] = lines[-1].rsplit(" ", 1)[0] if " " in lines[-1] else lines[-1][:-1]
        lines[-1] = lines[-1] + " ..."
    for i, line in enumerate(lines):
        draw.text((x, y + i * leading), line, font=fnt, fill=fill)
    return lines


def fit(draw, text, fnt_path, start_size, max_w):
    """Largest size at or below start_size whose text fits max_w."""
    size = start_size
    while size > 12:
        fnt = font(fnt_path, size)
        if draw.textlength(text, font=fnt) <= max_w:
            return fnt
        size -= 1
    return font(fnt_path, 12)


def rule(draw, x0, x1, y, width=2):
    draw.line([(x0, y), (x1, y)], fill=RULE, width=width)


# ---- pictogram icons: each draws inside the square (x, y, s) ----
def icon_scales(d, x, y, s):
    cx = x + s // 2
    top = y + s // 8
    beam_y = y + s // 4
    d.line([(cx, top), (cx, y + s * 7 // 8)], fill=INK, width=max(3, s // 28))
    d.line([(x + s // 8, beam_y), (x + s * 7 // 8, beam_y)], fill=INK, width=max(3, s // 28))
    d.line([(cx - s // 16, top), (cx + s // 16, top)], fill=RED, width=max(3, s // 28))
    for sx in (x + s // 8, x + s * 7 // 8):
        d.line([(sx, beam_y), (sx - s // 8, y + s * 5 // 8)], fill=INK, width=max(2, s // 40))
        d.line([(sx, beam_y), (sx + s // 8, y + s * 5 // 8)], fill=INK, width=max(2, s // 40))
        d.arc([sx - s // 8, y + s * 5 // 8 - s // 16, sx + s // 8, y + s * 5 // 8 + s // 16],
              0, 180, fill=INK, width=max(2, s // 40))
    d.line([(cx - s // 5, y + s * 7 // 8), (cx + s // 5, y + s * 7 // 8)], fill=INK, width=max(3, s // 28))


def icon_flags(d, x, y, s):
    cols = [RED, (31, 73, 125), (34, 120, 60)]
    for i, c in enumerate(cols):
        px = x + s // 6 + i * s // 3
        top = y + s // 6 + (0 if i == 1 else s // 12)
        d.line([(px, top), (px, y + s * 5 // 6)], fill=INK, width=max(2, s // 36))
        d.polygon([(px, top), (px + s // 4, top + s // 14), (px, top + s // 7)], fill=c)


def icon_bridge(d, x, y, s):
    deck_y = y + s * 2 // 3
    d.line([(x, deck_y), (x + s, deck_y)], fill=INK, width=max(3, s // 24))
    for tx in (x + s // 4, x + s * 3 // 4):
        d.line([(tx, y + s // 6), (tx, deck_y)], fill=INK, width=max(3, s // 28))
        d.line([(tx - s // 16, y + s // 6), (tx + s // 16, y + s // 6)], fill=RED, width=max(3, s // 28))
    d.arc([x + s // 8, y + s // 6, x + s * 7 // 8, y + s], 180, 360, fill=INK, width=max(2, s // 40))
    for i in range(5):
        vx = x + s // 6 + i * s // 6
        d.line([(vx, y + s // 3), (vx, deck_y)], fill=GREY, width=max(1, s // 60))


def icon_globe(d, x, y, s):
    cx, cy, r = x + s // 2, y + s // 2, s * 3 // 8
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=INK, width=max(3, s // 28))
    d.ellipse([cx - r // 2, cy - r, cx + r // 2, cy + r], outline=INK, width=max(2, s // 40))
    d.line([(cx - r, cy), (cx + r, cy)], fill=INK, width=max(2, s // 40))
    d.arc([cx - r, cy - r // 2, cx + r, cy + r // 2], 0, 180, fill=INK, width=max(2, s // 40))
    d.arc([cx - r, cy - r // 2, cx + r, cy + r // 2], 180, 360, fill=GREY, width=max(2, s // 40))
    d.polygon([(cx + r, cy - r // 2), (cx + r + s // 8, cy - r // 4), (cx + r, cy)], fill=RED)


def icon_chart(d, x, y, s):
    ox, oy = x + s // 8, y + s * 7 // 8
    d.line([(ox, y + s // 8), (ox, oy)], fill=INK, width=max(3, s // 28))
    d.line([(ox, oy), (x + s * 7 // 8, oy)], fill=INK, width=max(3, s // 28))
    bars = [s // 4, s // 2, s * 5 // 8]
    bw = s // 6
    for i, bh in enumerate(bars):
        bx = ox + s // 12 + i * (bw + s // 12)
        d.rectangle([bx, oy - bh, bx + bw, oy], fill=RED if i == 2 else INK)
    d.line([(ox, oy - s // 4), (ox + s // 3, oy - s // 2),
            (ox + s * 2 // 3, oy - s * 5 // 8)], fill=RED, width=max(3, s // 28))


def icon_people(d, x, y, s):
    for i, (cx, r, top) in enumerate((
            (x + s // 2, s // 7, y + s // 8),
            (x + s // 4, s // 8, y + s // 4),
            (x + s * 3 // 4, s // 8, y + s // 4))):
        d.ellipse([cx - r, top, cx + r, top + 2 * r], fill=RED if i == 0 else INK)
        d.arc([cx - r * 3 // 2, top + 2 * r, cx + r * 3 // 2, top + 2 * r + r * 2],
              180, 360, fill=RED if i == 0 else INK, width=max(2, s // 36))


def icon_tanker(d, x, y, s):
    hull_top = y + s * 3 // 5
    d.polygon([(x + s // 8, hull_top), (x + s * 7 // 8, hull_top),
               (x + s * 3 // 4, y + s * 5 // 6), (x + s // 4, y + s * 5 // 6)],
              fill=INK)
    d.rectangle([x + s // 5, y + s // 3, x + s * 2 // 5, hull_top], fill=RED)
    d.rectangle([x + s * 9 // 20, y + s // 4, x + s * 13 // 20, hull_top], fill=INK)
    d.line([(x + s // 6, y + s // 4), (x + s // 6, y + s // 3)], fill=GREY, width=max(2, s // 40))
    for wy in (y + s * 7 // 8, y + s * 15 // 16):
        d.arc([x, wy, x + s // 3, wy + s // 8], 180, 360, fill=GREY, width=max(2, s // 40))
        d.arc([x + s // 3, wy, x + s * 2 // 3, wy + s // 8], 180, 360, fill=GREY, width=max(2, s // 40))
        d.arc([x + s * 2 // 3, wy, x + s, wy + s // 8], 180, 360, fill=GREY, width=max(2, s // 40))


ICONS = {
    "scales": icon_scales,
    "flags": icon_flags,
    "bridge": icon_bridge,
    "globe": icon_globe,
    "chart": icon_chart,
    "people": icon_people,
    "tanker": icon_tanker,
}

# ---- the day's stories: every line from reporting of 19 November 2026 ----
LEAD = {
    "kicker": "THE HAGUE  ·  WORLD COURT",
    "headline": "MYANMAR GUILTY OF GENOCIDE",
    "body": ("The UN's top court rules Myanmar committed genocide against the "
             "Rohingya in its 2017 crackdown \u2014 the first time any state has "
             "been found responsible. Judges cite 10,000 killed and 730,000 "
             "driven into Bangladesh, and order safe return and compensation."),
    "icon": "scales",
}

GRID = [
    {
        "kicker": "SHENZHEN  ·  APEC",
        "headline": "Trump, Xi and Putin meet at last",
        "body": ("The three leaders hold their first trilateral as APEC "
                 "gathers; their villa once hosted Kim Jong-il."),
        "icon": "flags",
    },
    {
        "kicker": "UKRAINE  ·  CRIMEA",
        "headline": "Bridge hit a third time this week",
        "body": ("The Crimea Bridge is struck again overnight; rail traffic "
                 "is suspended while damage is assessed."),
        "icon": "bridge",
    },
    {
        "kicker": "COPENHAGEN  ·  ARCTIC",
        "headline": "Denmark seals Greenland pact with US",
        "body": ("MPs approve a security pact for Greenland, deepening "
                 "US-Danish defence ties in the Arctic."),
        "icon": "globe",
    },
    {
        "kicker": "MARKETS  ·  TECH",
        "headline": "Anthropic tops the biggest-IPO list",
        "body": ("Its record $81bn debut overtakes SpaceX as the world's "
                 "largest public listing."),
        "icon": "chart",
    },
    {
        "kicker": "WASHINGTON  ·  CONGRESS",
        "headline": "Jeffries nominated as first Black Speaker",
        "body": ("Democrats nominate Hakeem Jeffries to lead the House next "
                 "year, a first."),
        "icon": "people",
    },
    {
        "kicker": "ENERGY  ·  THE GULF",
        "headline": "Iran war remakes the energy order",
        "body": ("The war in Iran is redrawing global energy flows, analysts "
                 "say, as oil routes shift."),
        "icon": "tanker",
    },
]

BRIEFS = [
    "Musk calls his $446m midterm spending \u201cpretty foolish\u201d.",
    "Houthi missiles target Riyadh; a Saudi tower is damaged.",
    "Van Gogh sells for a record $190.4m at auction.",
]

FOOTER = ("Sources: Al Jazeera \u00b7 BBC \u00b7 The Guardian \u00b7 The New York Times "
          "\u00b7 DW \u00b7 AP  \u2014  all stories from reporting of 19 November 2026")


def draw_lead(d, y0, y1):
    """Full-width lead story: text left, scales icon right."""
    text_w = 700
    kx, ky = MARGIN, y0 + 6
    d.text((kx, ky), LEAD["kicker"], font=font(SANS_B, 16), fill=RED)
    head_f = fit(d, LEAD["headline"], SERIF_B, 46, text_w)
    hy = ky + 28
    d.text((kx, hy), LEAD["headline"], font=head_f, fill=INK)
    body_f = font(SANS, 20)
    para(d, kx, hy + 62, LEAD["body"], body_f, text_w, 27, max_lines=5)
    ix = W - MARGIN - 168
    iy = y0 + 4
    d.rectangle([ix - 10, iy - 6, ix + 178, iy + 172], outline=FAINT, width=2)
    ICONS[LEAD["icon"]](d, ix, iy, 168)


def draw_grid(d, y0, rows_y, row_h):
    """Two columns by three rows of stories; each has icon + kicker + headline + body."""
    col_w = (W - 2 * MARGIN - GUTTER) // 2
    for idx, story in enumerate(GRID):
        col, row = idx % 2, idx // 2
        x0 = MARGIN + col * (col_w + GUTTER)
        y = rows_y[row]
        icon_s = 84
        ICONS[story["icon"]](d, x0, y + 4, icon_s)
        tx = x0 + icon_s + 14
        tw = col_w - icon_s - 14
        d.text((tx, y), story["kicker"], font=font(SANS_B, 13), fill=RED)
        para(d, tx, y + 20, story["headline"], font(SERIF_B, 21), tw, 25,
             max_lines=2)
        para(d, tx, y + 72, story["body"], font(SANS, 15), tw, 20,
             max_lines=3, fill=(60, 60, 60))
        if row < 2:
            rule(d, x0, x0 + col_w, y + row_h - 12, width=1)


def draw_page():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # Masthead
    mast = "THE WORLD IN ONE PAGE"
    mast_f = fit(d, mast, SERIF_B, 62, W - 2 * MARGIN)
    mw = d.textlength(mast, font=mast_f)
    d.text(((W - mw) / 2, 26), mast, font=mast_f, fill=INK)
    rule(d, MARGIN, W - MARGIN, 104, width=3)
    rule(d, MARGIN, W - MARGIN, 110, width=1)

    # Dateline + deck
    date_f = font(SANS_B, 20)
    date = "THURSDAY, 19 NOVEMBER 2026"
    dw = d.textlength(date, font=date_f)
    d.text(((W - dw) / 2, 122), date, font=date_f, fill=INK)
    deck = "The world's biggest stories \u2014 in one page"
    deck_f = font(SERIF, 18)
    dekw = d.textlength(deck, font=deck_f)
    d.text(((W - dekw) / 2, 150), deck, font=deck_f, fill=GREY)

    # Lead story
    lead_y0, lead_y1 = 186, 386
    draw_lead(d, lead_y0, lead_y1)
    rule(d, MARGIN, W - MARGIN, lead_y1 + 6, width=2)

    # Grid of six
    grid_y0 = lead_y1 + 26
    row_h = 148
    rows_y = [grid_y0, grid_y0 + row_h, grid_y0 + 2 * row_h]
    draw_grid(d, grid_y0, rows_y, row_h)
    also_y = grid_y0 + 3 * row_h - 6
    rule(d, MARGIN, W - MARGIN, also_y, width=2)

    # Also-today strip: three briefs in three columns
    d.text((MARGIN, also_y + 12), "ALSO TODAY", font=font(SANS_B, 14), fill=RED)
    col_w = (W - 2 * MARGIN - 2 * GUTTER) // 3
    brief_f = font(SANS, 14)
    for i, brief in enumerate(BRIEFS):
        bx = MARGIN + i * (col_w + GUTTER)
        para(d, bx, also_y + 38, brief, brief_f, col_w, 19, max_lines=3)

    # Footer
    foot_y = H - 44
    rule(d, MARGIN, W - MARGIN, foot_y - 10, width=1)
    foot_f = font(SANS, 12)
    fw = d.textlength(FOOTER, font=foot_f)
    d.text(((W - fw) / 2, foot_y + 2), FOOTER, font=foot_f, fill=GREY)
    return img


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "entry.png"
    img = draw_page()
    img.save(out, "PNG")
    print("wrote", out, img.size, os.path.getsize(out), "bytes")


if __name__ == "__main__":
    main()
