#!/usr/bin/env python3
"""npm run check — run the whole Verify-PR pipeline locally, mirroring CI exactly.

Steps (same order as .github/workflows/verify.yml, which now runs this script):
  1. sync-npc-sources.py --check     all seven drag-and-drop JSONs match the
                                     pack sources (actors: loose→pack, scenes: pack→loose)
  2. check-actor-fixes.py --check    verification snapshot matches the loose JSONs
  3. check-fresh.mjs snapshot        snapshot the packs from GIT HEAD (see note)
  4. build                           compile all packs from packs/_source
  5. verify-packs.mjs                every source document survives the LevelDB round-trip
  6. check-scene-maps.mjs            every scene's background.src exists
  7. check-fresh.mjs                 committed packs match what the sources build to

Normal mode (CI, or any machine where node_modules can live in the repo):
runs everything in place. The freshness snapshot is taken from GIT HEAD, not
the working tree, so the verdict matches what CI would see on a clean
checkout — packs/ and packs/_source/ must therefore be free of uncommitted
changes (use --allow-dirty to snapshot the working tree instead).

exFAT drives can't host node_modules. Point --build-dir at a native-FS
checkout (e.g. /tmp/fvtt-pack-build with `npm ci` done) and steps 3–5 and 7
run there: the repo's committed packs are snapshotted from git HEAD, the
repo's pack sources are copied over, and the freshness gate compares the
git-HEAD snapshot against a fresh compile — the same comparison CI makes.

    npm run check                          # full pipeline (CI + normal mode)
    npm run check -- --build-dir /tmp/fvtt-pack-build   # exFAT-safe mode
    npm run check -- --allow-dirty         # snapshot working-tree packs
"""
import os
import shutil
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)

GREEN, DIM, RED, RESET = "\033[32m", "\033[2m", "\033[31m", "\033[0m"
if os.environ.get("NO_COLOR") or not sys.stdout.isatty():
    GREEN = DIM = RED = RESET = ""

# Scripts that must exist in the build dir (resolved against the build dir's
# own node_modules, so they are copied there in --build-dir mode).
NODE_SCRIPTS = ["build-pack.mjs", "verify-packs.mjs", "check-fresh.mjs"]


def sh(cmd, cwd):
    """Run a CI-equivalent command, streaming output. Returns (ok, duration_s)."""
    t0 = time.time()
    proc = subprocess.run(cmd, shell=True, cwd=cwd)
    return proc.returncode == 0, time.time() - t0


def packs_dirty():
    out = subprocess.run(
        ["git", "status", "--porcelain", "--", "packs", "packs/_source"],
        capture_output=True, text=True, cwd=REPO,
    )
    return [l for l in out.stdout.splitlines() if l.strip()]


def prepare_build_dir(build_dir, allow_dirty):
    """Copy sources + node scripts + the git-HEAD pack snapshot into the build dir."""
    snap = os.path.join(REPO, ".pack-snapshot")
    if not os.path.isdir(snap):
        print("  FAIL  no .pack-snapshot found (snapshot step should have created it)")
        return False
    shutil.rmtree(os.path.join(build_dir, ".pack-snapshot"), ignore_errors=True)
    shutil.copytree(snap, os.path.join(build_dir, ".pack-snapshot"))
    shutil.rmtree(os.path.join(build_dir, "packs", "_source"), ignore_errors=True)
    shutil.copytree(os.path.join(REPO, "packs", "_source"),
                    os.path.join(build_dir, "packs", "_source"))
    for script in NODE_SCRIPTS:
        shutil.copy2(os.path.join(REPO, script), os.path.join(build_dir, script))
    shutil.rmtree(snap, ignore_errors=True)  # repo stays clean
    return True


def main():
    argv = sys.argv[1:]
    allow_dirty = "--allow-dirty" in argv
    build_dir = None
    if "--build-dir" in argv:
        build_dir = os.path.abspath(argv[argv.index("--build-dir") + 1])
        if not os.path.isdir(os.path.join(build_dir, "node_modules", "@foundryvtt")):
            print(f"FAIL  {build_dir} has no @foundryvtt CLI installed — run `npm ci` there first")
            return 2

    node_cwd = build_dir or REPO
    print("=" * 72)
    print("Check pipeline — mirrors .github/workflows/verify.yml"
          + (f"  (build dir: {build_dir})" if build_dir else ""))
    print("=" * 72)

    failures = []

    def step(i, total, name, blurb):
        print(f"\n{GREEN}[{i}/{total}]{RESET} {name} {DIM}— {blurb}{RESET}")

    steps_total = 7

    step(1, steps_total, "sync-npc-sources --check",
         "all seven drag-and-drop JSONs match the pack sources")
    ok, dt = sh("python3 tools/sync-npc-sources.py --check", REPO)
    print(f"  {GREEN if ok else RED}{'ok' if ok else 'FAILED'}{RESET} {DIM}({dt:.1f}s){RESET}")
    if not ok: failures.append("sync check")

    step(2, steps_total, "verification-snapshot parity",
         "published snapshot matches the loose JSONs")
    ok, dt = sh("python3 tools/check-actor-fixes.py --check", REPO)
    print(f"  {GREEN if ok else RED}{'ok' if ok else 'FAILED'}{RESET} {DIM}({dt:.1f}s){RESET}")
    if not ok: failures.append("verification snapshot")

    step(3, steps_total, "snapshot committed packs",
         "packs snapshot taken from git HEAD (what CI would check out)")
    dirty = packs_dirty()
    if dirty and not allow_dirty:
        print("  FAIL  packs/ has uncommitted changes — CI checks committed state,")
        print("        so commit (or revert) first, or rerun with --allow-dirty:")
        for line in dirty[:8]:
            print(f"    {line}")
        failures.append("snapshot")
    else:
        ok, dt = sh("node check-fresh.mjs snapshot" + (" --allow-dirty" if dirty else ""),
                    REPO)
        print(f"  {GREEN if ok else RED}{'ok' if ok else 'FAILED'}{RESET} {DIM}({dt:.1f}s){RESET}")
        if not ok:
            failures.append("snapshot")
        elif build_dir and not prepare_build_dir(build_dir, allow_dirty):
            failures.append("snapshot")

    step(4, steps_total, "build", "all five packs compile from packs/_source")
    ok, dt = sh("node build-pack.mjs" if build_dir else "npm run build", node_cwd)
    print(f"  {GREEN if ok else RED}{'ok' if ok else 'FAILED'}{RESET} {DIM}({dt:.1f}s){RESET}")
    if not ok: failures.append("build")

    step(5, steps_total, "verify-packs",
         "every source document survives the LevelDB round-trip")
    ok, dt = sh("node verify-packs.mjs", node_cwd)
    print(f"  {GREEN if ok else RED}{'ok' if ok else 'FAILED'}{RESET} {DIM}({dt:.1f}s){RESET}")
    if not ok: failures.append("round-trip verify")

    step(6, steps_total, "scene maps",
         "every scene's background.src exists in the repo")
    ok, dt = sh("node check-scene-maps.mjs", REPO)
    print(f"  {GREEN if ok else RED}{'ok' if ok else 'FAILED'}{RESET} {DIM}({dt:.1f}s){RESET}")
    if not ok: failures.append("scene maps")

    step(7, steps_total, "freshness",
         "committed packs match what the sources build to")
    ok, dt = sh("node check-fresh.mjs", node_cwd)
    print(f"  {GREEN if ok else RED}{'ok' if ok else 'FAILED'}{RESET} {DIM}({dt:.1f}s){RESET}")
    if not ok: failures.append("freshness")

    print("\n" + "=" * 72)
    if failures:
        print(f"{RED}FAILED ({len(failures)}/{steps_total} steps):{RESET} " + ", ".join(failures))
        return 1
    print(f"{GREEN}ALL {steps_total} STEPS PASSED{RESET} — exactly what CI runs on a PR")
    return 0


if __name__ == "__main__":
    sys.exit(main())
