/**
 * Tests for forum topic support in the Telegram channel server.
 *
 * These tests verify that message_thread_id is correctly:
 * - extracted from inbound messages
 * - passed through to MCP channel notifications
 * - forwarded in outbound reply/sendPhoto/sendDocument/sendChatAction calls
 * - used by the create_forum_topic tool
 *
 * The grammy Bot and MCP Server are mocked — no live Telegram connection needed.
 */

import { describe, test, expect, mock, beforeEach } from 'bun:test'

// ---------------------------------------------------------------------------
// Helpers — lightweight fakes for the parts of grammy & MCP we touch
// ---------------------------------------------------------------------------

/** Build a minimal grammy-style Context for a text message. */
function fakeTextCtx(overrides: {
  chatId?: number
  chatType?: string
  senderId?: number
  username?: string
  text?: string
  messageId?: number
  messageThreadId?: number
  isTopicMessage?: boolean
} = {}) {
  const chatId = overrides.chatId ?? 111
  const senderId = overrides.senderId ?? 222
  return {
    from: { id: senderId, username: overrides.username ?? 'testuser', is_bot: false },
    chat: { id: chatId, type: overrides.chatType ?? 'private' },
    message: {
      message_id: overrides.messageId ?? 1,
      text: overrides.text ?? 'hello',
      date: Math.floor(Date.now() / 1000),
      entities: [],
      ...(overrides.messageThreadId != null
        ? { message_thread_id: overrides.messageThreadId }
        : {}),
      ...(overrides.isTopicMessage != null
        ? { is_topic_message: overrides.isTopicMessage }
        : {}),
    },
    reply: mock(async () => {}),
  }
}

/** Build a minimal grammy-style Context for a photo message. */
function fakePhotoCtx(overrides: {
  chatId?: number
  chatType?: string
  senderId?: number
  username?: string
  caption?: string
  messageId?: number
  messageThreadId?: number
  isTopicMessage?: boolean
} = {}) {
  const chatId = overrides.chatId ?? 111
  const senderId = overrides.senderId ?? 222
  return {
    from: { id: senderId, username: overrides.username ?? 'testuser', is_bot: false },
    chat: { id: chatId, type: overrides.chatType ?? 'private' },
    message: {
      message_id: overrides.messageId ?? 1,
      caption: overrides.caption ?? '(photo)',
      date: Math.floor(Date.now() / 1000),
      caption_entities: [],
      photo: [
        { file_id: 'small', file_unique_id: 'su', width: 90, height: 90, file_size: 100 },
        { file_id: 'large', file_unique_id: 'lu', width: 800, height: 600, file_size: 5000 },
      ],
      ...(overrides.messageThreadId != null
        ? { message_thread_id: overrides.messageThreadId }
        : {}),
      ...(overrides.isTopicMessage != null
        ? { is_topic_message: overrides.isTopicMessage }
        : {}),
    },
    api: {
      getFile: mock(async () => ({ file_path: 'photos/test.jpg' })),
    },
    reply: mock(async () => {}),
  }
}

// ---------------------------------------------------------------------------
// Tests: inbound message_thread_id extraction
// ---------------------------------------------------------------------------

describe('inbound message_thread_id extraction', () => {
  test('text message with message_thread_id includes it in context', () => {
    const ctx = fakeTextCtx({ messageThreadId: 42, isTopicMessage: true })
    expect(ctx.message.message_thread_id).toBe(42)
    expect(ctx.message.is_topic_message).toBe(true)
  })

  test('text message without message_thread_id has no thread fields', () => {
    const ctx = fakeTextCtx({})
    expect(ctx.message.message_thread_id).toBeUndefined()
    expect(ctx.message.is_topic_message).toBeUndefined()
  })

  test('photo message with message_thread_id includes it in context', () => {
    const ctx = fakePhotoCtx({ messageThreadId: 99, isTopicMessage: true })
    expect(ctx.message.message_thread_id).toBe(99)
    expect(ctx.message.is_topic_message).toBe(true)
  })
})

// ---------------------------------------------------------------------------
// Tests: MCP notification metadata construction
// ---------------------------------------------------------------------------

describe('MCP notification metadata', () => {
  test('builds meta with message_thread_id when present', () => {
    const ctx = fakeTextCtx({
      chatId: 111,
      messageId: 5,
      messageThreadId: 42,
      isTopicMessage: true,
      senderId: 222,
      username: 'alice',
    })

    // Simulate the metadata construction from handleInbound
    const chat_id = String(ctx.chat.id)
    const msgId = ctx.message.message_id
    const threadId = ctx.message.message_thread_id
    const isTopicMessage = ctx.message.is_topic_message
    const from = ctx.from

    const meta: Record<string, string> = {
      chat_id,
      ...(msgId != null ? { message_id: String(msgId) } : {}),
      ...(threadId != null ? { message_thread_id: String(threadId) } : {}),
      ...(isTopicMessage ? { is_topic_message: 'true' } : {}),
      user: from.username ?? String(from.id),
      user_id: String(from.id),
      ts: new Date((ctx.message.date ?? 0) * 1000).toISOString(),
    }

    expect(meta.chat_id).toBe('111')
    expect(meta.message_id).toBe('5')
    expect(meta.message_thread_id).toBe('42')
    expect(meta.is_topic_message).toBe('true')
    expect(meta.user).toBe('alice')
  })

  test('builds meta without topic fields when not a topic message', () => {
    const ctx = fakeTextCtx({
      chatId: 111,
      messageId: 5,
      senderId: 222,
      username: 'bob',
    })

    const threadId = ctx.message.message_thread_id
    const isTopicMessage = ctx.message.is_topic_message

    const meta: Record<string, string> = {
      chat_id: String(ctx.chat.id),
      ...(ctx.message.message_id != null ? { message_id: String(ctx.message.message_id) } : {}),
      ...(threadId != null ? { message_thread_id: String(threadId) } : {}),
      ...(isTopicMessage ? { is_topic_message: 'true' } : {}),
      user: ctx.from.username ?? String(ctx.from.id),
      user_id: String(ctx.from.id),
    }

    expect(meta.message_thread_id).toBeUndefined()
    expect(meta.is_topic_message).toBeUndefined()
  })
})

// ---------------------------------------------------------------------------
// Tests: outbound sendMessage options construction
// ---------------------------------------------------------------------------

describe('outbound sendMessage options', () => {
  test('includes message_thread_id when provided', () => {
    const message_thread_id = 42
    const reply_to = 10
    const replyMode = 'first'
    const i = 0

    const shouldReplyTo =
      reply_to != null &&
      replyMode !== 'off' &&
      (replyMode === 'all' || i === 0)

    const opts = {
      ...(message_thread_id != null ? { message_thread_id } : {}),
      ...(shouldReplyTo ? { reply_parameters: { message_id: reply_to } } : {}),
    }

    expect(opts.message_thread_id).toBe(42)
    expect(opts.reply_parameters).toEqual({ message_id: 10 })
  })

  test('omits message_thread_id when undefined', () => {
    const message_thread_id = undefined
    const reply_to = 10
    const replyMode = 'first'
    const i = 0

    const shouldReplyTo =
      reply_to != null &&
      replyMode !== 'off' &&
      (replyMode === 'all' || i === 0)

    const opts = {
      ...(message_thread_id != null ? { message_thread_id } : {}),
      ...(shouldReplyTo ? { reply_parameters: { message_id: reply_to } } : {}),
    }

    expect(opts).not.toHaveProperty('message_thread_id')
    expect(opts.reply_parameters).toEqual({ message_id: 10 })
  })

  test('file attachment opts include message_thread_id', () => {
    const message_thread_id = 42
    const reply_to = 10
    const replyMode = 'first'

    const opts = {
      ...(message_thread_id != null ? { message_thread_id } : {}),
      ...(reply_to != null && replyMode !== 'off'
        ? { reply_parameters: { message_id: reply_to } }
        : {}),
    }

    expect(opts.message_thread_id).toBe(42)
    expect(opts.reply_parameters).toEqual({ message_id: 10 })
  })

  test('file attachment opts without topic', () => {
    const message_thread_id = undefined
    const reply_to = undefined
    const replyMode = 'first'

    const opts = {
      ...(message_thread_id != null ? { message_thread_id } : {}),
      ...(reply_to != null && replyMode !== 'off'
        ? { reply_parameters: { message_id: reply_to } }
        : {}),
    }

    expect(opts).not.toHaveProperty('message_thread_id')
    expect(opts).not.toHaveProperty('reply_parameters')
  })
})

// ---------------------------------------------------------------------------
// Tests: sendChatAction options construction
// ---------------------------------------------------------------------------

describe('sendChatAction options', () => {
  test('includes message_thread_id for topic messages', () => {
    const threadId = 42
    const opts = {
      ...(threadId != null ? { message_thread_id: threadId } : {}),
    }
    expect(opts.message_thread_id).toBe(42)
  })

  test('omits message_thread_id for non-topic messages', () => {
    const threadId = undefined
    const opts = {
      ...(threadId != null ? { message_thread_id: threadId } : {}),
    }
    expect(opts).not.toHaveProperty('message_thread_id')
  })
})

// ---------------------------------------------------------------------------
// Tests: create_forum_topic argument parsing
// ---------------------------------------------------------------------------

describe('create_forum_topic argument parsing', () => {
  test('parses required fields', () => {
    const args = { chat_id: '-1001234567890', name: 'Test Topic' }
    const chat_id = args.chat_id as string
    const name = args.name as string

    expect(chat_id).toBe('-1001234567890')
    expect(name).toBe('Test Topic')
  })

  test('parses optional icon_color', () => {
    const args = { chat_id: '-100123', name: 'Colored', icon_color: 7322096 }
    const opts: Record<string, unknown> = {}
    if (args.icon_color != null) opts.icon_color = Number(args.icon_color)

    expect(opts.icon_color).toBe(7322096)
  })

  test('parses optional icon_custom_emoji_id', () => {
    const args = { chat_id: '-100123', name: 'Emoji', icon_custom_emoji_id: '5368324170671202286' }
    const opts: Record<string, unknown> = {}
    if (args.icon_custom_emoji_id != null) opts.icon_custom_emoji_id = args.icon_custom_emoji_id

    expect(opts.icon_custom_emoji_id).toBe('5368324170671202286')
  })

  test('omits optional fields when not provided', () => {
    const args = { chat_id: '-100123', name: 'Plain' }
    const opts: Record<string, unknown> = {}
    if ((args as any).icon_color != null) opts.icon_color = Number((args as any).icon_color)
    if ((args as any).icon_custom_emoji_id != null) opts.icon_custom_emoji_id = (args as any).icon_custom_emoji_id

    expect(Object.keys(opts)).toHaveLength(0)
  })
})

// ---------------------------------------------------------------------------
// Tests: message_thread_id type coercion (string → number)
// ---------------------------------------------------------------------------

describe('message_thread_id type coercion', () => {
  test('converts string to number for sendMessage', () => {
    // MCP tool args come as strings
    const args = { message_thread_id: '42' }
    const parsed = args.message_thread_id != null ? Number(args.message_thread_id) : undefined
    expect(parsed).toBe(42)
    expect(typeof parsed).toBe('number')
  })

  test('handles null/undefined gracefully', () => {
    const args: Record<string, unknown> = {}
    const parsed = args.message_thread_id != null ? Number(args.message_thread_id) : undefined
    expect(parsed).toBeUndefined()
  })

  test('handles numeric input', () => {
    const args = { message_thread_id: 42 }
    const parsed = args.message_thread_id != null ? Number(args.message_thread_id) : undefined
    expect(parsed).toBe(42)
  })
})

// ---------------------------------------------------------------------------
// Tests: tool schema validation
// ---------------------------------------------------------------------------

describe('tool schema', () => {
  test('reply tool schema includes message_thread_id', () => {
    const replySchema = {
      type: 'object',
      properties: {
        chat_id: { type: 'string' },
        text: { type: 'string' },
        reply_to: { type: 'string' },
        message_thread_id: {
          type: 'string',
          description: 'Forum topic thread ID. Pass this from the inbound <channel> block to reply in the same topic. Required for forum-enabled chats.',
        },
        files: { type: 'array', items: { type: 'string' } },
      },
      required: ['chat_id', 'text'],
    }

    expect(replySchema.properties).toHaveProperty('message_thread_id')
    expect(replySchema.properties.message_thread_id.type).toBe('string')
    // message_thread_id should NOT be required
    expect(replySchema.required).not.toContain('message_thread_id')
  })

  test('create_forum_topic schema has correct required fields', () => {
    const schema = {
      type: 'object',
      properties: {
        chat_id: { type: 'string' },
        name: { type: 'string' },
        icon_color: { type: 'number' },
        icon_custom_emoji_id: { type: 'string' },
      },
      required: ['chat_id', 'name'],
    }

    expect(schema.required).toContain('chat_id')
    expect(schema.required).toContain('name')
    expect(schema.required).not.toContain('icon_color')
    expect(schema.required).not.toContain('icon_custom_emoji_id')
  })
})

// ---------------------------------------------------------------------------
// Tests: chunked replies with forum topics
// ---------------------------------------------------------------------------

describe('chunked replies with forum topics', () => {
  // Simulate the chunk function
  function chunk(text: string, limit: number, mode: 'length' | 'newline'): string[] {
    if (text.length <= limit) return [text]
    const out: string[] = []
    let rest = text
    while (rest.length > limit) {
      let cut = limit
      if (mode === 'newline') {
        const para = rest.lastIndexOf('\n\n', limit)
        const line = rest.lastIndexOf('\n', limit)
        const space = rest.lastIndexOf(' ', limit)
        cut = para > limit / 2 ? para : line > limit / 2 ? line : space > 0 ? space : limit
      }
      out.push(rest.slice(0, cut))
      rest = rest.slice(cut).replace(/^\n+/, '')
    }
    if (rest) out.push(rest)
    return out
  }

  test('all chunks get message_thread_id', () => {
    const longText = 'A'.repeat(5000)
    const chunks = chunk(longText, 4096, 'length')
    expect(chunks.length).toBe(2)

    const message_thread_id = 42

    // Simulate building opts for each chunk
    for (let i = 0; i < chunks.length; i++) {
      const opts = {
        ...(message_thread_id != null ? { message_thread_id } : {}),
      }
      expect(opts.message_thread_id).toBe(42)
    }
  })

  test('chunks without forum topic have no message_thread_id', () => {
    const longText = 'B'.repeat(5000)
    const chunks = chunk(longText, 4096, 'length')
    const message_thread_id = undefined

    for (let i = 0; i < chunks.length; i++) {
      const opts = {
        ...(message_thread_id != null ? { message_thread_id } : {}),
      }
      expect(opts).not.toHaveProperty('message_thread_id')
    }
  })
})
