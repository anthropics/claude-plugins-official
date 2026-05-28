#!/usr/bin/env node
// discord-tool-notify.js — PreToolUse hook
// Posts a tool-execution notification to Discord before each tool runs.

const { readFileSync, writeFileSync } = require('fs')
const { request } = require('https')
const { join } = require('path')
const { homedir } = require('os')

const claudeDir = process.env.CLAUDE_CONFIG_DIR || join(homedir(), '.claude')
const personaPath = join(claudeDir, 'persona.md')
const tokenFile = join(claudeDir, 'discord-token')

function readFrontmatter(content) {
  const match = content.match(/^---\n([\s\S]*?)\n---/)
  if (!match) return {}
  const result = {}
  for (const line of match[1].split('\n')) {
    const m = line.match(/^(\w+):\s*"?([^"]*)"?\s*$/)
    if (m) result[m[1]] = m[2].trim()
  }
  return result
}

let persona = {}
try { persona = readFrontmatter(readFileSync(personaPath, 'utf8')) } catch {}

const channel = persona.discord_channel || ''
if (!channel) process.exit(0)

let token = ''
try { token = readFileSync(tokenFile, 'utf8').trim() } catch {}
if (!token) process.exit(0)

// Whitelist: only report tools we explicitly handle. Anything else (MCP tools,
// internal tools, future tools) is silently dropped — no noisy fallback.
function format(tool, inp) {
  if (tool === 'Bash') {
    const cmd = ((inp.command || '').split('\n')[0]).slice(0, 120)
    return `🔧 **Bash** \`${cmd}\``
  }
  if (tool === 'Read')      return `📖 **Read** \`${inp.file_path || ''}\``
  if (tool === 'Edit')      return `✏️ **Edit** \`${inp.file_path || ''}\``
  if (tool === 'Write')     return `📝 **Write** \`${inp.file_path || ''}\``
  if (tool === 'Agent') {
    const desc = (inp.description || inp.prompt || '').slice(0, 100)
    return `🤖 **Agent** — ${desc}`
  }
  if (tool === 'WebFetch')  return `🌐 **WebFetch** ${(inp.url || '').slice(0, 80)}`
  if (tool === 'WebSearch') return `🔍 **WebSearch** ${(inp.query || '').slice(0, 80)}`
  if (tool.startsWith('Task')) return `📋 **${tool}**`
  return ''
}

let raw = ''
process.stdin.on('data', chunk => { raw += chunk })
process.stdin.on('end', () => {
  let payload = {}
  try { payload = JSON.parse(raw) } catch { process.exit(0) }

  const tool = payload.tool_name || 'unknown'
  const inp = payload.tool_input || {}

  const msg = format(tool, inp)
  if (!msg) process.exit(0)

  const body = JSON.stringify({ content: msg, allowed_mentions: { parse: [] } })
  const req = request({
    hostname: 'discord.com',
    path: `/api/v10/channels/${channel}/messages`,
    method: 'POST',
    headers: {
      'Authorization': `Bot ${token}`,
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(body),
    },
  }, res => {
    let data = ''
    res.on('data', chunk => { data += chunk })
    res.on('end', () => {
      try {
        const json = JSON.parse(data)
        if (json.id) {
          writeFileSync('/tmp/deet-tool-notify-last', JSON.stringify({ msg_id: json.id, channel }))
        }
      } catch {}
      process.exit(0)
    })
  })
  req.on('error', () => process.exit(0))
  req.write(body)
  req.end()

  setTimeout(() => process.exit(0), 2000)
})
