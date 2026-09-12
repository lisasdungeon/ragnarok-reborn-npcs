# The New Ragnarok Reborn — NPCs (Foundry VTT Module)

An installable Foundry VTT module containing five ready-to-play **dnd5e 6.0.x** NPC actors
in a compendium pack, built for Foundry **v14** (minimum 14.367).

| Actor | CR | Contents |
|---|---|---|
| Ewoklin, Prankster of the Grove | 8 | Claws, Primitive Weapon (melee + thrown), Mischievous Surge (DC 15 WIS, status effects), Evasive Scamper reaction, **Multiplicity — summons real Ewoklings** |
| Ewokling | 2 | Pack Tactics, Claws, Primitive Spear (melee + thrown), Mischievous Spark (Recharge 6), Evasive Tumble |
| Umbrathor, the Shadow Tyrant | 18 | Dark Bolt, Terrifying Presence, Shadow Step, Dark Pact, 3 legendary actions, Cloak of Shadows + Amulet of the Night loot with working equip effects, **Shadow Cavern lair actions (initiative 20) + regional effects** |
| Umbrathor, the Shadow Tyrant (Level 8) | 13 | Scaled-down variant of the above with its own DC 18 lair-action set |
| Vorath, Demon Lord of Helheim | 15 | Legendary Resistance, Aura of Despair, Dreadful Gaze, Misty Escape, Shadow Fork, Necrotic Grasp, Dark Burst (Recharge 5–6), real spell list (Eldritch Blast, Animate Dead, Cloudkill, Dominate Person), 2 legendary actions, **Hellheim Throne Room lair actions (initiative 20) + regional effects** |

## Packs

- **The New Ragnarok Reborn — NPCs** (Actor pack, player-observable) — the five creatures.
- **The New Ragnarok Reborn — GM Guides** (Journal pack) — four entries:
  *Umbrathor's Shadow Cavern — Scene Guide* (five-page core-Foundry arena build),
  *Vorath's Hellheim Throne Room — Scene Guide* (its infernal twin: braziers, chasm,
  hover-and-truesight interplay), *Umbrathor — Phase-by-Phase
  Encounter Runbook* (HP thresholds, summon timing,
  lair-action picker, legendary-action priorities), and *Vorath — Phase-by-Phase
  Encounter Runbook* (spell-slot decisions, Legendary Resistance doctrine, fear
  engine, throne room lair actions). Markdown twins of the scene guides live
  next to the module (`Shadow Cavern Scene Guide.md`,
  `Hellheim Throne Room Scene Guide.md`).
- **The New Ragnarok Reborn — Party Handouts** (Journal pack, **player-readable**) —
  *Treasures of the Shadow Tyrant*: read-aloud rumor hooks, in-world descriptions, and
  clean player rules for the **Cloak of Shadows** and **Amulet of the Night**, plus one
  GM-locked page (mechanics recap + campaign hooks). Safe to drag into chat; the GM
  page stays hidden.
- **The New Ragnarok Reborn — Treasures** (Item pack) — standalone, drag-ready magic
  items: **Cloak of Shadows** (rare, attunement — Stealth advantage in dim light or
  darkness) and **Amulet of the Night** (rare, attunement — +1d6 necrotic on melee and
  ranged spell attacks). Effects enable automatically while equipped & attuned; new-ID
  versions so importing them doesn't collide with the copies embedded on the Umbrathor
  actors.

## Changelog

### 1.2.0
- Added **Vorath's Hellheim Throne Room — Scene Guide** to the GM Guides pack: the
  infernal twin of the Shadow Cavern guide (braziers, throne glow, hellfire fissures,
  chasm-and-colonnade walls, hover/truesight interplay, Ember Storm & Throne of Chains
  props, death beat, difficulty dials). Markdown twin added at the campaign root.

### 1.1.0 — Bosses, lairs, guides & loot

**Actors & combat mechanics**
- Fixed all weapon/spell attack activities dealing **no damage** when rolled — printed
  dice and flat attack bonuses are now encoded: Ewoklin +7/2d6+4 & 2d8+4, Ewokling
  +5/1d6+2, Umbrathor CR 18 +12/8d8 & CR 13 +9/6d8, Vorath's Shadow Fork +10/4d8+4 and
  Necrotic Grasp +12/8d6.
- Fixed Dark Pact / Dark Rejuvenation heal activities (now roll 1d8+6, 1d6+5, 1d8, 1d6
  as printed); removed an un-expressible half-heal activity from Vorath's Shadow Fork.
- Added **Shadow Cavern lair actions (initiative 20)** to both Umbrathors: Shadow Flood,
  Shadow Tendrils (with Shadow-rise rider on CR 18), Creeping Chill, Lair Shadow Grasp
  (real restrained effect), Lair Shadow Step — DC 20 (CR 18) / DC 18 (CR 13).
- Added **Hellheim Throne Room lair actions** to Vorath: Hellfire Bolt (+12, 3d10, 6d10
  vs frightened), Gates of Dread (AoE fear), Ember Storm (catch-fire), Throne of Chains
  (restrained), Lair Shadow Step — all DC 20.
- Added passive **Regional Effects** traits for both lairs, and enabled the system's
  `Lair Action` resource (initiative 20) so **Inside Lair?** applies the official +1 CR /
  +1 legendary action adjustment.

**Compendium packs (4)**
- *NPCs* — five actors: Ewoklin (CR 8), Ewokling (CR 2, real summon target), Umbrathor
  CR 18 & CR 13, Vorath (CR 15) with real spells, zombie summon, and legendary actions.
- *GM Guides* (GM-only) — Shadow Cavern scene guide, Umbrathor & Vorath phase-by-phase
  encounter runbooks (openers, HP thresholds, summon timing, Legendary Resistance
  doctrine, lair-action pickers, cheat sheets).
- *Party Handouts* (player-readable) — *Treasures of the Shadow Tyrant*: rumor hooks,
  read-aloud flavor, and player rules for the two treasures, with one GM-locked page.
- *Treasures* (Items) — standalone drag-ready **Cloak of Shadows** and **Amulet of the
  Night** (new IDs, no collisions with the actor-embedded copies; effects enable
  automatically while equipped & attuned).

**Tooling**
- `build-pack.mjs` now compiles all four packs; sources carry the `_key` fields the
  official compiler requires while root-level loose JSONs stay key-free for drag-and-drop.

### 1.0.2
- Added standalone **Treasures** Item pack: drag-ready Cloak of Shadows and Amulet of
  the Night (new IDs, equipped-activation effects, owner's-mark flavor from the handout).

### 1.0.1
- Fixed all weapon/spell attack activities dealing **no damage** when rolled (damage parts
  were empty; printed dice and flat attack bonuses now encoded: Ewoklin +7/2d6+4 & 2d8+4,
  Ewokling +5/1d6+2, Umbrathor CR 18 +12/8d8 & CR 13 +9/6d8, Vorath's Shadow Fork +10/4d8+4
  and Necrotic Grasp +12/8d6).
- Fixed Dark Pact / Dark Rejuvenation heal activities (now roll 1d8+6 / 1d8 etc. properly).
- Removed an un-expressible half-heal activity from Vorath's Shadow Fork (rider remains in
  the description text).
- Added Umbrathor phase-by-phase encounter runbook to the GM Guides pack.
- Added Vorath phase-by-phase encounter runbook (spell-slot doctrine, Legendary
  Resistance usage, fear engine, throne room lair actions).
- Added player-readable **Party Handouts** pack: *Treasures of the Shadow Tyrant*
  (rumors, read-aloud flavor, and player rules for the Cloak of Shadows and Amulet
  of the Night, with one GM-locked mechanics page).

### 1.0.0
- Initial release: five NPC actors, lair actions + regional effects for both bosses,
  Shadow Cavern scene guide.

## Install

### Option A — Foundry installer (recommended)
In Foundry: **Game Settings → Add-on Modules → Install Module**, paste this manifest URL:

```
https://github.com/lisasdungeon/ragnarok-reborn-npcs/releases/latest/download/module.json
```

The **dnd5e system (6.0.x)** is required; Foundry will prompt if missing. Future releases
install through the same URL via **Update Available** in Manage Modules.

### Option B — Zip
1. Download `ragnarok-reborn-npcs.zip` from the
   [releases page](https://github.com/lisasdungeon/ragnarok-reborn-npcs/releases) and extract
   into your Foundry `Data/modules/` directory (Foundry Config → *Show Data Location*).
2. **Game Settings → Manage Modules → find "The New Ragnarok Reborn — NPCs" → Enable**.
3. Open the **Compendium Packs** sidebar → *The New Ragnarok Reborn* packs → drag any
   actor onto a scene or into the Actors directory.

### Option B — Manual (no module install)
The loose `Ewoklin.json`, `Umbrathor.json`, `Umbrathor lvl 8.json`, `Vorath lvl 10 New.json`
and `Ewokling.json` files in the parent directory can be dragged directly onto the
Actors sidebar of any dnd5e 6.0 world, as before.

## Notes

- The compendium version of **Ewoklin's Multiplicity** summons Ewoklings straight from the
  compendium (stable UUIDs), so it works even before you import the Ewokling into the world.
- Summoning a compendium actor copies it into the world automatically — nothing else to set up.
- The loose JSONs reference `Actor.EwoklingNPC00001` instead, so for the drag-and-drop route
  the Ewokling should exist in the world first (or re-link the summon after import).
- Save DCs and attack bonuses are flat values exactly as printed in the source statblocks;
  HP formulas, proficiencies, and senses are system-native.
- **Lair actions**: both Umbrathors ship with `Lair Actions (Shadow Cavern)` — five rollable
  lair actions grouped under the sheet's Lair Actions section (Shadow Flood, Shadow Tendrils,
  Creeping Chill, Lair Shadow Grasp with a real restrained effect, Lair Shadow Step). The
  `Lair Action` resource toggle is enabled with initiative 20; tick **Inside Lair?** on the
  NPC sheet while the fight is in the cavern to get the official +1 CR / +1 legendary action
  adjustment.
- **Regional effects**: a passive `Regional Effects (Shadow Cavern)` trait documents the
  cavern's environmental warping (magical darkness, fear whispers, umbral murk).
- **Vorath's Hellheim Throne Room** ships the same setup: four infernal lair actions
  (Hellfire Bolt +12/3d10 fire, Gates of Dread AoE fear, Ember Storm with catch-fire,
  Throne of Chains with a real restrained effect) plus a Lair Shadow Step, all DC 20,
  and a passive Regional Effects trait (smoldering air, watchful dread, burning whispers).
  His `Lair Action` resource toggle is likewise enabled at initiative 20.

## Rebuilding the pack

```
cd ragnarok-reborn-npcs
npm install            # not possible on exFAT drives — use a native-FS folder or /tmp
node build-pack.mjs    # compiles packs/_source/ragnarok-reborn-npcs → packs/ragnarok-reborn-npcs
```

The build uses the official `@foundryvtt/foundryvtt-cli` (`compilePack`, LevelDB format),
the same tool the dnd5e system itself uses. `build-pack.mjs` compiles all four packs from
`packs/_source/<pack-name>/`. Source documents carry explicit `_key` fields
(`!actors!ID`, `!actors.items!actorId.itemId`, `!actors.items.effects!actorId.itemId.effectId`)
as required by the compiler; the root-level loose JSONs are intentionally kept key-free so
they remain simple drag-and-drop imports.
