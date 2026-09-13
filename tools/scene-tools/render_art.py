"""Renders the two battlemap PNGs from geometry.py.

Same features, same coordinates as the wall builder -> art and walls align
by construction. Deterministic (seeded) so rebuilds are stable.

    python3 render_art.py     -> build_scenes/maps/shadow-cavern.png
                                 build_scenes/maps/hellheim-throne-room.png
"""
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import geometry as G

OUT = os.path.join(os.path.dirname(__file__), "maps")
os.makedirs(OUT, exist_ok=True)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def rock_noise(w, h, scale, seed):
    """fractal-ish value noise as a float array 0..1"""
    rng = np.random.default_rng(seed)
    small = rng.random((max(2, h // scale), max(2, w // scale)))
    img = Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    a = np.asarray(img).astype(np.float32) / 255.0
    return a


def shade(base, noise, amount, tint=(0, 0, 0)):
    """multiply base color by (1 +- amount*noise), then mix in tint by noise"""
    n = (noise - 0.5) * 2.0 * amount
    out = np.zeros((*noise.shape, 3), dtype=np.float32)
    for c in range(3):
        out[..., c] = base[c] * (1.0 + n)
        out[..., c] = out[..., c] * (1 - 0.35) + tint[c] * 0.35 * noise
    return np.clip(out, 0, 255)


def jitter_polyline(pts, mag, seed):
    rng = random.Random(seed)
    out = []
    for i, (x, y) in enumerate(pts):
        if i in (0, len(pts) - 1):
            out.append((x, y))
        else:
            out.append((x + rng.uniform(-mag, mag), y + rng.uniform(-mag, mag)))
    return out


def to_px(pts):
    return [(x * G.CELL, y * G.CELL) for x, y in pts]


# ---------------------------------------------------------------------------
# SHADOW CAVERN
# ---------------------------------------------------------------------------
def draw_cavern():
    rng = random.Random(1207)
    W, H = G.W, G.H
    n1 = rock_noise(W, H, 97, 11)
    n2 = rock_noise(W, H, 23, 22)
    base = shade((46, 40, 58), 0.75 * n1 + 0.25 * n2, 0.28, tint=(20, 14, 34))
    img = Image.fromarray(base.astype(np.uint8))
    d = ImageDraw.Draw(img)

    cav = G.CAV

    # --- floor: the cavern interior, brighter violet-gray stone
    outline = to_px(cav["outline"])
    floor = Image.new("L", (W, H), 0)
    ImageDraw.Draw(floor).polygon(outline, fill=255)
    # corridor + dead ends join the floor
    ImageDraw.Draw(floor).line(to_px([cav["corridor"][0], cav["corridor"][1]]), fill=255, width=3 * G.CELL)
    ImageDraw.Draw(floor).line(to_px([cav["deadend_n"][0], cav["deadend_n"][1]]), fill=255, width=2 * G.CELL)
    ImageDraw.Draw(floor).line(to_px([cav["deadend_e"][0], cav["deadend_e"][1]]), fill=255, width=2 * G.CELL)
    floor = floor.filter(ImageFilter.GaussianBlur(6))

    stone = np.asarray(img).astype(np.float32)
    brightness = (np.asarray(floor).astype(np.float32) / 255.0)
    for c, v in enumerate((74, 66, 92)):     # floor tint
        stone[..., c] = stone[..., c] * (1 - brightness) + (stone[..., c] * 0.55 + v * 0.75) * brightness
    # mottling on the floor
    spots = rock_noise(W, H, 13, 33)
    floor_spots = brightness * spots
    for c in range(3):
        stone[..., c] -= floor_spots * 22
    img = Image.fromarray(np.clip(stone, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)

    # --- cavern wall edge: thick dark rim along the outline
    rim = jitter_polyline(outline + [outline[0]], 14, 5)
    d.line(rim, fill=(16, 11, 24), width=26, joint="curve")
    d.line(rim, fill=(30, 22, 44), width=12, joint="curve")

    # --- corridor & dead-end rims
    for seg, w in ((cav["corridor"], 3), (cav["deadend_n"], 2), (cav["deadend_e"], 2)):
        a, b = to_px([seg[0], seg[1]])
        d.line([a, b], fill=(16, 11, 24), width=w * G.CELL + 22)
        d.line([a, b], fill=(52, 44, 70), width=w * G.CELL)

    # --- dais: raised ring of stone
    cx, cy = G.pt(cav["dais_center"])
    rx, ry = cav["dais_rx"] * G.CELL, cav["dais_ry"] * G.CELL
    d.ellipse([cx - rx - 22, cy - ry - 22, cx + rx + 22, cy + ry + 22], fill=(30, 24, 46))
    d.ellipse([cx - rx - 10, cy - ry - 10, cx + rx + 10, cy + ry + 10], fill=(88, 76, 116))
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(104, 92, 134))
    # step shading inside
    for k in range(4):
        f = 0.55 + 0.15 * k
        d.ellipse([cx - rx * f, cy - ry * f, cx + rx * f, cy + ry * f],
                  outline=(60, 50, 84), width=4)
    # stair gap: carve an annular ramp through the ring band at gap_angle (SW),
    # spanning the same angle range the wall ring leaves open
    ga = math.radians(cav["gap_angle"])
    spread = math.radians(cav["dais_gap"] / 2)
    r_in, r_out = 0.45, 1.18
    band = []
    for i in range(25):
        a = ga - spread + (2 * spread) * i / 24
        band.append((cx + rx * r_out * math.cos(a), cy + ry * r_out * math.sin(a)))
    for i in range(25):
        a = ga + spread - (2 * spread) * i / 24
        band.append((cx + rx * r_in * math.cos(a), cy + ry * r_in * math.sin(a)))
    d.polygon(band, fill=(74, 66, 92))
    # step treads across the ramp
    for i in range(6):
        f = r_in + (r_out - r_in) * (i + 0.5) / 6
        seg = []
        for j in range(7):
            a = ga - spread + (2 * spread) * j / 6
            seg.append((cx + rx * f * math.cos(a), cy + ry * f * math.sin(a)))
        d.line(seg, fill=(44, 36, 64), width=4)

    # --- stalagmites: dark spiky blobs (terrain walls align to these)
    for (sx, sy, r) in cav["stalagmites"]:
        px, py = G.pt((sx, sy))
        R = r * G.CELL
        spikes = []
        for i in range(9):
            a = 2 * math.pi * i / 9 + rng.uniform(-0.2, 0.2)
            rr = R * rng.uniform(0.75, 1.15)
            spikes.append((px + rr * math.cos(a), py + rr * math.sin(a)))
        d.polygon(spikes, fill=(24, 17, 36), outline=(56, 44, 82))
        d.ellipse([px - R * 0.45, py - R * 0.45, px + R * 0.45, py + R * 0.45], fill=(38, 28, 58))

    # --- Shadow Heart: dark pool with faint violet glow on the dais
    hx, hy = G.pt(cav["heart"])
    for rr, col in ((150, (34, 22, 56)), (110, (48, 30, 84)), (70, (66, 40, 118)), (34, (96, 62, 160))):
        d.ellipse([hx - rr, hy - rr, hx + rr, hy + rr], fill=col)
    # pale bone cracks around it
    for i in range(12):
        a = rng.uniform(0, 2 * math.pi)
        x1, y1 = hx + 160 * math.cos(a), hy + 160 * math.sin(a)
        x2, y2 = hx + 260 * math.cos(a), hy + 260 * math.sin(a)
        d.line([(x1, y1), (x2, y2)], fill=(58, 48, 80), width=3)

    # --- braziers: iron bowl + glow
    for (bx, by) in cav["braziers"]:
        px, py = G.pt((bx, by))
        d.ellipse([px - 46, py - 46, px + 46, py + 46], fill=(70, 60, 92), outline=(24, 18, 36), width=6)
        d.ellipse([px - 26, py - 30, px + 26, py + 26], fill=(180, 120, 60), outline=(60, 34, 16), width=4)

    # --- rubble speckles over the floor
    for _ in range(500):
        x = rng.uniform(0, W); y = rng.uniform(0, H)
        if np.asarray(floor)[min(int(y), H - 1), min(int(x), W - 1)] > 100:
            rr = rng.uniform(2, 9)
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(38 + rng.randint(0, 30), 32 + rng.randint(0, 22), 56 + rng.randint(0, 30)))

    # subtle vignette
    vig = Image.new("L", (W, H), 0)
    ImageDraw.Draw(vig).ellipse([-W * 0.25, -H * 0.25, W * 1.25, H * 1.25], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(220))
    dark = np.asarray(vig).astype(np.float32) / 255.0
    arr = np.asarray(img).astype(np.float32)
    for c in range(3):
        arr[..., c] *= 0.35 + 0.65 * dark
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

    img.save(os.path.join(OUT, "shadow-cavern.png"))
    print("shadow-cavern.png", img.size)


# ---------------------------------------------------------------------------
# HELLHEIM THRONE ROOM
# ---------------------------------------------------------------------------
def draw_hellheim():
    rng = random.Random(666)
    W, H = G.W, G.H
    n1 = rock_noise(W, H, 97, 44)
    n2 = rock_noise(W, H, 23, 55)
    base = shade((66, 36, 30), 0.75 * n1 + 0.25 * n2, 0.3, tint=(40, 10, 8))
    img = Image.fromarray(base.astype(np.uint8))
    d = ImageDraw.Draw(img)
    hel = G.HEL

    x0, y0, x1, y1 = hel["hall"]
    hall_rect = [x0 * G.CELL, y0 * G.CELL, x1 * G.CELL, y1 * G.CELL]

    # --- hall floor: charred flagstones (grid of slabs with jitter)
    floor = Image.new("L", (W, H), 0)
    ImageDraw.Draw(floor).rectangle(hall_rect, fill=255)
    floor = floor.filter(ImageFilter.GaussianBlur(4))
    stone = np.asarray(img).astype(np.float32)
    bright = np.asarray(floor).astype(np.float32) / 255.0
    for c, v in enumerate((96, 58, 50)):
        stone[..., c] = stone[..., c] * (1 - bright) + (stone[..., c] * 0.5 + v * 0.8) * bright
    img = Image.fromarray(np.clip(stone, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)

    # flagstone joints
    for gx in range(x0 + 1, x1):
        d.line([(gx * G.CELL, y0 * G.CELL), (gx * G.CELL, y1 * G.CELL)], fill=(52, 30, 26), width=3)
    for gy in range(y0 + 1, y1):
        d.line([(x0 * G.CELL, gy * G.CELL), (x1 * G.CELL, gy * G.CELL)], fill=(52, 30, 26), width=3)

    # --- chasm: jagged dark pit across the hall with glow cracks
    cy0, cy1 = hel["chasm_y0"] * G.CELL, hel["chasm_y1"] * G.CELL
    cx0, cx1 = hel["chasm_x0"] * G.CELL, hel["chasm_x1"] * G.CELL
    chasm = Image.new("L", (W, H), 0)
    dc = ImageDraw.Draw(chasm)
    top = jitter_polyline([(cx0 + i * 90, cy0 + rng.uniform(-18, 18)) for i in range(int((cx1 - cx0) / 90) + 1)], 10, 7)
    bot = jitter_polyline([(cx0 + i * 90, cy1 + rng.uniform(-18, 18)) for i in range(int((cx1 - cx0) / 90) + 1)], 10, 8)
    pit = top + bot[::-1]
    dc.polygon(pit, fill=255)
    # bridges: gaps in the pit mask
    for bx in hel["bridges"]:
        bxpx = bx[0] * G.CELL
        dc.rectangle([bxpx - G.CELL, cy0 - 60, bxpx + G.CELL, cy1 + 60], fill=0)
    chasm = chasm.filter(ImageFilter.GaussianBlur(3))
    pit_a = np.asarray(chasm).astype(np.float32) / 255.0
    arr = np.asarray(img).astype(np.float32)
    for c, v in enumerate((12, 4, 6)):
        arr[..., c] = arr[..., c] * (1 - pit_a) + v * pit_a
    # hellfire glow deep in the chasm
    glow = rock_noise(W, H, 31, 9)
    for c, v in enumerate((120, 30, 10)):
        arr[..., c] = arr[..., c] + pit_a * glow * v * 0.5
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    # pit rims
    d.line(top, fill=(20, 8, 8), width=8, joint="curve")
    d.line(bot, fill=(20, 8, 8), width=8, joint="curve")

    # bridges (stone slabs over the pit)
    for bx in hel["bridges"]:
        bxpx = bx[0] * G.CELL
        d.rectangle([bxpx - G.CELL, cy0 - 30, bxpx + G.CELL, cy1 + 30], fill=(88, 54, 44), outline=(30, 16, 14), width=6)
        for yy in range(int(cy0) - 20, int(cy1) + 30, 40):
            d.line([(bxpx - G.CELL + 8, yy), (bxpx + G.CELL - 8, yy)], fill=(60, 36, 30), width=3)

    # fissures: glowing cracks in the hall floor (kept clear of the chasm band)
    for (x0f, y0f, x1f, y1f) in hel["fissures"]:
        a = (x0f * G.CELL, y0f * G.CELL)
        b = (x1f * G.CELL, y1f * G.CELL)
        pts = jitter_polyline([a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + rng.uniform(-30, 30)), b], 8, 12)
        d.line(pts, fill=(255, 120, 40), width=10, joint="curve")
        d.line(pts, fill=(255, 200, 90), width=4, joint="curve")

    # --- dais (north end): dark basalt with red inlay
    dx0, dy0, dx1, dy1 = hel["dais"]
    drect = [dx0 * G.CELL, dy0 * G.CELL, dx1 * G.CELL, dy1 * G.CELL]
    d.rectangle(drect, fill=(48, 26, 26), outline=(90, 30, 24), width=10)
    d.rectangle([drect[0] + 18, drect[1] + 18, drect[2] - 18, drect[3] - 18], outline=(140, 44, 30), width=4)
    # stairs down from the dais (south edge)
    for i, f in enumerate((0.25, 0.5, 0.75)):
        yy = drect[3] + (i + 1) * 26
        d.rectangle([drect[0] + (drect[2] - drect[0]) * 0.2 * f, yy - 22,
                     drect[2] - (drect[2] - drect[0]) * 0.2 * f, yy + 22],
                    fill=(70, 40, 34), outline=(40, 22, 20))

    # --- throne: obsidian seat with hellfire glow behind it
    tx, ty = G.pt(hel["throne"])
    for rr, col in ((120, (60, 12, 10)), (90, (110, 26, 16)), (60, (180, 60, 24))):
        d.ellipse([tx - rr, ty - rr - 40, tx + rr, ty + rr - 40], fill=col)
    d.polygon([(tx - 80, ty + 60), (tx - 55, ty - 70), (tx, ty - 30), (tx + 55, ty - 70), (tx + 80, ty + 60)],
              fill=(22, 12, 16), outline=(70, 30, 30))

    # --- columns (terrain walls align to these)
    for (colx, coly) in hel["columns"]:
        px, py = G.pt((colx, coly))
        R = hel["column_r"] * G.CELL
        d.ellipse([px - R, py - R, px + R, py + R], fill=(26, 14, 14), outline=(96, 40, 30), width=6)
        d.ellipse([px - R * 0.55, py - R * 0.55, px + R * 0.55, py + R * 0.55], fill=(58, 30, 26))
        d.ellipse([px - R * 0.2, py - R * 0.2, px + R * 0.2, py + R * 0.2], fill=(90, 46, 36))

    # --- braziers
    for (bx, by) in hel["braziers"]:
        px, py = G.pt((bx, by))
        d.ellipse([px - 46, py - 46, px + 46, py + 46], fill=(84, 44, 34), outline=(28, 14, 12), width=6)
        d.ellipse([px - 26, py - 30, px + 26, py + 26], fill=(220, 90, 30), outline=(70, 30, 10), width=4)

    # --- bone piles
    for (bx, by, br) in hel["bones"]:
        px, py = G.pt((bx, by))
        R = br * G.CELL
        for _ in range(14):
            a = rng.uniform(0, 2 * math.pi)
            rr = rng.uniform(0, R * 0.8)
            L = rng.uniform(8, 30)
            xx, yy = px + rr * math.cos(a), py + rr * math.sin(a)
            d.line([(xx, yy), (xx + L * math.cos(a + 1.2), yy + L * math.sin(a + 1.2))],
                   fill=(196, 178, 150), width=6)
            d.ellipse([xx - 4, yy - 4, xx + 4, yy + 4], fill=(220, 205, 175))

    # --- hall wall rim + scorch marks
    d.rectangle(hall_rect, outline=(18, 8, 8), width=24)
    for _ in range(60):
        x = rng.uniform(hall_rect[0], hall_rect[2])
        y = rng.uniform(hall_rect[1], hall_rect[3])
        rr = rng.uniform(20, 90)
        d.ellipse([x - rr, y - rr * 0.6, x + rr, y + rr * 0.6], fill=(44, 24, 20))

    img.save(os.path.join(OUT, "hellheim-throne-room.png"))
    print("hellheim-throne-room.png", img.size)


if __name__ == "__main__":
    draw_cavern()
    draw_hellheim()
