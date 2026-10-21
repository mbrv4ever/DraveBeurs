# -*- coding: utf-8 -*-
"""Icoon voor DraveBeurs (stijgende grafiek + muntje) met Pillow -> geldig ICO."""
import os
from PIL import Image, ImageDraw

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(ASSETS, exist_ok=True)
SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def draw(sz):
    k = sz / 256.0
    im = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, sz - 1, sz - 1], int(46 * k),
                        fill=(16, 22, 38, 255), outline=(60, 110, 170, 255),
                        width=int(6 * k))
    # stijgende lijn
    pts = [(40, 190), (90, 150), (130, 168), (180, 96), (216, 70)]
    pts = [(int(x * k), int(y * k)) for x, y in pts]
    d.line(pts, fill=(74, 208, 122, 255), width=int(10 * k), joint="curve")
    for x, y in pts:
        d.ellipse([x - int(7 * k), y - int(7 * k), x + int(7 * k),
                   y + int(7 * k)], fill=(74, 208, 122, 255))
    # muntje
    cx, cy, r = int(170 * k), int(180 * k), int(46 * k)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(245, 200, 60, 255),
              outline=(150, 115, 20, 255), width=int(5 * k))
    try:
        from PIL import ImageFont
        f = ImageFont.truetype("arialbd.ttf", int(46 * k))
        d.text((cx, cy), "€", fill=(120, 90, 15, 255), font=f, anchor="mm")
    except Exception:
        d.text((cx - int(12 * k), cy - int(20 * k)), "E",
               fill=(120, 90, 15, 255))
    return im


for n in (256, 64):
    draw(n).save(os.path.join(ASSETS, "icon-%d.png" % n))
draw(256).save(os.path.join(ASSETS, "icon.ico"), format="ICO", sizes=SIZES)
print("icons done")
