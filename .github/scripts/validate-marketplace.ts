#!/usr/bin/env bun
/**
 * Validates that marketplace.json is well-formed JSON with a plugins array.
 *
 * Usage:
 *   bun validate-marketplace.ts <path-to-marketplace.json>
 */

import { readFile } from "fs/promises";

async function main() {
  const filePath = process.argv[2];
  if (!filePath) {
    console.error("Usage: validate-marketplace.ts <path-to-marketplace.json>");
    process.exit(2);
  }

  const content = await readFile(filePath, "utf-8");

  let parsed: unknown;
  try {
    parsed = JSON.parse(content);
  } catch (err) {
    console.error(
      `ERROR: ${filePath} is not valid JSON: ${err instanceof Error ? err.message : err}`
    );
    process.exit(1);
  }

  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    console.error(`ERROR: ${filePath} must be a JSON object`);
    process.exit(1);
  }

  const marketplace = parsed as Record<string, unknown>;
  if (!Array.isArray(marketplace.plugins)) {
    console.error(`ERROR: ${filePath} missing "plugins" array`);
    process.exit(1);
  }

  console.log(
    `marketplace.json is valid (${marketplace.plugins.length} plugins)`
  );
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(2);
});
