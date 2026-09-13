#!/usr/bin/env python3
"""Assert the README's documented numbers match the loose JSONs — and vice versa.

Catches the two drift modes that have bitten this module:

  • README says X, data says Y  — a documented DC / attack bonus / heal formula
    that no longer matches the shipped data (or never existed in it).
  • data regressed silently     — the pre-1.3.1 pack regression (attacks with
    empty bonuses / no damage parts / non-flat encoding) and computed-instead-
    of-flat save DCs (the Hellfire Bolt / Cloudkill class of bug).

Three checks:

  SIGNATURE  every attack activity is flat with a printed bonus and damage
             parts; every save DC is a flat printed value; every heal is
             dice-encoded. Fails on the regression signatures regardless of
             what the README says.
  DATA→DOC   every attack (bonus + each damage part), every flat save DC and
             every heal formula in the loose JSONs must appear in README.md.
  DOC→DATA   every "DC n", "+n" (attack-bonus context) and "ndm+k" token in
             README.md must exist in the data, or be in TEXT_ONLY below with
             a reason (description-only riders, historical changelog values).
  CHECKLIST  the playtest-checklist journal (tools/gen-playtest.py output) is
             a third corpus: every activity's numbers must appear there too
             (players verify by rolling, not by reading), and every number
             the checklist quotes must exist in the data — so the checklist
             cannot silently rot when an actor changes.

    python3 tools/check-documented-data.py        # exit 1 on any drift
    (also exposed as `npm run check:docs`; runs as step 2 of `npm run check`)
"""
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOOSE = [
    "Ewoklin.json",
    "Ewokling.json",
    "Umbrathor.json",
    "Umbrathor lvl 8.json",
    "Vorath lvl 10 New.json",
]

# README tokens that intentionally have no activity-data encoding, with reasons.
# Keep this list short and honest: an entry here is a value a reader cannot
# verify by rolling the actor's printed activities.
TEXT_ONLY = {
    "6d10": "Hellfire Bolt rider: 6d10 only vs frightened targets (description text)",
    "+1": "Lair-action CR adjustment (+1 CR / +1 legendary action), not an attack bonus",
    "+21": "1.3.2 changelog: the OLD stacked Hellfire Bolt bonus, kept as history",
    "1d4": "Amulet of the Night CR 13 embedded copy's necrotic rider / Dark Pact bonus-in-darkness — description-level, not an activity",
}

# The generated playtest checklist (gen-playtest.py) — a third corpus whose
# numbers are asserted against the actors in both directions.
JOURNAL = os.path.join("packs", "_source", "ragnarok-reborn-gm-guides",
                       "playtest-checklist.json")

# Claims allowed to be absent from the playtest checklist, with reasons.
# Intended to stay EMPTY — every activity's numbers belong on the checklist.
CHECKLIST_OK = {}

# Claims allowed to be absent from the README: (kind, item, activity) -> reason.
# Intended to stay EMPTY — prefer documenting the value in README.md.
UNDOCUMENTED_OK = {}


def dice_str(part):
    n, den = part.get("number"), part.get("denomination")
    b = str(part.get("bonus", "") or "")
    return f"{n}d{den}+{b}" if b else f"{n}d{den}"


def load_claims():
    claims = []
    for fn in LOOSE:
        path = os.path.join(REPO, fn)
        doc = json.load(open(path, encoding="utf-8"))
        for it in doc.get("items", []):
            for a in (it.get("system", {}).get("activities") or {}).values():
                base = {
                    "actor": doc["name"], "item": it["name"],
                    "act": a.get("name") or a.get("type"), "file": fn,
                }
                t = a.get("type")
                if t == "attack":
                    at = a.get("attack", {})
                    claims.append({**base, "kind": "attack",
                                   "flat": bool(at.get("flat")),
                                   "bonus": (at.get("bonus") or "").strip(),
                                   "dice": [dice_str(p) for p in a.get("damage", {}).get("parts", [])]})
                elif t == "save":
                    s, dc = a.get("save", {}), (a.get("save", {}).get("dc", {}) or {})
                    claims.append({**base, "kind": "save",
                                   "calc": (dc.get("calculation") or "").strip(),
                                   "dc": (dc.get("formula") or "").strip(),
                                   "dice": [dice_str(p) for p in a.get("damage", {}).get("parts", [])]})
                elif t == "heal":
                    h = a.get("healing", {})
                    claims.append({**base, "kind": "heal",
                                   "formula": dice_str(h) if h.get("denomination") else "",
                                   "custom": bool((h.get("custom") or {}).get("enabled"))})
    return claims


def main():
    readme = open(os.path.join(REPO, "README.md"), encoding="utf-8").read()
    claims = load_claims()
    fails, warns = [], []

    def who(c):
        return f"{c['item']} / {c['act']}"

    # ---------------------------------------------------------- SIGNATURE
    for c in claims:
        if c["kind"] == "attack":
            if not c["flat"]:
                fails.append(f"SIGNATURE {who(c)}: attack is not flat (computed) — "
                             f"pre-1.3.1-style regression signature")
            if not c["bonus"]:
                fails.append(f"SIGNATURE {who(c)}: attack has no printed bonus")
            if not c["dice"]:
                fails.append(f"SIGNATURE {who(c)}: attack has no damage parts")
        elif c["kind"] == "save":
            if c["calc"]:
                fails.append(f"SIGNATURE {who(c)}: save DC is computed ('{c['calc']}') "
                             f"— must be the flat printed value")
            if not c["dc"]:
                fails.append(f"SIGNATURE {who(c)}: save has no flat DC")
        elif c["kind"] == "heal":
            if c["custom"] or not c["formula"]:
                fails.append(f"SIGNATURE {who(c)}: heal is not dice-encoded")

    # ---------------------------------------------------------- DATA → DOC
    def doc_has(text):
        return re.search(rf"(?<!\d){re.escape(text)}(?!\d)", readme) is not None

    for c in claims:
        key = (c["kind"], c["item"], c["act"])
        if c["kind"] == "attack":
            # stored bonus includes its '+' ('+7'); dice may be bare ('8d8')
            ok = doc_has(c["bonus"]) and all(doc_has(d) for d in c["dice"])
            want = f"{c['bonus']} and {' & '.join(c['dice'])}"
        elif c["kind"] == "save":
            ok = doc_has(f"DC {c['dc']}")
            want = f"DC {c['dc']}"
        else:
            ok = doc_has(c["formula"])
            want = c["formula"]
        if not ok and key in UNDOCUMENTED_OK:
            warns.append(f"allowlist entry now unnecessary (documented): {key}")
        elif not ok:
            fails.append(f"DATA→DOC  {who(c)} ({c['actor']}): {want} is not documented in README.md")
        elif ok and key in UNDOCUMENTED_OK:
            pass

    data_bonuses = {int(c["bonus"]) for c in claims if c["kind"] == "attack" and c["bonus"]}
    data_dcs = {int(c["dc"]) for c in claims if c["kind"] == "save" and c["dc"]}
    data_dice = set()
    for c in claims:
        data_dice |= set(c.get("dice", []))
        if c["kind"] == "heal" and c["formula"]:
            data_dice.add(c["formula"])

    # ------------------------------------------------- CHECKLIST (journal)
    journal_path = os.path.join(REPO, JOURNAL)
    if not os.path.exists(journal_path):
        fails.append(f"CHECKLIST missing journal source: {JOURNAL} "
                     f"(run tools/gen-playtest.py)")
        corpus = ""
    else:
        jdoc = json.load(open(journal_path, encoding="utf-8"))
        corpus = "\n".join(
            p.get("text", {}).get("content", "") for p in jdoc.get("pages", []))
    if corpus:
        def chk_has(text):
            return re.search(rf"(?<!\d){re.escape(text)}(?!\d)", corpus) is not None

        # every claim must be checkable by rolling → present in the checklist
        covered = 0
        for c in claims:
            key = (c["kind"], c["item"], c["act"])
            if c["kind"] == "attack":
                ok = chk_has(c["bonus"]) and all(chk_has(d) for d in c["dice"])
                want = f"{c['bonus']} and {' & '.join(c['dice'])}"
            elif c["kind"] == "save":
                ok = chk_has(f"DC {c['dc']}") and all(chk_has(d) for d in c["dice"])
                want = f"DC {c['dc']}"
                if c["dice"]:
                    want += f" and {' & '.join(c['dice'])}"
            else:
                ok = chk_has(c["formula"])
                want = c["formula"]
            if key in CHECKLIST_OK:
                if ok:
                    warns.append(f"CHECKLIST_OK entry now unnecessary: {key}")
            elif not ok:
                fails.append(f"DATA→CHK  {who(c)} ({c['actor']}): {want} is not on "
                             f"the playtest checklist — add a row or extend gen-playtest.py")
            else:
                covered += 1

        # every number the checklist quotes must exist in the data
        chk_dcs = {int(tok) for tok in re.findall(r"DC (\d+)", corpus)}
        for tok in sorted(chk_dcs, key=int):
            if tok not in data_dcs:
                fails.append(f"CHK→DATA  checklist documents DC {tok} — no save in the "
                             f"loose JSONs has it (data DCs: {sorted(data_dcs)})")
        chk_prose = re.sub(r"\d+d\d+(?:\s*\+\s*\d+)?", " ", corpus)
        for m in re.finditer(r"\+(\d+)(?!\d)", chk_prose):
            tok = int(m.group(1))
            if chk_prose[m.end():m.end() + 1] == "d":
                continue
            if tok not in data_bonuses and f"+{tok}" not in TEXT_ONLY:
                fails.append(f"CHK→DATA  checklist quotes attack bonus +{tok} — no attack "
                             f"in the loose JSONs has it (data bonuses: {sorted(data_bonuses)})")
        for tok in set(re.findall(r"(?<![\d.])(\d+d\d+(?:\+\d+)?)(?!\d)", corpus)):
            if tok not in data_dice and tok not in TEXT_ONLY:
                fails.append(f"CHK→DATA  checklist quotes dice '{tok}' — not present in "
                             f"any activity in the loose JSONs")

    # ---------------------------------------------------------- DOC → DATA
    for tok in sorted(set(re.findall(r"DC (\d+)", readme)), key=int):
        if int(tok) not in data_dcs:
            fails.append(f"DOC→DATA  README documents DC {tok} — no save in the loose "
                         f"JSONs has that DC (data DCs: {sorted(data_dcs)})")
    # Scan for '+n' attack-bonus claims, but first remove dice notation
    # ('2d6+4', '1d10') so dice suffixes aren't misread as attack bonuses.
    prose = re.sub(r"\d+d\d+(?:\s*\+\s*\d+)?", " ", readme)
    for m in re.finditer(r"\+(\d+)(?!\d)", prose):
        tok = int(m.group(1))
        if prose[m.end():m.end() + 1] == "d":   # "+1d6" — dice rider, not a bonus
            continue
        if tok not in data_bonuses and f"+{tok}" not in TEXT_ONLY:
            fails.append(f"DOC→DATA  README documents attack bonus +{tok} — no attack in "
                         f"the loose JSONs has it (data bonuses: {sorted(data_bonuses)})")
    for tok in set(re.findall(r"(?<![\d.])(\d+d\d+(?:\+\d+)?)(?!\d)", readme)):
        if tok not in data_dice and tok not in TEXT_ONLY:
            fails.append(f"DOC→DATA  README documents dice '{tok}' — not present in any "
                         f"activity in the loose JSONs")

    used = {t for t in TEXT_ONLY if t in readme or t in corpus}
    for t in sorted(set(TEXT_ONLY) - used):
        warns.append(f"TEXT_ONLY entry '{t}' no longer appears in README.md — prune it")

    # ------------------------------------------------------------- report
    for w in warns:
        print(f"warn: {w}")
    if fails:
        for f in fails:
            print(f"FAIL {f}", file=sys.stderr)
        print(f"\n{len(fails)} documented-data drift failure(s) — fix the JSONs or the "
              f"README so they agree.", file=sys.stderr)
        return 1
    n_att = sum(1 for c in claims if c["kind"] == "attack")
    n_save = sum(1 for c in claims if c["kind"] == "save")
    n_heal = sum(1 for c in claims if c["kind"] == "heal")
    n_chk = covered if corpus else 0
    print(f"OK  documented data matches the loose JSONs "
          f"({n_att} attacks, {n_save} saves, {n_heal} heals; "
          f"bonuses {sorted(data_bonuses)}, DCs {sorted(data_dcs)}; "
          f"checklist covers {n_chk}/{len(claims)} claims)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
