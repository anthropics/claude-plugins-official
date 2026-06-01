/**
 * Standalone Telegram poller for the claude-tg-agent channel.
 *
 * Why a separate process: on bun/node (aarch64) the MCP StdioServerTransport
 * stdin watcher inside server.ts starves an in-process grammy poll loop once
 * Claude drives the MCP connection — the loop silently never fires (even
 * setTimeout timers stall), so inbound updates are never consumed. This process
 * has an idle stdin and is unaffected; it long-polls getUpdates and forwards
 * each raw update to server.ts's /update HTTP endpoint, where bot.handleUpdate
 * runs network-driven (which IS serviced) and reuses all gate / pairing /
 * command logic + channel delivery.
 *
 * It is the SOLE getUpdates consumer for the token (server.ts no longer polls),
 * so there is no 409 conflict between the two processes.
 */
import { Bot } from 'grammy'
import { readFileSync, writeFileSync, mkdirSync, chmodSync } from 'fs'
import { join } from 'path'
import { request } from 'node:http'

const STATE_DIR =
  process.env.TELEGRAM_STATE_DIR ||
  join(process.env.HOME || '', '.claude', 'channels', 'telegram')
const ENV_FILE = join(STATE_DIR, '.env')
const PID_FILE = join(STATE_DIR, 'poller.pid')
const INJECT_PORT = parseInt(process.env.INJECT_PORT ?? '7842', 10)

// Load STATE_DIR/.env (real env wins) — same convention as server.ts.
try {
  chmodSync(ENV_FILE, 0o600)
  for (const line of readFileSync(ENV_FILE, 'utf8').split('\n')) {
    const m = line.match(/^(\w+)=(.*)$/)
    if (m && process.env[m[1]] === undefined) process.env[m[1]] = m[2]
  }
} catch {}

const TOKEN = process.env.TELEGRAM_BOT_TOKEN
if (!TOKEN) {
  process.stderr.write(`telegram poller: TELEGRAM_BOT_TOKEN required (set in ${ENV_FILE})\n`)
  process.exit(1)
}

// Replace any stale poller so a restart takes over the single getUpdates slot.
mkdirSync(STATE_DIR, { recursive: true, mode: 0o700 })
try {
  const stale = parseInt(readFileSync(PID_FILE, 'utf8'), 10)
  if (stale > 1 && stale !== process.pid) {
    process.kill(stale, 0)
    process.stderr.write(`telegram poller: replacing stale poller pid=${stale}\n`)
    process.kill(stale, 'SIGTERM')
  }
} catch {}
writeFileSync(PID_FILE, String(process.pid))

let shuttingDown = false
const shutdown = () => {
  shuttingDown = true
  process.exit(0)
}
process.on('SIGTERM', shutdown)
process.on('SIGINT', shutdown)

const bot = new Bot(TOKEN)

function forwardUpdate(update: unknown, me: unknown): Promise<boolean> {
  return new Promise(resolve => {
    const payload = JSON.stringify({ update, me })
    const req = request(
      {
        host: '127.0.0.1',
        port: INJECT_PORT,
        path: '/update',
        method: 'POST',
        headers: {
          'content-type': 'application/json',
          'content-length': Buffer.byteLength(payload),
        },
      },
      res => {
        res.resume()
        res.on('end', () => resolve(res.statusCode === 200))
      },
    )
    req.on('error', err => {
      process.stderr.write(`telegram poller: forward failed (server down?): ${err}\n`)
      resolve(false)
    })
    req.write(payload)
    req.end()
  })
}

async function main() {
  await bot.init()
  const me = bot.botInfo
  process.stderr.write(`telegram poller: polling as @${me.username}\n`)
  void bot.api
    .setMyCommands(
      [
        { command: 'start', description: 'Welcome and setup guide' },
        { command: 'help', description: 'What this bot can do' },
        { command: 'status', description: 'Check your pairing status' },
      ],
      { scope: { type: 'all_private_chats' } },
    )
    .catch(() => {})

  let offset: number | undefined
  while (!shuttingDown) {
    try {
      const updates = await bot.api.getUpdates({ offset, timeout: 25 })
      for (const update of updates) {
        offset = update.update_id + 1
        await forwardUpdate(update, me)
      }
    } catch (err) {
      const is409 = (err as { error_code?: number })?.error_code === 409
      const delay = is409 ? 3000 : 1000
      process.stderr.write(
        `telegram poller: ${is409 ? '409 Conflict' : `poll error: ${err}`}, retrying in ${delay / 1000}s\n`,
      )
      await new Promise(r => setTimeout(r, delay))
    }
  }
}

main().catch(err => {
  process.stderr.write(`telegram poller: fatal: ${err}\n`)
  process.exit(1)
})
