#!/usr/bin/env node
// SessionStart hook for discord-sessions (all platforms).
// Claude Code pipes {session_id, transcript_path, cwd, ...} on stdin.
// Writes sessions/<pid>.json for this process and its ancestors so the
// plugin's MCP server (a sibling child of the same Claude process) can find
// its own session by walking its parent-PID chain.
import { readFileSync, writeFileSync, mkdirSync, readdirSync, statSync, unlinkSync } from 'fs'
import { execFileSync } from 'child_process'
import { homedir } from 'os'
import { join } from 'path'

let input = ''
try {
  input = readFileSync(0, 'utf8')
} catch {}
let hook = {}
try {
  hook = JSON.parse(input)
} catch {}
if (!hook.session_id) process.exit(0)

const dir = join(
  process.env.DISCORD_STATE_DIR ?? join(homedir(), '.claude', 'channels', 'discord'),
  'sessions',
)
mkdirSync(dir, { recursive: true })

// prune stale entries (dead PIDs get reused eventually)
const weekAgo = Date.now() - 7 * 24 * 3600 * 1000
for (const f of readdirSync(dir)) {
  try {
    if (statSync(join(dir, f)).mtimeMs < weekAgo) unlinkSync(join(dir, f))
  } catch {}
}

const payload = JSON.stringify({
  sessionId: hook.session_id,
  transcriptPath: hook.transcript_path,
  cwd: hook.cwd,
})

// Process table lookup, per platform. Windows gets the whole table in one
// PowerShell call; POSIX reads /proc per pid with a ps fallback (macOS).
let winTable = null
function loadWinTable() {
  if (winTable) return winTable
  winTable = { ppid: new Map(), name: new Map() }
  try {
    const out = execFileSync('powershell.exe', [
      '-NoProfile', '-NonInteractive', '-Command',
      'Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,Name | ConvertTo-Csv -NoTypeInformation',
    ]).toString()
    for (const line of out.split('\n')) {
      const m = line.match(/"?(\d+)"?,"?(\d+)"?,"?([^"\r\n]*)"?/)
      if (m) {
        winTable.ppid.set(Number(m[1]), Number(m[2]))
        winTable.name.set(Number(m[1]), m[3])
      }
    }
  } catch {}
  return winTable
}

function ppidOf(pid) {
  if (process.platform === 'win32') return loadWinTable().ppid.get(pid) ?? NaN
  try {
    const stat = readFileSync(`/proc/${pid}/stat`, 'utf8')
    return Number(stat.slice(stat.lastIndexOf(')') + 2).trim().split(/\s+/)[1])
  } catch {
    try {
      return Number(execFileSync('ps', ['-o', 'ppid=', '-p', String(pid)]).toString().trim())
    } catch {
      return NaN
    }
  }
}

function nameOf(pid) {
  if (process.platform === 'win32') return loadWinTable().name.get(pid) ?? ''
  try {
    return readFileSync(`/proc/${pid}/comm`, 'utf8').trim()
  } catch {
    try {
      return execFileSync('ps', ['-o', 'comm=', '-p', String(pid)]).toString().trim()
    } catch {
      return ''
    }
  }
}

// Walk up from this hook process. Stop once the Claude process itself is
// written: going further would stomp files of sessions sharing the same
// terminal ancestor. Only a process actually named claude* counts as the
// stop point — Claude Code spawns hooks through transient node wrappers, so
// stopping at any node/bun ancestor ends the walk too early and the real
// Claude pid never gets written. If Claude runs under plain node (npm
// installs), no name matches and we simply write all 8 levels.
let p = process.pid
for (let i = 0; i < 8 && p > 1; i++) {
  try {
    writeFileSync(join(dir, `${p}.json`), payload)
  } catch {}
  if (i > 0 && /^claude/i.test(nameOf(p))) break
  const next = ppidOf(p)
  if (!Number.isFinite(next) || next === p) break
  p = next
}
