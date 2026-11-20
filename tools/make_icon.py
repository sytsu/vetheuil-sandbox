#!/usr/bin/env python3
"""Draw a 1024x1024 placeholder app icon (water lilies, loosely) with Pillow."""
import sys
from PIL import Image, ImageDraw, ImageFilter

S = 1024
out = sys.argv[1] if len(sys.argv) > 1 else "AppIcon.png"

img = Image.new("RGB", (S, S))
top, bottom = (78, 128, 150), (196, 186, 140)
for y in range(S):
    t = y / (S - 1)
    c = tuple(round(a + (b - a) * t) for a, b in zip(top, bottom))
    ImageDraw.Draw(img).line([(0, y), (S, y)], fill=c)

pads = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(pads)
for (cx, cy, rx, ry, col) in [
    (300, 640, 210, 90, (74, 120, 92, 235)),
    (720, 470, 170, 70, (92, 138, 100, 225)),
    (640, 820, 240, 95, (66, 110, 84, 240)),
]:
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=col)
for (cx, cy, r) in [(330, 600, 58), (700, 440, 44)]:
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(238, 196, 206, 255))
    d.ellipse([cx - r // 3, cy - r // 3, cx + r // 3, cy + r // 3], fill=(246, 222, 150, 255))
pads = pads.filter(ImageFilter.GaussianBlur(2))
img.paste(pads, (0, 0), pads)
img.save(out, optimize=True)
print("wrote", out)
