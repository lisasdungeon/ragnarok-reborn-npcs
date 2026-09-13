#!/usr/bin/env python3
"""Verify that imported actors/items carry the v1.3.1 attack-data fixes.

Users of older module versions can export an actor (or item) from their world
as JSON and check it against the exact fixed data this module ships:

    python3 tools/check-actor-fixes.py --snapshot          # (maintainers) regenerate docs/actor-verification.json from the loose JSONs
    python3 tools/check-actor-fixes.py --check             # (CI) snapshot must match what the loose JSONs build to
    python3 tools/check-actor-fixes.py --verify FILE [...] # (users) check exported actor JSON file(s)
    python3 tools/check-actor-fixes.py --verify --standalone FILE [...]
                                                           # (users) check exported Cloak/Amulet items instead of actors

Only the standard library is used, and the expected data ships pre-extracted in
docs/actor-verification.json — so the script works anywhere Python 3 runs,
including straight from an extracted release zip. Run it from the module folder
(or pass --snapshot to point at a different module root with --root DIR).
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE_ROOT = os.path.dirname(HERE)

LOOSE_ACTORS = ["Ewoklin.json", "Ewokling.json", "Umbrathor.json",
                "Umbrathor lvl 8.json", "Vorath lvl 10 New.json"]
LOOSE_ITEMS = ["packs/_source/ragnarok-reborn-loot/cloak-of-shadows.json",
               "packs/_source/ragnarok-reborn-loot/amulet-of-the-night.json"]
SNAPSHOT = os.path.join(MODULE_ROOT, "docs", "actor-verification.json")

# The silent regression users are checking for: attacks with empty bonus /
# flat=false rolled with no printed bonus and (pre-1.0.1) no damage.
BROKEN_HINT = ("this looks like the pre-1.3.1 pack regression — re-import the "
               "actor from v1.3.1+ or drag the loose JSON from the release zip")


def dice_part(p):
    """Human/compare form of one damage part: '2d6+4'."""
    d = p.get("damage", {}) if isinstance(p, dict) else {}
    if isinstance(p, dict) and "number" in p:
        d = p
    num, den, bon = d.get("number"), d.get("denomination"), d.get("bonus", "")
    return f"{num}d{den}+{bon}".rstrip("+") if den else "0"


# ---------------------------------------------------------------- extraction
def extract_actor(doc):
    """Actor JSON -> {actorId, actorName, activities: {itemId: [...]}, itemNames}."""
    acts = {}
    for it in doc.get("items", []):
        checks = []
        for a in (it.get("system", {}).get("activities") or {}).values():
            t = a.get("type")
            if t == "attack":
                checks.append({"kind": "attack", "name": a.get("name", "Attack"),
                               "bonus": a["attack"].get("bonus", ""), "flat": bool(a["attack"].get("flat")),
                               "damage": [dice_part(p) for p in a.get("damage", {}).get("parts", [])]})
            elif t == "heal":
                h = a.get("healing", {})
                checks.append({"kind": "heal", "name": a.get("name", "Heal"),
                               "formula": f"{h.get('number')}d{h.get('denomination')}+{h.get('bonus', '')}"})
            elif t == "save":
                dc = a.get("save", {}).get("dc", {})
                if dc.get("formula"):
                    checks.append({"kind": "save", "name": a.get("name", "Save"),
                                   "ability": a["save"].get("ability", []), "dc": dc.get("formula")})
        if checks:
            acts[it["_id"]] = {"itemName": it["name"], "checks": checks}
    return {"actorId": doc["_id"], "actorName": doc["name"], "activities": acts}


def extract_item(doc):
    """Standalone item JSON -> relevant effect changes."""
    fx = []
    for e in doc.get("effects", []):
        for c in (e.get("system", {}).get("changes") or []):
            fx.append({"effect": e.get("name", ""),
                       "key": c.get("key"), "mode": c.get("mode"), "value": c.get("value")})
    return {"itemId": doc["_id"], "itemName": doc["name"], "effects": fx}


def build_snapshot(root):
    snap = {"_meta": {"purpose": "Reference data for verifying imported actors/items "
                                   "carry the v1.3.1 attack fixes", "module": "ragnarok-reborn-npcs"},
            "actors": {}, "items": {}}
    for fn in LOOSE_ACTORS:
        path = os.path.join(root, fn)
        if not os.path.exists(path):
            continue
        doc = json.load(open(path, encoding="utf-8"))
        snap["actors"][doc["_id"]] = extract_actor(doc)
    for fn in LOOSE_ITEMS:
        path = os.path.join(root, fn)
        if not os.path.exists(path):
            continue
        doc = json.load(open(path, encoding="utf-8"))
        snap["items"][doc["_id"]] = extract_item(doc)
    return snap


# ------------------------------------------------------------------ checking
class Report:
    def __init__(self):
        self.lines = []
        self.ok = True

    def good(self, msg):
        self.lines.append(f"  \u2713 {msg}")

    def bad(self, msg):
        self.ok = False
        self.lines.append(f"  \u2717 {msg}")

    def note(self, msg):
        self.lines.append(f"    {msg}")


def compare_actor(doc, exp, rep):
    got_id, got_name = doc.get("_id", "?"), doc.get("name", "?")
    found_items = {it.get("_id"): it for it in doc.get("items", [])}
    by_name = {it.get("name"): it for it in doc.get("items", [])}

    for item_id, exp_item in exp["activities"].items():
        it = found_items.get(item_id) or by_name.get(exp_item["itemName"])
        if it is None:
            rep.bad(f"missing item: {exp_item['itemName']} (id {item_id})")
            continue
        acts = list((it.get("system", {}).get("activities") or {}).values())
        for chk in exp_item["checks"]:
            kind = chk["kind"]
            cands = [a for a in acts if a.get("type") == kind and (a.get("name") == chk.get("name") or not chk.get("name"))]
            if not cands:
                cands = [a for a in acts if a.get("type") == kind]
            if not cands:
                rep.bad(f"{exp_item['itemName']}: no {kind} activity found (expected {chk.get('name', kind)})")
                continue
            a = cands[0]
            label = f"{exp_item['itemName']} / {a.get('name', kind)}"
            if kind == "attack":
                got, want = a["attack"].get("bonus", ""), chk["bonus"]
                got_flat, want_flat = bool(a["attack"].get("flat")), chk["flat"]
                got_dmg = [dice_part(p) for p in a.get("damage", {}).get("parts", [])]
                if got == want and got_flat == want_flat and got_dmg == chk["damage"]:
                    rep.good(f"{label}: +{want.strip('+')} flat, {' & '.join(chk['damage'])}")
                else:
                    got_txt = f"+{got or '(empty bonus)'}" if got != want else f"+{got}"
                    rep.bad(f"{label}: want +{want.strip('+')} flat={'true' if want_flat else 'false'} "
                            f"{' & '.join(chk['damage'])} — got {got_txt} flat={'true' if got_flat else 'false'} "
                            f"{' & '.join(got_dmg) if got_dmg else '(no damage parts)'}")
                    if (not got or not got_flat) and got != want:
                        rep.note(BROKEN_HINT)
            elif kind == "heal":
                got = f"{a['healing'].get('number')}d{a['healing'].get('denomination')}+{a['healing'].get('bonus', '')}"
                if got == chk["formula"]:
                    rep.good(f"{label}: {got}")
                else:
                    rep.bad(f"{label}: want {chk['formula']} — got {got}")
                    rep.note(BROKEN_HINT)
            elif kind == "save":
                got_dc = a["save"].get("dc", {}).get("formula", "")
                if got_dc == chk["dc"]:
                    rep.good(f"{label}: DC {chk['dc']} ({'/'.join(chk['ability'])})")
                else:
                    rep.bad(f"{label}: want DC {chk['dc']} — got {got_dc or '(computed)'}")
    return rep.ok


def compare_item(doc, exp, rep):
    fx = extract_item(doc)["effects"]
    got = {(f["key"], f["mode"]): f["value"] for f in fx}
    for want in exp["effects"]:
        key = (want["key"], want["mode"])
        if got.get(key) == want["value"]:
            rep.good(f"{want['effect']}: {want['key']} = {want['value']}")
        else:
            got_val = got.get(key, "(absent)")
            rep.bad(f"{want['effect']}: {want['key']} want {want['value']} — got {got_val}")
            if want["value"] == "1d6[necrotic]" and got_val == "1d4[necrotic]":
                rep.note("got the 1d4 value — this is the CR 13 (Level 8) embedded copy; "
                         "the standalone Treasures-pack item uses 1d6")
    return rep.ok


def verify_files(files, snapshot, standalone):
    any_fail = False
    for path in files:
        try:
            with open(path, encoding="utf-8-sig") as fh:   # -sig: tolerate BOM from export tools
                doc = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"FAIL  {path}: cannot read JSON ({exc})")
            any_fail = True
            continue

        kind = "item" if standalone else "actor"
        table = snapshot["items"] if standalone else snapshot["actors"]
        doc_id, doc_name = doc.get("_id"), doc.get("name")
        exp = table.get(doc_id) or next((v for v in table.values() if v.get("actorName" if not standalone else "itemName") == doc_name), None)
        if standalone:
            exp = table.get(doc_id) or next((v for v in table.values() if v.get("itemName") == doc_name), None)

        rep = Report()
        if exp is None:
            print(f"FAIL  {path}: {doc_name!r} (id {doc_id}) is not one of this module's "
                  f"{'items' if standalone else 'actors'}. Known ids: {', '.join(table)}")
            any_fail = True
            continue

        ok = compare_item(doc, exp, rep) if standalone else compare_actor(doc, exp, rep)
        status = "PASS" if ok else "FAIL"
        print(f"{status}  {doc_name}  (id {doc_id}, {path})")
        for line in rep.lines:
            print(line)
        if not ok:
            any_fail = True
    return any_fail


# ---------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--snapshot", action="store_true", help="regenerate docs/actor-verification.json from the loose JSONs")
    ap.add_argument("--check", action="store_true", help="fail if the committed snapshot no longer matches the loose JSONs")
    ap.add_argument("--verify", action="store_true", help="verify exported actor/item JSON file(s)")
    ap.add_argument("--standalone", action="store_true", help="with --verify: files are standalone items (Cloak/Amulet), not actors")
    ap.add_argument("--root", default=MODULE_ROOT, help="module root (default: parent of tools/)")
    ap.add_argument("files", nargs="*", help="with --verify: exported JSON files to check")
    args = ap.parse_args()

    if args.snapshot:
        snap = build_snapshot(args.root)
        os.makedirs(os.path.dirname(SNAPSHOT), exist_ok=True)
        with open(SNAPSHOT, "w", encoding="utf-8") as fh:
            json.dump(snap, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        n_acts = sum(len(v["activities"]) for v in snap["actors"].values())
        print(f"wrote {SNAPSHOT} ({len(snap['actors'])} actors, {n_acts} activity groups, {len(snap['items'])} items)")
        return 0

    if args.check:
        fresh = build_snapshot(args.root)
        try:
            committed = json.load(open(SNAPSHOT, encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"FAIL: cannot read {SNAPSHOT}: {exc}")
            return 1
        if fresh == committed:
            n_acts = sum(len(v["activities"]) for v in fresh["actors"].values())
            print(f"OK: snapshot matches loose JSONs ({len(fresh['actors'])} actors, {n_acts} activity groups, {len(fresh['items'])} items)")
            return 0
        # name the drift for a useful CI failure
        for section in ("actors", "items"):
            for key in sorted(set(fresh[section]) | set(committed.get(section, {}))):
                if fresh[section].get(key) != committed.get(section, {}).get(key):
                    label = fresh[section].get(key, committed[section][key]).get("actorName") or \
                            fresh[section].get(key, committed[section][key]).get("itemName") or key
                    print(f"FAIL: snapshot drift on {section[:-1]} {label!r} ({key})")
        print("Run: python3 tools/check-actor-fixes.py --snapshot   then commit docs/actor-verification.json")
        return 1

    if args.verify:
        if not args.files:
            ap.error("--verify needs at least one exported JSON file")
        # Prefer the committed snapshot; fall back to live extraction from the
        # loose JSONs so a standalone script+JSONs download also works.
        try:
            snapshot = json.load(open(SNAPSHOT, encoding="utf-8"))
            source = "docs/actor-verification.json"
        except (OSError, json.JSONDecodeError):
            snapshot = build_snapshot(args.root)
            source = "loose JSONs (live)"
        print(f"Reference data: {source}\n")
        bad = verify_files(args.files, snapshot, args.standalone)
        print("\nAll checked " + ("actors/items match the v1.3.1 fixed data." if not bad
                                  else "MISMATCHES FOUND — see above."))
        return 1 if bad else 0

    ap.print_help()
    return 0 if args.files or args.snapshot or args.check else 0


if __name__ == "__main__":
    sys.exit(main())
