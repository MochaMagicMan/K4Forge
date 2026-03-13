/**
 * export-artifact.ts — Export a k4-engine artifact to web/public/demo/
 *
 * Usage:
 *   npx tsx scripts/export-artifact.ts <artifact-dir> <preset-id>
 *
 * Example:
 *   npx tsx scripts/export-artifact.ts ../runs/2026-03-13_basic_bz_da6667c1 basic-bz
 *
 * This reads the 5 JSON files from the artifact directory and writes
 * a combined artifact.json into web/public/demo/<preset-id>/, plus
 * copies the individual JSON files for raw-link access.
 */

import { readFileSync, writeFileSync, mkdirSync, copyFileSync, existsSync } from "fs";
import { join, resolve } from "path";

const ARTIFACT_FILES = [
  "manifest.json",
  "spec.json",
  "drive.json",
  "observables.json",
  "claim.json",
] as const;

function main() {
  const args = process.argv.slice(2);
  if (args.length < 2) {
    console.error("Usage: npx tsx scripts/export-artifact.ts <artifact-dir> <preset-id>");
    process.exit(1);
  }

  const [artifactDir, presetId] = args;
  const srcDir = resolve(artifactDir);
  const destDir = resolve(__dirname, "..", "public", "demo", presetId);

  // Validate source
  for (const file of ARTIFACT_FILES) {
    const p = join(srcDir, file);
    if (!existsSync(p)) {
      console.error(`Missing: ${p}`);
      process.exit(1);
    }
  }

  // Create destination
  mkdirSync(destDir, { recursive: true });

  // Read all files
  const data: Record<string, unknown> = {};
  for (const file of ARTIFACT_FILES) {
    const content = readFileSync(join(srcDir, file), "utf-8");
    const key = file.replace(".json", "");
    data[key] = JSON.parse(content);

    // Also copy individual file for raw-link access
    copyFileSync(join(srcDir, file), join(destDir, file));
  }

  // Write combined artifact.json
  const combined = JSON.stringify(data, null, 2);
  writeFileSync(join(destDir, "artifact.json"), combined, "utf-8");

  console.log(`Exported ${presetId} to ${destDir}`);
  console.log(`  Combined: artifact.json (${(combined.length / 1024).toFixed(1)} KB)`);
  console.log(`  Individual: ${ARTIFACT_FILES.join(", ")}`);

  // Copy figures if they exist
  const figDir = join(srcDir, "figures");
  if (existsSync(figDir)) {
    const destFigDir = join(destDir, "figures");
    mkdirSync(destFigDir, { recursive: true });
    const { readdirSync } = require("fs");
    const figs = readdirSync(figDir) as string[];
    for (const fig of figs) {
      copyFileSync(join(figDir, fig), join(destFigDir, fig));
    }
    console.log(`  Figures: ${figs.join(", ")}`);
  }
}

main();
