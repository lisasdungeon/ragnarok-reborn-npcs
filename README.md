# The New Ragnarok Reborn — NPCs (Foundry VTT Module)

An installable Foundry VTT module containing five ready-to-play **dnd5e 6.0.x** NPC actors,
two **pre-built battlemap Scenes** (walls, lights, tokens — zero manual setup), GM guides,
party handouts and drag-ready loot, built for Foundry **v14** (minimum 14.367).

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
- **The New Ragnarok Reborn — Battlemaps** (Scene pack) — import-and-play maps for both
  boss arenas with every wall, door, light and token pre-placed:
  *Umbrathor's Shadow Cavern* (soul lights, braziers, stalagmite blockers, dais with
  stair entrance, locked entry door, darkness 0.98) and *Vorath's Hellheim Throne Room*
  (braziers, throne glow, hellfire fissure lights, hidden Ember Storm prop, colonnade
  cover, movement-blocked chasm with two bridges). Boss tokens link to the NPC-pack
  actors by ID and carry their signature lighting; map art ships in `maps/` as
  optimized WebP (70×40 grid).

## Changelog

### 1.3.2
- `tools/sync-npc-sources.py` now syncs **all seven** drag-and-drop JSONs from one
  place: the five NPC actors still flow loose → pack (authoring format), and the two
  loose Scene JSONs are now **generated** from the scene pack sources by stripping the
  compiler `_key` hierarchy — scenes are authored in `tools/scene-tools/` and only
  there. The sync check covers all seven files on every PR.
- **Fixed the remaining attack/DC encoding bugs found by the data audit** (all on Vorath):
  - *Hellfire Bolt* (lair action) used a non-flat `+12` bonus, which the system **stacks on
    top of** the computed roll modifier — roughly +21 to hit instead of the printed +12.
    Now flat +12, like every other attack in the module.
  - *Eldritch Blast* computed its attack roll from DEX (+9); the statblock says +12 with
    spell attacks. Now flat +12 (damage stays the RAW-correct 1d10, 2 beams at caster
    level 10).
  - *Cloudkill*'s ongoing save and *Dominate Person*'s save used the system's computed
    spell DC (19 on this actor) instead of the printed DC 20. Now flat DC 20, matching
    every other DC in the module and the README's flat-DC convention.
- **Verification data extended**: `docs/actor-verification.json` now covers these saves
  too (30 activity groups). If you imported Vorath before this release, re-import from
  the compendium (or drag `Vorath lvl 10 New.json` from the zip root) and confirm with
  `python3 tools/check-actor-fixes.py --verify <export>`.

### 1.3.1
- **Verify your imported bosses carry these fixes**: release page ships
  `tools/check-actor-fixes.py` + `docs/actor-verification.json` — export the actor from
  your world and run the script against the export (see *Notes* below for the one-liner).
- **Fixed a data regression in the compendium NPC pack**: the pack sources had drifted
  from the loose JSONs, so actors imported from the compendium since v1.1.0 shipped with
  the pre-1.0.1 bug again — empty attack bonuses, no damage dice on weapon/spell attacks,
  and legacy heal formulas. Synced from the loose files: Ewoklin +7 (2d6+4), Ewokling +5
  (1d6+2), Umbrathor +12 (8d8) / CR 13 +9 (6d8), Vorath Shadow Fork +10 (4d8+4) and
  Necrotic Grasp +12 (8d6), Dark Pact heals 1d8+6 / 1d6+5. Effects keep GM-locked
  ownership; Ewoklin's Multiplicity summons from the compendium (pack-only improvement,
  preserved).
- **Loose JSONs now live in the repo and in every release zip**: the five NPC actors and
  both scenes ship as drag-and-drop backups at the zip root.
- **CI drift guard**: a sync check (`tools/sync-npc-sources.py --check`) runs on every PR —
  the loose JSONs are the authoring format, and the pack sources are generated from them,
  so the two can never silently diverge again.

### 1.3.0
- **Pre-built battlemap Scenes**: the Shadow Cavern and Hellheim Throne Room now exist
  as importable Scene documents in a new *Battlemaps* pack — 134 + 79 walls including
  sight-passing dais/chasm/colonnade movement blockers, a locked entry door and two
  bridge gaps, animated soul lights / braziers / fissure flames, and boss tokens with
  signature lighting. Map art generated from the same geometry as the walls, shipped as
  optimized WebP in `maps/`.
- **Pull-request gate**: a second workflow (`Verify PR`) compiles every pack, round-trip
  verifies all documents, checks that scene map art exists, and fails any PR whose
  committed compiled packs don't match what the sources build to — broken or stale pack
  sources can no longer reach `master`.
- Dev tooling: `tools/scene-tools/` (map renderer + scene builder), `check-scene-maps.mjs`,
  `check-fresh.mjs` freshness gate, `npm run check:maps` / `npm run check:fresh`.

### 1.2.1
- **Automated releases**: a GitHub Actions workflow now recompiles all four packs from
  source, round-trip-verifies every document, and publishes the release automatically
  whenever `module.json`'s version is bumped. No local build needed — even on exFAT
  drives. Pack sources now live in the repo so CI can rebuild them.

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

Every release zip also carries the **loose drag-and-drop JSONs at its root** — a backup of
the five NPC actors (`Ewoklin.json`, `Ewokling.json`, `Umbrathor.json`, `Umbrathor lvl 8.json`,
`Vorath lvl 10 New.json`) and both battlemap scenes — importable by drag-and-drop without
touching any compendium.

### Manual (no module install)
The same loose JSONs live in the repo root (and in every release zip): drag
`Ewoklin.json`, `Ewokling.json`, `Umbrathor.json`, `Umbrathor lvl 8.json` or
`Vorath lvl 10 New.json` directly onto the Actors sidebar of any dnd5e 6.0 world, and the
two `*(Scene).json` files onto the Scenes sidebar.

## Notes

- The compendium version of **Ewoklin's Multiplicity** summons Ewoklings straight from the
  compendium (stable UUIDs), so it works even before you import the Ewokling into the world.
- Summoning a compendium actor copies it into the world automatically — nothing else to set up.
- The loose JSONs reference `Actor.EwoklingNPC00001` instead, so for the drag-and-drop route
  the Ewokling should exist in the world first (or re-link the summon after import).
- Save DCs and attack bonuses are flat values exactly as printed in the source statblocks;
  HP formulas, proficiencies, and senses are system-native.
- **Verify the 1.3.1 attack fixes on your imported actors**: if you imported the bosses
  before v1.3.1, your world copies may still have the pre-fix data (empty attack bonuses,
  no damage dice). Download `tools/check-actor-fixes.py` and
  `docs/actor-verification.json` from any release page (or find them in the release zip),
  export the actor from your world (*right-click actor → Export Data*), and run:

  ```
  python3 tools/check-actor-fixes.py --verify "Umbrathor.json"
  ```

  Every printed attack, save DC, and heal formula on all five actors is checked against
  the exact shipped data, world-only noise (HP, temp HP, positions) is ignored, and the
  exit code tells CI — or your shell — whether anything is off. Add `--standalone` to
  check exported Cloak of Shadows / Amulet of the Night items instead.
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

## Rebuilding the packs

```
cd ragnarok-reborn-npcs
npm install            # not possible on exFAT drives — use a native-FS folder or /tmp
npm run check          # THE pipeline: runs everything CI runs on a PR, in order
npm run build          # compiles all packs/_source/<pack-name> → packs/<pack-name>
npm run verify         # round-trips each compiled pack back to JSON and checks every document
npm run check:maps     # scenes must reference map art that exists in the repo
npm run check:fresh    # committed packs must match what the sources build to (run `npm run check:fresh:snapshot` first)
npm run sync:npcs      # sync all seven drag-and-drop JSONs with the pack sources:
                       #   NPC actors: loose JSONs (authoring format) → pack sources
                       #   Scenes:     pack sources (from tools/scene-tools) → loose JSONs
npm run sync:npcs:check  # fail if any of the seven have drifted
```

`npm run check` is the one-command gate — the same script (`tools/check_all.py`) that
the *Verify PR* workflow executes on GitHub, so local and CI results can't diverge.
It refuses to run on a tree with uncommitted `packs/` changes (CI checks committed
state; `--allow-dirty` overrides) and takes the freshness snapshot from **git HEAD**,
so a stale local rebuild can't produce a false pass. On exFAT drives (no
`node_modules` in the repo), point it at a native-FS build dir that has had `npm ci`:

```
npm run check -- --build-dir /tmp/fvtt-pack-build
```

**Editing an NPC?** Edit the loose JSON at the repo root, then run `npm run sync:npcs` and
rebuild — the pack sources are generated, never hand-edited. The sync re-adds the compiler
`_key` hierarchy, converts module-actor summon UUIDs to compendium form (so Multiplicity
works straight from the pack), and keeps effect ownership GM-locked.

**Editing a scene?** Scenes flow the other way: the pack sources in
`packs/_source/ragnarok-reborn-scenes/` are authoritative (generated by
`tools/scene-tools/` — map art and scene data share one geometry module), and
`npm run sync:npcs` regenerates the loose drag-and-drop Scene JSONs from them by
stripping the compiler `_key` fields. Never hand-edit the loose scene files.

The build uses the official `@foundryvtt/foundryvtt-cli` (`compilePack`, LevelDB format),
the same tool the dnd5e system itself uses. `build-pack.mjs` compiles all five packs from
`packs/_source/<pack-name>/`. The battlemap art is generated from
`tools/scene-tools/` (`python3 render_art.py && python3 build_scenes.py`), which also
emits the scene JSONs — walls and art share one geometry module so they always align. Source documents carry explicit `_key` fields
(`!actors!ID`, `!actors.items!actorId.itemId`, `!actors.items.effects!actorId.itemId.effectId`)
as required by the compiler; the root-level loose JSONs are intentionally kept key-free so
they remain simple drag-and-drop imports.

## Automated releases

Cutting a release is a one-commit affair:

1. Bump `version` in `module.json`.
2. Add a `### X.Y.Z` section under **Changelog** in this README.
3. Commit to `master` with the message `Bump version to X.Y.Z` and push.

GitHub Actions then recompiles all packs from source, round-trip-verifies them, builds the
zip, tags `vX.Y.Z`, and publishes the release — the stable installer URLs
(`releases/latest/download/...`) pick it up automatically. The workflow lives at
`.github/workflows/release.yml`; "Run workflow" in the Actions tab can also build any
branch on demand (as a draft release).

If your drive is exFAT, don't install dependencies locally — just push the bump and let CI
drive (or work in a `/tmp` checkout like the manual instructions above).

## Pull-request gate

Every PR targeting `master` runs `npm run check` (`.github/workflows/verify.yml` just
invokes `tools/check_all.py`): sync parity for all seven drag-and-drop JSONs,
verification-snapshot parity, compile all packs, round-trip verify every document,
check scene map references, and confirm the **committed** compiled packs match a fresh
rebuild of the sources (snapshot taken from git HEAD — the same comparison a clean
checkout would make). A PR that edits `packs/_source/` without recommitting regenerated
`packs/` output fails with the exact pack and document that went stale — merge is
blocked until it's rebuilt. Because CI calls the same script you run locally, "green
locally but red on CI" can't happen from step drift.
