// CI gate: proves the freshly compiled packs are healthy before a release ships.
// For each pack: the compile output exists, is a readable LevelDB store, and
// contains every document from the source JSONs (matched by _id, _key ignored).
//
//   node verify-packs.mjs            → checks all four packs
//   node verify-packs.mjs <name>...  → checks only the listed packs
import { extractPack } from "@foundryvtt/foundryvtt-cli";
import fs from "node:fs";
import path from "node:path";

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

    console.log(`OK  ${name}: ${found.size}/${expected.size} documents round-tripped`);
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
