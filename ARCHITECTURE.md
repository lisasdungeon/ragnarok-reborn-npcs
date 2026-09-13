# Architecture — where data lives and how it flows

Every document this module ships exists in **three representations**: an
*authoring* file a human edits, a *pack source* the compiler consumes, and the
*compiled LevelDB pack* Foundry installs. On top of that, the seven
drag-and-drop JSONs are duplicated at the repo root for import-without-compendium
convenience, and the release zip carries everything a fourth time. This note
exists so nobody has to guess which copy is authoritative and which tool
regenerates which file.

**The one rule: never hand-edit a generated file.** Each file below lists its
single writer. If a check fails, fix the *upstream* file and re-run the tool —
don't patch the downstream copy.

```
                       ┌──────────────────────────────────────────────┐
                       │  AUTHORING (humans edit only these)          │
                       │                                              │
   NPC actors          │  Ewoklin.json … Vorath lvl 10 New.json       │
   (5 loose JSONs) ────┤  (repo root; world-style UUIDs, no _keys)    │
                       │                                              │
   Scenes              │  tools/scene-tools/build_scenes.py           │
                       │    + geometry.py (walls/lights/art share     │
                       │      one coordinate module)                  │
                       │                                              │
   Playtest checklist  │  tools/gen-playtest.py                       │
                       │    (actor JSONs + loot pack sources)         │
                       │                                              │
   GM guides,          │  packs/_source/ragnarok-reborn-gm-guides/    │
   handouts, loot      │  …-handouts/   (hand-edited JSONs)           │
                       └──────────────┬───────────────────────────────┘
                                      │
              tools/sync-npc-sources.py (the only bridge, both directions)
              • actors:   loose → pack   (adds _key hierarchy, compendium
              │            summon UUIDs, GM-locked effect ownership)
              • scenes:   pack  → loose  (strips _keys → drag-and-drop file)
              ▼
                       ┌──────────────────────────────────────────────┐
                       │  PACK SOURCES  packs/_source/<pack>/*.json   │
                       │  (compiler input; _keys, compendium UUIDs)   │
                       └──────────────┬───────────────────────────────┘
                                      │  npm run build   (build-pack.mjs,
                                      │  official @foundryvtt/foundryvtt-cli)
                                      ▼
                       ┌──────────────────────────────────────────────┐
                       │  COMPILED PACKS  packs/<pack>/  (LevelDB,    │
                       │  committed — what Foundry downloads)         │
                       └──────────────┬───────────────────────────────┘
                                      │  release.yml: zip + GitHub Release
                                      │  (stable manifest: /releases/latest/
                                      │   download/module.json)
                                      ▼
                       ┌──────────────────────────────────────────────┐
                       │  COMPENDIUM in Foundry  (5 packs declared in │
                       │  module.json) + 7 loose JSONs in the zip root│
                       └──────────────────────────────────────────────┘
```

Scene art rides a parallel rail out of the same geometry module:
`render_art.py` renders `tools/scene-tools/maps/*.png` (gitignored) →
`build_scenes.py` optimizes them to the **committed** `maps/*.webp` and writes
the scene pack sources whose `background.src` points at
`modules/ragnarok-reborn-npcs/maps/*.webp`. Art and walls align by
construction because both come from `geometry.py`.

## File ownership — who writes what

| File / path | Authoritative? | Written by | Notes |
|---|---|---|---|
| `Ewoklin.json`, `Ewokling.json`, `Umbrathor.json`, `Umbrathor lvl 8.json`, `Vorath lvl 10 New.json` | **YES** (actors) | humans | The authoring format. World-style summon UUIDs (`Actor.…`), no effect-ownership overrides. |
| `tools/scene-tools/*.py` | **YES** (scenes) | humans | `geometry.py` is the single source of coordinates; `build_scenes.py` writes pack sources + `maps/*.webp` and self-checks pack freshness; `render_art.py` only feeds build_scenes. |
| `tools/gen-playtest.py` | **YES** (checklist) | humans | Derives every checklist row from the loose actor JSONs (bonus/dice/DC/statuses from the data) and the Ledger's loot rows from the loot pack sources (effect changes → pass conditions, embedded-copy dice noted). Its OVERRIDES layer carries flavor wording only. |
| `packs/_source/ragnarok-reborn-gm-guides/*.json`, `…-handouts/*.json`, `…-loot/*.json` (except the checklist) | **YES** | humans | Hand-edited journal/item sources. |
| `packs/_source/ragnarok-reborn-npcs/*.json` | derived | `sync-npc-sources.py` | Loose JSONs + `_key` hierarchy + compendium summon UUIDs + GM-locked `ownership`. **Never edit directly.** |
| `packs/_source/ragnarok-reborn-scenes/*.json` | derived | `build_scenes.py` | Art and walls from one geometry module. **Never edit directly.** |
| `packs/_source/ragnarok-reborn-gm-guides/playtest-checklist.json` | derived | `gen-playtest.py` | **Never edit directly.** |
| `Umbrathor's Shadow Cavern (Scene).json`, `Vorath's Hellheim Throne Room (Scene).json` | derived | `sync-npc-sources.py` (pack → loose) | Byte-stable 2-space indent; safe to delete — the sync regenerates them. |
| `packs/<pack>/` (LevelDB) | derived | `build-pack.mjs` | Committed so Foundry can download it, but never edited by hand. |
| `maps/*.webp` | derived | `build_scenes.py` | |
| `docs/actor-verification.json` | derived | `check-actor-fixes.py --snapshot` | Reference data for the user-facing verifier; must match the loose JSONs (`--check` gate). |
| `README.md` | **YES** | humans | Doubles as the documentation contract: the documented-data gate asserts its numbers against the actors. |
| `module.json` | **YES** | humans | Version bump here is the release trigger. |

## Recipes — "I want to change…"

**…an NPC's stats, spells, or items** (loose → pack, three derived copies):
1. Edit the loose JSON at the repo root — it's the authoring format.
2. `npm run sync:npcs` → regenerates the pack source.
3. `npm run verify:snapshot` → refreshes `docs/actor-verification.json`.
4. If the value appears in the README or the playtest checklist, update there
   too (`npm run check:docs` will name any you miss — it checks README **and**
   the checklist against the actors in both directions).
5. Recompile: `npm run build` (or just open the PR — CI does it; see below).

**…a scene (walls, lights, tokens, art):**
1. Edit `tools/scene-tools/geometry.py` / `build_scenes.py` — never the JSONs.
2. `python3 tools/scene-tools/render_art.py` then
   `python3 tools/scene-tools/build_scenes.py` (writes pack sources + `maps/*.webp`).
   The script **self-checks scene freshness** before exiting: it recompiles the
   scenes pack into a scratch dir (`check-fresh.mjs --packs ragnarok-reborn-scenes
   --from-head`) and compares against the committed pack — a geometry change
   can't ship with stale compiled scenes, because the generator itself exits 1
   with a `npm run build` reminder. (`SKIP_SCENE_FRESHNESS=1` skips; on exFAT
   checkouts set `FVTT_CLI_DIR` to a native-FS install.)
3. `npm run sync:npcs` → refreshes the loose Scene JSONs from the pack sources.
4. Before opening the PR: the scene-maps gate verifies the art files, and the
   sync's `--check` guarantees loose and pack copies agree — though after step 2
   the freshness hook has already told you whether `packs/ragnarok-reborn-scenes`
   needs a recompile-and-commit.

**…a GM guide / handout:**
Edit the JSON in `packs/_source/<pack>/` directly, then recompile. If it quotes
actor numbers, `npm run check:docs` holds it honest too.

**…a loot item (Cloak/Amulet):**
Edit `packs/_source/ragnarok-reborn-loot/*.json` — the effect `changes` there
are the single source of truth. The checklist's Ledger rows derive from them
(rerun `gen-playtest.py`), and `npm run check:docs` asserts each effect die
against the README line naming the item and the item's own Ledger row.

**…the playtest checklist:** rows derive themselves — just rerun
`python3 tools/gen-playtest.py` after any actor or loot-item change and new
activities (and loot-effect values) appear automatically. Only edit the script
for flavor wording (OVERRIDES/PROSE) or page structure; the documented-data
gate still refuses values that don't exist in the sources.

## The gate — `npm run check` (CI runs the same script)

`tools/check_all.py` (called identically by `.github/workflows/verify.yml` —
the workflow is just `npm run check`, so local and CI cannot drift):

1. **sync** — all seven drag-and-drop JSONs match their counterparts (both directions).
2. **documented data** — README + playtest checklist ↔ loose JSONs, both
   directions, plus regression signatures (non-flat attacks, computed DCs,
   undice-encoded heals — the exact shapes of the 1.3.1 and 1.3.2 bugs).
3. **architecture doc** — this file's factual claims (file existence, zip list,
   pack declarations, gate steps, script flags) match the actual repo. The doc
   gates itself.
4. **verification snapshot** — `docs/actor-verification.json` matches the loose JSONs.
5. **pack snapshot** — from git HEAD (not the working tree, so a local rebuild can't fake a pass).
6. **build** — compile all five packs from sources.
7. **verify-packs** — every source document survives the LevelDB round-trip.
8. **scene maps** — every scene's `background.src` exists in `maps/`.
9. **freshness** — committed packs are exactly what the sources compile to.

`check-fresh.mjs` also has a self-contained single-shot mode
(`--packs <name> --from-head`, plus `--cli-dir`/`FVTT_CLI_DIR` for checkouts
without their own `node_modules`): snapshot the committed pack from git HEAD,
freshly compile the listed sources, compare, exit 1 on drift.
`tools/scene-tools/build_scenes.py` runs it automatically after every scene
build, so the freshness verdict reaches the scene author the moment they run
the generator — not at PR time. `build-pack.mjs` mirrors the same options
(`<name>…` filter, `--out <dir>`) so a human can do the identical compile.

On exFAT checkouts (no `node_modules` possible), use
`npm run check -- --build-dir /tmp/fvtt-pack-build` — see the `check_all.py`
docstring.

## Release flow

`.github/workflows/release.yml` fires when `module.json`'s version changes on
master: compile → verify → zip (module.json, README, **ARCHITECTURE.md**, packs,
maps, tools, docs, **plus the seven loose JSONs at the zip root**) → GitHub
Release with four assets (zip, manifest, `check-actor-fixes.py`,
`docs/actor-verification.json`).
Release notes are extracted from the README changelog section for that version.
The stable installer URL is
`https://github.com/lisasdungeon/ragnarok-reborn-npcs/releases/latest/download/module.json`.

## Golden rules

1. **One writer per file.** The table above is the contract.
2. **Authoring copies win.** Loose JSONs for actors, `tools/scene-tools/` for
   scenes, hand-edited sources for guides/handouts/loot.
3. **Run the sync after editing anything** — it's bidirectional, cheap, and
   `--check` is what CI enforces.
4. **Every player-visible number must appear in the README and on the
   playtest checklist**; the gate fails the PR otherwise. `TEXT_ONLY` /
   `CHECKLIST_OK` allowlists exist in `check-documented-data.py` for genuine
   description-only riders — every entry must carry a reason.
5. **A PR that only fixes the generated copy is wrong** — fix upstream, let
   the tools regenerate, commit everything together.
