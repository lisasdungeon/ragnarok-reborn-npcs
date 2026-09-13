// Compiles compendium pack sources into Foundry LevelDB packs
// using the official @foundryvtt/foundryvtt-cli (same tool the dnd5e system uses).
//
//   packs/_source/ragnarok-reborn-npcs      → packs/ragnarok-reborn-npcs       (Actor)
//   packs/_source/ragnarok-reborn-gm-guides → packs/ragnarok-reborn-gm-guides  (JournalEntry)
//   packs/_source/ragnarok-reborn-handouts  → packs/ragnarok-reborn-handouts   (JournalEntry)
//   packs/_source/ragnarok-reborn-loot      → packs/ragnarok-reborn-loot       (Item)
//   packs/_source/ragnarok-reborn-scenes    → packs/ragnarok-reborn-scenes     (Scene)
//   packs/_source/ragnarok-reborn-demo      → packs/ragnarok-reborn-demo       (Adventure)
//
// Usage:
//   node build-pack.mjs                    → compile all packs to packs/
//   node build-pack.mjs <name> [...]       → compile only the listed packs
//   node build-pack.mjs --out <DIR> [...]  → compile the listed (or all) packs to
//                                            <DIR>/<name> instead of packs/ —
//                                            used by check-fresh.mjs single-shot
//                                            mode and the scene-tools hook
import { compilePack } from "@foundryvtt/foundryvtt-cli";
import path from "node:path";

const packs = [
  "ragnarok-reborn-npcs",
  "ragnarok-reborn-gm-guides",
  "ragnarok-reborn-handouts",
  "ragnarok-reborn-loot",
  "ragnarok-reborn-scenes",
  "ragnarok-reborn-demo",
];

const args = process.argv.slice(2);
const outIdx = args.indexOf("--out");
const outBase = outIdx >= 0 ? path.resolve(args[outIdx + 1]) : null;
const selected = args.filter(
  (a, i) => a !== "--out" && (outIdx < 0 || i !== outIdx + 1),
);
const unknown = selected.filter((s) => !packs.includes(s));
if (unknown.length) {
  console.error(`unknown pack(s): ${unknown.join(", ")} (known: ${packs.join(", ")})`);
  process.exit(2);
}
const list = selected.length ? packs.filter((p) => selected.includes(p)) : packs;

for (const name of list) {
  const src = `packs/_source/${name}`;
  const dest = outBase ? path.join(outBase, name) : path.join("packs", name);
  await compilePack(src, dest, { log: true });
  console.log(`Pack compiled: ${dest}`);
}
