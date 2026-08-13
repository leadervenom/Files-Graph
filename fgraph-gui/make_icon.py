"""Generates fgraph's app icon: a small glowing node-graph on a dark rounded
square, echoing the Obsidian-style 3D graph the app renders. Run once with
the .venv python; output is icon.ico (+ icon_1024.png source) in this dir.
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).parent
SIZE = 1024
BG_TOP = (13, 18, 32)      # #0d1220
BG_BOTTOM = (5, 7, 13)     # #05070d
ROOT_NODE = (167, 139, 250)   # violet-300, matches Obsidian-style graph accent
LEAF_NODE = (34, 211, 238)    # cyan-400
EDGE = (99, 102, 241, 120)    # indigo, translucent

# Node layout: one bright root at center, five leaves orbiting it, plus a
# couple of second-ring nodes for depth -- a minimal "file graph" glyph.
CENTER = (SIZE / 2, SIZE / 2)
ROOT_R = SIZE * 0.075
LEAF_R = SIZE * 0.042
RING1_RADIUS = SIZE * 0.24
RING2_RADIUS = SIZE * 0.37

leaves = []
for i, ang in enumerate([90, 18, -54, -126, -198]):
    rad = math.radians(ang)
    leaves.append((CENTER[0] + RING1_RADIUS * math.cos(rad),
                   CENTER[1] - RING1_RADIUS * math.sin(rad)))

ring2 = []
for ang in [54, -18, -270]:
    rad = math.radians(ang)
    ring2.append((CENTER[0] + RING2_RADIUS * math.cos(rad),
                  CENTER[1] - RING2_RADIUS * math.sin(rad)))


def rounded_bg():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    grad = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for y in range(SIZE):
        t = y / SIZE
        c = tuple(int(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * t) for i in range(3))
        gd.line([(0, y), (SIZE, y)], fill=c + (255,))
    mask = Image.new("L", (SIZE, SIZE), 0)
    md = ImageDraw.Draw(mask)
    radius = int(SIZE * 0.22)
    md.rounded_rectangle([0, 0, SIZE - 1, SIZE - 1], radius=radius, fill=255)
    img.paste(grad, (0, 0), mask)
    return img


def glow_circle(draw_target, center, r, color, glow_strength=3.0):
    glow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([center[0] - r * 2.2, center[1] - r * 2.2,
                center[0] + r * 2.2, center[1] + r * 2.2],
               fill=color + (110,))
    glow = glow.filter(ImageFilter.GaussianBlur(r * glow_strength / 3))
    draw_target.alpha_composite(glow)
    solid = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    sd = ImageDraw.Draw(solid)
    sd.ellipse([center[0] - r, center[1] - r, center[0] + r, center[1] + r],
               fill=color + (255,))
    draw_target.alpha_composite(solid)


def build():
    img = rounded_bg()

    edges = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ed = ImageDraw.Draw(edges)
    for lx, ly in leaves:
        ed.line([CENTER, (lx, ly)], fill=EDGE, width=int(SIZE * 0.006))
    for i, (rx, ry) in enumerate(ring2):
        lx, ly = leaves[i % len(leaves)]
        ed.line([(lx, ly), (rx, ry)], fill=EDGE, width=int(SIZE * 0.004))
    edges = edges.filter(ImageFilter.GaussianBlur(SIZE * 0.001))
    img.alpha_composite(edges)

    for rx, ry in ring2:
        glow_circle(img, (rx, ry), LEAF_R * 0.6, LEAF_NODE, glow_strength=2.0)
    for lx, ly in leaves:
        glow_circle(img, (lx, ly), LEAF_R, LEAF_NODE, glow_strength=2.5)
    glow_circle(img, CENTER, ROOT_R, ROOT_NODE, glow_strength=3.5)

    return img


if __name__ == "__main__":
    icon = build()
    png_path = ROOT / "icon_1024.png"
    icon.save(png_path)

    sizes = [16, 24, 32, 48, 64, 128, 256]
    icon.save(ROOT / "icon.ico", sizes=[(s, s) for s in sizes])
    print(f"Wrote {png_path} and {ROOT / 'icon.ico'}")
