#!/usr/bin/env node
// PreToolUse hook — blocks dangerous Bash commands, warns on sensitive file edits

let input = '';

process.stdin.setEncoding('utf-8');
process.stdin.on('data', (chunk) => { input += chunk; });
process.stdin.on('end', () => {
  let data;
  try {
    data = JSON.parse(input);
  } catch {
    process.exit(0);
  }

  const toolName = data.tool_name || '';
  const toolInput = data.tool_input || {};

  if (toolName === 'Bash') {
    const cmd = toolInput.command || '';
    const dangerous = [
      /rm\s+-rf\s+[/~]/,
      /rm\s+-rf\s+\.\./,
      /git\s+push\s+.*\s--force/,
      /git\s+push\s+.*\s-f\b/,
      /DROP\s+(TABLE|DATABASE)/i,
      /git\s+reset\s+--hard/,
      /chmod\s+-R\s+777/,
      />\s*\/dev\/(sd|null|zero)/,
    ];
    for (const pattern of dangerous) {
      if (pattern.test(cmd)) {
        process.stdout.write(JSON.stringify({
          decision: 'block',
          reason: `[KSK Security] Dangerous command blocked: ${cmd.slice(0, 80)}\nReview and confirm manually if intended.`,
        }));
        process.exit(0);
      }
    }
  }

  if (toolName === 'Write' || toolName === 'Edit') {
    const filePath = toolInput.file_path || '';
    const sensitivePatterns = [/\.env(\.\w+)?$/, /credentials/, /secrets/, /\.pem$/, /\.key$/, /id_rsa/, /id_ed25519/];
    for (const pattern of sensitivePatterns) {
      if (pattern.test(filePath)) {
        process.stdout.write(`<system-reminder>[KSK Security] Writing to sensitive file: ${filePath}. Ensure no secrets are hardcoded.</system-reminder>`);
        process.exit(0);
      }
    }
  }

  // Allow
  process.exit(0);
});
