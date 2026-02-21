/**
 * Creet - SessionStart Hook
 * Scans installed skills, loads memory, and injects context into the session.
 */

const path = require('path');
const fs = require('fs');

// Resolve plugin root (hooks/ is one level deep)
const PLUGIN_ROOT = path.resolve(__dirname, '..');

// Load modules
const { scanInstalledSkills, formatSkillTable } = require(path.join(PLUGIN_ROOT, 'lib', 'skill-scanner'));
const { loadMemory, saveMemory, recordSessionStart, formatMemorySummary } = require(path.join(PLUGIN_ROOT, 'lib', 'memory-store'));
const { formatKeywordTable, saveScanCache } = require(path.join(PLUGIN_ROOT, 'lib', 'keyword-matcher'));
const { KNOWN_PLUGINS } = require(path.join(PLUGIN_ROOT, 'lib', 'plugin-registry'));

// Load config
let config = {};
try {
  const configPath = path.join(PLUGIN_ROOT, 'creet.config.json');
  if (fs.existsSync(configPath)) {
    config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
  }
} catch {
  config = {};
}

// ── Main ──────────────────────────────────────────────────

function main() {
  try {
    // 1. Scan installed skills and cache for UserPromptSubmit hook
    const skills = scanInstalledSkills();
    saveScanCache(skills);
    const skillTable = formatSkillTable(skills);

    // 2. Load and update memory
    const memoryPath = config.memoryPath || null;
    const memory = loadMemory(memoryPath);
    recordSessionStart(memory);
    saveMemory(memory, memoryPath);
    const memorySummary = formatMemorySummary(memory);

    // 3. Build keyword table from scan results (dynamic, not hardcoded)
    const keywordTable = formatKeywordTable(skills);

    // 4. Build additional context
    const additionalContext = buildAdditionalContext({
      skillTable,
      memorySummary,
      keywordTable,
      skillCount: skills.length,
      pluginCount: [...new Set(skills.map(s => s.plugin))].length,
      config,
    });

    // 5. Output response
    const response = {
      systemMessage: `Creet v1.3.0 activated - ${skills.length} skills from ${[...new Set(skills.map(s => s.plugin))].length} plugins detected`,
      hookSpecificOutput: {
        hookEventName: 'SessionStart',
        skillCount: skills.length,
        sessionNumber: memory.sessionCount,
        additionalContext,
      },
    };

    console.log(JSON.stringify(response));
    process.exit(0);
  } catch (err) {
    // Fail gracefully - don't break the session
    const fallback = {
      systemMessage: 'Creet v1.3.0 activated (scan skipped)',
      hookSpecificOutput: {
        hookEventName: 'SessionStart',
        error: err.message,
        additionalContext: buildFallbackContext(),
      },
    };
    console.log(JSON.stringify(fallback));
    process.exit(0);
  }
}

// ── Context Builder ───────────────────────────────────────

function buildAdditionalContext({ skillTable, memorySummary, keywordTable, skillCount, pluginCount, config: cfg }) {
  const autoRecommend = cfg.autoRecommend !== false;
  const showReport = cfg.showReport !== false;

  let ctx = '';

  // Header
  ctx += `# Creet v1.3.0 - Session Startup\n\n`;

  // Skill inventory
  ctx += `## Installed Skills (Auto-Scanned)\n\n`;
  ctx += skillTable + '\n\n';

  // Session memory
  ctx += `## Session Memory\n\n`;
  ctx += memorySummary + '\n\n';

  // Auto-recommendation rules
  if (autoRecommend) {
    ctx += `## Auto-Recommendation Rules\n\n`;
    ctx += `When the user's message matches keywords below, proactively suggest the matching skill.\n`;
    ctx += `Do NOT auto-execute - just mention: "This task matches /skill-name. Want me to run it?"\n\n`;
    ctx += keywordTable + '\n\n';
    ctx += `### Recommendation Behavior\n`;
    ctx += `- Only suggest if confidence is high (multiple keyword matches)\n`;
    ctx += `- If user already specified a skill (e.g., /commit), do NOT re-recommend\n`;
    ctx += `- Maximum 2 skill suggestions per message\n`;
    ctx += `- Use the user's language for suggestions\n\n`;
  }

  // Plugin Discovery Registry
  ctx += `## Plugin Discovery Registry\n\n`;
  ctx += `When NO installed skill matches the user's request, search this registry and suggest installable plugins.\n\n`;
  ctx += `| Plugin | Source | Domain | Description |\n`;
  ctx += `|--------|--------|--------|-------------|\n`;
  for (const p of KNOWN_PLUGINS) {
    ctx += `| ${p.name} | ${p.source} | ${p.domain} | ${p.description} |\n`;
  }
  ctx += `\n`;
  ctx += `### Discovery Rules\n`;
  ctx += `- Only show when NO installed skill matches the request\n`;
  ctx += `- Match user's request keywords against plugin keywords\n`;
  ctx += `- Show max 3 matching plugins with install commands\n`;
  ctx += `- Format: "No installed skill matches, but you can install: \`install-command\`"\n`;
  ctx += `- Use the user's language for the suggestion\n\n`;

  // Creet usage guide
  ctx += `## Quick Commands\n\n`;
  ctx += `- \`/c <request>\` - Scan + Recommend + Execute workflow\n`;
  ctx += `- \`/c\` (no args) - Show full skill inventory\n\n`;

  // Report rule
  if (showReport) {
    ctx += `## Creet Suggestion Line (Recommended for all responses)\n\n`;
    ctx += `When a user's request clearly matches an installed skill but they didn't use /c,\n`;
    ctx += `add a single-line suggestion at the end of your response:\n\n`;
    ctx += '```\n';
    ctx += `── Creet ──────────────────────────────\n`;
    ctx += `Tip: /skill-name can help with this task\n`;
    ctx += `─────────────────────────────────────────\n`;
    ctx += '```\n\n';
    ctx += `Rules:\n`;
    ctx += `- Only show when there's a clear skill match\n`;
    ctx += `- Don't show if user already used /c or a specific skill\n`;
    ctx += `- Don't show for simple questions or chat\n`;
    ctx += `- Maximum 1 suggestion per response\n`;
  }

  return ctx;
}

function buildFallbackContext() {
  return `# Creet v1.3.0 - Session Startup

Skill scan was skipped (no plugins cache found or scan error).
Use \`/c <request>\` to manually scan and get recommendations.
`;
}

// ── Run ───────────────────────────────────────────────────

main();
