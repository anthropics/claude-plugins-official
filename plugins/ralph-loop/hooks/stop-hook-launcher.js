#!/usr/bin/env node
/**
 * Ralph Loop Stop Hook - Cross-Platform Launcher
 *
 * This launcher enables the ralph-loop plugin to work on both Unix and Windows
 * by detecting the platform at runtime and invoking the appropriate native script:
 *   - Windows: PowerShell (stop-hook.ps1)
 *   - Unix/macOS: Bash (stop-hook.sh)
 *
 * Why Node.js?
 *   - Claude Code is a Node.js application, so Node.js is guaranteed to be installed
 *   - Unlike Python, Node.js doesn't require separate installation on Windows
 *   - Single hooks.json configuration works across all platforms
 *
 * @see https://github.com/anthropics/claude-plugins-official/tree/main/plugins/ralph-loop
 */

const { spawn } = require('child_process');
const path = require('path');
const os = require('os');

const hooksDir = __dirname;
const isWindows = os.platform() === 'win32';

let childProcess;

if (isWindows) {
    // On Windows, use PowerShell with execution policy bypass for scripts
    const psScript = path.join(hooksDir, 'stop-hook.ps1');
    childProcess = spawn('powershell.exe', [
        '-NoProfile',
        '-ExecutionPolicy', 'Bypass',
        '-File', psScript
    ], {
        stdio: ['inherit', 'inherit', 'inherit']
    });
} else {
    // On Unix-like systems (Linux, macOS), use bash
    const bashScript = path.join(hooksDir, 'stop-hook.sh');
    childProcess = spawn('bash', [bashScript], {
        stdio: ['inherit', 'inherit', 'inherit']
    });
}

childProcess.on('close', (code) => {
    process.exit(code || 0);
});

childProcess.on('error', (err) => {
    console.error(`Ralph Loop: Failed to start hook script: ${err.message}`);
    process.exit(1);
});
