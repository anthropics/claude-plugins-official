#!/usr/bin/env bun
import { Server } from '@modelcontextprotocol/sdk/server/index.js'
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js'
import { ListToolsRequestSchema, CallToolRequestSchema } from '@modelcontextprotocol/sdk/types.js'
import * as lark from '@larksuiteoapi/node-sdk'
import * as fs from 'fs'
import * as path from 'path'
import * as os from 'os'
import * as crypto from 'crypto'

// ── Config paths ───────────────────────────────────────────────────────────────
const CONFIG_DIR  = path.join(os.homedir(), '.claude', 'channels', 'feishu')
const ENV_FILE    = path.join(CONFIG_DIR, '.env')
const ACCESS_FILE = path.join(CONFIG_DIR, 'access.json')
const APPROVED_DIR = path.join(CONFIG_DIR, 'approved')

// ── .env loader ────────────────────────────────────────────────────────────────
function loadEnvFile(filePath: string): Record<string, string> {
  try {
    const result: Record<string, string> = {}
    for (const line of fs.readFileSync(filePath, 'utf8').split('\n')) {
      const t = line.trim()
      if (!t || t.startsWith('#')) continue
      const idx = t.indexOf('=')
      if (idx === -1) continue
      result[t.slice(0, idx).trim()] = t.slice(idx + 1).trim()
    }
    return result
  } catch { return {} }
}

// ── Access control ─────────────────────────────────────────────────────────────
interface PendingEntry { senderId: string; chatId: string; createdAt: number; expiresAt: number }
interface AccessConfig {
  dmPolicy: 'pairing' | 'allowlist' | 'disabled'
  allowFrom: string[]
  pending: Record<string, PendingEntry>
}

function loadAccess(): AccessConfig {
  try { return JSON.parse(fs.readFileSync(ACCESS_FILE, 'utf8')) }
  catch { return { dmPolicy: 'pairing', allowFrom: [], pending: {} } }
}

function saveAccess(cfg: AccessConfig) {
  fs.mkdirSync(path.dirname(ACCESS_FILE), { recursive: true })
  fs.writeFileSync(ACCESS_FILE, JSON.stringify(cfg, null, 2))
}

// ── Credentials ────────────────────────────────────────────────────────────────
const envVars   = loadEnvFile(ENV_FILE)
const APP_ID     = process.env.FEISHU_APP_ID     || envVars.FEISHU_APP_ID     || ''
const APP_SECRET = process.env.FEISHU_APP_SECRET || envVars.FEISHU_APP_SECRET || ''

if (!APP_ID || !APP_SECRET) {
  process.stderr.write(`Feishu channel: credentials missing.\nSet FEISHU_APP_ID and FEISHU_APP_SECRET in ${ENV_FILE}\n`)
  process.exit(1)
}

// ── Feishu client ──────────────────────────────────────────────────────────────
const feishu = new lark.Client({ appId: APP_ID, appSecret: APP_SECRET })

async function sendText(chatId: string, text: string) {
  await feishu.im.message.create({
    params: { receive_id_type: 'chat_id' },
    data: { receive_id: chatId, msg_type: 'text', content: JSON.stringify({ text }) },
  })
}

async function sendTextToUser(openId: string, text: string) {
  await feishu.im.message.create({
    params: { receive_id_type: 'open_id' },
    data: { receive_id: openId, msg_type: 'text', content: JSON.stringify({ text }) },
  })
}

// ── Poll approved dir (written by /feishu:access pair skill) ──────────────────
fs.mkdirSync(APPROVED_DIR, { recursive: true })
setInterval(() => {
  try {
    for (const file of fs.readdirSync(APPROVED_DIR)) {
      const filePath = path.join(APPROVED_DIR, file)
      try {
        const chatId = fs.readFileSync(filePath, 'utf8').trim()
        fs.unlinkSync(filePath)
        sendText(chatId, '✅ 配对成功！现在可以和 Claude Code 对话了。').catch(() => {})
      } catch {}
    }
  } catch {}
}, 1000)

// ── Dedup ──────────────────────────────────────────────────────────────────────
const seen = new Set<string>()

// ── Startup notification ────────────────────────────────────────────────────────
let startupNotified = false
function notifyStartup() {
  if (startupNotified) return
  const access = loadAccess()
  if (!access.allowFrom.length) return
  startupNotified = true
  const chatId = fs.existsSync(path.join(CONFIG_DIR, 'last_chat_id'))
    ? fs.readFileSync(path.join(CONFIG_DIR, 'last_chat_id'), 'utf8').trim()
    : null
  if (chatId) {
    sendText(chatId, '✅ Claude Code 已就绪，可以发消息了').catch(() => {})
  }
}

// ── MCP server ─────────────────────────────────────────────────────────────────
const mcp = new Server(
  { name: 'feishu', version: '0.0.1' },
  {
    capabilities: {
      experimental: { 'claude/channel': {} },
      tools: {},
    },
    instructions: `You are connected to Feishu (飞书). Messages arrive as <channel source="feishu" chat_id="..." sender_id="..." message_id="...">text</channel>. Reply with the reply tool using the chat_id from the tag. Use plain text only, no Markdown.`,
  },
)

mcp.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [{
    name: 'reply',
    description: 'Send a text message back to a Feishu conversation',
    inputSchema: {
      type: 'object',
      properties: {
        chat_id:  { type: 'string', description: 'chat_id from the channel event' },
        text:     { type: 'string', description: 'Message text to send' },
      },
      required: ['chat_id', 'text'],
    },
  }],
}))

mcp.setRequestHandler(CallToolRequestSchema, async req => {
  if (req.params.name === 'reply') {
    const { chat_id, text } = req.params.arguments as { chat_id: string; text: string }
    await sendText(chat_id, text)
    return { content: [{ type: 'text', text: 'sent' }] }
  }
  throw new Error(`unknown tool: ${req.params.name}`)
})

await mcp.connect(new StdioServerTransport())

// ── WebSocket long connection ──────────────────────────────────────────────────
const ws = new lark.WSClient({
  appId: APP_ID,
  appSecret: APP_SECRET,
  loggerLevel: lark.LoggerLevel.info,
  wsConfig: { PingInterval: 30, PingTimeout: 5 },
})

ws.start({
  eventDispatcher: new lark.EventDispatcher({}).register({
    'im.message.receive_v1': async (data: any) => {
      try {
        const senderId  = data.sender?.sender_id?.open_id
        const chatId    = data.message?.chat_id
        const msgType   = data.message?.message_type
        const messageId = data.message?.message_id

        if (!senderId || !chatId || msgType !== 'text') return
        if (seen.has(messageId)) return
        seen.add(messageId)
        if (seen.size > 500) {
          const first = seen.values().next().value
          if (first) seen.delete(first)
        }

        const parsed = JSON.parse(data.message?.content || '{}')
        const text = (parsed.text || '').trim()
        if (!text) return

        const access = loadAccess()

        if (access.allowFrom.includes(senderId)) {
          // 记录最后一个 chat_id，用于启动通知
          fs.writeFileSync(path.join(CONFIG_DIR, 'last_chat_id'), chatId)

          // /ping 直接处理，不走 Claude
          if (text === '/ping') {
            await sendText(chatId, '🟢 Claude Code 在线')
            return
          }

          // 收到消息立即 ack
          await sendText(chatId, '⏳ 收到，处理中...').catch(() => {})

          await mcp.notification({
            method: 'notifications/claude/channel',
            params: {
              content: text,
              meta: { chat_id: chatId, sender_id: senderId, message_id: messageId },
            },
          })
          return
        }

        if (access.dmPolicy === 'disabled') return

        if (access.dmPolicy === 'pairing') {
          // Clean expired
          const now = Date.now()
          for (const [code, entry] of Object.entries(access.pending)) {
            if (entry.expiresAt < now) delete access.pending[code]
          }
          // Generate new code
          const code = crypto.randomBytes(3).toString('hex')
          access.pending[code] = { senderId, chatId, createdAt: now, expiresAt: now + 3_600_000 }
          saveAccess(access)

          await sendTextToUser(senderId,
            `配对码：${code}\n\n请在 Claude Code 中运行：\n/feishu:access pair ${code}`)
        }
      } catch (err) {
        process.stderr.write(`[feishu] message error: ${err}\n`)
      }
    },
  }),
})

process.stderr.write(`[feishu] channel started (${APP_ID.slice(0, 8)}...)\n`)
setTimeout(notifyStartup, 3000)
