/**
 * MCP tool definitions and handlers for the Feishu channel.
 *
 * Exposes 5 tools: reply, react, edit_message, fetch_messages, download_attachment.
 */

import type { Server } from '@modelcontextprotocol/sdk/server/index.js'
import {
  ListToolsRequestSchema,
  CallToolRequestSchema,
} from '@modelcontextprotocol/sdk/types.js'
import { readFileSync, writeFileSync, mkdirSync, statSync } from 'fs'
import { join } from 'path'
import type { Access } from './access.js'
import {
  STATE_DIR,
  INBOX_DIR,
  loadAccess,
} from './access.js'
import {
  chunk,
  assertSendable,
  safeAttName,
  fileTypeFromExt,
  isImageExt,
  noteSent,
  MAX_CHUNK_LIMIT,
  MAX_ATTACHMENT_BYTES,
} from './message.js'

// ── Types ──────────────────────────────────────────────────────────────────

type FeishuClient = {
  im: {
    message: {
      create: (req: any) => Promise<any>
      reply: (req: any) => Promise<any>
      patch: (req: any) => Promise<any>
      list: (req: any) => Promise<any>
      get: (req: any) => Promise<any>
    }
    messageReaction: {
      create: (req: any) => Promise<any>
    }
    messageResource: {
      get: (req: any) => Promise<any>
    }
    file: {
      create: (req: any) => Promise<any>
      get: (req: any) => Promise<any>
    }
    image: {
      create: (req: any) => Promise<any>
      get: (req: any) => Promise<any>
    }
    chat: {
      get: (req: any) => Promise<any>
    }
  }
}

type ChatTypeMap = Map<string, 'p2p' | 'group'>

// ── Outbound validation ────────────────────────────────────────────────────

async function fetchAllowedChat(
  chatId: string,
  client: FeishuClient,
  chatTypeMap: ChatTypeMap,
): Promise<void> {
  const access = loadAccess()
  let chatType = chatTypeMap.get(chatId)

  if (!chatType) {
    // Fall back to API lookup
    try {
      const res = await client.im.chat.get({ path: { chat_id: chatId } })
      chatType = res?.data?.chat_type === 'p2p' ? 'p2p' : 'group'
      chatTypeMap.set(chatId, chatType)
    } catch {
      throw new Error(`chat ${chatId} not found or inaccessible`)
    }
  }

  if (chatType === 'p2p') {
    // For p2p, we check if any allowFrom entry maps to this chat.
    // Since inbound events populate chatTypeMap, the chat must have been
    // seen from an allowed sender. If we got here via API fallback,
    // we can't verify the sender — accept if allowFrom is non-empty.
    if (access.allowFrom.length === 0) {
      throw new Error(`chat ${chatId} is not allowlisted — add via /feishu:access`)
    }
  } else {
    if (!(chatId in access.groups)) {
      throw new Error(`chat ${chatId} is not allowlisted — add via /feishu:access group add`)
    }
  }
}

// ── Tool registration ──────────────────────────────────────────────────────

export function registerTools(
  mcp: Server,
  client: FeishuClient,
  recentSentIds: Set<string>,
  chatTypeMap: ChatTypeMap,
): void {
  mcp.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: [
      {
        name: 'reply',
        description:
          'Reply on Feishu. Pass chat_id from the inbound message. Optionally pass reply_to (message_id) for threading, and files (absolute paths) to attach images or other files.',
        inputSchema: {
          type: 'object',
          properties: {
            chat_id: { type: 'string' },
            text: { type: 'string' },
            reply_to: {
              type: 'string',
              description:
                'Message ID to thread under. Use message_id from the inbound <channel> block, or an id from fetch_messages.',
            },
            files: {
              type: 'array',
              items: { type: 'string' },
              description:
                'Absolute file paths to attach (images, logs, etc). Max 10 files, 25MB each. Images and files are sent as separate messages.',
            },
          },
          required: ['chat_id', 'text'],
        },
      },
      {
        name: 'react',
        description:
          'Add an emoji reaction to a Feishu message. Use Feishu emoji_type strings like "THUMBSUP", "SMILE", "JIAYI" — not Unicode emoji.',
        inputSchema: {
          type: 'object',
          properties: {
            chat_id: { type: 'string' },
            message_id: { type: 'string' },
            emoji: {
              type: 'string',
              description: 'Feishu emoji_type string, e.g. "THUMBSUP".',
            },
          },
          required: ['chat_id', 'message_id', 'emoji'],
        },
      },
      {
        name: 'edit_message',
        description:
          'Edit a message the bot previously sent. Useful for progress updates (send "working…" then edit to the result). Only works on text and post messages.',
        inputSchema: {
          type: 'object',
          properties: {
            chat_id: { type: 'string' },
            message_id: { type: 'string' },
            text: { type: 'string' },
          },
          required: ['chat_id', 'message_id', 'text'],
        },
      },
      {
        name: 'download_attachment',
        description:
          'Download attachments from a specific Feishu message to the local inbox. Use after fetch_messages shows a message has attachments (marked with +Natt). Returns file paths ready to Read.',
        inputSchema: {
          type: 'object',
          properties: {
            chat_id: { type: 'string' },
            message_id: { type: 'string' },
          },
          required: ['chat_id', 'message_id'],
        },
      },
      {
        name: 'fetch_messages',
        description:
          'Fetch recent messages from a Feishu chat. Returns oldest-first with message IDs.',
        inputSchema: {
          type: 'object',
          properties: {
            channel: { type: 'string' },
            limit: {
              type: 'number',
              description: 'Max messages (default 20, max 50).',
            },
          },
          required: ['channel'],
        },
      },
    ],
  }))

  mcp.setRequestHandler(CallToolRequestSchema, async (req) => {
    const args = (req.params.arguments ?? {}) as Record<string, unknown>
    try {
      switch (req.params.name) {
        // ── reply ──────────────────────────────────────────────────
        case 'reply': {
          const chat_id = args.chat_id as string
          const text = args.text as string
          const reply_to = args.reply_to as string | undefined
          const files = (args.files as string[] | undefined) ?? []

          await fetchAllowedChat(chat_id, client, chatTypeMap)

          // Validate files
          for (const f of files) {
            assertSendable(f, STATE_DIR)
            const st = statSync(f)
            if (st.size > MAX_ATTACHMENT_BYTES) {
              throw new Error(
                `file too large: ${f} (${(st.size / 1024 / 1024).toFixed(1)}MB, max 25MB)`,
              )
            }
          }
          if (files.length > 10) throw new Error('max 10 attachments per message')

          const access = loadAccess()
          const limit = Math.max(1, Math.min(access.textChunkLimit ?? MAX_CHUNK_LIMIT, MAX_CHUNK_LIMIT))
          const mode = access.chunkMode ?? 'newline'
          const replyMode = access.replyToMode ?? 'first'
          const chunks = chunk(text, limit, mode)
          const sentIds: string[] = []

          // Send text chunks
          for (let i = 0; i < chunks.length; i++) {
            const shouldReplyTo =
              reply_to != null &&
              replyMode !== 'off' &&
              (replyMode === 'all' || i === 0)

            let res: any
            if (shouldReplyTo) {
              res = await client.im.message.reply({
                path: { message_id: reply_to },
                data: {
                  content: JSON.stringify({ text: chunks[i] }),
                  msg_type: 'text',
                },
              })
            } else {
              res = await client.im.message.create({
                params: { receive_id_type: 'chat_id' },
                data: {
                  receive_id: chat_id,
                  content: JSON.stringify({ text: chunks[i] }),
                  msg_type: 'text',
                },
              })
            }
            const msgId = res?.data?.message_id
            if (msgId) {
              noteSent(msgId, recentSentIds)
              sentIds.push(msgId)
            }
          }

          // Upload and send file attachments
          for (const f of files) {
            const name = f.split('/').pop() ?? 'file'
            const ext = name.includes('.') ? name.slice(name.lastIndexOf('.') + 1) : ''

            if (isImageExt(ext)) {
              const imgRes = await client.im.image.create({
                data: {
                  image_type: 'message',
                  image: readFileSync(f),
                },
              })
              const imageKey = imgRes?.data?.image_key
              if (imageKey) {
                const sendRes = await client.im.message.create({
                  params: { receive_id_type: 'chat_id' },
                  data: {
                    receive_id: chat_id,
                    content: JSON.stringify({ image_key: imageKey }),
                    msg_type: 'image',
                  },
                })
                const msgId = sendRes?.data?.message_id
                if (msgId) {
                  noteSent(msgId, recentSentIds)
                  sentIds.push(msgId)
                }
              }
            } else {
              const fileRes = await client.im.file.create({
                data: {
                  file_type: fileTypeFromExt(ext),
                  file_name: name,
                  file: readFileSync(f),
                },
              })
              const fileKey = fileRes?.data?.file_key
              if (fileKey) {
                const sendRes = await client.im.message.create({
                  params: { receive_id_type: 'chat_id' },
                  data: {
                    receive_id: chat_id,
                    content: JSON.stringify({ file_key: fileKey }),
                    msg_type: 'file',
                  },
                })
                const msgId = sendRes?.data?.message_id
                if (msgId) {
                  noteSent(msgId, recentSentIds)
                  sentIds.push(msgId)
                }
              }
            }
          }

          const result =
            sentIds.length === 1
              ? `sent (id: ${sentIds[0]})`
              : `sent ${sentIds.length} parts (ids: ${sentIds.join(', ')})`
          return { content: [{ type: 'text', text: result }] }
        }

        // ── fetch_messages ─────────────────────────────────────────
        case 'fetch_messages': {
          const channel = args.channel as string
          const requestedLimit = Math.min((args.limit as number) ?? 20, 50)

          await fetchAllowedChat(channel, client, chatTypeMap)

          const allMessages: any[] = []
          let pageToken: string | undefined
          let remaining = requestedLimit

          while (remaining > 0) {
            const pageSize = Math.min(remaining, 50)
            const res = await client.im.message.list({
              params: {
                container_id_type: 'chat',
                container_id: channel,
                page_size: pageSize,
                ...(pageToken ? { page_token: pageToken } : {}),
              },
            })
            const items = res?.data?.items ?? []
            allMessages.push(...items)
            remaining -= items.length
            pageToken = res?.data?.page_token
            if (!pageToken || items.length === 0) break
          }

          if (allMessages.length === 0) {
            return { content: [{ type: 'text', text: '(no messages)' }] }
          }

          // Feishu returns newest-first; reverse for oldest-first.
          allMessages.reverse()

          const botId = '' // bot's own messages will show sender_id
          const out = allMessages
            .map((m: any) => {
              const senderId = m.sender?.id
              const who = senderId === botId ? 'me' : (m.sender?.sender_type === 'app' ? 'bot' : senderId ?? 'unknown')
              let text = ''
              try {
                const parsed = JSON.parse(m.body?.content ?? '{}')
                text = parsed.text ?? parsed.content ?? `[${m.msg_type}]`
              } catch {
                text = `[${m.msg_type}]`
              }
              // Count attachments heuristically
              const msgType = m.msg_type ?? ''
              const isAttachment = ['image', 'file', 'media', 'audio'].includes(msgType)
              const attMark = isAttachment ? ' +1att' : ''
              const sanitized = text.replace(/[\r\n]+/g, ' ⏎ ')
              const ts = m.create_time
                ? new Date(parseInt(m.create_time)).toISOString()
                : ''
              return `[${ts}] ${who}: ${sanitized}  (id: ${m.message_id}${attMark})`
            })
            .join('\n')
          return { content: [{ type: 'text', text: out }] }
        }

        // ── react ──────────────────────────────────────────────────
        case 'react': {
          const chat_id = args.chat_id as string
          const message_id = args.message_id as string
          const emoji = args.emoji as string

          await fetchAllowedChat(chat_id, client, chatTypeMap)
          await client.im.messageReaction.create({
            path: { message_id },
            data: { reaction_type: { emoji_type: emoji } },
          })
          return { content: [{ type: 'text', text: 'reacted' }] }
        }

        // ── edit_message ───────────────────────────────────────────
        case 'edit_message': {
          const chat_id = args.chat_id as string
          const message_id = args.message_id as string
          const text = args.text as string

          await fetchAllowedChat(chat_id, client, chatTypeMap)
          await client.im.message.patch({
            path: { message_id },
            data: { content: JSON.stringify({ text }) },
          })
          return { content: [{ type: 'text', text: `edited (id: ${message_id})` }] }
        }

        // ── download_attachment ────────────────────────────────────
        case 'download_attachment': {
          const chat_id = args.chat_id as string
          const message_id = args.message_id as string

          await fetchAllowedChat(chat_id, client, chatTypeMap)

          // Fetch message to inspect its content.
          // API returns { data: { items: [...] } } — extract first item.
          const msgRes = await client.im.message.get({
            path: { message_id },
          })
          const msg = msgRes?.data?.items?.[0] ?? msgRes?.data
          if (!msg) throw new Error('message not found')

          const msgType = msg.msg_type ?? msg.message_type ?? ''
          const rawContent = msg.body?.content ?? msg.content ?? '{}'
          const lines: string[] = []

          mkdirSync(INBOX_DIR, { recursive: true })

          // Extract the resource key and determine type for messageResource API.
          let resourceKey: string | undefined
          let resourceType: string = msgType // 'image', 'file', etc.
          let fileName = ''

          try {
            const parsed = JSON.parse(rawContent)
            if (msgType === 'image') {
              resourceKey = parsed.image_key
            } else {
              resourceKey = parsed.file_key ?? parsed.image_key
              fileName = parsed.file_name ?? ''
            }
          } catch {}

          if (!resourceKey) {
            return {
              content: [{ type: 'text', text: 'message has no downloadable attachments' }],
            }
          }

          // Use messageResource API for all types — im.image.get and im.file.get
          // return 400 for message attachments; messageResource works universally.
          // API: GET /im/v1/messages/:message_id/resources/:file_key?type=<type>
          const resp = await client.im.messageResource.get({
            path: { message_id, file_key: resourceKey },
            params: { type: resourceType },
          })

          // Determine output filename
          let ext = 'bin'
          if (msgType === 'image') {
            ext = 'png'
          } else if (fileName.includes('.')) {
            ext = fileName.slice(fileName.lastIndexOf('.') + 1).replace(/[^a-zA-Z0-9]/g, '') || 'bin'
          }
          const outPath = join(INBOX_DIR, `${Date.now()}-${safeAttName(fileName || resourceKey)}.${ext}`)

          if (resp?.writeFile) {
            await resp.writeFile(outPath)
          } else {
            const buf = resp?.data ?? resp
            writeFileSync(outPath, Buffer.isBuffer(buf) ? buf : Buffer.from(buf))
          }
          lines.push(`  ${outPath}  (${msgType}, ${fileName || resourceKey})`)

          return {
            content: [
              {
                type: 'text',
                text: `downloaded ${lines.length} attachment(s):\n${lines.join('\n')}`,
              },
            ],
          }
        }

        default:
          return {
            content: [{ type: 'text', text: `unknown tool: ${req.params.name}` }],
            isError: true,
          }
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      return {
        content: [{ type: 'text', text: `${req.params.name} failed: ${msg}` }],
        isError: true,
      }
    }
  })
}
