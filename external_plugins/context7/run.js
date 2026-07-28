'use strict';

const { spawn } = require('node:child_process');

// On Windows, `npx` resolves to the `npx.cmd` shim, which Node's child_process
// cannot spawn directly without a shell (see anthropics/claude-plugins-official#4589).
// The command is passed as a single string (not an args array) so Node doesn't
// emit the DEP0190 unescaped-shell-args warning.
const child = process.platform === 'win32'
  ? spawn('npx -y @upstash/context7-mcp', { stdio: 'inherit', shell: true })
  : spawn('npx', ['-y', '@upstash/context7-mcp'], { stdio: 'inherit' });

child.on('error', (err) => {
  console.error(`context7 mcp: failed to launch npx (${err.message})`);
  process.exit(1);
});

child.on('exit', (code, signal) => {
  process.exit(signal ? 1 : (code ?? 1));
});
