"""Builds the scene pack sources + optimized map images.

Outputs:
  ../ragnarok-reborn-npcs/packs/_source/ragnarok-reborn-scenes/*.json   keyed pack sources
  ../ragnarok-reborn-npcs/maps/*.webp                  optimized map art

Art and walls come from the same geometry module, so they align by construction.

The loose drag-and-drop Scene JSONs at the repo root are NOT written here —
regenerate them with `python3 tools/sync-npc-sources.py` (or `npm run sync:npcs`),
which derives them from the pack sources by stripping the compiler `_key` fields.
"""
import json
import math
import os
import time

from PIL import Image

import geometry as G

HERE = os.path.dirname(__file__)
MODULE = os.path.abspath(os.path.join(HERE, "..", ".."))
ROOT = MODULE
MAPS_OUT = os.path.join(MODULE, "maps")
PACK_SRC = os.path.join(MODULE, "packs", "_source", "ragnarok-reborn-scenes")
os.makedirs(MAPS_OUT, exist_ok=True)
os.makedirs(PACK_SRC, exist_ok=True)

TS = int(time.time() * 1000)

# ---------------------------------------------------------------- constants
WALL_SENSE = 20     # CONST.EDGE_SENSE_TYPES.NORMAL
SENSE_NONE = 0
MOVE_NORMAL = 20
DOOR_NONE, DOOR_DOOR = 0, 1
DS_CLOSED, DS_LOCKED = 0, 2
GRID_SQUARE = 1
OWN_OBSERVER = 2    # CONST.DOCUMENT_OWNERSHIP_LEVELS.OBSERVER
DEFAULT_LEVEL = "defaultLevel0000"

# verified core icon paths (all present in the actors' own files)
IMG_BOSS_UMB = "icons/magic/death/skull-humanoid-white-red.webp"
IMG_BOSS_VOR = "icons/magic/unholy/strike-beam-blood-large-red-purple.webp"
IMG_SHADOW = "icons/magic/perception/silhouette-stealth-shadow.webp"
IMG_ZOMBIE = "icons/magic/death/undead-skeleton-deformed-red.webp"

UMB_ACTOR = "UmbrathorCR1800001"
VOR_ACTOR = "VorathDemonLd0001"

MAP_CAV = "modules/ragnarok-reborn-npcs/maps/shadow-cavern.webp"
MAP_HEL = "modules/ragnarok-reborn-npcs/maps/hellheim-throne-room.webp"


# ---------------------------------------------------------------- builders
def wall(coords, *, door=DOOR_NONE, ds=DS_CLOSED, move=MOVE_NORMAL,
         light=WALL_SENSE, sight=WALL_SENSE, sound=WALL_SENSE, wid):
    return {
        "_id": wid,
        "c": coords,
        "light": light,
        "move": move,
        "sight": sight,
        "sound": sound,
        "dir": 0,
        "door": door,
        "ds": ds,
        "threshold": {"attenuation": False},
        "animation": None,
        "flags": {},
    }


def light_doc(lid, name, x, y, *, dim, bright, color, alpha=0.5, anim=None,
              anim_speed=3, anim_intensity=3, luminosity=0.5, hidden=False,
              negative=False, coloration=1):
    return {
        "_id": lid,
        "name": name,
        "x": int(x), "y": int(y),
        "elevation": 0,
        "rotation": 0,
        "walls": True,
        "vision": False,
        "hidden": hidden,
        "locked": False,
        "config": {
            "negative": negative,
            "priority": 0,
            "alpha": alpha,
            "angle": 360,
            "bright": bright,
            "color": color,
            "coloration": coloration,
            "dim": dim,
            "attenuation": 0.5,
            "luminosity": luminosity,
            "saturation": 0,
            "contrast": 0,
            "shadows": 0,
            "animation": {
                "type": anim,
                "speed": anim_speed,
                "intensity": anim_intensity,
                "reverse": False,
            },
            "darkness": {"min": 0, "max": 1},
        },
        "flags": {},
    }


def token_doc(tid, name, x, y, *, actor_id=None, img, width=1, height=1,
              disposition=-1, hidden=False, elevation=0, light=None, sight=None,
              display_mode=20, tint="#ffffff"):
    t = {
        "_id": tid,
        "name": name,
        "actorId": actor_id,
        "actorLink": False,
        "delta": None,
        "width": width,
        "height": height,
        "elevation": elevation,
        "x": int(x),
        "y": int(y),
        "sort": 0,
        "disposition": disposition,
        "displayName": display_mode,
        "lockRotation": False,
        "rotation": 0,
        "texture": {
            "src": img,
            "tint": tint,
            "scaleX": 1,
            "scaleY": 1,
            "anchorX": 0.5,
            "anchorY": 0.5,
            "fit": "contain",
            "alphaThreshold": 0.75,
        },
        "hidden": hidden,
        "level": DEFAULT_LEVEL,
        "shape": 1,
        "flags": {},
    }
    if light is not None:
        t["light"] = light
    if sight is not None:
        t["sight"] = sight
    return t


def default_token_light():
    return {
        "negative": False, "priority": 0, "alpha": 1, "angle": 360,
        "bright": 0, "color": None, "coloration": 1, "dim": 0,
        "attenuation": 0.5, "luminosity": 0.5, "saturation": 0,
        "contrast": 0, "shadows": 0,
        "animation": {"type": None, "speed": 5, "intensity": 5, "reverse": False},
        "darkness": {"min": 0, "max": 1},
    }


def default_token_sight(range_ft=60):
    return {
        "angle": 360, "enabled": True, "range": range_ft, "brightness": 0,
        "visionMode": "basic", "color": None, "attenuation": 0.1,
        "saturation": 0, "contrast": 0,
    }


def octagon_walls(cx, cy, r, start_id, base_move=MOVE_NORMAL, base_sight=WALL_SENSE):
    """8 wall segments around (cx, cy) with radius r (square units)."""
    pts = []
    for i in range(8):
        a = 2 * math.pi * i / 8 + math.pi / 8
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    out = []
    for i in range(8):
        a, b = pts[i], pts[(i + 1) % 8]
        out.append(wall(
            [round(a[0] * G.CELL), round(a[1] * G.CELL), round(b[0] * G.CELL), round(b[1] * G.CELL)],
            move=base_move, sight=base_sight, light=base_sight,
            wid=f"{start_id}{i:02d}",
        ))
    return out


def scene_skeleton(sid, name, img, darkness, lock, grid_alpha=0.07):
    return {
        "_id": sid,
        "name": name,
        "active": False,
        "navigation": True,
        "navOrder": 0,
        "navName": "",
        "thumb": None,
        "width": G.W,
        "height": G.H,
        "padding": 0.25,
        "shiftX": 0,
        "shiftY": 0,
        "initial": {"x": G.W // 2, "y": G.H // 2, "scale": 0.35},
        "background": {
            "src": img,
            "tint": None,
            "alphaThreshold": None,
            "anchorX": 0.5,
            "anchorY": 0.5,
            "offsetX": 0,
            "offsetY": 0,
            "scaleX": 1,
            "scaleY": 1,
            "rotation": 0,
            "fit": "fill",
        },
        "foreground": None,
        "foregroundElevation": None,
        "grid": {
            "type": GRID_SQUARE,
            "size": G.CELL,
            "style": "solidLines",
            "thickness": 1,
            "color": "#ffffff",
            "alpha": grid_alpha,
            "distance": 5,
            "units": "ft",
        },
        "tokenVision": True,
        "environment": {
            "darknessLevel": darkness,
            "darknessLock": lock,
        },
        "weather": "",
        "drawings": [],
        "tokens": [],
        "lights": [],
        "notes": [],
        "sounds": [],
        "regions": [],
        "tiles": [],
        "walls": [],
        "journal": None,
        "playlist": null(),
        "playlistSound": null(),
        "folder": null(),
        "sort": 0,
        "ownership": {"default": OWN_OBSERVER},
        "flags": {},
    }


def null():
    return None


# =========================================================================
# SHADOW CAVERN
# =========================================================================
def build_cavern():
    cav = G.CAV
    s = scene_skeleton("UmbSceneCav001", "Umbrathor's Shadow Cavern", MAP_CAV,
                       darkness=0.98, lock=True, grid_alpha=0.06)

    walls = []
    # cavern outline (polygon corners -> wall segments), skipping the corridor mouth
    outline = cav["outline"]
    mouth = cav["outline_mouth"]
    for i in range(len(outline)):
        a, b = outline[i], outline[(i + 1) % len(outline)]
        seg = (a, b)
        if seg == mouth or (b, a) == mouth:
            continue
        walls.append(wall(G.segment(a, b), wid=f"UmbW{i:03d}"))
    # entrance corridor: vertical shaft x 11..17, y 34..37.5 (mouth is open)
    (p0x, p0y), (p1x, _p1y), (p2x, p2y), (p3x, p3y) = cav["corridor"]
    walls.append(wall(G.segment((p0x, p0y), (p3x, p3y)), wid="UmbW090"))      # west side
    walls.append(wall(G.segment((p1x, _p1y), (p2x, p2y)), wid="UmbW091"))     # east side
    walls.append(wall(G.segment((p3x, p3y), (p2x, p2y)), wid="UmbW093"))      # map-edge seal
    # locked door across the corridor
    (dx0, dy0), (dx1, dy1d) = cav["door"]
    walls.append(wall(G.segment((dx0, dy0), (dx1, dy0)), door=DOOR_DOOR, ds=DS_LOCKED, wid="UmbW092"))
    # dais ring: movement-blocking low wall with the stair gap left open
    ring = G.dais_ring(cav, steps=40)
    for i in range(len(ring) - 1):   # open polyline: NO wraparound segment
        a, b = ring[i], ring[i + 1]
        walls.append(wall(
            [round(a[0] * G.CELL), round(a[1] * G.CELL), round(b[0] * G.CELL), round(b[1] * G.CELL)],
            move=MOVE_NORMAL, sight=SENSE_NONE, light=SENSE_NONE, sound=SENSE_NONE,
            wid=f"UmbR{i:03d}",
        ))
    # stalagmites: full blockers (vision + light + movement)
    for k, (sx, sy, r) in enumerate(cav["stalagmites"]):
        walls += octagon_walls(sx, sy, r, f"UmbS{k}0")

    lights = []
    for k, (sx, sy) in enumerate(cav["soul_lights"]):
        x, y = G.pt((sx, sy))
        lights.append(light_doc(f"UmbL{k:03d}", "Soul Light", x, y, dim=400, bright=150,
                                color="#7b6fd0", alpha=0.35, anim="pulse",
                                anim_speed=3, anim_intensity=3, luminosity=0.35))
    for k, (bx, by) in enumerate(cav["braziers"]):
        x, y = G.pt((bx, by))
        lights.append(light_doc(f"UmbLB{k:02d}", "Brazier", x, y, dim=400, bright=400,
                                color="#ff9a3c", alpha=0.6, anim="torch",
                                anim_speed=4, anim_intensity=4))
    hx, hy = G.pt(cav["heart"])
    lights.append(light_doc("UmbLHrt1", "Shadow Heart", hx, hy, dim=700, bright=300,
                            color="#3b2d6e", alpha=0.7, anim="pulse",
                            anim_speed=2, anim_intensity=5, luminosity=0.45))
    fx, fy = G.pt(cav["flood"])
    lights.append(light_doc("UmbLFld1", "Shadow Flood (reveal for lair action)", fx, fy,
                            dim=1200, bright=1200, color=None, alpha=1.0, hidden=True,
                            negative=True, luminosity=1))

    boss_light = default_token_light()
    boss_light.update({"dim": 300, "color": "#6a5acd", "alpha": 0.5, "luminosity": 0.35,
                       "animation": {"type": "pulse", "speed": 3, "intensity": 3, "reverse": False}})
    shadow_sight = default_token_sight(90)
    tokens = [
        token_doc("UmbTBoss01", "Umbrathor, the Shadow Tyrant", *px_topleft(cav["boss"]),
                  actor_id=UMB_ACTOR, img=IMG_BOSS_UMB, light=boss_light,
                  sight=default_token_sight(120)),
        # Placeholder Shadow minions (the real ones arrive via the lair action's
        # summon, which spawns the official dnd5e compendium Shadow actor).
        token_doc("UmbTShad1", "Shadow (lair action)", *px_topleft(cav["shadows"][0]),
                  img=IMG_SHADOW, hidden=True, tint="#8888aa", sight=shadow_sight),
        token_doc("UmbTShad2", "Shadow (lair action)", *px_topleft(cav["shadows"][1]),
                  img=IMG_SHADOW, hidden=True, tint="#8888aa", sight=shadow_sight),
    ]

    s["walls"], s["lights"], s["tokens"] = walls, lights, tokens
    return s


# =========================================================================
# HELLHEIM THRONE ROOM
# =========================================================================
def build_hellheim():
    hel = G.HEL
    s = scene_skeleton("VorSceneHell01", "Vorath's Hellheim Throne Room", MAP_HEL,
                       darkness=0.7, lock=True, grid_alpha=0.06)

    walls = []
    hx0, hy0, hx1, hy1 = hel["hall"]
    dsx0, dsx1 = hel["door_s"]
    dex0, dex1 = hel["door_e"]
    # south wall with the grand double doors
    walls.append(wall(G.segment((hx0, hy1), (dsx0, hy1)), wid="VorW010"))
    walls.append(wall(G.segment((dsx0, hy1), ((dsx0 + dsx1) / 2, hy1)), door=DOOR_DOOR, ds=DS_LOCKED, wid="VorW011"))
    walls.append(wall(G.segment(((dsx0 + dsx1) / 2, hy1), (dsx1, hy1)), door=DOOR_DOOR, ds=DS_LOCKED, wid="VorW012"))
    walls.append(wall(G.segment((dsx1, hy1), (hx1, hy1)), wid="VorW013"))
    # east wall with the servants' door (closed, unlocked)
    walls.append(wall(G.segment((hx1, hy0), (hx1, dex0)), wid="VorW014"))
    walls.append(wall(G.segment((hx1, dex0), (hx1, dex1)), door=DOOR_DOOR, ds=DS_CLOSED, wid="VorW015"))
    walls.append(wall(G.segment((hx1, dex1), (hx1, hy1)), wid="VorW016"))
    # north + west walls
    walls.append(wall(G.segment((hx0, hy0), (hx1, hy0)), wid="VorW017"))
    walls.append(wall(G.segment((hx0, hy0), (hx0, hy1)), wid="VorW018"))
    # colonnade: columns block movement but not sight (they are slender)
    for k, (cx, cy) in enumerate(hel["columns"]):
        walls += octagon_walls(cx, cy, hel["column_r"], f"VorC{k}", base_sight=SENSE_NONE)
    # chasm: movement-only pit edges (vision passes; movement blocked except bridges)
    cy0, cy1 = hel["chasm_y0"] * G.CELL, hel["chasm_y1"] * G.CELL
    cx0, cx1 = hel["chasm_x0"] * G.CELL, hel["chasm_x1"] * G.CELL
    bridges = [(b[0] * G.CELL - hel["bridge_w"] * G.CELL // 2,
                b[0] * G.CELL + hel["bridge_w"] * G.CELL // 2) for b in hel["bridges"]]
    for edge_y in (cy0, cy1):
        spans, cur = [], cx0
        for b0, b1 in bridges:
            spans.append((cur, b0))
            cur = b1
        spans.append((cur, cx1))
        for i, (a, b) in enumerate(spans):
            walls.append(wall([int(a), int(edge_y), int(b), int(edge_y)],
                              move=MOVE_NORMAL, light=SENSE_NONE, sight=SENSE_NONE,
                              sound=SENSE_NONE, wid=f"VorP{0 if edge_y == cy0 else 1}{i}"))

    lights = []
    for k, (bx, by) in enumerate(hel["braziers"]):
        x, y = G.pt((bx, by))
        lights.append(light_doc(f"VorLB{k:02d}", "Brazier", x, y, dim=500, bright=450,
                                color="#ff7a2f", alpha=0.6, anim="flame",
                                anim_speed=4, anim_intensity=4))
    tx, ty = G.pt(hel["throne"])
    lights.append(light_doc("VorLThr1", "Throne Glow", tx, ty - 40, dim=500, bright=200,
                            color="#ff2a1a", alpha=0.7, anim="pulse",
                            anim_speed=2, anim_intensity=4, luminosity=0.55))
    # hellfire fissures: a string of small flames along each crack
    k = 0
    for (x0f, y0f, x1f, y1f) in hel["fissures"]:
        n = 4
        for i in range(n):
            fx = x0f + (x1f - x0f) * (i + 0.5) / n
            fy = y0f + (y1f - y0f) * (i + 0.5) / n
            x, y = G.pt((fx, fy))
            lights.append(light_doc(f"VorLF{k:02d}", "Hellfire Fissure", x, y, dim=250, bright=120,
                                    color="#ff6a20", alpha=0.5, anim="flame",
                                    anim_speed=5, anim_intensity=5, luminosity=0.6))
            k += 1
    ex, ey = G.pt(hel["ember"])
    lights.append(light_doc("VorLEmb1", "Ember Storm (reveal for lair action)", ex, ey,
                            dim=600, bright=600, color="#ff5a1f", alpha=0.8, hidden=True,
                            anim="flame", anim_speed=8, anim_intensity=8, luminosity=0.9))

    boss_light = default_token_light()
    boss_light.update({"bright": 300, "dim": 600, "color": "#ff4500", "alpha": 0.6,
                       "luminosity": 0.5,
                       "animation": {"type": "flame", "speed": 3, "intensity": 4, "reverse": False}})
    tokens = [
        token_doc("VorTBoss01", "Vorath, Demon Lord of Helheim", *px_topleft(hel["boss"]),
                  actor_id=VOR_ACTOR, img=IMG_BOSS_VOR, elevation=hel["boss_elevation"],
                  light=boss_light, sight=default_token_sight(120)),
        # Placeholder zombie guards (his Animate Dead summon spawns the official
        # dnd5e compendium Zombie; these bodies mark the throne positions).
        token_doc("VorTZomb1", "Zombie Guard", *px_topleft(hel["zombies"][0]), img=IMG_ZOMBIE),
        token_doc("VorTZomb2", "Zombie Guard", *px_topleft(hel["zombies"][1]), img=IMG_ZOMBIE),
    ]

    s["walls"], s["lights"], s["tokens"] = walls, lights, tokens
    return s


def px_topleft(sq):
    return G.px(sq)


# =========================================================================
# pack-source variants (_keys) + outputs
# =========================================================================
def key_scene(s):
    """return a copy with _key fields for the LevelDB compiler"""
    sid = s["_id"]
    out = dict(s)
    out["_key"] = f"!scenes!{sid}"
    out["walls"] = [dict(w, _key=f"!scenes.walls!{sid}.{w['_id']}") for w in s["walls"]]
    out["lights"] = [dict(l, _key=f"!scenes.lights!{sid}.{l['_id']}") for l in s["lights"]]
    out["tokens"] = [dict(t, _key=f"!scenes.tokens!{sid}.{t['_id']}") for t in s["tokens"]]
    return out


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("wrote", os.path.relpath(path, ROOT))


def export_maps():
    for src, dst in (("maps/shadow-cavern.png", "shadow-cavern.webp"),
                     ("maps/hellheim-throne-room.png", "hellheim-throne-room.webp")):
        im = Image.open(os.path.join(HERE, "maps", os.path.basename(src))).convert("RGB")
        out = os.path.join(MAPS_OUT, dst)
        im.save(out, "WEBP", quality=80, method=5)
        print(f"{dst}: {os.path.getsize(out) // 1024} KB")


if __name__ == "__main__":
    cav = build_cavern()
    hel = build_hellheim()

    # loose drag-and-drop copies (no _keys)
    write_json(os.path.join(ROOT, "Umbrathor's Shadow Cavern (Scene).json"), cav)
    write_json(os.path.join(ROOT, "Vorath's Hellheim Throne Room (Scene).json"), hel)

    # keyed pack sources
    write_json(os.path.join(PACK_SRC, "umbrathors-shadow-cavern.json"), key_scene(cav))
    write_json(os.path.join(PACK_SRC, "voraths-hellheim-throne-room.json"), key_scene(hel))

    export_maps()

    for s in (cav, hel):
        print(f"{s['name']}: {len(s['walls'])} walls, {len(s['lights'])} lights, {len(s['tokens'])} tokens")
