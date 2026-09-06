// Regression test for anthropics/claude-code#81571: starting a second
// Claude Code session must not kill the Telegram poller a first session is
// using, and the polling slot must hand off to a surviving server when the
// holder exits.
//
// Run from this directory (deps installed via `bun install`):
//   bun test test/poller-lifecycle.test.ts
//
// The pid-slot logic runs before any network call, so a dummy token is
// enough — polling errors from the fake token are expected and irrelevant.

import { afterEach, expect, test } from 'bun:test'
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'fs'
import { tmpdir } from 'os'
import { join } from 'path'

const SERVER = join(import.meta.dir, '..', 'server.ts')

type Server = ReturnType<typeof Bun.spawn>
const spawned: Server[] = []

function startServer(stateDir: string): Server {
  const proc = Bun.spawn(['bun', SERVER], {
    env: { ...process.env, TELEGRAM_STATE_DIR: stateDir },
    stdin: 'pipe', // held open — the server treats stdin EOF as session exit
    stdout: 'ignore',
    stderr: 'ignore',
  })
  spawned.push(proc)
  return proc
}

function pidFileContents(stateDir: string): number | null {
  try {
    return parseInt(readFileSync(join(stateDir, 'bot.pid'), 'utf8'), 10)
  } catch {
    return null
  }
}

async function waitFor(cond: () => boolean, ms: number): Promise<boolean> {
  const deadline = Date.now() + ms
  while (Date.now() < deadline) {
    if (cond()) return true
    await new Promise(r => setTimeout(r, 100))
  }
  return cond()
}

function isAlive(pid: number): boolean {
  try {
    process.kill(pid, 0)
    return true
  } catch {
    return false
  }
}

function makeStateDir(): string {
  const dir = mkdtempSync(join(tmpdir(), 'tg-poller-test-'))
  writeFileSync(join(dir, '.env'), 'TELEGRAM_BOT_TOKEN=123456789:AAHdummy_token_for_pid_logic_only\n')
  return dir
}

afterEach(() => {
  for (const proc of spawned) {
    try {
      proc.kill()
    } catch {}
  }
  spawned.length = 0
})

test('second server does not kill the incumbent poller; slot hands off on exit', async () => {
  const stateDir = makeStateDir()
  try {
    // A starts and claims the polling slot.
    const a = startServer(stateDir)
    expect(await waitFor(() => pidFileContents(stateDir) === a.pid, 10_000)).toBe(true)

    // B starts while A is healthy: B must defer, A must survive as holder.
    const b = startServer(stateDir)
    expect(await waitFor(() => pidFileContents(stateDir) === b.pid, 4_000)).toBe(false)
    expect(isAlive(a.pid)).toBe(true)
    expect(isAlive(b.pid)).toBe(true)
    expect(pidFileContents(stateDir)).toBe(a.pid)

    // A's session ends (stdin EOF): B's standby watcher takes over the slot.
    a.stdin.end()
    await a.exited
    expect(await waitFor(() => pidFileContents(stateDir) === b.pid, 10_000)).toBe(true)
    expect(isAlive(b.pid)).toBe(true)

    // Last session exits: the owner removes its pid file.
    b.stdin.end()
    await b.exited
    expect(await waitFor(() => pidFileContents(stateDir) === null, 5_000)).toBe(true)
  } finally {
    rmSync(stateDir, { recursive: true, force: true })
  }
}, 60_000)

test('a standby exiting leaves the incumbent and its pid file untouched', async () => {
  const stateDir = makeStateDir()
  try {
    const a = startServer(stateDir)
    expect(await waitFor(() => pidFileContents(stateDir) === a.pid, 10_000)).toBe(true)

    // Short-lived second session: starts, defers, exits.
    const b = startServer(stateDir)
    await new Promise(r => setTimeout(r, 1_500))
    b.stdin.end()
    await b.exited

    // The incumbent still holds the slot — the exact end state #81571 broke
    // (no poller left and no pid file at all).
    expect(isAlive(a.pid)).toBe(true)
    expect(pidFileContents(stateDir)).toBe(a.pid)
  } finally {
    rmSync(stateDir, { recursive: true, force: true })
  }
}, 60_000)
