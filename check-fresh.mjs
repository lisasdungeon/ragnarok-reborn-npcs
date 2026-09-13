// Freshness gate: proves the *committed* compiled packs match what the
// committed sources actually build to.
//
// Used by the pull-request workflow in two invocations:
//
//   node check-fresh.mjs snapshot [--allow-dirty]
//                                   → copy packs/<name> aside (.pack-snapshot/).
//                                     Default source is GIT HEAD (what CI would
//                                     check out); --allow-dirty snapshots the
//                                     working tree instead (dev rebuilds).
//   ... npm run build overwrites packs/<name> from packs/_source ...
//   node check-fresh.mjs            → extract both and compare document sets
//
// Mismatch means the PR changed pack sources without recompiling, or
// hand-edited compiled LevelDB output. Either way: run `npm run build` and
// commit the regenerated packs.
//
// LevelDB bytes are NOT deterministic across builds (file numbering, LOG
// timestamps), so comparison is semantic: every document extracted from both
// sides must have an identical canonical form (recursively key-sorted JSON),
// matched by _id.
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const packs = [
  "ragnarok-reborn-npcs",
  "ragnarok-reborn-gm-guides",
  "ragnarok-reborn-handouts",
  "ragnarok-reborn-loot",
  "ragnarok-reborn-scenes",
];

const SNAP = ".pack-snapshot";

// Recursively sort object keys so JSON comparison ignores key order.
const canon = (v) => {
  if (Array.isArray(v)) return v.map(canon);
  if (v && typeof v === "object") {
    return Object.fromEntries(
      Object.entries(v)
        .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
        .map(([k, val]) => [k, canon(val)]),
    );
  }
  return v;
};

// Walk a directory of extracted pack JSON, collecting docs by _id.
function collect(dir, into) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, entry.name);
    if (entry.isDirectory()) collect(p, into);
    else if (entry.name.endsWith(".json")) {
      const doc = JSON.parse(fs.readFileSync(p, "utf8"));
      if (doc._id) into.set(doc._id, JSON.stringify(canon(doc)));
    }
  }
  return into;
}

async function extract(packDir, outDir) {
  fs.rmSync(outDir, { recursive: true, force: true });
  await extractPack(packDir, outDir, { log: false });
  const docs = collect(outDir, new Map());
  fs.rmSync(outDir, { recursive: true, force: true });
  return docs;
}

// ---------------------------------------------------------------- snapshot
if (process.argv[2] === "snapshot") {
  const allowDirty = process.argv.includes("--allow-dirty");
  const status = execFileSync("git", ["status", "--porcelain", "--", "packs", "packs/_source"], {
    encoding: "utf8",
  });
  const dirty = status.split("\n").filter((l) => l.trim());
  if (dirty.length && !allowDirty) {
    console.error(
      "packs/ or packs/_source/ has uncommitted changes; CI checks committed " +
        "state. Commit (or revert) first, or pass --allow-dirty to snapshot the " +
        "working tree.",
    );
    process.exit(1);
  }
  fs.rmSync(SNAP, { recursive: true, force: true });
  fs.mkdirSync(SNAP);
  let source = "git HEAD";
  if (dirty.length || !fs.existsSync(".git")) {
    // Working-tree snapshot (explicit --allow-dirty, or no git repo).
    source = "working tree";
    for (const name of packs) {
      fs.cpSync(path.join("packs", name), path.join(SNAP, name), { recursive: true });
    }
  } else {
    // Default: archive the committed packs so a dev with local rebuilds gets
    // the same verdict CI would give a clean checkout. git archive entries
    // are prefixed `packs/<name>/`, so strip those two components on extract.
    for (const name of packs) {
      const tarball = execFileSync("git", ["archive", "HEAD", "--", path.join("packs", name)], {
        maxBuffer: 1024 * 1024 * 64,
      });
      fs.mkdirSync(path.join(SNAP, name), { recursive: true });
      execFileSync("tar", ["-x", "--strip-components=2", "-C", path.join(SNAP, name)], {
        input: tarball,
      });
    }
  }
  console.log(`Snapshot: ${packs.length} committed packs copied to ${SNAP}/ (from ${source})`);
  process.exit(0);
}

// ----------------------------------------------------------------- compare
// The CLI is imported lazily: the snapshot mode above needs only node
// builtins (fs/git/tar), so it can run where the CLI isn't installed.
const { extractPack } = await import("@foundryvtt/foundryvtt-cli");

let failures = 0;
for (const name of packs) {
  const snapDir = path.join(SNAP, name);
  const packDir = path.join("packs", name);
  try {
    if (!fs.existsSync(snapDir)) throw new Error("no snapshot taken (run `node check-fresh.mjs snapshot` first)");
    if (!fs.existsSync(packDir)) throw new Error(`freshly built pack missing: ${packDir}`);

    const committed = await extract(snapDir, path.join(SNAP, `_extract-${name}`));
    const fresh = await extract(packDir, path.join(SNAP, `_extract-fresh-${name}`));

    const missing = [...committed.keys()].filter((id) => !fresh.has(id));
    const extra = [...fresh.keys()].filter((id) => !committed.has(id));
    const changed = [...committed.keys()].filter((id) => fresh.has(id) && fresh.get(id) !== committed.get(id));

    if (missing.length || extra.length || changed.length) {
      const brief = (ids) => ids.slice(0, 4).join(", ") + (ids.length > 4 ? ` (+${ids.length - 4} more)` : "");
      const parts = [];
      if (changed.length) parts.push(`changed: ${brief(changed)}`);
      if (missing.length) parts.push(`missing from fresh build: ${brief(missing)}`);
      if (extra.length) parts.push(`not in committed pack: ${brief(extra)}`);
      throw new Error(`compiled pack is stale (${parts.join("; ")}) — run \`npm run build\` and commit packs/${name}`);
    }
    console.log(`OK  ${name}: committed packs match sources (${committed.size} documents)`);
  } catch (err) {
    failures++;
    console.error(`FAIL ${name}: ${err.message}`);
  }
}

fs.rmSync(SNAP, { recursive: true, force: true });

if (failures) {
  console.error(`\n${failures} pack(s) out of sync with sources`);
  process.exit(1);
}
console.log("\nAll committed packs are fresh");
