#!/usr/bin/env python3
"""Sync the seven root-level drag-and-drop JSONs with the pack sources.

Two authoring directions, one tool:

  • NPC ACTORS (5) — loose → pack. The loose JSONs at the repo root
    (Ewoklin.json, Ewokling.json, Umbrathor.json, "Umbrathor lvl 8.json",
    "Vorath lvl 10 New.json") are the authoring format: no _key fields, world-style
    summon UUIDs, no effect ownership overrides. The pack sources
    (packs/_source/ragnarok-reborn-npcs/) must carry pack-specific adjustments:

      1. _key hierarchy required by @foundryvtt/foundryvtt-cli:
           actor  → !actors!<actorId>
           item   → !actors.items!<actorId>.<itemId>
           effect → !actors.items.effects!<actorId>.<itemId>.<effectId>
      2. Summon activity profiles that reference one of THIS module's actors are
         rewritten from world UUIDs (Actor.<id>) to compendium UUIDs
         (Compendium.ragnarok-reborn-npcs.ragnarok-reborn-npcs.Actor.<id>), because
         a bare world UUID cannot resolve from inside a compendium document.
         References to anything else (e.g. the official dnd5e zombie/shadow) pass
         through untouched.
      3. Effects get ownership {"default": 0} (GM-locked) when missing, matching
         every release since 1.0.0.

  • SCENES (2) — pack → loose. The scene pack sources
    (packs/_source/ragnarok-reborn-scenes/) are authored by tools/scene-tools/
    (build_scenes.py), so they are authoritative. The loose drag-and-drop files
    at the repo root are generated from them by recursively stripping the
    compiler `_key` fields — nothing else differs (verified field-by-field).

    python3 tools/sync-npc-sources.py            # sync all seven files
    python3 tools/sync-npc-sources.py --check    # exit 1 if any are out of sync (CI)
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOOSE_DIR = REPO
PACK_SRC_NPCS = os.path.join(REPO, "packs", "_source", "ragnarok-reborn-npcs")
PACK_SRC_SCENES = os.path.join(REPO, "packs", "_source", "ragnarok-reborn-scenes")

MODULE_ID = "ragnarok-reborn-npcs"
ACTOR_IDS = {
    "Ewoklin.json": "EwoklinNPC0000001",
    "Ewokling.json": "EwoklingNPC00001",
    "Umbrathor.json": "UmbrathorCR1800001",
    "Umbrathor lvl 8.json": "UmbrathorCR1300001",
    "Vorath lvl 10 New.json": "VorathDemonLd0001",
}
# loose filename → (pack-source filename, scene document id)
SCENE_IDS = {
    "Umbrathor's Shadow Cavern (Scene).json": ("umbrathors-shadow-cavern.json", "UmbSceneCav001"),
    "Vorath's Hellheim Throne Room (Scene).json": ("voraths-hellheim-throne-room.json", "VorSceneHell01"),
}


def canon(v):
    return json.dumps(v, sort_keys=True, ensure_ascii=False)


def strip_keys(o):
    if isinstance(o, dict):
        return {k: strip_keys(v) for k, v in o.items() if k != "_key"}
    if isinstance(o, list):
        return [strip_keys(v) for v in o]
    return o


def ensure_effect_ownership(o):
    """Add ownership {"default": 0} to any ActiveEffect dict missing it (in place).

    An ActiveEffect is recognizable by carrying a `statuses` key (its
    `type` varies: base / onsave / ...). Loose world exports omit ownership
    (defaults to owner); in the pack we keep the shipped behavior of
    GM-locked (default: 0) effects.
    """
    if isinstance(o, dict):
        if "statuses" in o:
            o.setdefault("ownership", {"default": 0})
        for v in o.values():
            ensure_effect_ownership(v)
    elif isinstance(o, list):
        for v in o:
            ensure_effect_ownership(v)


def transform_actor(loose_name, doc):
    """Loose actor JSON → pack-source actor JSON (returns a new dict)."""
    actor_id = ACTOR_IDS[loose_name]
    out = json.loads(json.dumps(doc))  # deep copy
    out["_key"] = f"!actors!{actor_id}"
    for item in out.get("items", []):
        item["_key"] = f"!actors.items!{actor_id}.{item['_id']}"
        for eff in item.get("effects", []):
            eff["_key"] = f"!actors.items.effects!{actor_id}.{item['_id']}.{eff['_id']}"
    for eff in out.get("effects", []):
        eff["_key"] = f"!actors.effects!{actor_id}.{eff['_id']}"

    def rekey_uuids(o):
        if isinstance(o, dict):
            if o.get("uuid", "").startswith("Actor."):
                target = o["uuid"].split(".", 1)[1]
                if target in ACTOR_IDS.values():
                    o["uuid"] = f"Compendium.{MODULE_ID}.{MODULE_ID}.Actor.{target}"
            for v in o.values():
                rekey_uuids(v)
        elif isinstance(o, list):
            for v in o:
                rekey_uuids(v)

    rekey_uuids(out)
    ensure_effect_ownership(out)
    return out


def transform_scene(pack_doc):
    """Pack-source scene JSON → loose drag-and-drop scene JSON (returns a new dict).

    The two differ only by the compiler `_key` hierarchy; strip it recursively.
    """
    return strip_keys(json.loads(json.dumps(pack_doc)))


def main():
    check_only = "--check" in sys.argv
    missing = []   # authoritative-file problems — fatal in every mode
    drift = []     # content drift — fatal only in --check mode
    synced = 0
    in_sync = 0

    # ---- NPCs: loose (authoring) → pack source -----------------------------
    for loose_name, actor_id in ACTOR_IDS.items():
        loose_path = os.path.join(LOOSE_DIR, loose_name)
        pack_path = os.path.join(PACK_SRC_NPCS, loose_name)
        if not os.path.exists(loose_path):
            missing.append(f"{loose_name}: loose file missing at repo root")
            continue
        if not os.path.exists(pack_path):
            missing.append(f"{loose_name}: pack source missing ({os.path.relpath(pack_path, REPO)})")
            continue
        loose = json.load(open(loose_path, encoding="utf-8"))
        pack = json.load(open(pack_path, encoding="utf-8"))
        expected = transform_actor(loose_name, loose)
        if canon(strip_keys(expected)) == canon(strip_keys(pack)):
            in_sync += 1
            print(f"in sync    {loose_name}")
        elif check_only:
            drift.append(f"{loose_name}: pack source out of sync with loose file")
        else:
            with open(pack_path, "w", encoding="utf-8") as f:
                json.dump(expected, f, indent=2, ensure_ascii=False)
                f.write("\n")
            synced += 1
            print(f"synced     {loose_name} → {os.path.relpath(pack_path, REPO)}")

    # ---- Scenes: pack source (authoritative, from tools/scene-tools) → loose
    for loose_name, (pack_name, _scene_id) in SCENE_IDS.items():
        loose_path = os.path.join(LOOSE_DIR, loose_name)
        pack_path = os.path.join(PACK_SRC_SCENES, pack_name)
        if not os.path.exists(pack_path):
            missing.append(f"{pack_name}: scene pack source missing ({os.path.relpath(pack_path, REPO)})")
            continue
        pack = json.load(open(pack_path, encoding="utf-8"))
        expected = transform_scene(pack)
        exists = os.path.exists(loose_path)
        if exists:
            loose = json.load(open(loose_path, encoding="utf-8"))
            if canon(strip_keys(expected)) == canon(strip_keys(loose)):
                in_sync += 1
                print(f"in sync    {loose_name}")
                continue
        if check_only:
            drift.append(f"{loose_name}: loose scene file "
                         f"{'missing' if not exists else 'out of sync with pack source'}")
        else:
            with open(loose_path, "w", encoding="utf-8") as f:
                json.dump(expected, f, indent=2, ensure_ascii=False)
                f.write("\n")
            synced += 1
            print(f"synced     {os.path.relpath(pack_path, REPO)} → {loose_name}")

    if missing:
        for p in missing:
            print(f"MISSING    {p}", file=sys.stderr)
        sys.exit(1)
    if check_only and drift:
        for p in drift:
            print(f"OUT OF SYNC  {p}", file=sys.stderr)
        print("\nRun `python3 tools/sync-npc-sources.py` and recommit.", file=sys.stderr)
        sys.exit(1)
    if check_only:
        print(f"All 5 NPC pack sources and 2 loose scene JSONs in sync ({in_sync} pairs)")
    elif synced == 0:
        print("Nothing to do — all seven files already in sync")


if __name__ == "__main__":
    main()
