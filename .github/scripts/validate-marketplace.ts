#!/usr/bin/env bun
/**
 * Validates marketplace.json: well-formed JSON, plugins array present,
 * each entry has required fields, no duplicate plugin names, and valid source format.
 *
 * Usage:
 *   bun validate-marketplace.ts <path-to-marketplace.json>
 */

import { readFile } from "fs/promises";

const VALID_SOURCE_TYPES = ["url"] as const;
const URL_PATTERN = /^https?:\/\/.+/;

function validateSource(
  source: unknown,
  pluginIndex: number,
  pluginName: string
): string[] {
  const errors: string[] = [];
  const prefix = `plugins[${pluginIndex}] (${pluginName})`;

  // source can be a string (local path) or an object (remote source)
  if (typeof source === "string") {
    // Local path like "./plugins/xxx" or "./external_plugins/xxx"
    return errors;
  }

  if (!source || typeof source !== "object" || Array.isArray(source)) {
    errors.push(`${prefix}: source must be a string or object`);
    return errors;
  }

  const srcObj = source as Record<string, unknown>;
  const srcType = srcObj.source;

  // Validate source.source type
  if (typeof srcType !== "string") {
    errors.push(`${prefix}: source.source must be a string`);
    return errors;
  }

  if (!VALID_SOURCE_TYPES.includes(srcType as typeof VALID_SOURCE_TYPES[number])) {
    errors.push(
      `${prefix}: source.source must be one of: ${VALID_SOURCE_TYPES.join(", ")}; got "${srcType}"`
    );
    return errors;
  }

  // Validate source.url
  const url = srcObj.url;
  if (typeof url !== "string") {
    errors.push(`${prefix}: source.url is required when source.source is "${srcType}"`);
    return errors;
  }

  if (!URL_PATTERN.test(url)) {
    errors.push(
      `${prefix}: source.url must be a full URL (https://...); got "${url}"`
    );
  }


  return errors;
}

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

  const errors: string[] = [];
  const seen = new Set<string>();
  const required = ["name", "description", "source"] as const;

  marketplace.plugins.forEach((p, i) => {
    if (!p || typeof p !== "object") {
      errors.push(`plugins[${i}]: must be an object`);
      return;
    }
    const entry = p as Record<string, unknown>;
    for (const field of required) {
      if (!entry[field]) {
        errors.push(`plugins[${i}] (${entry.name ?? "?"}): missing required field "${field}"`);
      }
    }
    if (typeof entry.name === "string") {
      if (seen.has(entry.name)) {
        errors.push(`plugins[${i}]: duplicate plugin name "${entry.name}"`);
      }
      seen.add(entry.name);
    }

    // Validate source format
    if (entry.source) {
      errors.push(...validateSource(entry.source, i, String(entry.name ?? "?")));
    }
  });

  if (errors.length) {
    console.error(`ERROR: ${filePath} has ${errors.length} validation error(s):`);
    for (const e of errors) console.error(`  - ${e}`);
    process.exit(1);
  }

  console.log(`OK: ${marketplace.plugins.length} plugins, no duplicates, all required fields present`);
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(2);
});
