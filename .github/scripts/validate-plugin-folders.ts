#!/usr/bin/env bun
/**
 * Validates the plugin folders in this repository (plugin-dirs.sh) with
 * `claude plugin validate`. Needs `claude` on PATH; run from the repo root.
 *
 * Each folder is checked twice, because neither check is enough alone:
 *
 *  1. On its own, which covers the manifest and the plugin's files. This
 *     rejects names such as "claude-security" as reserved for Anthropic: the
 *     CLI can't tell from a bare folder that the plugin is ours. So a problem
 *     with `name` is ignored here and left to check 2.
 *  2. All together, listed in a throwaway marketplace with this marketplace's
 *     name. Reserved names are allowed there and other bad names are not, and
 *     a plugin need not be listed in the real marketplace.json to be checked.
 */

import { spawnSync } from "child_process";
import {
  cpSync,
  existsSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "fs";
import { tmpdir } from "os";
import { basename, dirname, join } from "path";

const MARKETPLACE_NAME = "claude-plugins-official";
const CLI_TIMEOUT_MS = 120_000;
// Files the plugin loader reads. The CLI doesn't report every one of these
// when it isn't valid JSON.
const JSON_FILES = [".mcp.json", ".lsp.json", "hooks/hooks.json"];

interface Issue {
  path: string;
  message: string;
}
interface FileReport {
  file: string;
  errors: Issue[];
  warnings: Issue[];
}
interface Report {
  success: boolean;
  manifest: FileReport | null;
  contents: FileReport[];
}

function run(cmd: string, args: string[]) {
  const r = spawnSync(cmd, args, {
    encoding: "utf8",
    maxBuffer: 64 * 1024 * 1024,
    timeout: CLI_TIMEOUT_MS,
  });
  if (r.error) throw r.error;
  return r;
}

function cliValidate(path: string): Report {
  // Exits 1 with a report on stdout when the plugin is not valid.
  const r = run("claude", ["plugin", "validate", "--json", path]);
  try {
    const report = JSON.parse(r.stdout) as Report;
    if (typeof report.success !== "boolean" || !Array.isArray(report.contents))
      throw new Error("unexpected report shape");
    return report;
  } catch (err) {
    throw new Error(
      `claude plugin validate gave no usable report for ${path} (exit ${r.status}): ${err}\n${r.stdout}${r.stderr}`
    );
  }
}

function checkFolder(dir: string): { problems: string[]; name: string | null } {
  const manifestPath = join(dir, ".claude-plugin/plugin.json");
  if (!existsSync(manifestPath))
    return { problems: ["no .claude-plugin/plugin.json"], name: null };

  const problems: string[] = [];
  let name: string | null = null;
  try {
    const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
    const value = manifest?.name;
    if (typeof value === "string" && value) name = value;
  } catch {
    // Not JSON: the CLI reports it below.
  }
  if (name !== null && name !== basename(dir))
    problems.push(`plugin.json name "${name}" is not the folder's name`);

  for (const file of JSON_FILES) {
    const path = join(dir, file);
    if (!existsSync(path)) continue;
    try {
      JSON.parse(readFileSync(path, "utf8"));
    } catch (err) {
      problems.push(`${file}: not valid JSON (${err})`);
    }
  }

  const report = cliValidate(dir);
  for (const w of report.manifest?.warnings ?? [])
    console.log(`warn ${dir} plugin.json ${w.path}: ${w.message}`);
  const manifestErrors = report.manifest?.errors ?? [];
  // Check 2 judges the name, and can only do so when there is one.
  const ignored = name === null ? [] : manifestErrors.filter((e) => e.path === "name");
  const reported = manifestErrors.filter((e) => !ignored.includes(e));
  for (const e of reported) problems.push(`plugin.json ${e.path}: ${e.message}`);
  let fileErrors = 0;
  for (const f of report.contents) {
    for (const e of f.errors) {
      fileErrors++;
      problems.push(`${f.file} ${e.path}: ${e.message}`);
    }
    for (const w of f.warnings ?? [])
      console.log(`warn ${f.file} ${w.path}: ${w.message}`);
  }
  // A failure with no error we can name must still fail.
  if (!report.success && !ignored.length && !reported.length && !fileErrors)
    problems.push("claude plugin validate failed without naming an error");

  return { problems, name };
}

function checkTogether(plugins: { dir: string; name: string }[]): string[] {
  const root = mkdtempSync(join(tmpdir(), "plugin-folders-"));
  try {
    for (const { dir } of plugins) {
      mkdirSync(join(root, dirname(dir)), { recursive: true });
      cpSync(dir, join(root, dir), { recursive: true });
    }
    const file = join(root, ".claude-plugin/marketplace.json");
    mkdirSync(dirname(file));
    writeFileSync(
      file,
      JSON.stringify({
        name: MARKETPLACE_NAME,
        owner: { name: "Anthropic", email: "support@anthropic.com" },
        plugins: plugins.map(({ dir, name }) => ({ name, source: `./${dir}` })),
      })
    );
    const report = cliValidate(file);
    const problems = [report.manifest, ...report.contents].flatMap((f) =>
      (f?.errors ?? []).map((e) => {
        // "plugins[4] plugin.json → version" or "plugins.4.name"
        const i = /^plugins[[.](\d+)/.exec(e.path)?.[1];
        const dir = i === undefined ? undefined : plugins[Number(i)]?.dir;
        return `${dir ? `${dir}: ` : ""}${e.path}: ${e.message}`;
      })
    );
    if (!report.success && problems.length === 0)
      problems.push("claude plugin validate failed without naming an error");
    return problems;
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
}

// Entries of the real marketplace.json whose plugin lives in this repository.
function checkListedFoldersExist(): string[] {
  const { plugins } = JSON.parse(
    readFileSync(".claude-plugin/marketplace.json", "utf8")
  ) as { plugins: { name: string; source: unknown }[] };
  return plugins.flatMap(({ name, source }) =>
    typeof source === "string" &&
    !existsSync(join(source, ".claude-plugin/plugin.json"))
      ? [`marketplace.json lists "${name}" at ${source}, which has no plugin`]
      : []
  );
}

const list = run("bash", [".github/scripts/plugin-dirs.sh"]);
if (list.status !== 0) throw new Error(`plugin-dirs.sh failed: ${list.stderr}`);
const dirs = list.stdout.split("\n").filter(Boolean);
if (dirs.length === 0) throw new Error("found no plugin folders");

const problems: string[] = [];
const named: { dir: string; name: string }[] = [];
for (const dir of dirs) {
  let result: ReturnType<typeof checkFolder>;
  try {
    result = checkFolder(dir);
  } catch (err) {
    result = { problems: [String(err)], name: null };
  }
  console.log(`${result.problems.length ? "FAIL" : "ok  "} ${dir}`);
  for (const p of result.problems) problems.push(`${dir}: ${p}`);
  if (result.name !== null) named.push({ dir, name: result.name });
}
for (const check of [() => checkTogether(named), checkListedFoldersExist]) {
  try {
    problems.push(...check());
  } catch (err) {
    problems.push(String(err));
  }
}

if (problems.length > 0) {
  console.log();
  // %0A keeps a multi-line message in one annotation.
  for (const p of problems) console.log(`::error::${p.replace(/\r?\n/g, "%0A")}`);
  console.log(`\n${problems.length} problem(s) in ${dirs.length} plugin folders.`);
  process.exit(1);
}
console.log(`\nAll ${dirs.length} plugin folders are valid.`);
