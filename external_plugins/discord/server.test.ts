/**
 * Tests for Discord plugin reply threading logic.
 * Mocks discord.js to verify reply_to context building.
 */

import { describe, test, expect, mock, beforeEach } from 'bun:test'

// Mock message factory
function createMockMessage(opts: {
  id: string
  content: string
  authorUsername: string
  authorId?: string
  referenceMessageId?: string
  fetchReferenceResult?: ReturnType<typeof createMockMessage>
}) {
  const msg = {
    id: opts.id,
    content: opts.content,
    author: {
      username: opts.authorUsername,
      id: opts.authorId ?? `user_${opts.authorUsername}`,
    },
    reference: opts.referenceMessageId ? { messageId: opts.referenceMessageId } : null,
    createdAt: new Date('2026-07-16T00:00:00Z'),
    channelId: 'test_channel',
    attachments: new Map(),
    fetchReference: opts.fetchReferenceResult
      ? mock(() => Promise.resolve(opts.fetchReferenceResult))
      : mock(() => Promise.reject(new Error('No reference'))),
  }
  return msg
}

// Extract the reply context building logic for testing
async function buildReplyContext(msg: ReturnType<typeof createMockMessage>): Promise<Record<string, unknown> | undefined> {
  let replyContext: Record<string, unknown> | undefined
  if (msg.reference?.messageId) {
    try {
      const parent = await msg.fetchReference()
      replyContext = {
        message_id: parent.id,
        user: parent.author.username,
        content: parent.content,
      }
      // Second level
      if (parent.reference?.messageId) {
        try {
          const grandparent = await parent.fetchReference()
          const level2: Record<string, unknown> = {
            message_id: grandparent.id,
            user: grandparent.author.username,
            content: grandparent.content,
          }
          // Third level — just the ID as a breadcrumb
          if (grandparent.reference?.messageId) {
            level2.reply_to = { message_id: grandparent.reference.messageId }
          }
          replyContext.reply_to = level2
        } catch {}
      }
    } catch {}
  }
  return replyContext
}

// Format message line for fetch_messages output
function formatMessageLine(m: ReturnType<typeof createMockMessage>, meId?: string): string {
  const who = m.author.id === meId ? 'me' : m.author.username
  const atts = m.attachments.size > 0 ? ` +${m.attachments.size}att` : ''
  const replyTo = m.reference?.messageId ? `, reply_to: ${m.reference.messageId}` : ''
  const text = m.content.replace(/[\r\n]+/g, ' ⏎ ')
  return `[${m.createdAt.toISOString()}] ${who}: ${text}  (id: ${m.id}${atts}${replyTo})`
}

describe('reply context building', () => {
  test('no reply returns undefined', async () => {
    const msg = createMockMessage({
      id: 'msg1',
      content: 'Hello world',
      authorUsername: 'alice',
    })

    const ctx = await buildReplyContext(msg)
    expect(ctx).toBeUndefined()
  })

  test('single-level reply includes parent content', async () => {
    const parent = createMockMessage({
      id: 'parent1',
      content: 'the department of maybe don\'t doesn\'t need ownership to file a concern.',
      authorUsername: 'Aster',
    })

    const msg = createMockMessage({
      id: 'msg1',
      content: 'Pure comedic gold',
      authorUsername: 'jaykraykray',
      referenceMessageId: 'parent1',
      fetchReferenceResult: parent,
    })

    const ctx = await buildReplyContext(msg)
    expect(ctx).toEqual({
      message_id: 'parent1',
      user: 'Aster',
      content: 'the department of maybe don\'t doesn\'t need ownership to file a concern.',
    })
  })

  test('two-level reply includes grandparent content', async () => {
    const grandparent = createMockMessage({
      id: 'gp1',
      content: 'Original message',
      authorUsername: 'alice',
    })

    const parent = createMockMessage({
      id: 'parent1',
      content: 'Reply to original',
      authorUsername: 'bob',
      referenceMessageId: 'gp1',
      fetchReferenceResult: grandparent,
    })

    const msg = createMockMessage({
      id: 'msg1',
      content: 'Reply to reply',
      authorUsername: 'charlie',
      referenceMessageId: 'parent1',
      fetchReferenceResult: parent,
    })

    const ctx = await buildReplyContext(msg)
    expect(ctx).toEqual({
      message_id: 'parent1',
      user: 'bob',
      content: 'Reply to original',
      reply_to: {
        message_id: 'gp1',
        user: 'alice',
        content: 'Original message',
      },
    })
  })

  test('three-level reply includes breadcrumb ID only for level 3', async () => {
    const greatGrandparent = createMockMessage({
      id: 'ggp1',
      content: 'Very original',
      authorUsername: 'root',
    })

    const grandparent = createMockMessage({
      id: 'gp1',
      content: 'First reply',
      authorUsername: 'alice',
      referenceMessageId: 'ggp1',
      fetchReferenceResult: greatGrandparent,
    })

    const parent = createMockMessage({
      id: 'parent1',
      content: 'Second reply',
      authorUsername: 'bob',
      referenceMessageId: 'gp1',
      fetchReferenceResult: grandparent,
    })

    const msg = createMockMessage({
      id: 'msg1',
      content: 'Third reply',
      authorUsername: 'charlie',
      referenceMessageId: 'parent1',
      fetchReferenceResult: parent,
    })

    const ctx = await buildReplyContext(msg)
    expect(ctx).toEqual({
      message_id: 'parent1',
      user: 'bob',
      content: 'Second reply',
      reply_to: {
        message_id: 'gp1',
        user: 'alice',
        content: 'First reply',
        reply_to: {
          message_id: 'ggp1',
        },
      },
    })
  })

  test('handles fetch failure gracefully', async () => {
    const msg = createMockMessage({
      id: 'msg1',
      content: 'Reply to deleted message',
      authorUsername: 'alice',
      referenceMessageId: 'deleted123',
      // fetchReference will reject by default
    })

    const ctx = await buildReplyContext(msg)
    expect(ctx).toBeUndefined()
  })
})

describe('fetch_messages format', () => {
  test('includes reply_to ID in output line', () => {
    const msg = createMockMessage({
      id: 'msg1',
      content: 'This is a reply',
      authorUsername: 'alice',
      referenceMessageId: 'parent123',
    })

    const line = formatMessageLine(msg)
    expect(line).toContain('reply_to: parent123')
    expect(line).toContain('id: msg1')
  })

  test('omits reply_to when no reference', () => {
    const msg = createMockMessage({
      id: 'msg1',
      content: 'Standalone message',
      authorUsername: 'alice',
    })

    const line = formatMessageLine(msg)
    expect(line).not.toContain('reply_to')
    expect(line).toContain('id: msg1')
  })

  test('replaces newlines with arrow symbol', () => {
    const msg = createMockMessage({
      id: 'msg1',
      content: 'Line one\nLine two\nLine three',
      authorUsername: 'alice',
    })

    const line = formatMessageLine(msg)
    expect(line).toContain('Line one ⏎ Line two ⏎ Line three')
    expect(line).not.toContain('\n')
  })

  test('shows "me" for bot messages', () => {
    const msg = createMockMessage({
      id: 'msg1',
      content: 'Bot message',
      authorUsername: 'TestBot',
      authorId: 'bot123',
    })

    const line = formatMessageLine(msg, 'bot123')
    expect(line).toContain('] me:')
    expect(line).not.toContain('TestBot')
  })
})
