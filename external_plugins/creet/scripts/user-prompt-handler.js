/**
 * Creet - UserPromptSubmit Hook
 * Analyzes user input and suggests matching skills.
 */

const path = require('path');
const fs = require('fs');

const PLUGIN_ROOT = path.resolve(__dirname, '..');

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

// Skip if auto-recommend is disabled
if (config.autoRecommend === false) {
  console.log(JSON.stringify({ systemMessage: '' }));
  process.exit(0);
}

const { matchKeywords } = require(path.join(PLUGIN_ROOT, 'lib', 'keyword-matcher'));
const { searchRegistry } = require(path.join(PLUGIN_ROOT, 'lib', 'plugin-registry'));

function main() {
  try {
    // Read user message from stdin (Claude Code passes it via environment or stdin)
    const input = getInput();
    if (!input || !input.userMessage) {
      console.log(JSON.stringify({ systemMessage: '' }));
      process.exit(0);
    }

    const message = input.userMessage;

    // Skip if user already used a skill command
    if (message.startsWith('/')) {
      console.log(JSON.stringify({ systemMessage: '' }));
      process.exit(0);
    }

    // Skip very short messages
    if (message.length < 5) {
      console.log(JSON.stringify({ systemMessage: '' }));
      process.exit(0);
    }

    // Match keywords dynamically against cached scan results
    const customMap = config.customKeywords || null;
    const matches = matchKeywords(message, null, customMap);

    // Take top match (only suggest if score is high enough)
    const MIN_SCORE = config.minMatchScore || 5;

    if (matches.length > 0 && matches[0].score >= MIN_SCORE) {
      // Installed skill match found
      const suggestions = matches.slice(0, 2).map(m => `/${m.skill}`).join(', ');
      const hint = `Creet detected skill match: ${suggestions} may help with this request. Suggest it naturally if appropriate.`;

      const response = {
        systemMessage: hint,
        hookSpecificOutput: {
          hookEventName: 'UserPromptSubmit',
          matchType: 'installed',
          matchedSkills: matches.slice(0, 2),
          userMessage: message.substring(0, 50),
        },
      };

      console.log(JSON.stringify(response));
      process.exit(0);
    }

    // No installed skill match — search plugin registry
    const registryMatches = searchRegistry(message);

    if (registryMatches.length > 0) {
      const pluginNames = registryMatches.map(r => r.name).join(', ');
      const hint = `Creet: No installed skill matches, but external plugins may help: ${pluginNames}. Suggest them if the user uses /c.`;

      const response = {
        systemMessage: hint,
        hookSpecificOutput: {
          hookEventName: 'UserPromptSubmit',
          matchType: 'registry',
          suggestedPlugins: registryMatches.map(r => ({
            name: r.name,
            domain: r.domain,
            description: r.description,
            installCmd: r.installCmd,
          })),
          userMessage: message.substring(0, 50),
        },
      };

      console.log(JSON.stringify(response));
      process.exit(0);
    }

    // No match at all
    console.log(JSON.stringify({ systemMessage: '' }));
    process.exit(0);
  } catch {
    console.log(JSON.stringify({ systemMessage: '' }));
    process.exit(0);
  }
}

/**
 * Get input from environment or stdin.
 */
function getInput() {
  // Try environment variable first
  if (process.env.CLAUDE_USER_MESSAGE) {
    return { userMessage: process.env.CLAUDE_USER_MESSAGE };
  }

  // Try reading from stdin (non-blocking)
  try {
    const stdinData = fs.readFileSync('/dev/stdin', 'utf-8');
    if (stdinData) {
      return JSON.parse(stdinData);
    }
  } catch {
    // stdin not available
  }

  // Try reading from process.argv
  if (process.argv[2]) {
    try {
      return JSON.parse(process.argv[2]);
    } catch {
      return { userMessage: process.argv[2] };
    }
  }

  return null;
}

main();
