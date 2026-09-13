#!/usr/bin/env python3
"""Generate the ragnarok-reborn-demo Adventure pack source — derived, not hand-made.

One Adventure document that bundles everything a GM needs to start playing:
the five NPC actors, both pre-built scenes (whose tokens already carry the
real actor _ids, so tokens bind to actors on import), the two magic items,
and all seven journals. Import the adventure, click "Import All", play.

Layout produced (the official CLI's adventure format — one file per
document; reconstructAdventure reads each referenced file as a single
doc and embeds it):

  packs/_source/ragnarok-reborn-demo/
    demo-adventure.json   the Adventure doc; collections list sidecar paths
    actors/<_id>.json     the five actors   (loose files, world-style)
    scenes/<_id>.json     the two scenes    (from the scenes pack source)
    items/<_id>.json      the two loot items (from the loot pack source)
    journal/<_id>.json    all seven journals (gm-guides + handouts)

compilePack expands the referenced files into fully embedded documents
(reconstructAdventure), which is the form Foundry's adventure importer
consumes. Sidecars are regenerated from their single upstream writers —
never edit them; edit the loose actors / pack sources and rerun this.

    python3 tools/gen-adventure.py
"""
import json
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(REPO, "packs", "_source", "ragnarok-reborn-demo")

ACTOR_FILES = [
    "Ewoklin.json",
    "Ewokling.json",
    "Umbrathor.json",
    "Umbrathor lvl 8.json",
    "Vorath lvl 10 New.json",
]
SCENE_SOURCES = [
    "packs/_source/ragnarok-reborn-scenes/umbrathors-shadow-cavern.json",
    "packs/_source/ragnarok-reborn-scenes/voraths-hellheim-throne-room.json",
]
LOOT_SOURCES = [
    "packs/_source/ragnarok-reborn-loot/cloak-of-shadows.json",
    "packs/_source/ragnarok-reborn-loot/amulet-of-the-night.json",
]
JOURNAL_SOURCES = [
    # player-readable first: import order is the array order
    "packs/_source/ragnarok-reborn-handouts/welcome-players-guide.json",
    "packs/_source/ragnarok-reborn-handouts/treasures-of-the-shadow-tyrant.json",
    "packs/_source/ragnarok-reborn-gm-guides/umbrathors-shadow-cavern.json",
    "packs/_source/ragnarok-reborn-gm-guides/vorath-scene-guide.json",
    "packs/_source/ragnarok-reborn-gm-guides/umbrathor-encounter-runbook.json",
    "packs/_source/ragnarok-reborn-gm-guides/vorath-encounter-runbook.json",
    "packs/_source/ragnarok-reborn-gm-guides/playtest-checklist.json",
]

ADVENTURE_ID = "DemoAdvRagReb001"


def strip_keys(v):
    """Recursively remove compendium `_key` markers (adventures are world data)."""
    if isinstance(v, dict):
        return {k: strip_keys(x) for k, x in v.items() if k != "_key"}
    if isinstance(v, list):
        return [strip_keys(x) for x in v]
    return v


def load(path):
    return json.load(open(os.path.join(REPO, path), encoding="utf-8"))


def main():
    actors = [strip_keys(load(f)) for f in ACTOR_FILES]
    scenes = [strip_keys(load(f)) for f in SCENE_SOURCES]
    items = [strip_keys(load(f)) for f in LOOT_SOURCES]
    journals = [strip_keys(load(f)) for f in JOURNAL_SOURCES]

    # Cross-link sanity before we ship anything: every scene token that
    # references an actor by _id must find its match among the bundled actors.
    actor_ids = {a["_id"] for a in actors}
    for sc in scenes:
        for t in sc.get("tokens", []):
            aid = t.get("actorId")
            if aid and aid not in actor_ids:
                raise SystemExit(
                    f"scene '{sc['name']}' token '{t['name']}' references actor "
                    f"_id {aid} which is not bundled — fix the scene source")

    bundles = {
        "actors": actors,
        "scenes": scenes,
        "items": items,
        "journal": journals,
    }

    adventure = {
        "name": "The New Ragnarok Reborn — Demo Adventure",
        "img": "modules/ragnarok-reborn-npcs/maps/shadow-cavern.webp",
        "description": (
            "<p>Everything in this module bundled as one playable import: the five "
            "NPCs (Ewoklin, the Ewokling, Umbrathor at CR 18 and CR 13, Vorath), "
            "both pre-built battlemaps with walls, lighting, and pre-placed tokens, "
            "the Cloak of Shadows and Amulet of the Night, and all journals — "
            "player guide, party handouts, scene guides, encounter runbooks, and "
            "the 10-minute playtest checklist.</p>"
            "<p><strong>To play:</strong> import this adventure, click "
            "<em>Import All</em> (or pick pieces), activate a scene, and run the "
            "encounter from its runbook. The journal links below jump to the "
            "guides; the scene tokens are already bound to the bundled actors.</p>"
            "<ul>"
            "<li>@UUID[JournalEntry.PlayerGuide0001.JournalEntryPage.{What's in the Box}]{Player's Guide}</li>"
            "<li>@UUID[JournalEntry.UmbEncRunbook01.JournalEntryPage.{Before the Fight}]{Umbrathor runbook}</li>"
            "<li>@UUID[JournalEntry.VorEncRunbook01.JournalEntryPage.{Before the Fight}]{Vorath runbook}</li>"
            "<li>@UUID[JournalEntry.PlayTestChecklist01.JournalEntryPage.{Overview & Setup}]{Playtest checklist}</li>"
            "</ul>"
        ),
        "actors": [f"actors/{a['_id']}.json" for a in actors],
        "combats": [],
        "cards": [],
        "folders": [],
        "items": [f"items/{i['_id']}.json" for i in items],
        "journal": [f"journal/{j['_id']}.json" for j in journals],
        "macros": [],
        "playlists": [],
        "scenes": [f"scenes/{s['_id']}.json" for s in scenes],
        "tables": [],
        "_id": ADVENTURE_ID,
        "ownership": {"default": 0},
        "flags": {},
        "_stats": {
            "duplicateSource": None, "coreVersion": "13.344",
            "systemId": "dnd5e", "systemVersion": "6.0.1",
            "createdTime": None, "modifiedTime": None,
            "lastModifiedBy": None, "exportSource": None,
        },
        "_key": f"!adventures!{ADVENTURE_ID}",
    }

    os.makedirs(OUT_DIR, exist_ok=True)
    # wipe stale sidecars first so the source dir never accumulates junk
    for sub in ("actors", "scenes", "items", "journal"):
        d = os.path.join(OUT_DIR, sub)
        if os.path.isdir(d):
            for fn in os.listdir(d):
                os.remove(os.path.join(d, fn))
    def write(rel, doc):
        p = os.path.join(OUT_DIR, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)
            f.write("\n")
    write("demo-adventure.json", adventure)
    for sub, docs_ in bundles.items():
        for doc in docs_:
            write(f"{sub}/{doc['_id']}.json", doc)

    token_links = sum(
        1 for sc in scenes for t in sc.get("tokens", []) if t.get("actorId"))
    print(
        f"wrote packs/_source/ragnarok-reborn-demo/  "
        f"({len(actors)} actors, {len(scenes)} scenes, {len(items)} items, "
        f"{len(journals)} journals; {token_links} tokens pre-bound to actor _ids)")


if __name__ == "__main__":
    main()
