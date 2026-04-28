#!/usr/bin/env bun
/**
 * Fake chat for Claude Code.
 *
 * Localhost web UI for testing the channel contract. No external service,
 * no tokens, no access control.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js'
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js'
import {
  ListToolsRequestSchema,
  CallToolRequestSchema,
} from '@modelcontextprotocol/sdk/types.js'
import { readFileSync, writeFileSync, mkdirSync, statSync, copyFileSync } from 'fs'
import { homedir } from 'os'
import { join, extname, basename } from 'path'
import type { ServerWebSocket } from 'bun'

const PORT = Number(process.env.FAKECHAT_PORT ?? 8787)
const STATE_DIR = join(homedir(), '.claude', 'channels', 'fakechat')
const INBOX_DIR = join(STATE_DIR, 'inbox')
const OUTBOX_DIR = join(STATE_DIR, 'outbox')

type Msg = {
  id: string
  from: 'user' | 'assistant'
  text: string
  ts: number
  replyTo?: string
  file?: { url: string; name: string }
}

type Wire =
  | ({ type: 'msg' } & Msg)
  | { type: 'edit'; id: string; text: string }

const clients = new Set<ServerWebSocket<unknown>>()
let seq = 0

function nextId() {
  return `m${Date.now()}-${++seq}`
}

function broadcast(m: Wire) {
  const data = JSON.stringify(m)
  for (const ws of clients) if (ws.readyState === 1) ws.send(data)
}

function mime(ext: string) {
  const m: Record<string, string> = {
    '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
    '.gif': 'image/gif', '.webp': 'image/webp', '.svg': 'image/svg+xml',
    '.pdf': 'application/pdf', '.txt': 'text/plain',
  }
  return m[ext] ?? 'application/octet-stream'
}

const mcp = new Server(
  { name: 'fakechat', version: '0.1.0' },
  {
    capabilities: { tools: {}, experimental: { 'claude/channel': {} } },
    instructions: `The sender reads the fakechat UI, not this session. Anything you want them to see must go through the reply tool — your transcript output never reaches the UI.\n\nMessages from the fakechat web UI arrive as <channel source="fakechat" chat_id="web" message_id="...">. If the tag has a file_path attribute, Read that file — it is an upload from the UI. Reply with the reply tool. UI is at http://localhost:${PORT}.`,
  },
)

mcp.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: 'reply',
      description: 'Send a message to the fakechat UI. Pass reply_to for quote-reply, files for attachments.',
      inputSchema: {
        type: 'object',
        properties: {
          text: { type: 'string' },
          reply_to: { type: 'string' },
          files: { type: 'array', items: { type: 'string' } },
        },
        required: ['text'],
      },
    },
    {
      name: 'edit_message',
      description: 'Edit a previously sent message.',
      inputSchema: {
        type: 'object',
        properties: { message_id: { type: 'string' }, text: { type: 'string' } },
        required: ['message_id', 'text'],
      },
    },
  ],
}))

mcp.setRequestHandler(CallToolRequestSchema, async req => {
  const args = (req.params.arguments ?? {}) as Record<string, unknown>
  try {
    switch (req.params.name) {
      case 'reply': {
        const text = args.text as string
        const replyTo = args.reply_to as string | undefined
        const files = (args.files as string[] | undefined) ?? []
        const ids: string[] = []

        // Text + files collapse into a single message, matching the client's [filename]-under-text rendering.
        mkdirSync(OUTBOX_DIR, { recursive: true })
        let file: { url: string; name: string } | undefined
        if (files[0]) {
          const f = files[0]
          const st = statSync(f)
          if (st.size > 50 * 1024 * 1024) throw new Error(`file too large: ${f}`)
          const ext = extname(f).toLowerCase()
          const out = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}${ext}`
          copyFileSync(f, join(OUTBOX_DIR, out))
          file = { url: `/files/${out}`, name: basename(f) }
        }
        const id = nextId()
        broadcast({ type: 'msg', id, from: 'assistant', text, ts: Date.now(), replyTo, file })
        ids.push(id)
        return { content: [{ type: 'text', text: `sent (${ids.join(', ')})` }] }
      }
      case 'edit_message': {
        broadcast({ type: 'edit', id: args.message_id as string, text: args.text as string })
        return { content: [{ type: 'text', text: 'ok' }] }
      }
      default:
        return { content: [{ type: 'text', text: `unknown: ${req.params.name}` }], isError: true }
    }
  } catch (err) {
    return { content: [{ type: 'text', text: `${req.params.name}: ${err instanceof Error ? err.message : err}` }], isError: true }
  }
})

await mcp.connect(new StdioServerTransport())

function deliver(id: string, text: string, file?: { path: string; name: string }): void {
  // file_path goes in meta only — an in-content "[attached — Read: PATH]"
  // annotation is forgeable by typing that string into the UI.
  void mcp.notification({
    method: 'notifications/claude/channel',
    params: {
      content: text || `(${file?.name ?? 'attachment'})`,
      meta: {
        chat_id: 'web', message_id: id, user: 'web', ts: new Date().toISOString(),
        ...(file ? { file_path: file.path } : {}),
      },
    },
  })
}

Bun.serve({
  port: PORT,
  hostname: '127.0.0.1',
  fetch(req, server) {
    const url = new URL(req.url)

    if (url.pathname === '/ws') {
      if (server.upgrade(req)) return
      return new Response('upgrade failed', { status: 400 })
    }

    if (url.pathname.startsWith('/files/')) {
      const f = url.pathname.slice(7)
      if (f.includes('..') || f.includes('/')) return new Response('bad', { status: 400 })
      try {
        return new Response(readFileSync(join(OUTBOX_DIR, f)), {
          headers: { 'content-type': mime(extname(f).toLowerCase()) },
        })
      } catch {
        return new Response('404', { status: 404 })
      }
    }

    if (url.pathname === '/upload' && req.method === 'POST') {
      return (async () => {
        const form = await req.formData()
        const id = String(form.get('id') ?? '')
        const text = String(form.get('text') ?? '')
        const f = form.get('file')
        if (!id) return new Response('missing id', { status: 400 })
        let file: { path: string; name: string } | undefined
        if (f instanceof File && f.size > 0) {
          mkdirSync(INBOX_DIR, { recursive: true })
          const ext = extname(f.name).toLowerCase() || '.bin'
          const path = join(INBOX_DIR, `${Date.now()}${ext}`)
          writeFileSync(path, Buffer.from(await f.arrayBuffer()))
          file = { path, name: f.name }
        }
        deliver(id, text, file)
        return new Response(null, { status: 204 })
      })()
    }

    if (url.pathname === '/') {
      return new Response(HTML, { headers: { 'content-type': 'text/html; charset=utf-8' } })
    }
    return new Response('404', { status: 404 })
  },
  websocket: {
    open: ws => { clients.add(ws) },
    close: ws => { clients.delete(ws) },
    message: (_, raw) => {
      try {
        const { id, text } = JSON.parse(String(raw)) as { id: string; text: string }
        if (id && text?.trim()) deliver(id, text.trim())
      } catch {}
    },
  },
})

process.stderr.write(`fakechat: http://localhost:${PORT}\n`)

const HTML = `<!doctype html>
<meta charset="utf-8">
<title>fakechat</title>
<style>
body { font-family: monospace; margin: 0; padding: 1em 1em 7em; }
#log { white-space: pre-wrap; word-break: break-word; }
form { position: fixed; bottom: 0; left: 0; right: 0; padding: 1em; background: #fff; }
#text { width: 100%; box-sizing: border-box; font: inherit; margin-bottom: 0.5em; }
#file { display: none; }
#row { display: flex; gap: 1ch; }
#row button[type=submit] { margin-left: auto; }
</style>
<h3>fakechat</h3>
<pre id=log></pre>
<form id=form>
  <textarea id=text rows=2 autocomplete=off autofocus></textarea>
  <div id=row>
    <button type=button onclick="file.click()">attach</button><input type=file id=file>
    <span id=chip></span>
    <button type=submit>send</button>
  </div>
</form>

<script>
const log = document.getElementById('log')
document.getElementById('file').onchange = e => { const f = e.target.files[0]; chip.textContent = f ? '[' + f.name + ']' : '' }
const form = document.getElementById('form')
const input = document.getElementById('text')
const fileIn = document.getElementById('file')
const chip = document.getElementById('chip')
const msgs = {}

const ws = new WebSocket('ws://' + location.host + '/ws')
ws.onmessage = e => {
  const m = JSON.parse(e.data)
  if (m.type === 'msg') add(m)
  if (m.type === 'edit') { const x = msgs[m.id]; if (x) { x.body.textContent = m.text + ' (edited)' } }
}

let uid = 0
form.onsubmit = e => {
  e.preventDefault()
  const text = input.value.trim()
  const file = fileIn.files[0]
  if (!text && !file) return
  input.value = ''; fileIn.value = ''; chip.textContent = ''
  const id = 'u' + Date.now() + '-' + (++uid)
  add({ id, from: 'user', text, file: file ? { url: URL.createObjectURL(file), name: file.name } : undefined })
  if (file) {
    const fd = new FormData(); fd.set('id', id); fd.set('text', text); fd.set('file', file)
    fetch('/upload', { method: 'POST', body: fd })
  } else {
    ws.send(JSON.stringify({ id, text }))
  }
}

function add(m) {
  const who = m.from === 'user' ? 'you' : 'bot'
  const el = line(who, m.text, m.replyTo, m.file)
  log.appendChild(el); scroll()
  msgs[m.id] = { body: el.querySelector('.body') }
}

function line(who, text, replyTo, file) {
  const div = document.createElement('div')
  const t = new Date().toTimeString().slice(0, 8)
  const reply = replyTo && msgs[replyTo] ? ' ↳ ' + (msgs[replyTo].body.textContent || '(file)').slice(0, 40) : ''
  div.innerHTML = '[' + t + '] <b>' + who + '</b>' + reply + ': <span class=body></span>'
  const body = div.querySelector('.body')
  body.textContent = text || ''
  if (file) {
    const indent = 11 + who.length + 2  // '[HH:MM:SS] ' + who + ': '
    if (text) body.appendChild(document.createTextNode('\\n' + ' '.repeat(indent)))
    const a = document.createElement('a')
    a.href = file.url; a.download = file.name; a.textContent = '[' + file.name + ']'
    body.appendChild(a)
  }
  return div
}

function scroll() { window.scrollTo(0, document.body.scrollHeight) }
input.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); form.requestSubmit() } })
</script>
`
