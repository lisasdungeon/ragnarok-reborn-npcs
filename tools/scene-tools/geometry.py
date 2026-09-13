"""Shared geometry for the two Ragnarok Reborn scenes.

Single source of truth: 100px grid, so every coordinate below is in *squares*
and gets multiplied by CELL. The map renderer draws the same features the wall
builder emits walls for, so art and collisions can never drift apart.

  56 x 38 squares, origin top-left.
"""
import math

CELL = 100          # px per grid square
COLS = 56           # scene width  in squares -> 5600 px
ROWS = 38           # scene height in squares -> 3800 px

W = COLS * CELL
H = ROWS * CELL


def px(sq):
    """square coords (x, y) -> pixel coords (top-left of the square)"""
    return (sq[0] * CELL, sq[1] * CELL)


def pt(sq):
    """square coords (x, y) -> pixel point (center of the square)"""
    return (sq[0] * CELL + CELL // 2, sq[1] * CELL + CELL // 2)


def segment(a, b):
    """two square-corner coords -> wall pixel segment [x0, y0, x1, y1] (ints)"""
    return [int(round(a[0] * CELL)), int(round(a[1] * CELL)),
            int(round(b[0] * CELL)), int(round(b[1] * CELL))]


def wall_rect(x0, y0, x1, y1):
    """solid room rectangle: returns 4 wall segments around (x0,y0)-(x1,y1) in square corners"""
    return [
        segment((x0, y0), (x1, y0)),
        segment((x1, y0), (x1, y1)),
        segment((x1, y1), (x0, y1)),
        segment((x0, y1), (x0, y0)),
    ]


# ---------------------------------------------------------------------------
# SHADOW CAVERN  (Umbrathor CR 18 / CR 13 arena)
# ---------------------------------------------------------------------------
CAV = {
    # Main cavern outline (irregular polygon, square corners).
    # The edge from (17,34) to (11,34) is LEFT OPEN - it is the corridor mouth.
    "outline": [(4, 4), (24, 2), (42, 5), (51, 12), (50, 26), (41, 34), (17, 34), (11, 34), (9, 33), (3, 24), (3, 12)],
    "outline_mouth": ((17, 34), (11, 34)),   # skipped segment of the outline
    # Entrance corridor: vertical shaft south of the mouth, x 11..17
    "corridor": [(11.0, 34.0), (17.0, 34.0), (17.0, 37.5), (11.0, 37.5)],
    "door": [(11.0, 36.5), (17.0, 36.5)],
    # Collapsed passages (dead ends, drawn as rubble culs-de-sac)
    "deadend_n": [(30, 2), (31, 5)],
    "deadend_e": [(50, 20), (53, 21)],
    # Central dais (raised ring) - ellipse in squares
    "dais_center": (27, 19),
    "dais_rx": 6.5,
    "dais_ry": 4.5,
    "dais_gap": 60,    # degrees of the ring left open (stairs, centered at gap_angle)
    "gap_angle": 135,  # canvas coords: 0=+x, 90=down; 135 points at the SW entrance
    # Braziers on the approach to the dais
    "braziers": [(22, 25), (32, 25)],
    # Soul-lights around the cavern rim
    "soul_lights": [(7, 8), (45, 8), (46, 28), (10, 29), (17, 5), (38, 4)],
    # Shadow Heart (centerpiece light on the dais)
    "heart": (27, 19),
    # Stalagmites: (cx, cy, radius_squares) terrain walls + art
    "stalagmites": [(9, 16, 1.2), (12, 11, 1.0), (38, 9, 1.1), (44, 17, 1.2),
                    (41, 29, 1.0), (18, 30, 1.1), (34, 32, 1.0), (25, 8, 0.9),
                    (47, 25, 0.8), (7, 27, 0.9)],
    # Umbrathor token start (on the dais, just behind the Shadow Heart)
    "boss": (27, 17),
    # two pre-placed Shadows flanking the dais
    "shadows": [(24, 22), (30, 22)],
    # hero staging zone (just inside the entrance corridor)
    "staging": (14, 35.5),
    # hidden chaos light for Shadow Flood (GM toggles on)
    "flood": (27, 19),
}

# ---------------------------------------------------------------------------
# HELLHEIM THRONE ROOM  (Vorath CR 15 arena)
# ---------------------------------------------------------------------------
HEL = {
    # Rectangular hall, square corners
    "hall": (5, 4, 50, 33),
    # Grand double doors on the south wall, both locked
    "door_s": [26.0, 29.0],
    # Side entrance, east wall (unlocked door) - servants' door
    "door_e": [18.0, 20.0],
    # Dais with throne (north end), rect platform + colonnade ring
    "dais": (20, 4, 35, 11),
    "throne": (27.5, 7),
    # Colonnade: pairs of columns flanking the nave (terrain walls + art)
    "columns": [(13, 14), (19, 14), (36, 14), (42, 14),
                (13, 21), (19, 21), (36, 21), (42, 21)],
    "column_r": 0.55,
    # Chasm (optional brutal feature): wide pit across the hall center with two bridges
    "chasm_y0": 17.5,
    "chasm_y1": 20.5,
    "chasm_x0": 10,
    "chasm_x1": 45,
    "bridges": [(16, 20.0), (39, 20.0)],   # x centers of the 2-sq-wide bridges
    "bridge_w": 2,
    # Braziers along the nave
    "braziers": [(10, 13), (10, 24), (45, 13), (45, 24)],
    # Fissures (hellfire light strips in the hall floor, clear of the chasm band)
    "fissures": [(12, 15.5, 22, 15.5), (34, 23.0, 44, 23.0)],
    # Bone piles (cover, drawn)
    "bones": [(8, 8, 1.6), (23, 26, 1.8), (40, 7, 1.4), (46, 28, 1.5), (15, 29, 1.3)],
    # Vorath hovers over his throne
    "boss": (27, 9),
    "boss_elevation": 15,
    # Two zombie guards flanking the dais stairs
    "zombies": [(24, 12), (31, 12)],
    # hero staging (just inside the grand doors)
    "staging": (27, 31),
    # hidden chaos light for Ember Storm (GM toggles on)
    "ember": (27, 18),
}


# ---------------------------------------------------------------------------
# geometry helpers used by both the art renderer and the wall builder
# ---------------------------------------------------------------------------
def ellipse_arc(cx, cy, rx, ry, start_deg, end_deg, steps=64):
    """points along an ellipse arc, degrees CCW from +x axis (math convention, y up)
    NOTE: canvas y grows downward, so callers negate as needed."""
    pts = []
    for i in range(steps + 1):
        a = math.radians(start_deg + (end_deg - start_deg) * i / steps)
        pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
    return pts


def dais_ring(cfg, steps=96):
    """the dais ring as a list of polyline points in *square* units,
    with the stair gap removed. Returned in canvas coords (y down)."""
    cx, cy = cfg["dais_center"]
    rx, ry = cfg["dais_rx"], cfg["dais_ry"]
    gap = cfg["dais_gap"]
    ga = cfg["gap_angle"]
    # ring runs from gap end around to gap start (leaving the gap open)
    start = ga + gap / 2
    end = ga - gap / 2 + 360
    pts = []
    for i in range(steps + 1):
        a = math.radians(start + (end - start) * i / steps)
        # canvas coords: y = cy - sin(a) would put angle CCW math-style;
        # we simply use y = cy + sin(a) so the gap at 210 deg lands SW (stairs side)
        pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
    return pts
