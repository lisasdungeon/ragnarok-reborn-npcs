// Scene source sanity check: every scene in packs/_source/ragnarok-reborn-scenes
// must reference map art that actually exists in the repo (maps/), so a scene
// can never be committed pointing at a missing/renamed image.
//
//   node check-scene-maps.mjs
import fs from "node:fs";
import path from "node:path";

const SCENES = path.join("packs", "_source", "ragnarok-reborn-scenes");

let failures = 0;
for (const file of fs.readdirSync(SCENES)) {
  if (!file.endsWith(".json")) continue;
  const scene = JSON.parse(fs.readFileSync(path.join(SCENES, file), "utf8"));
  const src = scene?.background?.src;
  const name = scene.name || file;
  try {
    if (typeof src !== "string" || !src) throw new Error("no background.src set");
    // This module's own assets: modules/ragnarok-reborn-npcs/<rest> → <rest>
    // must exist in the repo. Other Foundry paths (worlds/..., other modules)
    // are resolved by the VTT at runtime and can't be checked here.
    const own = src.match(/^modules\/ragnarok-reborn-npcs\/(.+)$/);
    const rel = own ? own[1] : src;
    if (!fs.existsSync(rel)) throw new Error(`map art missing on disk: ${rel}`);
    console.log(`OK  ${name}: ${rel} exists (${Math.round(fs.statSync(rel).size / 1024)} KB)`);
  } catch (err) {
    failures++;
    console.error(`FAIL ${name}: ${err.message}`);
  }
}

if (failures) {
  console.error(`\n${failures} scene(s) reference missing map art`);
  process.exit(1);
}
console.log("\nAll scene map references check out");
