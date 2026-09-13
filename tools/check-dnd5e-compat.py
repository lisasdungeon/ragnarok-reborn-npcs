#!/usr/bin/env python3
"""Nightly dependency-rot probe: does the module still tolerate upstream's latest?

The PR/release gates check the repo against ITSELF. This script checks the repo
against the WORLD — the two upstream dependencies that move without us:

  dnd5e   GitHub releases/latest → that release's system.json. Must satisfy
          module.json's `systems` entry:
            • latest >= systems.minimum        (module still installable)
            • latest's minor line <= systems.verified's minor line
              ("6.0" verifies the whole 6.0.* patch line)
            • latest <= systems.max, if declared
  CLI     `npm view @foundryvtt/foundryvtt-cli version` vs the package.json
          devDependency. A caret range auto-tolerates same-major updates;
          only a new MAJOR needs a human (re-test, bump, re-verify packs).

Every expectation is read from the repo files at runtime — nothing about the
dnd5e or CLI versions is hardcoded here, so updating module.json/package.json
is the whole fix when this fails.

Exit codes: 0 = fresh, 1 = rot found (or probe broke — that IS rot),
2 = usage error.

  python3 tools/check-dnd5e-compat.py            # probe both
  GITHUB_TOKEN=... python3 tools/check-dnd5e-compat.py   # raise API rate limit
"""
import json
import os
import re
import subprocess
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GITHUB_API = "https://api.github.com/repos/foundryvtt/dnd5e/releases/latest"


def fail(msg):
    print(f"ROT  {msg}")
    sys.exit(1)


def ok(msg):
    print(f"ok   {msg}")


def get_json(url, token=None):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except Exception as e:  # noqa: BLE001 — any network/shape failure is rot
        fail(f"could not probe {url}: {e}")


def pad3(v):
    """'6.0' -> (6, 0, 0); '6.0.1' -> (6, 0, 1). Non-numeric parts ignored."""
    nums = [int(n) for n in re.findall(r"\d+", str(v))]
    while len(nums) < 3:
        nums.append(0)
    return tuple(nums[:3])


def line(v):
    """The minor 'line' of a version: '6.0.1' and '6.0.7' are both line (6, 0).

    Foundry's `verified` convention ("6.0") stamps a whole patch line, so
    patch-level upstream releases are not drift; new minor lines are.
    """
    nums = [int(n) for n in re.findall(r"\d+", str(v))]
    return tuple(nums[:2])


def main():
    token = os.environ.get("GITHUB_TOKEN") or None
    module = json.load(open(os.path.join(REPO, "module.json")))

    # ------------------------------------------------------------- dnd5e ---
    # v11+ manifests nest the range under `compatibility`; older ones put
    # minimum/verified at the entry's top level. Accept both.
    entry = None
    for s in module.get("systems", []) or []:
        if s.get("id") == "dnd5e":
            entry = s.get("compatibility") or s
            break
    if not entry:
        fail("module.json has no systems entry with id 'dnd5e' — the check has nothing to assert")

    rel = get_json(GITHUB_API, token)
    tag = rel.get("tag_name")
    if not tag or "message" in rel and not tag:
        fail(f"GitHub API response shape changed (keys: {sorted(rel)[:6]})")
    sysjson = get_json(
        f"https://raw.githubusercontent.com/foundryvtt/dnd5e/{tag}/system.json", token
    )
    if sysjson.get("id") != "dnd5e":
        fail(f"system.json at {tag} has id {sysjson.get('id')!r} — repo restructured?")

    latest = sysjson.get("version")
    if not latest:
        fail(f"system.json at {tag} has no version field")
    print(f"upstream: dnd5e {latest} ({tag}, released {rel.get('published_at', '?')[:10]})")

    if pad3(latest) < pad3(entry.get("minimum", "0")):
        fail(
            f"dnd5e {latest} < systems.minimum {entry['minimum']} — the module can no "
            f"longer be installed alongside current dnd5e. Lower systems.minimum or "
            f"fix the incompatibility."
        )
    ok(f"latest dnd5e {latest} >= systems.minimum {entry.get('minimum')}")

    verified = entry.get("verified")
    if verified and line(latest) > line(verified):
        fail(
            f"dnd5e {latest} is a newer minor line than systems.verified {verified} — "
            f"re-test the module against it, then bump systems.verified in module.json."
        )
    ok(f"latest dnd5e line {line(latest)} within verified line {line(verified)} ({verified})")

    if entry.get("max") and pad3(latest) > pad3(entry["max"]):
        fail(f"dnd5e {latest} > systems.max {entry['max']} — incompatible with current dnd5e")

    # ---------------------------------------------------------------- CLI ---
    pkg = json.load(open(os.path.join(REPO, "package.json")))
    spec = pkg.get("devDependencies", {}).get("@foundryvtt/foundryvtt-cli")
    if not spec:
        fail("package.json has no @foundryvtt/foundryvtt-cli devDependency")
    nums = [int(n) for n in re.findall(r"\d+", spec)]  # "^3.0.4" -> [3, 0, 4]
    base = tuple((nums + [0, 0, 0])[:3])

    try:
        cli_latest = subprocess.run(
            ["npm", "view", "@foundryvtt/foundryvtt-cli", "version"],
            capture_output=True, text=True, timeout=60, check=True,
        ).stdout.strip()
    except Exception as e:  # noqa: BLE001
        fail(f"npm view @foundryvtt/foundryvtt-cli failed: {e}")
    print(f"upstream: foundryvtt-cli {cli_latest} (package.json pins {spec})")

    if pad3(cli_latest)[0] > base[0]:
        fail(
            f"@foundryvtt/foundryvtt-cli {cli_latest} is a new MAJOR (package.json pins "
            f"{spec}) — re-verify the packs with it, then bump the devDependency."
        )
    ok(f"latest CLI {cli_latest} within the {spec} caret range")

    print("\nAll upstream dependencies still inside their declared ranges.")


if __name__ == "__main__":
    main()
