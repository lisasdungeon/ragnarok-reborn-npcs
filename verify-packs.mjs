// CI gate: proves the freshly compiled packs are healthy before a release ships.
// For each pack: the compile output exists, is a readable LevelDB store, and
// every document from the source JSONs survives the round-trip (matched by
// _id, _key ignored).
//
// Adventure packs are verified semantically: the compiled store legitimately
// holds one record per Adventure with the embedded collections inside it. For
// each source Adventure the gate asserts the round-tripped adventure doc
// embeds every source document — actors, scenes, items, journals — matched
// by _id and compared by canonical (key-sorted) JSON.
//
// The playtest-checklist journal carries a pinned structural assertion: the
// shipped journal must have exactly EXPECTED_PAGES pages and EXPECTED_ROWS
// activity rows. This is the last line of defense before a release — if a
// gen-playtest.py regression ever regenerates the journal wrong (rows dropped,
// pages lost, a broken merge), the release dies here instead of publishing.
// Intentionally duplicated from tools/gen-playtest.py's own coverage count:
// the two tools must agree, and a silent change to one is a FAIL in the other.
//
//   node verify-packs.mjs            → checks all six packs
//   node verify-packs.mjs <name>...  → checks only the listed packs
import { extractPack } from "@foundryvtt/foundryvtt-cli";
import fs from "node:fs";
import path from "node:path";

// --- pinned shape of the shipped playtest checklist -----------------------
const CHECKLIST_NAME_PREFIX = "10-Minute Playtest Checklist";
const EXPECTED_PAGES = 5;
const EXPECTED_ROWS = 48; // 11 Ewok + 14 Umbrathor + 23 Vorath (ledger excluded)

// --- pinned inventory of the shipped demo adventure -----------------------
// The demo's whole point is "everything bundled", so a consistent-but-incomplete
// bundle is a regression too — pin the per-collection counts here (mirrors
// tools/gen-adventure.py's source lists).
const DEMO_INVENTORY = { actors: 5, scenes: 2, items: 2, journal: 7 };

const packs = process.argv.slice(2).length
  ? process.argv.slice(2)
  : [
      "ragnarok-reborn-npcs",
      "ragnarok-reborn-gm-guides",
      "ragnarok-reborn-handouts",
      "ragnarok-reborn-loot",
      "ragnarok-reborn-scenes",
      "ragnarok-reborn-demo",
    ];

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

let failures = 0;

for (const name of packs) {
  const srcDir = path.join("packs", "_source", name);
  const packDir = path.join("packs", name);
  const tmpDir = path.join(".verify-tmp", name);

  try {
    if (!fs.existsSync(packDir)) {
      throw new Error(`compiled pack missing: ${packDir}`);
    }

    // Source of truth: every document _id in the source JSONs (recursive —
    // adventure packs keep one file per document in subdirectories).
    const expected = new Map();
    const readSources = (dir) => {
      for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        const p = path.join(dir, entry.name);
        if (entry.isDirectory()) readSources(p);
        else if (entry.name.endsWith(".json")) {
          const raw = JSON.parse(fs.readFileSync(p, "utf8"));
          const docs = Array.isArray(raw) ? raw : [raw];
          for (const doc of docs) {
            if (!doc._id) throw new Error(`${p}: document has no _id`);
            if (expected.has(doc._id)) throw new Error(`duplicate _id ${doc._id} across sources`);
            expected.set(doc._id, doc);
          }
        }
      }
    };
    readSources(srcDir);

    // Round-trip the compiled LevelDB pack back to JSON via the official CLI.
    fs.rmSync(tmpDir, { recursive: true, force: true });
    await extractPack(packDir, tmpDir, { log: false });

    const found = new Map();
    const walk = (dir) => {
      for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        const p = path.join(dir, entry.name);
        if (entry.isDirectory()) walk(p);
        else if (entry.name.endsWith(".json")) {
          const doc = JSON.parse(fs.readFileSync(p, "utf8"));
          if (doc._id) found.set(doc._id, doc);
        }
      }
    };
    walk(tmpDir);

    if (name === "ragnarok-reborn-demo") {
      // Adventure pack: one record per adventure, collections embedded inside.
      // Assert every non-adventure source doc is embedded, matched by _id and
      // compared by canonical JSON (the round-tripped adventure is re-serialized
      // by Foundry, so only semantic identity counts).
      const isAdventure = (doc) =>
        (doc._key ?? "").startsWith("!adventures");
      const advSourceIds = [...expected.values()]
        .filter(isAdventure)
        .map((d) => d._id);
      const embedded = new Map();
      let adventures = 0;
      for (const adv of [...found.values()]) {
        const colls = ["actors", "scenes", "items", "journal"];
        if (!colls.every((k) => Array.isArray(adv[k]))) continue;
        adventures++;
        for (const coll of colls) {
          for (const doc of adv[coll]) {
            if (doc?._id) embedded.set(doc._id, doc);
          }
        }
      }
      if (adventures < 1) {
        throw new Error("no adventure record with embedded collections in the compiled pack");
      }
      // pinned inventory: every collection must bundle exactly the pinned count
      const counts = {};
      for (const adv of [...found.values()]) {
        const colls = ["actors", "scenes", "items", "journal"];
        if (!colls.every((k) => Array.isArray(adv[k]))) continue;
        for (const coll of colls) {
          counts[coll] = (counts[coll] ?? 0) + adv[coll].length;
        }
      }
      for (const [coll, want] of Object.entries(DEMO_INVENTORY)) {
        if ((counts[coll] ?? 0) !== want) {
          throw new Error(
            `demo inventory changed: ${counts[coll] ?? 0} ${coll} embedded ` +
            `(expected ${want}). If this is intentional, update DEMO_INVENTORY in ` +
            `verify-packs.mjs together with tools/gen-adventure.py.`);
        }
      }
      const toCheck = [...expected.keys()].filter((id) => !advSourceIds.includes(id));
      const missing = toCheck.filter((id) => !embedded.has(id));
      if (missing.length) {
        throw new Error(`adventure does not embed: ${missing.join(", ")}`);
      }
      const drifted = toCheck.filter(
        (id) =>
          JSON.stringify(canon(embedded.get(id))) !==
          JSON.stringify(canon(expected.get(id))),
      );
      if (drifted.length) {
        throw new Error(
          `embedded doc(s) differ from source after round-trip: ${drifted.join(", ")}`);
      }
      console.log(
        `OK  ${name}: adventure embeds ${embedded.size}/${toCheck.length} source documents`,
      );
      continue;
    }

    const missing = [...expected.keys()].filter((id) => !found.has(id));
    if (missing.length) {
      throw new Error(`documents missing from compiled pack: ${missing.join(", ")}`);
    }

    let extra = "";
    if (name === "ragnarok-reborn-gm-guides") {
      const journal = [...found.values()]
        .find((d) => (d.name || "").startsWith(CHECKLIST_NAME_PREFIX));
      if (!journal) {
        throw new Error(`pinned-shape check: no journal named '${CHECKLIST_NAME_PREFIX}…' in the compiled pack`);
      }
      const pages = journal.pages ?? [];
      let rows = 0;
      for (const p of pages) {
        const c = p?.text?.content ?? "";
        rows += (c.match(/<tr>/g) ?? []).length - (c.match(/<tr><th/g) ?? []).length;
      }
      const ledger = pages.find((p) => (p.name || "").startsWith("Ledger"));
      const ledgerRows = ledger
        ? ((ledger.text?.content ?? "").match(/<tr>/g) ?? []).length -
          ((ledger.text?.content ?? "").match(/<tr><th/g) ?? []).length
        : 0;
      const activityRows = rows - ledgerRows;
      if (pages.length !== EXPECTED_PAGES || activityRows !== EXPECTED_ROWS) {
        throw new Error(
          `pinned shape changed: ${pages.length} pages / ${activityRows} activity rows ` +
          `(expected ${EXPECTED_PAGES} / ${EXPECTED_ROWS}). If this is intentional, update ` +
          `EXPECTED_PAGES/EXPECTED_ROWS in verify-packs.mjs together with ` +
          `tools/gen-playtest.py.`);
      }
      extra = `; pinned shape: ${pages.length} pages / ${activityRows} activity rows`;
    }

    console.log(`OK  ${name}: ${found.size}/${expected.size} documents round-tripped${extra}`);
  } catch (err) {
    failures++;
    console.error(`FAIL ${name}: ${err.message}`);
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
}

fs.rmSync(".verify-tmp", { recursive: true, force: true });

if (failures) {
  console.error(`\n${failures} pack(s) failed verification`);
  process.exit(1);
}
console.log("\nAll packs verified");
