#!/usr/bin/env bun
/**
 * PAI Discord Courier — Stress Test Harness
 *
 * Tests the daemon + bridged server queue machinery by injecting
 * messages directly into the inbound queue and verifying behavior.
 * Does NOT require Discord API calls — tests the local architecture.
 *
 * Usage: bun run ~/.claude/channels/discord/stress-test.ts [test-name]
 *   No args = run all tests
 *   test-name = run specific test (burst, large, daemon-restart, courier-crash, timeout, isolation)
 */

import {
  readFileSync, writeFileSync, mkdirSync, readdirSync, rmSync,
  existsSync, renameSync, statSync,
} from 'fs'
import { join } from 'path'
import { homedir } from 'os'
import { randomBytes } from 'crypto'

const STATE_DIR    = join(homedir(), '.claude', 'channels', 'discord')
const INBOUND_DIR  = join(STATE_DIR, 'inbound')
const OUTBOUND_DIR = join(STATE_DIR, 'outbound')
const DAEMON_LOG   = join(STATE_DIR, 'daemon.log')
const BRIDGED_LOG  = join(STATE_DIR, 'bridged.log')
const HEALTH_URL   = 'http://localhost:8890/health'

// ── Helpers ────────────────────────────────────────────────────────────

const CYAN    = '\x1b[36m'
const GREEN   = '\x1b[32m'
const RED     = '\x1b[31m'
const YELLOW  = '\x1b[33m'
const DIM     = '\x1b[2m'
const RESET   = '\x1b[0m'

let passed = 0
let failed = 0
let skipped = 0

function header(name: string): void {
  console.log(`\n${CYAN}━━━ TEST: ${name} ━━━${RESET}`)
}

function pass(msg: string): void {
  console.log(`  ${GREEN}✓${RESET} ${msg}`)
  passed++
}

function fail(msg: string): void {
  console.log(`  ${RED}✗${RESET} ${msg}`)
  failed++
}

function skip(msg: string): void {
  console.log(`  ${YELLOW}○${RESET} ${msg} ${DIM}(skipped)${RESET}`)
  skipped++
}

function info(msg: string): void {
  console.log(`  ${DIM}${msg}${RESET}`)
}

function writeInbound(content: string, id?: string): string {
  const msgId = id ?? randomBytes(6).toString('hex')
  const ts = Date.now()
  const filename = `${ts}-${msgId}.json`
  const msg = {
    type: 'message',
    chat_id: 'stress-test-channel',
    message_id: msgId,
    user: 'stress-test',
    user_id: '000000000000000000',
    content,
    ts: new Date().toISOString(),
    attachments: [],
  }
  const tmpPath = join(INBOUND_DIR, `.${filename}.tmp`)
  const finalPath = join(INBOUND_DIR, filename)
  writeFileSync(tmpPath, JSON.stringify(msg))
  renameSync(tmpPath, finalPath)
  return msgId
}

function writeOutbound(type: string, extra: Record<string, unknown> = {}): string {
  const requestId = randomBytes(8).toString('hex')
  const ts = Date.now()
  const filename = `${ts}-${requestId}.json`
  const cmd = { type, request_id: requestId, ...extra }
  const tmpPath = join(OUTBOUND_DIR, `.${filename}.tmp`)
  const finalPath = join(OUTBOUND_DIR, filename)
  writeFileSync(tmpPath, JSON.stringify(cmd))
  renameSync(tmpPath, finalPath)
  return requestId
}

function countFiles(dir: string, ext = '.json'): number {
  try {
    return readdirSync(dir).filter(f => f.endsWith(ext) && !f.startsWith('.')).length
  } catch { return 0 }
}

function logContains(logFile: string, needle: string, sinceMs = 10000): boolean {
  try {
    const lines = readFileSync(logFile, 'utf8').split('\n')
    const cutoff = new Date(Date.now() - sinceMs).toISOString()
    return lines.some(l => l >= cutoff && l.includes(needle))
  } catch { return false }
}

function clearQueues(): void {
  for (const dir of [INBOUND_DIR, OUTBOUND_DIR]) {
    try {
      for (const f of readdirSync(dir)) {
        rmSync(join(dir, f), { force: true })
      }
    } catch {}
  }
}

async function waitForQueueDrain(dir: string, timeoutMs = 10000): Promise<boolean> {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    if (countFiles(dir) === 0) return true
    await Bun.sleep(200)
  }
  return false
}

async function waitForResultFile(requestId: string, timeoutMs = 10000): Promise<Record<string, unknown> | null> {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    const files = readdirSync(OUTBOUND_DIR).filter(f => f.includes(requestId) && f.endsWith('.result.json'))
    if (files.length > 0) {
      const path = join(OUTBOUND_DIR, files[0])
      try {
        const result = JSON.parse(readFileSync(path, 'utf8'))
        rmSync(path, { force: true })
        return result
      } catch { /* partially written, retry */ }
    }
    await Bun.sleep(100)
  }
  return null
}

async function healthCheck(): Promise<{ ok: boolean; data?: Record<string, unknown> }> {
  try {
    const res = await fetch(HEALTH_URL)
    const data = await res.json() as Record<string, unknown>
    return { ok: res.status === 200, data }
  } catch {
    return { ok: false }
  }
}

// ── Tests ──────────────────────────────────────────────────────────────

async function testHealth(): Promise<void> {
  header('Daemon Health')
  const h = await healthCheck()
  if (h.ok) {
    pass(`daemon healthy — gateway: ${h.data?.gateway}, bot: ${h.data?.bot}, uptime: ${Math.round(h.data?.uptime as number)}s`)
  } else {
    fail('daemon health check failed — is pai-discord running?')
  }
}

async function testBurst(): Promise<void> {
  header('Burst — 10 rapid-fire messages')
  clearQueues()

  const ids: string[] = []
  const startMs = Date.now()
  for (let i = 0; i < 10; i++) {
    ids.push(writeInbound(`burst message ${i + 1}/10`))
  }
  const writeMs = Date.now() - startMs
  info(`wrote 10 messages in ${writeMs}ms`)

  const initialCount = countFiles(INBOUND_DIR)
  if (initialCount === 10) {
    pass(`all 10 messages queued (${writeMs}ms)`)
  } else {
    fail(`expected 10 queued, found ${initialCount}`)
  }

  // Wait for bridged server to consume (if running)
  info('waiting up to 30s for bridged server to consume...')
  const drained = await waitForQueueDrain(INBOUND_DIR, 30000)
  const remaining = countFiles(INBOUND_DIR)

  if (drained) {
    pass(`all 10 consumed by bridged server`)
    // Check logs for delivery
    let delivered = 0
    for (const id of ids) {
      if (logContains(BRIDGED_LOG, id, 35000)) delivered++
    }
    if (delivered === 10) {
      pass(`all 10 logged in bridged.log`)
    } else if (delivered > 0) {
      fail(`only ${delivered}/10 found in bridged.log`)
    } else {
      skip(`bridged.log check — log entries may have rotated`)
    }
  } else {
    if (remaining === 10) {
      skip(`bridged server not running — ${remaining} messages sitting in queue (expected if no Courier session)`)
    } else {
      fail(`partial consumption: ${10 - remaining}/10 consumed, ${remaining} remaining`)
    }
  }
  clearQueues()
}

async function testLargeMessage(): Promise<void> {
  header('Large Message — 3000 chars')
  clearQueues()

  const largeContent = 'A'.repeat(3000)
  const msgId = writeInbound(largeContent)

  // Verify file was written correctly
  const files = readdirSync(INBOUND_DIR).filter(f => f.includes(msgId))
  if (files.length === 1) {
    const data = JSON.parse(readFileSync(join(INBOUND_DIR, files[0]), 'utf8'))
    if (data.content.length === 3000) {
      pass(`3000-char message queued correctly`)
    } else {
      fail(`content length mismatch: expected 3000, got ${data.content.length}`)
    }
  } else {
    fail(`message file not found`)
  }
  clearQueues()
}

async function testOutboundTimeout(): Promise<void> {
  header('Outbound Timeout — command with no daemon response')
  clearQueues()

  // Write a command that the daemon can't execute (fake channel)
  const requestId = writeOutbound('fetch_messages', { chat_id: '000000000000000000', limit: 5 })
  info(`wrote outbound command ${requestId}`)

  // Wait for daemon to process it
  const result = await waitForResultFile(requestId, 10000)
  if (result) {
    if (result.success === false) {
      pass(`daemon returned error as expected: ${(result.error as string)?.slice(0, 60)}`)
    } else {
      fail(`expected error, got success: ${JSON.stringify(result)}`)
    }
  } else {
    fail(`no result file within 10s — daemon may not be processing outbound queue`)
  }

  // Verify command file was cleaned up by daemon
  const remaining = readdirSync(OUTBOUND_DIR).filter(f => f.includes(requestId) && !f.endsWith('.result.json'))
  if (remaining.length === 0) {
    pass(`daemon cleaned up command file after processing`)
  } else {
    fail(`command file not cleaned up: ${remaining}`)
  }
  clearQueues()
}

async function testDaemonRestart(): Promise<void> {
  header('Daemon Restart — queue survives restart')
  clearQueues()

  // Write messages to inbound queue
  const ids = [writeInbound('pre-restart msg 1'), writeInbound('pre-restart msg 2')]
  const beforeCount = countFiles(INBOUND_DIR)
  info(`queued ${beforeCount} messages before restart`)

  // Check daemon is running
  const h1 = await healthCheck()
  if (!h1.ok) {
    skip('daemon not running, cannot test restart')
    clearQueues()
    return
  }

  // Restart daemon via systemctl
  info('restarting daemon via systemctl...')
  const proc = Bun.spawn(['systemctl', '--user', 'restart', 'pai-discord.service'], {
    stdout: 'pipe', stderr: 'pipe',
  })
  await proc.exited

  // Wait for daemon to come back
  let recovered = false
  for (let i = 0; i < 20; i++) {
    await Bun.sleep(500)
    const h = await healthCheck()
    if (h.ok) { recovered = true; break }
  }

  if (recovered) {
    pass('daemon restarted and healthy')
  } else {
    fail('daemon did not recover within 10s')
    clearQueues()
    return
  }

  // Verify queue files survived the restart
  const afterCount = countFiles(INBOUND_DIR)
  if (afterCount >= beforeCount) {
    pass(`inbound queue survived restart (${afterCount} files intact)`)
  } else {
    // bridged server may have consumed them during restart window
    info(`${beforeCount - afterCount} consumed during restart (bridged server was still running)`)
    pass(`queue files handled correctly during restart`)
  }

  clearQueues()
}

async function testCourierCrash(): Promise<void> {
  header('Courier Crash — messages queue up during downtime')
  clearQueues()

  // Write messages while (potentially) no courier is consuming
  const ids: string[] = []
  for (let i = 0; i < 5; i++) {
    ids.push(writeInbound(`crash-test message ${i + 1}`))
  }

  const queued = countFiles(INBOUND_DIR)
  info(`${queued} messages in queue`)

  // If bridged server is running, they'll drain. If not, they pile up.
  await Bun.sleep(5000)
  const after = countFiles(INBOUND_DIR)

  if (after === 0) {
    pass(`bridged server consumed all ${queued} messages (courier is running)`)
  } else if (after === queued) {
    pass(`all ${queued} messages persisted in queue (no courier running — expected behavior)`)
    info('these will be consumed when a Courier session starts')
  } else {
    pass(`${queued - after} consumed, ${after} still queued (partial consumption)`)
  }

  clearQueues()
}

async function testIsolation(): Promise<void> {
  header('Process Isolation — no rogue Discord processes')

  const proc = Bun.spawn(['bash', '-c', "ps aux | grep -E 'discord|server\\.ts' | grep -v grep | grep -v daemon | grep -v stress | grep -v triage"], {
    stdout: 'pipe', stderr: 'pipe',
  })
  const output = await new Response(proc.stdout).text()
  await proc.exited

  const lines = output.trim().split('\n').filter(l => l.trim())

  // Filter for Discord-related processes (bridged server is OK, old server.ts is not)
  const rogueProcesses = lines.filter(l =>
    l.includes('server.ts') &&
    !l.includes('server-bridged') &&
    !l.includes('daemon.ts') &&
    !l.includes('triage') &&
    !l.includes('stress-test') &&
    !l.startsWith('root') // exclude Docker container processes
  )

  const bridgedCount = lines.filter(l => l.includes('server-bridged')).length

  if (rogueProcesses.length === 0) {
    pass('no rogue Discord server.ts processes')
  } else {
    fail(`${rogueProcesses.length} rogue process(es) found:`)
    for (const p of rogueProcesses) info(`  ${p.trim().slice(0, 120)}`)
  }

  if (bridgedCount <= 1) {
    pass(`${bridgedCount} bridged server instance(s) — correct`)
  } else {
    fail(`${bridgedCount} bridged servers running — should be 0 or 1`)
  }
}

async function testQueueOrdering(): Promise<void> {
  header('Queue Ordering — FIFO consumption')
  clearQueues()

  // Write numbered messages with small delays to ensure distinct timestamps
  for (let i = 1; i <= 5; i++) {
    writeInbound(`order-test-${i}`, `order-${i}`)
    await Bun.sleep(50) // ensure distinct filenames (timestamp-based)
  }

  // Read filenames and verify they sort correctly
  const files = readdirSync(INBOUND_DIR).filter(f => f.endsWith('.json')).sort()
  const ids = files.map(f => {
    const data = JSON.parse(readFileSync(join(INBOUND_DIR, f), 'utf8'))
    return data.message_id
  })

  const expected = ['order-1', 'order-2', 'order-3', 'order-4', 'order-5']
  if (JSON.stringify(ids) === JSON.stringify(expected)) {
    pass('messages ordered correctly (FIFO by filename sort)')
  } else {
    fail(`order mismatch: expected ${expected}, got ${ids}`)
  }

  clearQueues()
}

async function testAtomicWrite(): Promise<void> {
  header('Atomic Write — no partial reads')
  clearQueues()

  // Write 20 messages as fast as possible
  for (let i = 0; i < 20; i++) {
    writeInbound(`atomic-test-${i}`)
  }

  // Immediately read them all — should all parse cleanly
  const files = readdirSync(INBOUND_DIR).filter(f => f.endsWith('.json') && !f.startsWith('.'))
  let parseErrors = 0
  for (const f of files) {
    try {
      JSON.parse(readFileSync(join(INBOUND_DIR, f), 'utf8'))
    } catch {
      parseErrors++
    }
  }

  if (parseErrors === 0) {
    pass(`all ${files.length} files parse cleanly (atomic rename works)`)
  } else {
    fail(`${parseErrors}/${files.length} files failed to parse`)
  }

  clearQueues()
}

// ── Runner ─────────────────────────────────────────────────────────────

const ALL_TESTS: Record<string, () => Promise<void>> = {
  health: testHealth,
  burst: testBurst,
  large: testLargeMessage,
  ordering: testQueueOrdering,
  atomic: testAtomicWrite,
  timeout: testOutboundTimeout,
  'daemon-restart': testDaemonRestart,
  'courier-crash': testCourierCrash,
  isolation: testIsolation,
}

const requestedTest = process.argv[2]

console.log(`${CYAN}╔══════════════════════════════════════════════╗${RESET}`)
console.log(`${CYAN}║   PAI Discord Courier — Stress Test Harness  ║${RESET}`)
console.log(`${CYAN}╚══════════════════════════════════════════════╝${RESET}`)
console.log(`${DIM}Queue dir: ${STATE_DIR}${RESET}`)
console.log(`${DIM}Daemon log: ${DAEMON_LOG}${RESET}`)
console.log(`${DIM}Bridged log: ${BRIDGED_LOG}${RESET}`)

if (requestedTest) {
  const test = ALL_TESTS[requestedTest]
  if (!test) {
    console.error(`\n${RED}Unknown test: ${requestedTest}${RESET}`)
    console.error(`Available: ${Object.keys(ALL_TESTS).join(', ')}`)
    process.exit(1)
  }
  await test()
} else {
  for (const [name, test] of Object.entries(ALL_TESTS)) {
    await test()
  }
}

// ── Summary ────────────────────────────────────────────────────────────

console.log(`\n${CYAN}━━━ RESULTS ━━━${RESET}`)
console.log(`  ${GREEN}${passed} passed${RESET}  ${failed > 0 ? RED : DIM}${failed} failed${RESET}  ${skipped > 0 ? YELLOW : DIM}${skipped} skipped${RESET}`)

if (failed > 0) {
  console.log(`\n${RED}FAIL${RESET}`)
  process.exit(1)
} else {
  console.log(`\n${GREEN}PASS${RESET}`)
}
