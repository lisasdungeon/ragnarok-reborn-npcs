// Compiles all compendium pack sources into Foundry LevelDB packs
// using the official @foundryvtt/foundryvtt-cli (same tool the dnd5e system uses).
//
//   packs/_source/ragnarok-reborn-npcs      → packs/ragnarok-reborn-npcs       (Actor)
//   packs/_source/ragnarok-reborn-gm-guides → packs/ragnarok-reborn-gm-guides  (JournalEntry)
//   packs/_source/ragnarok-reborn-handouts  → packs/ragnarok-reborn-handouts   (JournalEntry)
//   packs/_source/ragnarok-reborn-loot      → packs/ragnarok-reborn-loot       (Item)
import { compilePack } from "@foundryvtt/foundryvtt-cli";

const packs = [
  "ragnarok-reborn-npcs",
  "ragnarok-reborn-gm-guides",
  "ragnarok-reborn-handouts",
  "ragnarok-reborn-loot",
];

for (const name of packs) {
  const src = `packs/_source/${name}`;
  const dest = `packs/${name}`;
  await compilePack(src, dest, { log: true });
  console.log(`Pack compiled: ${dest}`);
}
