"""Generate the GM Guides playtest-checklist journal source.

Every activity on all five actors becomes one clickable checklist row with the
exact values the chat card should show — so a data bug is caught by rolling,
not by reading JSON. Expected values here mirror the loose JSONs; the
documented-data checker reads this journal too, so the checklist can't drift
from the actors.

    python3 tools/gen-playtest.py
"""
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "packs", "_source", "ragnarok-reborn-gm-guides",
                   "playtest-checklist.json")


def page(pid, name, content, sort):
    return {
        "name": name,
        "type": "text",
        "title": {"show": True, "level": 2},
        "text": {"format": 1, "content": content, "markdown": ""},
        "_id": pid,
        "image": {},
        "video": {"controls": True, "volume": 0.5},
        "src": None,
        "system": {"tooltip": "", "type": "rule"},
        "sort": sort,
        "ownership": {"default": 0},
        "flags": {},
        "_key": f"!journal.pages!PlayTestChecklist01.{pid}",
    }


def table(rows, headers):
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows
    )
    return (f'<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>')


CHECK = "&#9744;"  # ballot box

OVERVIEW = (
    "<p>A <strong>10-minute in-Foundry smoke test</strong> that exercises every activity "
    "on all five actors (plus both magic items) by actually rolling them. If every box "
    "checks out, the compendium data is behaving exactly as documented — no JSON reading "
    "required.</p>"
    "<p><strong>Setup (1 minute):</strong> import the five actors from the "
    "<em>New Ragnarok Reborn — NPCs</em> compendium into a blank scene, drag the "
    "<em>Cloak of Shadows</em> and <em>Amulet of the Night</em> from the loot pack onto "
    "any player token, and enable <em>GM eye</em> so you can see every chat card.</p>"
    "<p><strong>How to read the table:</strong> each row is one click on an actor sheet. "
    "The <em>Should show</em> column is what the chat card must display. Any mismatch — "
    "wrong bonus, wrong dice, missing effect, empty recharge — is a data bug: note it and "
    "compare against the release's <code>check-actor-fixes.py</code> output before "
    "reporting.</p>"
    "<p>Budget: <strong>3 min</strong> for the Ewoks, <strong>4 min</strong> for "
    "Umbrathor, <strong>3 min</strong> for Vorath. Empty checkbox = untested.</p>"
)

EWOK_ROWS = [
    ["1", "Ewoklin — Claws", "Attack roll", "<code>+7</code> to hit; <code>2d6+4</code> slashing"],
    ["2", "Ewoklin — Primitive Weapon", "Melee Attack roll", "<code>+7</code>; <code>2d8+4</code> piercing"],
    ["3", "Ewoklin — Primitive Weapon", "Thrown (20/60) roll", "<code>+7</code>; <code>2d8+4</code> piercing"],
    ["4", "Ewoklin — Mischievous Surge", "Fey Chaos — DC 15 WIS save", "<code>6d6</code> psychic on fail, half on success; random rider on fail"],
    ["5", "Ewoklin — Evasive Scamper", "Scamper (utility)", "no roll — free reposition without opportunity attacks"],
    ["6", "Ewoklin — Multiplicity (1/Day)", "Split into Ewoklings", "pick 1–4; that many real Ewokling tokens spawn from the compendium"],
    ["7", "Ewokling — Claws", "Attack roll", "<code>+5</code>; <code>1d6+2</code> slashing"],
    ["8", "Ewokling — Primitive Spear", "Melee Attack roll", "<code>+5</code>; <code>1d6+2</code> piercing"],
    ["9", "Ewokling — Primitive Spear", "Thrown (20/60) roll", "<code>+5</code>; <code>1d6+2</code> piercing"],
    ["10", "Ewokling — Mischievous Spark", "Fey Spark — DC 13 WIS save", "<code>2d6</code> psychic on fail, half on success; Laughter on fail"],
    ["11", "Ewokling — Evasive Tumble (1/Day)", "Tumble (utility)", "no roll — disengage-style reposition"],
]
EWOK_RIDERS = (
    "<p><strong>Surge riders (row 4)</strong> — a failed save applies one random effect for "
    "1 minute; roll it three times if you can spare the clicks:</p>"
    "<ul>"
    "<li><strong>Laughter</strong> — target gains <em>incapacitated</em> (status icon visible)</li>"
    "<li><strong>Fear of Technology</strong> — no icon; refusal flavor only (state it aloud)</li>"
    "<li><strong>Battle Fury</strong> — attack rolls improve by 2, AC reduced by 2 while active</li>"
    "</ul>"
    "<p>Recharge chips: Surge recharges on 5–6, Spark on 6 — verify the little die badge "
    "on the item appears after a short-rest recovery or a manual recharge.</p>"
)

UMBRA_ROWS = [
    ["12", "Dark Bolt", "Attack roll", "<code>+12</code>; <code>8d8</code> necrotic (<code>6d8</code> on the Level 8 copy)"],
    ["13", "Terrifying Presence", "Fear Save — DC 20 WIS", "frightened 1 minute on fail"],
    ["14", "Shadow Grasp", "Grasp Save — DC 20 STR", "restrained + <code>3d8</code> necrotic (CR 18 copy)"],
    ["15", "Nightmare Visions (2 Actions)", "Nightmare Save — DC 20 WIS", "<code>8d8</code> psychic; stunned on fail (CR 18 copy only)"],
    ["16", "Summon Shadows (1/Encounter)", "Summon 1d4 Shadows", "1–4 official dnd5e <em>Shadow</em> tokens spawn"],
    ["17", "Shadow Step", "Teleport", "no roll — teleports to a point in dim light/darkness"],
    ["18", "Dark Pact", "Dark Pact Healing", "heals <code>1d8+6</code> (<code>1d6+5</code> Level 8); description adds bonus healing in darkness"],
    ["19", "Dark Rejuvenation", "Rejuvenate", "heals <code>1d8</code> (<code>1d6</code> Level 8) — no other card effects"],
]
UMBRA_LAIR = [
    ["20", "Lair — Shadow Flood", "DC 20 CON save", "no damage — darkness closes in (scene effect)"],
    ["21", "Lair — Shadow Tendrils", "DC 20 DEX save", "<code>4d8</code> necrotic, half on success (Level 8: <code>3d8</code>)"],
    ["22", "Lair — Creeping Chill", "DC 20 CON save", "<code>2d10</code> cold, half on success (Level 8: <code>2d8</code>)"],
    ["23", "Lair — Shadow Grasp", "DC 20 STR save", "<code>3d8</code> necrotic + restrained on fail"],
    ["24", "Lair — Shadow Step", "Utility", "no roll — repositions"],
]
UMBRA_NOTE = (
    "<p><strong>Level 8 vs CR 18:</strong> the Level 8 copy has no Nightmare Visions and "
    "smaller dice everywhere (rows show both where they differ). Test whichever you "
    "imported; the parenthetical values cover the other one. The Level 8 copy's attack is "
    "<code>+9</code> and <strong>every one of its saves is DC 18</strong> (vs the CR 18 "
    "copy's +12 / DC 20).</p>"
    "<p><strong>Dark Bolt on-hit:</strong> a hit should apply <em>Max HP Reduced</em> to the "
    "target (effect appears on the victim's sheet; hp.max drops). Check row 12's target "
    "after the hit.</p>"
    "<p>Lair actions: enable the lair from the <em>Lair Actions (Shadow Cavern)</em> item "
    "(initiative 20), or just roll each activity manually from the item — manual rolls are "
    "enough for this checklist.</p>"
)

VORATH_ROWS = [
    ["25", "Shadow Fork", "Attack roll", "<code>+10</code>; <code>4d8+4</code> necrotic"],
    ["26", "Necrotic Grasp", "Attack roll", "<code>+12</code>; <code>8d6</code> necrotic; on hit applies <em>Max HP Reduced</em>"],
    ["27", "Necrotic Grasp", "Max HP Drain — DC 20 CON save", "secondary save activity on the same item"],
    ["28", "Dark Burst (Recharge 5–6)", "Dark Burst — DC 20 DEX save", "<code>10d8</code> necrotic, half on success; blinded on fail; recharges 5–6"],
    ["29", "Eldritch Blast", "Cast — attack roll", "<code>+12</code> to hit (flat, exactly as printed); <code>1d10</code> force per beam"],
    ["30", "Eldritch Blast", "beam count", "one extra beam per 2 spell-caster levels beyond the first — set the level on the cast dialog and confirm the card rolls the right number of beams"],
    ["31", "Cloudkill", "Cast (utility)", "no roll — consumes a slot and starts concentration only; the cloud does the damage"],
    ["32", "Cloudkill", "Enter / Start of Turn — DC 20 CON save", "<code>5d8</code> poison, half on success"],
    ["33", "Dominate Person", "Cast — DC 20 WIS save", "charmed 1 minute on fail; consumes a slot"],
    ["34", "Aura of Despair", "Despair Save — DC 20 WIS", "<code>3d6</code> psychic + frightened on fail"],
    ["35", "Dreadful Gaze", "Gaze Save — DC 20 WIS", "paralyzed on fail"],
    ["36", "Horrifying Visage (Costs 2 Actions)", "Visage Save — DC 20 WIS", "frightened on fail"],
    ["37", "Legendary Resistance (2/Day)", "Persevere (utility)", "no roll — auto-success counter decrements"],
    ["38", "Animate Dead", "Raise Zombie", "one official dnd5e <em>Zombie</em> spawns"],
    ["39", "Dark Pact Healing", "Heal", "heals <code>1d8+6</code>"],
    ["40", "Legendary: Cast a Spell", "Cast Eldritch Blast", "same flat <code>+12</code> card as row 29"],
    ["41", "Legendary: Shadow Teleportation", "Teleport", "no roll"],
]
VORATH_LAIR = [
    ["42", "Lair — Hellfire Bolt", "Attack roll", "<code>+12</code>; <code>3d10</code> fire (plus the <code>6d10</code> rider vs frightened targets, per the description text)"],
    ["43", "Lair — Gates of Dread", "DC 20 WIS save", "frightened on fail"],
    ["44", "Lair — Ember Storm", "DC 20 DEX save", "<code>2d10</code> fire, half on success"],
    ["45", "Lair — Throne of Chains", "DC 20 STR save", "restrained on fail"],
    ["46", "Lair — Shadow Step", "Utility", "no roll"],
]
VORATH_NOTE = (
    "<p><strong>Spell DCs are flat 20</strong> — every save Vorath forces shows DC 20 in "
    "the chat card regardless of his abilities. If a card shows a computed DC, that's the "
    "pre-1.3.2 bug: re-import the actor.</p>"
    "<p><strong>Legendary actions</strong> (rows 40–41) appear under the actor's legendary "
    "actions bar; rows 40–41 can be rolled from the items directly if you don't want to "
    "drive the action economy.</p>"
    "<p>Lair actions: enable from <em>Lair Actions (Hellheim Throne Room)</em> (initiative "
    "20) or roll manually as above.</p>"
)

LEDGER_ROWS = [
    ["A", "Recharge counters", "after Surge/Spark/Dark Burst, the item shows its recharge die (5–6 / 6 / 5–6) and comes back after a rest or manual recharge"],
    ["B", "Duration chips", "failed riders (frightened, charmed, paralyzed, restrained, stunned, incapacitated) show status icons and expire after their 1-minute duration"],
    ["C", "Concentration", "Cloudkill's Cast marks Vorath concentrating; a second concentration spell prompts to drop it"],
    ["D", "Legendary actions", "Vorath's legendary action counter is visible and spends on rows 40–41"],
    ["E", "Cloak of Shadows", "dragged item applies its effect to the wearer: advantage on Stealth checks"],
    ["F", "Amulet of the Night", "weapon attacks gain a necrotic rider — <code>1d6</code> on the standalone item (<code>1d4</code> on the CR 13 embedded copy, matching its own text)"],
    ["G", "Summons", "every spawned token (Ewoklings, Shadows, Zombie) has a working sheet with its own attacks — click one attack to confirm"],
    ["H", "Death housekeeping", "0 HP shows defeated; Dark Pact healing at 0 HP revives him conscious"],
]
VERDICT = (
    "<p><strong>Verdict:</strong> 46/46 activity rows and A–H all checked with zero "
    "surprises — the pack is table-ready. Any mismatch: note the row, then run "
    "<code>python3 tools/check-actor-fixes.py --verify &lt;exported-actor.json&gt;</code> "
    "against the release's snapshot to pinpoint which value drifted, and compare with the "
    "changelog to see when it broke.</p>"
    "<p><em>This checklist is generated from the same data the CI gate asserts — its "
    "expected values cannot silently drift from the actors.</em></p>"
)

journal = {
    "name": "10-Minute Playtest Checklist — Every Activity",
    "pages": [
        page("PlayTestPrep00001", "Overview & Setup", OVERVIEW, 100000),
        page("PlayTestEwoks001", "Ewoklin & Ewokling (3 min)",
             table(EWOK_ROWS, ["#", "Activity", "Roll", "Should show"]) + EWOK_RIDERS,
             200000),
        page("PlayTestUmbra001", "Umbrathor (4 min)",
             table(UMBRA_ROWS, ["#", "Activity", "Roll", "Should show"]) +
             table(UMBRA_LAIR, ["#", "Lair action", "Roll", "Should show"]) + UMBRA_NOTE,
             300000),
        page("PlayTestVorath01", "Vorath (3 min)",
             table(VORATH_ROWS, ["#", "Activity", "Roll", "Should show"]) +
             table(VORATH_LAIR, ["#", "Lair action", "Roll", "Should show"]) + VORATH_NOTE,
             400000),
        page("PlayTestLedger01", "Ledger & Verdict",
             table(LEDGER_ROWS, ["", "Check", "Pass condition"]) + VERDICT,
             500000),
    ],
    "_id": "PlayTestChecklist01",
    "_key": "!journal!PlayTestChecklist01",
    "flags": {"core": {"viewMode": 2}},
    "folder": None,
    "ownership": {"default": 0},
    "sort": 400000,
    "_stats": {
        "duplicateSource": None,
        "coreVersion": "13.344",
        "systemId": "dnd5e",
        "systemVersion": "6.0.1",
        "createdTime": None,
        "modifiedTime": None,
        "lastModifiedBy": None,
        "exportSource": None,
    },
}


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(journal, f, indent=2, ensure_ascii=False)
        f.write("\n")
    n_rows = sum(len(r) for r in (EWOK_ROWS, UMBRA_ROWS, UMBRA_LAIR, VORATH_ROWS, VORATH_LAIR))
    print(f"wrote {os.path.relpath(OUT, REPO)}  ({len(journal['pages'])} pages, {n_rows} activity rows)")


if __name__ == "__main__":
    main()
