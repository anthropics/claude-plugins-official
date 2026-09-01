// Pure-logic coverage for the delivery helpers: status-reaction resolution,
// button keyboard building, format/limit resolution and draft chat validation.
import { readFileSync, writeFileSync } from 'fs'

const EXTRACTED = '/tmp/tg-helpers-extracted.ts'
const src = readFileSync(new URL('../server.ts', import.meta.url), 'utf8')

function grab(header: string): string {
  const start = src.indexOf(header)
  if (start < 0) throw new Error(`missing: ${header}`)
  // The body brace is the last one on the signature line — an object return
  // type would otherwise be matched instead.
  const open = src.lastIndexOf('{', src.indexOf('\n', start))
  let depth = 0
  for (let j = open; j < src.length; j++) {
    if (src[j] === '{') depth++
    else if (src[j] === '}' && --depth === 0) return src.slice(start, j + 1)
  }
  throw new Error(`unbalanced: ${header}`)
}

const line = (re: RegExp) => src.match(re)![0]

writeFileSync(EXTRACTED, [
  `import { InlineKeyboard } from 'grammy'`,
  `import { randomBytes } from 'crypto'`,
  `type StatusStage = 'received' | 'working' | 'done' | 'error'`,
  `type OutboundFormat = 'rich' | 'markdownv2' | 'text'`,
  // Only the fields the extracted helpers touch.
  `type Access = any`,
  `type ButtonSpec = { text?: unknown; action?: unknown; copy?: unknown; url?: unknown }`,
  src.match(/^const DEFAULT_STATUS_REACTIONS[\s\S]*?^}/m)![0],
  line(/^const OUTBOUND_FORMATS\b.*$/m),
  line(/^const MAX_BUTTONS = .*$/m),
  line(/^const MAX_PENDING_ACTIONS = .*$/m),
  line(/^const MAX_CHUNK_LIMIT = .*$/m),
  line(/^const MAX_RICH_CHUNK_LIMIT = .*$/m),
  `const pendingActions = new Map<string, { chat_id: string; action: string }>()`,
  grab('function isOutboundFormat('),
  grab('function statusEmojiFor('),
  grab('function resolveFormat('),
  grab('function clampLimit('),
  grab('function assertDraftableChat('),
  grab('function registerAction('),
  grab('function assertButtonUrl('),
  grab('function buildKeyboard('),
  `export { statusEmojiFor, resolveFormat, clampLimit, assertDraftableChat, buildKeyboard, pendingActions, MAX_CHUNK_LIMIT, MAX_RICH_CHUNK_LIMIT }`,
].join('\n\n'))

const m = await import(EXTRACTED)
const { statusEmojiFor, resolveFormat, clampLimit, assertDraftableChat, buildKeyboard, MAX_CHUNK_LIMIT, MAX_RICH_CHUNK_LIMIT } = m

let fails = 0
const ok = (cond: boolean, msg: string) => {
  console.log(`${cond ? 'PASS' : 'FAIL'}  ${msg}`)
  if (!cond) fails++
}
const throws = (fn: () => unknown, match: RegExp, msg: string) => {
  try {
    fn()
    ok(false, `${msg} (no error thrown)`)
  } catch (e) {
    ok(match.test(String(e)), `${msg}`)
  }
}

// --- status reactions -------------------------------------------------------
ok(statusEmojiFor({}, 'received') === '👀', 'defaults: received is 👀')
ok(statusEmojiFor({}, 'working') === '✍', 'defaults: working is ✍')
ok(statusEmojiFor({}, 'done') === '👌', 'defaults: done is 👌')
ok(statusEmojiFor({}, 'error') === '😢', 'defaults: error is 😢')

ok(statusEmojiFor({ statusReactions: false }, 'received') === '', 'false disables every stage')
ok(statusEmojiFor({ statusReactions: false }, 'done') === '', 'false disables done too')

ok(
  statusEmojiFor({ statusReactions: { done: '🎉' } }, 'done') === '🎉',
  'an overridden stage wins over the default',
)
ok(
  statusEmojiFor({ statusReactions: { done: '🎉' } }, 'received') === '👀',
  'unlisted stages keep their default',
)
ok(
  statusEmojiFor({ statusReactions: { working: '' } }, 'working') === '',
  'empty string skips just that stage',
)

// ackReaction is the pre-existing key and has to keep working.
ok(
  statusEmojiFor({ ackReaction: '🔥' }, 'received') === '🔥',
  'ackReaction wins for received',
)
ok(
  statusEmojiFor({ ackReaction: '🔥' }, 'done') === '👌',
  'ackReaction does not leak into other stages',
)
ok(
  statusEmojiFor({ ackReaction: '', statusReactions: { received: '👀' } }, 'received') === '',
  'ackReaction:"" still disables receipt, as it always did',
)

// --- format and limits ------------------------------------------------------
ok(resolveFormat(undefined, {}) === 'rich', 'format defaults to rich')
ok(resolveFormat('text', {}) === 'text', 'an explicit format is honoured')
ok(resolveFormat(undefined, { defaultFormat: 'markdownv2' }) === 'markdownv2', 'defaultFormat applies')
ok(resolveFormat('nonsense', {}) === 'rich', 'an unknown format falls back rather than passing through')
ok(resolveFormat('nonsense', { defaultFormat: 'text' }) === 'text', 'unknown falls back to the configured default')

ok(clampLimit(undefined, MAX_CHUNK_LIMIT) === 4096, 'unset limit uses the cap')
ok(clampLimit(99999, MAX_RICH_CHUNK_LIMIT) === 32768, 'an oversized limit clamps to the cap')
ok(clampLimit(0, MAX_CHUNK_LIMIT) === 1, 'zero clamps up to 1, so chunking terminates')
ok(clampLimit(-5, MAX_CHUNK_LIMIT) === 1, 'a negative limit clamps up to 1')
ok(clampLimit(500, MAX_CHUNK_LIMIT) === 500, 'a sane limit passes through')

// --- draft chat validation --------------------------------------------------
ok(assertDraftableChat('485056', { groups: {} }) === 485056, 'a private chat id is accepted')
throws(() => assertDraftableChat('-1001654782309', { groups: {} }), /private-chat only/, 'a negative id is rejected as a group')
throws(() => assertDraftableChat('485056', { groups: { '485056': {} } }), /private-chat only/, 'an allowlisted group is rejected even with a positive id')
throws(() => assertDraftableChat('@channel', { groups: {} }), /numeric private chat id/, 'a username is rejected')
throws(() => assertDraftableChat('12.5', { groups: {} }), /numeric private chat id/, 'a non-integer is rejected')

// --- buttons ----------------------------------------------------------------
const rows = (kb: { inline_keyboard: unknown[][] }) => kb.inline_keyboard.map(r => r.length)

ok(
  JSON.stringify(rows(buildKeyboard('1', [{ text: 'Go' }, { text: 'Stop' }]))) === '[2]',
  'two short labels share a row',
)
ok(
  JSON.stringify(rows(buildKeyboard('1', [{ text: 'Go' }, { text: 'Stop' }, { text: 'More' }]))) === '[2,1]',
  'a third short label starts a new row',
)
ok(
  JSON.stringify(rows(buildKeyboard('1', [{ text: 'Go' }, { text: 'A very long button label' }]))) === '[1,1]',
  'a long label takes a row of its own',
)

const kb = buildKeyboard('1', [
  { text: 'Act' },
  { text: 'Copy', copy: 'npm run build' },
  { text: 'Open', url: 'https://t.me' },
])
const flat = kb.inline_keyboard.flat() as Record<string, unknown>[]
ok(typeof flat[0].callback_data === 'string' && /^act:[0-9a-f]{12}$/.test(String(flat[0].callback_data)), 'action button carries a token, not the text')
ok(String(flat[0].callback_data).length <= 64, "callback_data stays within Telegram's 64-byte cap")
ok((flat[1].copy_text as { text: string })?.text === 'npm run build', 'copy button carries the payload')
ok(flat[2].url === 'https://t.me', 'url button carries the link')

ok(
  buildKeyboard('1', [{ text: 'Go', action: 'do the thing' }]).inline_keyboard[0].length === 1,
  'a custom action still builds one button',
)

throws(() => buildKeyboard('1', [{ text: '  ' }]), /non-empty text/, 'a blank label is rejected')
throws(() => buildKeyboard('1', [{ text: 'x', url: 'javascript:alert(1)' }]), /http\(s\) or tg/, 'a javascript: url is rejected')
throws(() => buildKeyboard('1', [{ text: 'x', url: 'file:///etc/passwd' }]), /http\(s\) or tg/, 'a file: url is rejected')
ok(
  buildKeyboard('1', [{ text: 'x', url: 'tg://user?id=1' }]).inline_keyboard[0].length === 1,
  'a tg: url is allowed',
)
throws(
  () => buildKeyboard('1', Array.from({ length: 13 }, (_, i) => ({ text: `b${i}` }))),
  /too many buttons/,
  'more than 12 buttons is rejected',
)

// The action registry must not grow without bound across a long session.
const before = m.pendingActions.size
for (let i = 0; i < 300; i++) buildKeyboard('1', [{ text: `b${i}` }])
ok(m.pendingActions.size <= 200, `action registry stays bounded (${before} → ${m.pendingActions.size})`)

console.log(fails ? `\n${fails} FAILURE(S)` : '\nall green')
process.exit(fails ? 1 : 0)
