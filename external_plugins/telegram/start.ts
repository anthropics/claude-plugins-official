// Launcher for the channel server.
//
// Every session on a machine loads this plugin from the same cache directory,
// so `bun install` on each start is not a private act: it re-links
// node_modules/.bin underneath live sibling processes and takes their pollers
// down with it, and two sessions starting at once lose the race against each
// other outright ("Failed to link which: EEXIST") and come up with no poller
// at all. It also makes an offline start fail on a plugin that is already
// fully installed.
//
// So the test for "can this run" is the import itself, which is exact where a
// check of node_modules would only approximate: it covers the packages
// server.ts imports, the ones those import, and a tree left half written by
// an interrupted install. Installing is what is conditional, not the check.

import { execFileSync, spawnSync } from 'node:child_process'
import { mkdirSync, readFileSync, renameSync, rmSync, statSync, writeFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const SELF = fileURLToPath(import.meta.url)
const ROOT = dirname(SELF)
const LOCK = join(ROOT, '.install.lock')
const OWNER = join(LOCK, 'owner')
const STAMP = join(ROOT, '.install.stamp')
const STARTED_AT = Date.now()
const REPAIRED = 'TELEGRAM_DEPENDENCIES_REPAIRED'

const WAIT_STEP_MS = 250
// Shorter than the client's own budget for starting an MCP server: waiting
// past that loses the session its tools anyway, so hand over to the relaunch
// and let it report instead.
const WAIT_MS = 20000
const ORPHAN_LOCK_MS = 2000
const INSTALL_TIMEOUT_MS = 180000

type Claim = 'held' | 'busy' | 'unlockable'

function claimLock(): Claim {
  try {
    mkdirSync(LOCK)
  } catch (err) {
    // Only EEXIST means someone else is installing. Any other failure — a
    // read-only plugin directory, say — means locking is unavailable here,
    // and an unlocked install is still better than no server.
    return (err as NodeJS.ErrnoException).code === 'EEXIST' ? 'busy' : 'unlockable'
  }
  try {
    writeFileSync(OWNER, String(process.pid))
  } catch {
    // A lock nobody can be identified from is worse than none: a waiter would
    // break it after a moment and install on top of this one.
    releaseLock()
    return 'unlockable'
  }
  return 'held'
}

function releaseLock(): void {
  try {
    rmSync(LOCK, { recursive: true, force: true })
  } catch {}
}

// Removing the directory outright would let two waiters each delete what the
// other had just created and both go on to install. A rename can only succeed
// for one of them, and the loser finds the lock either gone (so it claims it)
// or freshly held (so it waits).
function breakLock(): boolean {
  const aside = `${LOCK}.abandoned.${process.pid}`
  try {
    renameSync(LOCK, aside)
  } catch {
    return false
  }
  try {
    rmSync(aside, { recursive: true, force: true })
  } catch {}
  return true
}

// An install that died leaves its lock behind, and there is no clock to judge
// that by: a slow install and an abandoned one look identical for as long as
// you care to wait. The owner's own liveness is the signal.
function lockOwner(): number | null {
  let raw: string
  try {
    raw = readFileSync(OWNER, 'utf8').trim()
  } catch {
    return null
  }
  const pid = Number(raw)
  return Number.isInteger(pid) && pid > 1 ? pid : null
}

function pidIsAlive(pid: number): boolean {
  // kill(0, …) signals our own process group for a pid of zero or less.
  if (pid <= 1) return false
  try {
    process.kill(pid, 0)
    return true
  } catch (err) {
    return (err as NodeJS.ErrnoException).code === 'EPERM'
  }
}

function modifiedAt(path: string): number {
  try {
    return statSync(path).mtimeMs
  } catch {
    return 0
  }
}

// An import that resolves says the tree is usable, not that it is the tree
// this version of the plugin asked for. A lockfile written after the last
// install is the one case where a working tree is still the wrong one.
function lockfileIsNewerThanInstall(): boolean {
  const installed = modifiedAt(join(ROOT, 'node_modules'))
  return installed > 0 && modifiedAt(join(ROOT, 'bun.lock')) > installed
}

function runInstall(args: string[]): void {
  // process.execPath is the bun running this file. Resolving "bun" through
  // PATH instead would fail on Windows, where it is a .cmd shim that
  // CreateProcess cannot launch. stdout is the MCP stream, so bun's own
  // output goes to stderr and never there.
  execFileSync(process.execPath, ['install', '--no-summary', ...args], {
    cwd: ROOT,
    stdio: ['ignore', 2, 2],
    timeout: INSTALL_TIMEOUT_MS,
    windowsHide: true,
  })
}

function install(): void {
  try {
    // Written only on success, and only read against this process's own start
    // time: an install that finished after this one began is the install this
    // one needed, whoever ran it.
    // The committed lockfile is what this plugin was published against, so
    // honour it rather than re-resolve versions nobody tested. A lockfile
    // that cannot satisfy this machine is worth an unpinned install, but
    // only as a second choice.
    runInstall(['--frozen-lockfile'])
    stamp()
    return
  } catch {}
  try {
    runInstall([])
    stamp()
  } catch (err) {
    process.stderr.write(`telegram channel: installing dependencies failed: ${err}\n`)
  }
}

function stamp(): void {
  try {
    writeFileSync(STAMP, new Date().toISOString())
  } catch {}
}

async function installOnce(): Promise<void> {
  const deadline = Date.now() + WAIT_MS
  let ownerlessSince = 0
  let announced = false

  for (;;) {
    // An install that completed since this process started is the one it
    // needed. Running a second on top of it would re-link node_modules under
    // whatever session the first has just unblocked.
    if (modifiedAt(STAMP) > STARTED_AT) return

    const claim = claimLock()
    if (claim === 'held') {
      try {
        install()
      } finally {
        releaseLock()
      }
      return
    }
    if (claim === 'unlockable') {
      install()
      return
    }

    const owner = lockOwner()
    if (owner === null) {
      // Either a claim that has not written its owner yet, or a lock from a
      // version that never did. Give it a moment before breaking it.
      if (ownerlessSince === 0) ownerlessSince = Date.now()
      if (Date.now() - ownerlessSince > ORPHAN_LOCK_MS && breakLock()) {
        ownerlessSince = 0
        continue
      }
    } else if (!pidIsAlive(owner)) {
      // Whatever that process was doing, it did not finish: no stamp, no
      // owner. Take the lock over.
      if (breakLock()) continue
    } else {
      ownerlessSince = 0
    }

    if (Date.now() > deadline) {
      // Starting a second install beside one that is still running is the
      // race this file exists to prevent. Hand over to the relaunch instead:
      // if the other session finished, the child's import resolves, and if it
      // did not, the child says so.
      process.stderr.write('telegram channel: gave up waiting for another session to install\n')
      return
    }
    if (!announced) {
      process.stderr.write(
        'telegram channel: another session is installing the plugin dependencies; waiting for it\n',
      )
      announced = true
    }
    await new Promise(resolve => setTimeout(resolve, WAIT_STEP_MS))
  }
}

// Bun caches a failed module resolution for the lifetime of the process, so
// the server cannot be imported by the process that installed it for it. The
// child inherits this process's stdio, which is the MCP transport.
function relaunch(): never {
  const result = spawnSync(process.execPath, [SELF, ...process.argv.slice(2)], {
    cwd: ROOT,
    stdio: 'inherit',
    env: { ...process.env, [REPAIRED]: '1' },
  })
  if (result.error) {
    process.stderr.write(`telegram channel: could not restart after installing: ${result.error}\n`)
    process.exit(1)
  }
  process.exit(result.status ?? 1)
}

if (!process.env[REPAIRED] && lockfileIsNewerThanInstall()) {
  await installOnce()
  relaunch()
}

try {
  await import('./server.ts')
} catch (err) {
  // Not just an unresolvable package: a half-written dependency fails to
  // parse instead, and the shapes those take are not worth enumerating. One
  // repair is attempted for any of them, and if the import still fails the
  // original error is what the user needs to see.
  if (process.env[REPAIRED]) {
    process.stderr.write(
      'telegram channel: the dependencies are still missing after an install; the error below is what the server failed on\n',
    )
    throw err
  }
  process.stderr.write(`telegram channel: could not load the server (${err}); checking dependencies\n`)
  await installOnce()
  relaunch()
}
