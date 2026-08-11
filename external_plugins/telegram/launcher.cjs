#!/usr/bin/env node
/**
 * Cross-runtime launcher for the Telegram channel server.
 *
 * On POSIX the server runs under Bun, exactly as before. On Windows, Bun's
 * stdin pipe does not interoperate with being spawned from a Node parent:
 * the server process starts and polls Telegram, but never receives stdin,
 * so the MCP stdio handshake times out and Claude Code drops the connection
 * (-32000). See anthropics/claude-code#36964 and anthropics/claude-code#39776.
 *
 * server.ts uses only erasable TypeScript and no Bun-specific APIs, so on
 * Windows we run it under Node instead — Node is guaranteed to be present
 * (Claude Code itself is distributed through npm) and Node >= 22.6 can run
 * .ts files via type stripping. Dependencies are installed with the npm
 * that ships alongside the running Node binary, resolved by absolute path
 * because plugin MCP servers are spawned with a sanitized environment.
 */

const { spawn, spawnSync } = require('node:child_process')
const { existsSync } = require('node:fs')
const { join } = require('node:path')

const ROOT = __dirname
const SERVER = join(ROOT, 'server.ts')

function run(cmd, args) {
  const child = spawn(cmd, args, { cwd: ROOT, stdio: 'inherit' })
  child.on('exit', (code, signal) => process.exit(code ?? (signal ? 1 : 0)))
  child.on('error', (err) => {
    process.stderr.write(`telegram launcher: failed to start ${cmd}: ${err.message}\n`)
    process.exit(1)
  })
}

if (process.platform !== 'win32') {
  // Original behavior: bun install + bun server.ts (see package.json "start").
  run('bun', ['run', '--cwd', ROOT, '--shell=bun', '--silent', 'start'])
} else {
  if (!existsSync(join(ROOT, 'node_modules'))) {
    const npmCli = join(process.execPath, '..', 'node_modules', 'npm', 'bin', 'npm-cli.js')
    const result = spawnSync(
      process.execPath,
      [npmCli, 'install', '--no-audit', '--no-fund', '--loglevel=error'],
      { cwd: ROOT, stdio: ['ignore', 'ignore', 'inherit'] },
    )
    if (result.status !== 0) {
      process.stderr.write('telegram launcher: npm install failed\n')
      process.exit(1)
    }
  }

  const [major, minor] = process.versions.node.split('.').map(Number)
  if (major > 23 || (major === 23 && minor >= 6)) {
    // Type stripping is on by default.
    run(process.execPath, [SERVER])
  } else if (major > 22 || (major === 22 && minor >= 6)) {
    run(process.execPath, ['--experimental-strip-types', SERVER])
  } else {
    process.stderr.write(
      `telegram launcher: Node >= 22.6 is required on Windows (found ${process.versions.node})\n`,
    )
    process.exit(1)
  }
}
