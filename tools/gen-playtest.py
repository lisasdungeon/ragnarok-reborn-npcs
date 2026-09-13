"""Generate the GM Guides playtest-checklist journal source — derived, not hand-listed.

Every activity on all five actors becomes one checklist row with the exact
values the chat card should show. Rows are DERIVED from the loose actor JSONs:
add an activity to an actor, rerun this script, and the checklist gains the
row automatically — no hand-editing. A small OVERRIDES layer only supplies
flavor wording; values always come from the data, and the documented-data
checker reads this journal too, so the checklist can't drift from the actors.

The Ledger's loot rows (Cloak of Shadows, Amulet of the Night) are likewise
derived from the loot pack sources — their effect changes are parsed into pass
conditions, and copies embedded in the actor JSONs with different values are
noted automatically. Edit a loot item's effect and the row follows.

Boss rows carry a Runbook link: the generator matches each activity against
the encounter runbooks by name (activity name first, then item name) and links
to the page that guides it, so a failed roll jumps straight to the GM advice.
The documented-data gate verifies every emitted link target exists.

Actors with two variants (Umbrathor CR 18 / Level 8) are reconciled: rows come
from the primary file, and whenever the secondary's same-named activity has
different values, a "(Level 8: …)" parenthetical is appended automatically.
Activities only the secondary has would be added as extra rows.

    python3 tools/gen-playtest.py
"""
import json
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "packs", "_source", "ragnarok-reborn-gm-guides",
                   "playtest-checklist.json")
LOOT_DIR = os.path.join("packs", "_source", "ragnarok-reborn-loot")

# Effect-change keys this generator knows how to phrase into pass conditions.
ATTACK_KEYS = {
    "rsak": "ranged spell attacks", "msak": "melee spell attacks",
    "rwak": "ranged weapon attacks", "mwak": "melee weapon attacks",
}
SKILL_LABELS = {"ste": "Stealth"}   # extend as loot effects gain skill keys

# Row → runbook-page links: boss actors' activities are matched against their
# encounter runbook's pages by name (activity name first, then item name, then
# the item name sans parenthetical). Coverage is asserted by the
# documented-data gate — a runbook that stops naming an activity fails the PR.
RUNBOOK_MAP = {
    "Umbrathor.json": "umbrathor-encounter-runbook.json",
    "Umbrathor lvl 8.json": "umbrathor-encounter-runbook.json",
    "Vorath lvl 10 New.json": "vorath-encounter-runbook.json",
}
GUIDE_DIR = os.path.join("packs", "_source", "ragnarok-reborn-gm-guides")

_runbook_pages = {}   # runbook file → [(page name, page text)] in sort order
_runbook_ids = {}     # runbook file → journal _id


def load_runbooks():
    for fn in set(RUNBOOK_MAP.values()):
        d = json.load(open(os.path.join(REPO, GUIDE_DIR, fn), encoding="utf-8"))
        _runbook_ids[fn] = d["_id"]
        _runbook_pages[fn] = [(p["name"], p["text"]["content"])
                              for p in sorted(d.get("pages", []),
                                              key=lambda p: p.get("sort", 0))]


def _strip_suffix(s):
    return re.sub(r"\s*\([^)]*\)\s*$", "", s)


def find_runbook_page(fname, item, aname):
    """Name of the runbook page that guides this activity, or None."""
    pages = _runbook_pages[RUNBOOK_MAP[fname]]
    for probe in dict.fromkeys([aname, item, _strip_suffix(item)]):
        if not probe:
            continue
        for pname, content in pages:
            if probe in content:
                return pname
    return None


def runbook_link(fname, item, aname):
    """Compendium link anchor for the row's Runbook cell, or ''."""
    pname = find_runbook_page(fname, item, aname) if fname in RUNBOOK_MAP else None
    if not pname:
        return ""
    jid = _runbook_ids[RUNBOOK_MAP[fname]]
    return f"@UUID[JournalEntry.{jid}.JournalEntryPage.{{{pname}}}]{{{pname}}}"

GROUPS = [
    {"page_id": "PlayTestEwoks001", "page_name": "Ewoklin & Ewokling (3 min)",
     "actors": [("Ewoklin.json", None), ("Ewokling.json", None)], "prose": "riders"},
    {"page_id": "PlayTestUmbra001", "page_name": "Umbrathor (4 min)",
     "actors": [("Umbrathor.json", "Umbrathor lvl 8.json")], "prose": "umbra_note"},
    {"page_id": "PlayTestVorath01", "page_name": "Vorath (3 min)",
     "actors": [("Vorath lvl 10 New.json", None)], "prose": "vor_note"},
]

# Display label for a variant file in reconciled parentheticals.
VARIANT_LABEL = {"Umbrathor lvl 8.json": "Level 8"}

# Flavor wording that derivation can't know. Keyed (file, item, activity name)
# → {"roll": …, "show": …}; either key may be omitted to keep the derived one.
# Values (bonuses, dice, DCs) NEVER belong here — derive them.
OVERRIDES = {
    ("Ewoklin.json", "Evasive Scamper", "Scamper"):
        {"show": "no roll — free reposition without opportunity attacks"},
    ("Ewoklin.json", "Multiplicity (1/Day)", "Split into Ewoklings"):
        {"show": "pick <code>1–4</code>; that many real Ewokling tokens spawn from the compendium"},
    ("Ewokling.json", "Evasive Tumble (1/Day)", "Tumble"):
        {"show": "no roll — disengage-style reposition"},
    ("Umbrathor.json", "Shadow Manipulation", "Hide"):
        {"show": "a d20 check card appears (hiding runs on perception rules)"},
    ("Umbrathor.json", "Shadow Step", "Shadow Step"):
        {"show": "no roll — teleports to a point in dim light/darkness"},
    ("Umbrathor.json", "Dark Pact", "Dark Pact Healing"):
        {"show": "heals <code>1d8+6</code>; description adds bonus healing in darkness"},
    ("Umbrathor.json", "Lair Actions (Shadow Cavern)", "Shadow Flood"):
        {"show": "no damage — darkness closes in (scene effect)"},
    ("Umbrathor.json", "Lair Actions (Shadow Cavern)", "Lair Shadow Step"):
        {"show": "no roll — repositions"},
    ("Umbrathor.json", "Summon Shadows (1/Encounter)", "Summon 1d4 Shadows"):
        {"show": "<code>1–4</code> official dnd5e <em>Shadow</em> tokens spawn"},
    ("Vorath lvl 10 New.json", "Legendary Resistance (2/Day)", "Persevere"):
        {"show": "no roll — auto-success counter decrements"},
    ("Vorath lvl 10 New.json", "Misty Escape", "Misty Escape"):
        {"show": "no roll — teleports away in mist"},
    ("Vorath lvl 10 New.json", "Cloudkill", "Cast"):
        {"show": "no roll — consumes a slot and starts concentration only; the cloud does the damage"},
    ("Vorath lvl 10 New.json", "Animate Dead", "Raise Zombie"):
        {"show": "one official dnd5e <em>Zombie</em> spawns"},
    ("Vorath lvl 10 New.json", "Shadow Teleportation (Legendary)", "Shadow Teleportation"):
        {"show": "no roll"},
    ("Vorath lvl 10 New.json", "Cast a Spell (Legendary)", "Cast Eldritch Blast"):
        {"show": "same flat <code>+12</code> card as Eldritch Blast, spent from the legendary action economy"},
    ("Vorath lvl 10 New.json", "Lair Actions (Hellheim Throne Room)", "Hellfire Bolt"):
        {"show": "<code>+12</code>; <code>3d10</code> fire (plus the <code>6d10</code> rider vs frightened targets, per the description text)"},
    ("Vorath lvl 10 New.json", "Lair Actions (Hellheim Throne Room)", "Lair Shadow Step"):
        {"show": "no roll"},
}

# Static extra rows appended after an actor's derived rows: (item, roll, show).
EXTRAS = {
    "Vorath lvl 10 New.json": [
        ("Eldritch Blast", "beam count",
         "one extra beam per 2 spell-caster levels beyond the first — set the "
         "level on the cast dialog and confirm the card rolls the right number of beams"),
    ],
}

PROSE = {
    "riders": (
        "<p><strong>Surge riders</strong> — a failed save applies one random effect for "
        "1 minute; roll it three times if you can spare the clicks:</p>"
        "<ul>"
        "<li><strong>Laughter</strong> — target gains <em>incapacitated</em> (status icon visible)</li>"
        "<li><strong>Fear of Technology</strong> — no icon; refusal flavor only (state it aloud)</li>"
        "<li><strong>Battle Fury</strong> — attack rolls improve by 2, AC reduced by 2 while active</li>"
        "</ul>"
        "<p>Recharge chips: Surge recharges on 5–6, Spark on 6 — verify the little die badge "
        "on the item appears after a short-rest recovery or a manual recharge.</p>"
    ),
    "umbra_note": (
        "<p><strong>Level 8 vs CR 18:</strong> rows show the CR 18 values, with the Level 8 "
        "copy's differing values in parentheses. Test whichever you imported. The Level 8 "
        "copy has no Nightmare Visions.</p>"
        "<p><strong>Dark Bolt on-hit:</strong> a hit should apply <em>Max HP Reduced</em> to the "
        "target (effect appears on the victim's sheet; hp.max drops). Check that target "
        "after the hit.</p>"
        "<p>Lair actions: enable the lair from the <em>Lair Actions (Shadow Cavern)</em> item "
        "(initiative 20), or just roll each activity manually from the item — manual rolls are "
        "enough for this checklist.</p>"
    ),
    "vor_note": (
        "<p><strong>Spell DCs are flat 20</strong> — every save Vorath forces shows DC 20 in "
        "the chat card regardless of his abilities. If a card shows a computed DC, that's the "
        "pre-1.3.2 bug: re-import the actor.</p>"
        "<p><strong>Legendary actions</strong> appear under the actor's legendary actions bar; "
        "the two legendary items can also be rolled directly if you don't want to drive the "
        "action economy.</p>"
        "<p>Lair actions: enable from <em>Lair Actions (Hellheim Throne Room)</em> (initiative "
        "20) or roll manually as above.</p>"
    ),
}

OVERVIEW = (
    "<p>A <strong>10-minute in-Foundry smoke test</strong> that exercises every activity "
    "on all five actors (plus both magic items) by actually rolling them. If every box "
    "checks out, the compendium data is behaving exactly as documented — no JSON reading "
    "required.</p>"
    "<p><strong>Setup (1 minute):</strong> import the five actors from the "
    "<em>New Ragnarok Reborn — NPCs</em> compendium into a blank scene, drag the "
    "loot items from the Treasures pack onto any player token, and enable "
    "<em>GM eye</em> so you can see every chat card.</p>"
    "<p><strong>How to read the table:</strong> each row is one click on an actor sheet. "
    "The <em>Should show</em> column is what the chat card must display. Any mismatch — "
    "wrong bonus, wrong dice, missing effect, empty recharge — is a data bug: note it and "
    "compare against the release's <code>check-actor-fixes.py</code> output before "
    "reporting. The <em>Runbook</em> column links straight to the matching page of the "
    "encounter runbook, so a failed roll lands on the GM guidance for that ability.</p>"
    "<p>Budget: <strong>3 min</strong> for the Ewoks, <strong>4 min</strong> for "
    "Umbrathor, <strong>3 min</strong> for Vorath. Empty checkbox = untested. This "
    "checklist is generated from the actor data — a new activity on any actor appears "
    "here automatically after <code>python3 tools/gen-playtest.py</code>.</p>"
)

# Ledger rows that are structural Foundry checks, not item data — before and
# after the derived loot rows. Letters are assigned positionally, so the loot
# section can grow without renumbering.
LEDGER_BEFORE = [
    ["Recharge counters", "after Surge/Spark/Dark Burst, the item shows its recharge die (5–6 / 6 / 5–6) and comes back after a rest or manual recharge"],
    ["Duration chips", "failed riders (frightened, charmed, paralyzed, restrained, stunned, incapacitated) show status icons and expire after their 1-minute duration"],
    ["Concentration", "Cloudkill's Cast marks Vorath concentrating; a second concentration spell prompts to drop it"],
    ["Legendary actions", "Vorath's legendary action counter is visible and spends on the two legendary items"],
]
LEDGER_AFTER = [
    ["Summons", "every spawned token (Ewoklings, Shadows, Zombie) has a working sheet with its own attacks — click one attack to confirm"],
    ["Death housekeeping", "0 HP shows defeated; Dark Pact healing at 0 HP revives him conscious"],
]
VERDICT_TMPL = (
    "<p><strong>Verdict:</strong> {n}/{n} activity rows and A–H all checked with zero "
    "surprises — the pack is table-ready. Any mismatch: note the row, then run "
    "<code>python3 tools/check-actor-fixes.py --verify &lt;exported-actor.json&gt;</code> "
    "against the release's snapshot to pinpoint which value drifted, and compare with the "
    "changelog to see when it broke.</p>"
    "<p><em>This checklist is generated from the same data the CI gate asserts — its "
    "expected values cannot silently drift from the actors.</em></p>"
)


# ------------------------------------------------------------ derivation
def dice(part):
    n, den = part.get("number"), part.get("denomination")
    b = str(part.get("bonus", "") or "")
    return f"{n}d{den}+{b}" if b else f"{n}d{den}"


def dmg_str(act):
    parts = act.get("damage", {}).get("parts", [])
    out = []
    for p in parts:
        t = "/".join(p.get("types", []))
        out.append(f"<code>{dice(p)}</code>" + (f" {t}" if t else ""))
    return out


def change_dice(val):
    """'1d6[necrotic]' → ('1d6', 'necrotic'); non-dice values → ('', '')."""
    m = re.match(r"(\d+d\d+)(?:\[([^\]]+)\])?", str(val or ""))
    return (m.group(1), m.group(2) or "") if m else ("", "")


def effect_phrases(effects):
    """Loot effect changes → (pass-condition phrases, conditions). Values only."""
    dmg, skills, conds = {}, [], []
    for e in effects:
        sysd = e.get("system", {})
        conds += sysd.get("conditions", [])
        for c in sysd.get("changes", []):
            key = c.get("key", "")
            d, typ = change_dice(c.get("value"))
            if d:
                segs = key.split(".")
                # bonus keys look like system.bonuses.rsak.damage — kind is
                # the segment before the trailing 'damage'/'attack' segment
                token = segs[-2] if len(segs) > 1 and segs[-1] in ("damage", "attack") else segs[-1]
                kind = ATTACK_KEYS.get(token, "attacks")
                dmg.setdefault((d, typ), set()).add(kind)
            else:
                m = re.search(r"\.skill\.([a-z]{3})$", key)
                if m and c.get("mode") == 0:
                    skills.append(SKILL_LABELS.get(m.group(1), m.group(1).upper()))
    phrases = []
    for (d, typ), kinds in sorted(dmg.items()):
        kt = " and ".join(sorted(kinds))
        phrases.append(f"<strong>{kt}</strong> deal an extra <code>{d}</code>"
                       + (f" <em>{typ}</em>" if typ else ""))
    for s in sorted(set(skills)):
        phrases.append(f"<strong>advantage on {s} checks</strong>")
    return phrases, conds


def primary_dice(item):
    """The standalone item's effect-dice set (for spotting differing copies)."""
    return {d for e in item.get("effects", [])
            for c in e.get("system", {}).get("changes", [])
            for d, _ in [change_dice(c.get("value"))] if d}


def differing_copies(item):
    """Actor-embedded copies of this loot item whose effect dice differ from
    the standalone source → [(dice, label)] with the actor's variant/CR label.
    Matched by name (identifier is system-level and may not survive embedding)."""
    base = primary_dice(item)
    out = []
    for fname, doc in _actors.items():
        for it in doc.get("items", []):
            if it.get("name") != item.get("name"):
                continue
            ds = primary_dice(it)
            if ds and ds != base:
                cr = doc["system"]["details"]["cr"]
                cr = cr if isinstance(cr, int) else cr.get("value")
                if fname == "Umbrathor.json":
                    label = f"{doc['name']} (CR {cr})"
                else:
                    label = f"{VARIANT_LABEL.get(fname, fname)} (CR {cr})"
                out.append(("/".join(sorted(ds)), label))
    return out


def build_ledger_rows():
    """Ledger rows: structural checks, then loot rows derived from the loot
    pack sources, then the rest. Letters assigned by position."""
    rows = [[c for c in r] for r in LEDGER_BEFORE]
    loot_dir = os.path.join(REPO, LOOT_DIR)
    names = []
    for fn in sorted(os.listdir(loot_dir)):
        if not fn.endswith(".json"):
            continue
        item = json.load(open(os.path.join(loot_dir, fn), encoding="utf-8"))
        names.append(item["name"])
        phrases, conds = effect_phrases(item.get("effects", []))
        text = "dragged item applies its effect to the wearer: " + "; ".join(phrases)
        if conds:
            text += " (condition: " + "; ".join(conds) + " — toggle the effect on when it applies)"
        copies = differing_copies(item)
        if copies:
            text += " — " + ", ".join(
                f"<code>{d}</code> on the {label} copy, matching its own text"
                for d, label in copies)
        rows.append([item["name"], text])
    rows += [list(r) for r in LEDGER_AFTER]
    return [[chr(65 + i)] + r for i, r in enumerate(rows)], names


def effects_index(d, item):
    """id → effect, across actor-level and item-embedded effects."""
    idx = {}
    for e in d.get("effects", []):
        idx[e["_id"]] = e
    for e in item.get("effects", []):
        idx[e["_id"]] = e
    return idx


def riders(act, idx):
    """(statuses, names) from the activity's linked effects."""
    stats, names = [], []
    for ref in act.get("effects", []):
        e = idx.get(ref.get("_id") or ref.get("id"))
        if not e:
            continue
        if e.get("statuses"):
            stats.extend(e["statuses"])
        else:
            names.append(e["name"].split(": ")[-1])
    return stats, names


def dur_text(e):
    d = e.get("duration", {})
    v, u = d.get("value"), d.get("units", "")
    if not v or u not in ("minutes", "rounds", "turns"):
        return ""
    unit = u[:-1] if v == 1 else u
    return f" {v} {unit}"


def short_val(act):
    """Compact value summary — used for CR18/Level-8 comparison."""
    t = act.get("type")
    if t == "attack":
        bits = [act.get("attack", {}).get("bonus", "")]
        bits += [dice(p) for p in act.get("damage", {}).get("parts", [])]
        return "; ".join(b for b in bits if b)
    if t == "save":
        dc = (act.get("save", {}).get("dc", {}) or {}).get("formula", "")
        bits = [f"DC {dc}"] if dc else []
        bits += [dice(p) for p in act.get("damage", {}).get("parts", [])]
        return "; ".join(bits)
    if t == "heal":
        h = act.get("healing", {})
        return dice(h) if h.get("denomination") else ""
    if t == "summon":
        return f"1–{len(act.get('profiles', []))}"
    return ""


def derive(item, act, fname):
    """Return (roll, show) for one activity, values straight from the data."""
    t = act.get("type")
    aname = act.get("name", "")
    iname = item["name"]
    idx = effects_index(_actors[fname], item)
    ov = OVERRIDES.get((fname, iname, aname), {})
    label = iname if aname.lower() in ("attack", "cast") or aname == iname else aname

    if t == "attack":
        roll = ov.get("roll", f"{label} — attack roll" if aname.lower() == "cast"
                      else ("Attack roll" if aname.lower() == "attack" else label))
        parts = dmg_str(act)
        show = f"<code>{act.get('attack', {}).get('bonus', '')}</code>"
        show += ("; " + "; ".join(parts)) if parts else ""
        stats, names = riders(act, idx)
        if stats:
            show += f"; on hit applies <em>{stats[0]}</em>"
        elif names:
            show += f"; on hit applies <em>{names[0]}</em>"
        return roll, ov.get("show", show)

    if t == "save":
        s = act.get("save", {})
        dc = (s.get("dc", {}) or {}).get("formula", "")
        ab = "/".join(a.upper() for a in s.get("ability", []))
        roll = ov.get("roll", f"{label} — DC {dc} {ab} save".strip(" —"))
        show = f"<code>DC {dc}</code>"
        parts = dmg_str(act)
        if parts:
            show += "; " + ", ".join(p + ", half on success" for p in parts)
        stats, names = riders(act, idx)
        if len(stats) + len(names) > 1:
            show += "; one random rider on fail (see below)"
        elif stats:
            e = idx.get((act.get("effects") or [{}])[0].get("_id"))
            show += f"; <em>{stats[0]}</em>{dur_text(e) if e else ''} on fail"
        elif names:
            show += "; " + " / ".join(f"<em>{n}</em>" for n in names) + " on fail"
        return roll, ov.get("show", show)

    if t == "heal":
        h = act.get("healing", {})
        roll = ov.get("roll", label if aname != iname else "Heal")
        show = ov.get("show", f"heals <code>{dice(h)}</code>")
        return roll, show

    if t == "summon":
        roll = ov.get("roll", aname)
        show = ov.get("show", f"<code>1–{len(act.get('profiles', []))}</code> tokens spawn from the compendium")
        return roll, show

    if t == "teleport":
        return ov.get("roll", label), ov.get("show", "no roll — teleports")

    if t == "check":
        return ov.get("roll", f"{label} — check"), ov.get("show", "ability check card")

    if t == "cast":
        return ov.get("roll", label), ov.get("show", "triggers the spell's own activity")

    # utility
    roll = ov.get("roll", f"{label} (utility)" if aname.lower() == "cast" else label)
    return roll, ov.get("show", "no roll")


_actors = {}  # file → parsed actor JSON (filled in build_rows)


def build_rows(fname, alt_fname=None):
    """One actor's rows: [(item, aname, roll, show, is_lair)], values from the
    JSONs. With alt_fname (a variant of the SAME actor), differing values get a
    parenthetical and variant-only activities are appended."""
    d = _actors[fname]
    alt_idx = {}
    if alt_fname:
        for it in _actors[alt_fname]["items"]:
            alt_idx[it["name"]] = {
                a.get("name", it["name"]): a
                for a in it.get("system", {}).get("activities", {}).values()
            }

    def alt_act_for(item_name, aname):
        """The alt variant's activity: same name, or the item's only one
        (names drift across variants — 'Summon 1d4' vs 'Summon 1d3')."""
        acts = alt_idx.get(item_name, {})
        if aname in acts:
            return acts[aname]
        return next(iter(acts.values())) if len(acts) == 1 else None

    rows = []
    for item in d.get("items", []):
        acts = item.get("system", {}).get("activities", {})
        for act in acts.values():
            aname = act.get("name", "")
            is_lair = item["name"].startswith("Lair Actions")
            roll, show = derive(item, act, fname)
            link = runbook_link(fname, item["name"], aname)
            if alt_fname:
                alt_act = alt_act_for(item["name"], aname)
                if alt_act is not None:
                    alt_short = short_val(alt_act)
                    if alt_short and alt_short != short_val(act):
                        vl = VARIANT_LABEL.get(alt_fname, "variant")
                        tail = f"{vl} lair: " if is_lair else f"{vl}: "
                        show += f" ({tail}<code>{alt_short}</code>)"
            rows.append((item["name"], aname, roll, show, is_lair, link))
    for item_name, roll, show in EXTRAS.get(fname, []):
            is_lair = item_name.startswith("Lair Actions")
            extra = (item_name, "", roll, show, is_lair, "")
            # Insert right after the item's last derived row so numbering flows.
            pos = max((i for i, r in enumerate(rows) if r[0] == item_name),
                      default=len(rows) - 1) + 1
            # inherit the item's runbook link (extras are follow-ups to it)
            src = next((r for r in rows if r[0] == item_name), None)
            extra = extra[:5] + (src[5] if src else "",)
            rows.insert(pos, extra)
    # variant-only activities become extra rows (an item that exists on both
    # sides is already covered by the reconciled parenthetical above)
    if alt_fname:
        primary_items = {it["name"] for it in d["items"]}
        alt_label = VARIANT_LABEL.get(alt_fname,
                                      _actors[alt_fname]["name"])
        for it in _actors[alt_fname]["items"]:
            if it["name"] in primary_items:
                continue
            for a in it.get("system", {}).get("activities", {}).values():
                aname = a.get("name", it["name"])
                roll, show = derive(it, a, alt_fname)
                rows.append((it["name"], aname, f"{roll} ({alt_label} only)", show,
                             it["name"].startswith("Lair Actions"),
                             runbook_link(alt_fname, it["name"], aname)))
    return rows


# ---------------------------------------------------------------- output
def page(pid, name, content, sort):
    return {
        "name": name, "type": "text",
        "title": {"show": True, "level": 2},
        "text": {"format": 1, "content": content, "markdown": ""},
        "_id": pid, "image": {},
        "video": {"controls": True, "volume": 0.5},
        "src": None,
        "system": {"tooltip": "", "type": "rule"},
        "sort": sort, "ownership": {"default": 0}, "flags": {},
        "_key": f"!journal.pages!PlayTestChecklist01.{pid}",
    }


def table(rows, headers):
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows
    )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def main():
    for g in GROUPS:
        for f, alt in g["actors"]:
            for fname in (f, alt):
                if fname and fname not in _actors:
                    _actors[fname] = json.load(open(os.path.join(REPO, fname),
                                                    encoding="utf-8"))

    n = 0
    pages = []
    links = 0
    load_runbooks()
    for g in GROUPS:
        main_rows, lair_rows = [], []
        multi = len(g["actors"]) > 1
        for fname, alt in g["actors"]:
            prefix = fname[:-len(".json")] if multi else ""
            for item_name, aname, roll, show, is_lair, link in build_rows(fname, alt):
                n += 1
                label = f"{item_name} — {aname}" if aname and aname != item_name else item_name
                links += bool(link)
                cell = [str(n), f"{prefix} — {label}" if prefix else label,
                        roll, show, link]
                (lair_rows if is_lair else main_rows).append(cell)
        content = table(main_rows, ["#", "Activity", "Roll", "Should show", "Runbook"])
        if lair_rows:
            content += table(lair_rows, ["#", "Lair action", "Roll", "Should show", "Runbook"])
        content += PROSE[g["prose"]]
        total_rows = n
        pages.append(page(g["page_id"], g["page_name"], content,
                          100000 * (len(pages) + 2)))

    ledger_rows, loot_names = build_ledger_rows()
    ledger = table(ledger_rows, ["", "Check", "Pass condition"]) + VERDICT_TMPL.format(n=total_rows)
    pages.append(page("PlayTestLedger01", "Ledger & Verdict", ledger, 500000))

    journal = {
        "name": "10-Minute Playtest Checklist — Every Activity",
        "pages": [page("PlayTestPrep00001", "Overview & Setup", OVERVIEW, 100000)] + pages,
        "_id": "PlayTestChecklist01",
        "_key": "!journal!PlayTestChecklist01",
        "flags": {"core": {"viewMode": 2}},
        "folder": None,
        "ownership": {"default": 0},
        "sort": 400000,
        "_stats": {
            "duplicateSource": None, "coreVersion": "13.344",
            "systemId": "dnd5e", "systemVersion": "6.0.1",
            "createdTime": None, "modifiedTime": None,
            "lastModifiedBy": None, "exportSource": None,
        },
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(journal, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"wrote {os.path.relpath(OUT, REPO)}  "
          f"({len(journal['pages'])} pages, {total_rows} activity rows — derived from "
          f"{len(_actors)} actor JSONs and {len(loot_names)} loot items; "
          f"{links} rows linked to runbook pages)")


if __name__ == "__main__":
    main()
