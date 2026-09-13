// Freshness gate: proves the *committed* compiled packs match what the
// committed sources actually build to.
//
// Used by the pull-request workflow in three invocations:
//
//   node check-fresh.mjs snapshot [--allow-dirty]
//                                   → copy packs/<name> aside (.pack-snapshot/).
//                                     Default source is GIT HEAD (what CI would
//                                     check out); --allow-dirty snapshots the
//                                     working tree instead (dev rebuilds).
//   ... npm run build overwrites packs/<name> from packs/_source ...
//   node check-fresh.mjs            → extract both and compare document sets
//
//   node check-fresh.mjs --packs ragnarok-reborn-scenes --from-head [--fresh-dir <DIR>]
//                                   → self-contained single-shot mode for the
//                                     scene-tools build hook: snapshot just the
//                                     listed packs from GIT HEAD (no dirty-tree
//                                     refusal — the point is to compare committed
//                                     scenes against the just-built working tree),
//                                     freshly compile their sources, compare, and
//                                     exit 1 with a `npm run build` reminder on
//                                     mismatch. --fresh-dir keeps the fresh compile
//                                     under a known path (default: a temp dir
//                                     removed afterwards).
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
import os from "node:os";
import path from "node:path";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

const packs = [
  "ragnarok-reborn-npcs",
  "ragnarok-reborn-gm-guides",
  "ragnarok-reborn-handouts",
  "ragnarok-reborn-loot",
  "ragnarok-reborn-scenes",
  "ragnarok-reborn-demo",
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
  if (!extractPack) throw new Error("@foundryvtt/foundryvtt-cli not loaded (lazy import failed)");
  fs.rmSync(outDir, { recursive: true, force: true });
  await extractPack(packDir, outDir, { log: false });
  const docs = collect(outDir, new Map());
  fs.rmSync(outDir, { recursive: true, force: true });
  return docs;
}

// ---------------------------------------------------------------- options
// Parse the single-shot options before the snapshot branch; the compare mode
// ignores them.
const allPacks = [...packs];
const optPacks = [];
for (let i = 2; i < process.argv.length; i++) {
  if (process.argv[i] === "--packs") {
    for (const p of process.argv[++i].split(",")) {
      if (!allPacks.includes(p)) {
        console.error(`unknown pack: ${p} (known: ${allPacks.join(", ")})`);
        process.exit(2);
      }
      optPacks.push(p);
    }
  }
}
if (optPacks.length) packs.length = 0, packs.push(...optPacks);
const FRESH_DIR =
  process.argv.includes("--fresh-dir")
    ? path.resolve(process.argv[process.argv.indexOf("--fresh-dir") + 1])
    : null;
const FROM_HEAD = process.argv.includes("--from-head");
const SINGLE_SHOT = optPacks.length > 0 && FROM_HEAD;

// Where to resolve @foundryvtt/foundryvtt-cli from: the repo's own
// node_modules (native-FS checkout / CI) if present, else --cli-dir / the
// FVTT_CLI_DIR env var (exFAT checkouts can't host node_modules — point this
// at a native-FS checkout with `npm ci` done, e.g. /tmp/fvtt-pack-build).
const CLI_DIR = process.argv.includes("--cli-dir")
  ? path.resolve(process.argv[process.argv.indexOf("--cli-dir") + 1])
  : process.env.FVTT_CLI_DIR || null;

function resolveCliEntry() {
  const bases = [path.join(process.cwd(), "node_modules")];
  if (CLI_DIR) bases.push(path.join(CLI_DIR, "node_modules"));
  for (const nm of bases) {
    if (fs.existsSync(path.join(nm, "@foundryvtt", "foundryvtt-cli"))) {
      return createRequire(path.join(nm, "noop.js")).resolve("@foundryvtt/foundryvtt-cli");
    }
  }
  return null;
}
function cliMissing() {
  console.error(
    "@foundryvtt/foundryvtt-cli not found — install it in the repo (npm ci) or " +
      "pass --cli-dir <dir> / set FVTT_CLI_DIR to a checkout that has it",
  );
  process.exit(2);
}

// The CLI is loaded lazily (assigned to this binding): the snapshot mode
// needs only node builtins, so it can run where the CLI isn't installed.
let extractPack = null;

async function loadCli() {
  const entry = resolveCliEntry();
  if (!entry) cliMissing();
  ({ extractPack } = await import(pathToFileURL(entry)));
}

// ---------------------------------------------------------------- snapshot
if (process.argv[2] === "snapshot" || SINGLE_SHOT) {
  const allowDirty = process.argv.includes("--allow-dirty");
  const status = execFileSync("git", ["status", "--porcelain", "--", "packs", "packs/_source"], {
    encoding: "utf8",
  });
  const dirty = status.split("\n").filter((l) => l.trim());
  // --from-head (single-shot) EXPECTS a dirty tree — the whole point is
  // comparing the committed scenes against the just-rebuilt working tree.
  if (dirty.length && !allowDirty && !FROM_HEAD) {
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
  if (!FROM_HEAD && (dirty.length || !fs.existsSync(".git"))) {
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
  console.log(`Snapshot: ${packs.length} pack(s) copied to ${SNAP}/ (from ${source})`);

  if (!SINGLE_SHOT) process.exit(0);  // classic snapshot mode ends here
}

// ------------------------------------------------- single-shot compare mode
// Used by the scene-tools build hook: freshly compile the listed packs to
// --fresh-dir and compare against the git-HEAD snapshot just taken, then
// clean up. Shares the canonical/collect/extract helpers with the two-step
// pipeline mode below.
if (SINGLE_SHOT) {
  const tmp = FRESH_DIR || fs.mkdtempSync(path.join(os.tmpdir(), "fresh-"));
  for (const name of packs) {
    if (!fs.existsSync(path.join("packs", "_source", name))) {
      console.error(`FAIL ${name}: no pack sources found (run from the module repo root)`);
      fs.rmSync(SNAP, { recursive: true, force: true });
      process.exit(2);
    }
  }
  // Compile the fresh pack in a CHILD process — an in-process compile while
  // we hold iterators over the same LevelDB store trips the CLI
  // ("Iterator is not open"). The child imports the CLI by resolved absolute
  // path, so this works both where the repo has node_modules and on exFAT
  // checkouts that borrow a --cli-dir install. build-pack.mjs --out does the
  // same thing for humans in native-FS repos.
  const entry = resolveCliEntry();
  if (!entry) {
    fs.rmSync(SNAP, { recursive: true, force: true });
    cliMissing();
  }
  const jobs = packs.map((name) => ({
    src: path.resolve("packs", "_source", name),
    dest: path.join(tmp, name),
  }));
  const launcher = path.join(tmp, "_compile.mjs");
  fs.writeFileSync(
    launcher,
    `import { compilePack } from ${JSON.stringify(pathToFileURL(entry).href)};\n` +
      `const jobs = ${JSON.stringify(jobs)};\n` +
      `for (const j of jobs) { await compilePack(j.src, j.dest, { log: true }); console.log("fresh compile:", j.dest); }\n`,
  );
  try {
    execFileSync(process.execPath, [launcher], { stdio: "inherit" });
  } catch {
    fs.rmSync(SNAP, { recursive: true, force: true });
    console.error("fresh compile failed — see output above");
    process.exit(2);
  }
  await loadCli();
  let ssFailures = 0;
  for (const name of packs) {
    try {
      if (!fs.existsSync(path.join(tmp, name))) {
        throw new Error(`fresh compile produced no output at ${path.join(tmp, name)}`);
      }
      const committed = await extract(path.join(SNAP, name), path.join(SNAP, `_extract-${name}`));
      const fresh = await extract(path.join(tmp, name), path.join(tmp, `_extract-${name}`));
      const missing = [...committed.keys()].filter((id) => !fresh.has(id));
      const extra = [...fresh.keys()].filter((id) => !committed.has(id));
      const changed = [...committed.keys()].filter((id) => fresh.has(id) && fresh.get(id) !== committed.get(id));
      if (missing.length || extra.length || changed.length) {
        const brief = (ids) => ids.slice(0, 4).join(", ") + (ids.length > 4 ? ` (+${ids.length - 4} more)` : "");
        const parts = [];
        if (changed.length) parts.push(`changed: ${brief(changed)}`);
        if (missing.length) parts.push(`missing from fresh build: ${brief(missing)}`);
        if (extra.length) parts.push(`not in committed pack: ${brief(extra)}`);
        throw new Error(`compiled scenes are STALE (${parts.join("; ")}) — run \`npm run build\` and commit packs/${name}`);
      }
      console.log(`OK  ${name}: committed pack is fresh (${committed.size} documents)`);
    } catch (err) {
      ssFailures++;
      console.error(`FAIL ${name}: ${err.message}`);
    }
  }
  if (!FRESH_DIR) fs.rmSync(tmp, { recursive: true, force: true });
  fs.rmSync(SNAP, { recursive: true, force: true });
  if (ssFailures) process.exit(1);
  process.exit(0);
}

// ----------------------------------------------------------------- compare
// The CLI import happened lazily above (or happens here for two-step mode).
if (!extractPack) await loadCli();

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
