#!/usr/bin/env node
/**
 * Ralph Loop Setup Script - Cross-Platform Launcher
 *
 * This launcher enables the ralph-loop setup to work on both Unix and Windows
 * by detecting the platform at runtime and invoking the appropriate native script:
 *   - Windows: PowerShell (setup-ralph-loop.ps1)
 *   - Unix/macOS: Bash (setup-ralph-loop.sh)
 *
 * Arguments are passed through to the underlying script.
 */

const { spawn } = require('child_process');
const path = require('path');
const os = require('os');

const scriptsDir = __dirname;
const isWindows = os.platform() === 'win32';

// Get arguments (skip node and script path)
const args = process.argv.slice(2);

let childProcess;

if (isWindows) {
    // On Windows, use PowerShell with execution policy bypass
    const psScript = path.join(scriptsDir, 'setup-ralph-loop.ps1');
    childProcess = spawn('powershell.exe', [
        '-NoProfile',
        '-ExecutionPolicy', 'Bypass',
        '-File', psScript,
        ...args
    ], {
        stdio: ['inherit', 'inherit', 'inherit']
    });
} else {
    // On Unix-like systems (Linux, macOS), use bash
    const bashScript = path.join(scriptsDir, 'setup-ralph-loop.sh');
    childProcess = spawn('bash', [bashScript, ...args], {
        stdio: ['inherit', 'inherit', 'inherit']
    });
}

childProcess.on('close', (code) => {
    process.exit(code || 0);
});

childProcess.on('error', (err) => {
    console.error(`Ralph Loop: Failed to start setup script: ${err.message}`);
    process.exit(1);
});
