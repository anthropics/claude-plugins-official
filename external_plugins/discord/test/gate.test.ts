import { expect, test, beforeEach, afterAll } from 'bun:test'
import { ChannelType } from 'discord.js'
import { BOT_ID, cleanup, mkChannel, mkMsg, writeAccess } from './harness'
import { client, gate } from '../server'

client.user = { id: BOT_ID, username: 'claude' } as any

const CHANNEL = '200000000000000001'
const OTHER = '200000000000000002'
const OWNER = '510000000000000001'

// The access.json shape ACCESS.md documents today, as a baseline for changes to
// the gate: every outcome below is current behaviour.
beforeEach(() => {
  writeAccess({
    dmPolicy: 'pairing',
    allowFrom: [OWNER],
    groups: { [CHANNEL]: { requireMention: true, allowFrom: [] } },
    pending: {},
    mentionPatterns: ['^hey claude\\b'],
    ackReaction: '👀',
    replyToMode: 'first',
    textChunkLimit: 2000,
    chunkMode: 'newline',
  })
})
afterAll(cleanup)

test('a mention in an opted-in channel is delivered', async () => {
  expect((await gate(mkMsg({ authorId: OWNER, mentionsBot: true }))).action).toBe('deliver')
})

test('unrelated chatter in an opted-in channel is dropped', async () => {
  expect((await gate(mkMsg({ authorId: OWNER, content: 'unrelated chatter' }))).action).toBe('drop')
})

test('a mentionPatterns match counts as a mention', async () => {
  expect((await gate(mkMsg({ authorId: OWNER, content: 'hey claude ping' }))).action).toBe('deliver')
})

test('a channel that is not opted in is dropped', async () => {
  const msg = mkMsg({ channel: mkChannel({ id: OTHER }), authorId: OWNER, mentionsBot: true })
  expect((await gate(msg)).action).toBe('drop')
})

test('a DM from the allowlist is delivered without a mention', async () => {
  const dm = mkChannel({ id: '600000000000000001', type: ChannelType.DM })
  expect((await gate(mkMsg({ channel: dm, authorId: OWNER }))).action).toBe('deliver')
})

test('a channel allowFrom list keeps everyone else out', async () => {
  writeAccess({
    dmPolicy: 'pairing',
    allowFrom: [OWNER],
    groups: { [CHANNEL]: { requireMention: false, allowFrom: [OWNER] } },
  })
  expect((await gate(mkMsg({ authorId: OWNER }))).action).toBe('deliver')
  expect((await gate(mkMsg({ authorId: '520000000000000002' }))).action).toBe('drop')
})
