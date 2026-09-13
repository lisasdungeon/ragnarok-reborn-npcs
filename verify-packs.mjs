// CI gate: proves the freshly compiled packs are healthy before a release ships.
// For each pack: the compile output exists, is a readable LevelDB store, and
// contains every document from the source JSONs (matched by _id, _key ignored).
//
// The playtest-checklist journal carries a pinned structural assertion: the
// shipped journal must have exactly EXPECTED_PAGES pages and EXPECTED_ROWS
// activity rows. This is the last line of defense before a release — if a
// gen-playtest.py regression ever regenerates the journal wrong (rows dropped,
// pages lost, a broken merge), the release dies here instead of publishing.
// Intentionally duplicated from tools/gen-playtest.py's own coverage count:
// the two tools must agree, and a silent change to one is a FAIL in the other.
//
//   node verify-packs.mjs            → checks all five packs
//   node verify-packs.mjs <name>...  → checks only the listed packs
import { extractPack } from "@foundryvtt/foundryvtt-cli";
import fs from "node:fs";
import path from "node:path";

// --- pinned shape of the shipped playtest checklist -----------------------
const CHECKLIST_NAME_PREFIX = "10-Minute Playtest Checklist";
const EXPECTED_PAGES = 5;
const EXPECTED_ROWS = 48; // 11 Ewok + 14 Umbrathor + 23 Vorath (ledger excluded)

const packs = process.argv.slice(2).length
  ? process.argv.slice(2)
  : [
      "ragnarok-reborn-npcs",
      "ragnarok-reborn-gm-guides",
      "ragnarok-reborn-handouts",
      "ragnarok-reborn-loot",
      "ragnarok-reborn-scenes",
    ];

let failures = 0;

for (const name of packs) {
  const srcDir = path.join("packs", "_source", name);
  const packDir = path.join("packs", name);
  const tmpDir = path.join(".verify-tmp", name);

  try {
    if (!fs.existsSync(packDir)) {
      throw new Error(`compiled pack missing: ${packDir}`);
    }

    // Source of truth: every document _id in the source JSONs.
    const expected = new Map();
    for (const file of fs.readdirSync(srcDir)) {
      if (!file.endsWith(".json")) continue;
      const raw = JSON.parse(fs.readFileSync(path.join(srcDir, file), "utf8"));
      const docs = Array.isArray(raw) ? raw : [raw];
      for (const doc of docs) {
        if (!doc._id) throw new Error(`${file}: document has no _id`);
        if (expected.has(doc._id)) throw new Error(`duplicate _id ${doc._id} across sources`);
        expected.set(doc._id, doc);
      }
    }

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
