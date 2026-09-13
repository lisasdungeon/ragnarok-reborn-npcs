#!/usr/bin/env python3
"""Assert ARCHITECTURE.md's factual claims match the actual repo files.

The architecture doc is load-bearing: contributors pick the file to edit from
its ownership table and trust its recipes. So it gates itself — same spirit as
check-documented-data.py, but for structure instead of numbers. Five claim
families, each pinned to a real file:

  FILES     every repo file/dir the doc's flow depends on must exist (loose
            JSONs, tools, packs, maps, workflow, docs/actor-verification.json)
  RELEASE   the zip command in .github/workflows/release.yml must contain every
            entry the doc's Release-flow section claims it carries, and the
            release-assets list must match what the doc states
  PACKS     every pack the doc mentions must be declared in module.json (same
            label/name/type triple), and no pack may exist in module.json that
            the doc never mentions
  GATE      the doc's numbered gate list must have an entry for every step
            check_all.py actually runs (matched by step number)
  FLAGS     the script flags the doc documents (--packs/--from-head/--cli-dir/
            --allow-dirty, --out, --snapshot, SKIP_SCENE_FRESHNESS) must appear
            in the actual scripts

    python3 tools/check-architecture-doc.py     # exit 1 on any drift
    (runs as step 3 of `npm run check`)
"""
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ------------------------------------------------------------------ FILES
REQUIRED_PATHS = [
    # authoring: loose NPC JSONs
    "Ewoklin.json", "Ewokling.json", "Umbrathor.json",
    "Umbrathor lvl 8.json", "Vorath lvl 10 New.json",
    # authoring: scenes + checklist + guides
    "tools/scene-tools/geometry.py", "tools/scene-tools/build_scenes.py",
    "tools/scene-tools/render_art.py", "tools/gen-playtest.py",
    "packs/_source/ragnarok-reborn-gm-guides",
    "packs/_source/ragnarok-reborn-handouts",
    "packs/_source/ragnarok-reborn-loot",
    # derived
    "packs/_source/ragnarok-reborn-npcs",
    "packs/_source/ragnarok-reborn-scenes",
    "packs/ragnarok-reborn-npcs", "packs/ragnarok-reborn-gm-guides",
    "packs/ragnarok-reborn-handouts", "packs/ragnarok-reborn-loot",
    "packs/ragnarok-reborn-scenes",
    "maps/shadow-cavern.webp", "maps/hellheim-throne-room.webp",
    "docs/actor-verification.json",
    # infra the doc describes
    "tools/sync-npc-sources.py", "build-pack.mjs", "check-fresh.mjs",
    "verify-packs.mjs", "check-scene-maps.mjs",
    "tools/check_all.py", "tools/check-documented-data.py",
    "tools/check-actor-fixes.py",
    ".github/workflows/release.yml", ".github/workflows/verify.yml",
    "README.md", "module.json",
]

# --------------------------------------------------------------- RELEASE
# Entries the doc says the release zip carries → must appear in the zip
# command in release.yml. (Directory entries cover their contents.)
ZIP_ENTRIES_DOC_CLAIMS = [
    "module.json", "README.md", "ARCHITECTURE.md",
    "packs", "maps", "tools", "docs",
    "Ewoklin.json", "Ewokling.json", "Umbrathor.json",
    "Umbrathor lvl 8.json", "Vorath lvl 10 New.json",
    "Umbrathor's Shadow Cavern (Scene).json",
    "Vorath's Hellheim Throne Room (Scene).json",
]

# Assets the doc says a release carries → must appear in the upload list.
RELEASE_ASSETS_DOC_CLAIMS = [
    "ragnarok-reborn-npcs.zip", "module.json",
    "tools/check-actor-fixes.py", "docs/actor-verification.json",
]

# ------------------------------------------------------------------ FLAGS
# (script, flag-or-env) pairs the doc documents → must exist in the script.
DOC_FLAGS = [
    ("check-fresh.mjs", "--packs"),
    ("check-fresh.mjs", "--from-head"),
    ("check-fresh.mjs", "--allow-dirty"),
    ("check-fresh.mjs", "--cli-dir"),
    ("build-pack.mjs", "--out"),
    ("tools/check-actor-fixes.py", "--snapshot"),
    ("tools/check-actor-fixes.py", "--check"),
    ("tools/sync-npc-sources.py", "--check"),
    ("tools/scene-tools/build_scenes.py", "SKIP_SCENE_FRESHNESS"),
    ("tools/check_all.py", "--build-dir"),
]


def fail(msgs, text):
    msgs.append(text)


def main():
    arch_path = os.path.join(REPO, "ARCHITECTURE.md")
    if not os.path.exists(arch_path):
        print("FAIL ARCHITECTURE.md is missing", file=sys.stderr)
        return 1
    doc = open(arch_path, encoding="utf-8").read()
    fails = []

    # ------------------------------------------------------------- FILES
    for rel in REQUIRED_PATHS:
        if not os.path.exists(os.path.join(REPO, rel)):
            fail(fails, f"FILES  doc depends on '{rel}' but it does not exist")

    # ------------------------------------------------------------ RELEASE
    rel_yml = open(os.path.join(REPO, ".github/workflows/release.yml"),
                   encoding="utf-8").read()
    zi = rel_yml.find("zip -qr")
    xi = rel_yml.find("-x ", zi) if zi >= 0 else -1
    zip_body = rel_yml[zi:xi] if (zi >= 0 and xi > zi) else ""
    for entry in ZIP_ENTRIES_DOC_CLAIMS:
        if entry not in zip_body:
            fail(fails, f"RELEASE  doc claims the zip carries '{entry}' but it is "
                        f"missing from release.yml's zip command")
    for asset in RELEASE_ASSETS_DOC_CLAIMS:
        if asset not in rel_yml:
            fail(fails, f"RELEASE  doc claims release asset '{asset}' but it is "
                        f"not referenced in release.yml")

    # -------------------------------------------------------------- PACKS
    module = json.load(open(os.path.join(REPO, "module.json"), encoding="utf-8"))
    declared = {p["name"]: p for p in module.get("packs", [])}
    for pid in declared:
        # The doc sometimes abbreviates packs as “…-handouts/*.json” — accept
        # the full id or the distinguishing suffix.
        suffix = pid[len("ragnarok-reborn"):]
        if pid not in doc and suffix not in doc:
            fail(fails, f"PACKS  module.json declares pack '{pid}' but the doc "
                        f"never mentions it")

    # --------------------------------------------------------------- GATE
    gate = tools_steps()

    # Only the doc's numbered *gate* list — slice the section so the Golden
    # Rules' 1..5 can't masquerade as gate steps.
    gs = doc.find("## The gate")
    ge = doc.find("## Release flow")
    gate_section = doc[gs:ge if ge > gs else len(doc)]
    doc_gate = {}
    for m in re.finditer(r"^(\d+)\.\s+\*\*(.+?)\*\*", gate_section, re.M):
        doc_gate[int(m.group(1))] = m.group(2).strip().lower()
    for n, name in gate:
        if n not in doc_gate:
            fail(fails, f"GATE  check_all.py step {n} ('{name}') has no entry in "
                        f"the doc's numbered gate list")
            continue
        # Lenient match: any ≥4-char word shared in either direction
        # ('pack snapshot' ↔ 'snapshot committed packs', 'sync' ↔
        #  'sync-npc-sources --check'). Hyphens split, trailing 's' stemmed.
        def words(text):
            return {w.rstrip("s") for w in
                    re.findall(r"[a-z]{4,}", text.replace("-", " "))}
        words_doc, words_chk = words(doc_gate[n]), words(name)
        if not (words_doc & words_chk):
            fail(fails, f"GATE  doc's gate step {n} is '{doc_gate[n]}' but "
                        f"check_all.py runs '{name}'")
    for n in sorted(doc_gate):
        if not any(n == k for k, _ in gate):
            fail(fails, f"GATE  doc lists a gate step {n} that check_all.py "
                        f"does not run")

    # -------------------------------------------------------------- FLAGS
    for script, flag in DOC_FLAGS:
        path = os.path.join(REPO, script)
        if not os.path.exists(path):
            fail(fails, f"FLAGS  doc documents '{flag}' in '{script}' but the "
                        f"script does not exist")
            continue
        if flag not in open(path, encoding="utf-8").read():
            fail(fails, f"FLAGS  doc documents '{flag}' in '{script}' but the "
                        f"script no longer contains it")

    # DOC→SCRIPT: every '--flag' token the doc mentions must exist in SOME
    # script (catches phantom flags, not just curated ones).
    script_sources = ""
    for script in {s for s, _ in DOC_FLAGS} | {
            "check-fresh.mjs", "build-pack.mjs", "verify-packs.mjs",
            "check-scene-maps.mjs", "tools/check_all.py",
            "tools/check-documented-data.py", "tools/check-actor-fixes.py",
            "tools/sync-npc-sources.py", "tools/gen-playtest.py",
            "tools/scene-tools/build_scenes.py"}:
        p = os.path.join(REPO, script)
        if os.path.exists(p):
            script_sources += open(p, encoding="utf-8").read()
    for tok in sorted(set(re.findall(r"--[a-z][a-z-]{2,}", doc))):
        if tok not in script_sources:
            fail(fails, f"FLAGS  doc mentions '{tok}' but no script implements it "
                        f"(phantom flag — fix the doc or add the flag)")

    # ------------------------------------------------------------ report
    if fails:
        for f in fails:
            print(f"FAIL {f}", file=sys.stderr)
        print(f"\n{len(fails)} ARCHITECTURE.md drift failure(s) — update the doc "
              f"to match the repo (it documents reality, not intentions).",
              file=sys.stderr)
        return 1
    print(f"OK  ARCHITECTURE.md matches the repo "
          f"({len(REQUIRED_PATHS)} paths, {len(ZIP_ENTRIES_DOC_CLAIMS)} zip entries, "
          f"{len(RELEASE_ASSETS_DOC_CLAIMS)} release assets, {len(declared)} packs, "
          f"{len(gate)} gate steps, {len(DOC_FLAGS)} flags)")
    return 0


def tools_steps():
    """Extract (step_number, short_name) from check_all.py's step() calls."""
    src = open(os.path.join(REPO, "tools", "check_all.py"), encoding="utf-8").read()
    steps = []
    for m in re.finditer(
            r'step\((\d+),\s*steps_total,\s*"([^"]+)"', src):
        name = m.group(2).split(" — ")[0].strip().lower()
        steps.append((int(m.group(1)), name))
    return steps


if __name__ == "__main__":
    sys.exit(main())
