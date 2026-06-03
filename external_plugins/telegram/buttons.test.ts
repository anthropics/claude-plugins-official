// Smash-test for the OTTO-97 telegram buttons feature. Drives the REAL vendored
// server.ts with grammy + the MCP SDK mocked out — no network, no token, no
// poller. Fires synthetic reply/edit_message tool calls and synthetic
// callback_query taps at the actual handlers and asserts behaviour across the
// whole surface: SEND validation, callback round-trip, auth, once-consume, TTL,
// the #2103 message_id fix, perm: regression, unknown-callback drop.
import { test, expect, mock, beforeAll } from 'bun:test'
import { mkdtempSync, writeFileSync, mkdirSync } from 'fs'
import { tmpdir } from 'os'
import { join } from 'path'
// real schemas (NOT mocked) so Map lookups match server.ts's references
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js'
// real, pure InlineKeyboard (absolute path; not caught by the 'grammy' mock)
import { InlineKeyboard } from './node_modules/grammy/out/convenience/keyboard.js'

// ---- temp state dir with a controlled access.json -------------------------
const STATE = mkdtempSync(join(tmpdir(), 'tgtest-'))
mkdirSync(STATE, { recursive: true })
writeFileSync(join(STATE, 'access.json'), JSON.stringify({
  dmPolicy: 'allowlist',
  allowFrom: ['111', '222'],          // 111,222 are "operators"
  groups: { '-900': { requireMention: false, allowFrom: [] } },
  pending: {},
}))
process.env.TELEGRAM_STATE_DIR = STATE
process.env.TELEGRAM_BOT_TOKEN = 'test:token'

// ---- capture buckets ------------------------------------------------------
const cap = {
  call: new Map<unknown, Function>(),
  notif: new Map<unknown, Function>(),
  notifications: [] as any[],
  bot: new Map<string, Function>(),
  api: [] as { method: string; args: any[] }[],
}
let nextId = 1000

// ---- mock the MCP server + transport --------------------------------------
mock.module('@modelcontextprotocol/sdk/server/stdio.js', () => ({
  StdioServerTransport: class { },
}))
mock.module('@modelcontextprotocol/sdk/server/index.js', () => ({
  Server: class {
    constructor(_i: any, _o: any) {}
    setRequestHandler(schema: unknown, h: Function) { cap.call.set(schema, h) }
    setNotificationHandler(schema: unknown, h: Function) { cap.notif.set(schema, h) }
    async notification(msg: any) { cap.notifications.push(msg) }
    async connect() {}
  },
}))

// ---- mock grammy (FakeBot; real InlineKeyboard) ---------------------------
function makeApi() {
  return new Proxy({}, {
    get: (_t, method: string) => async (...args: any[]) => {
      cap.api.push({ method, args })
      if (['sendMessage', 'editMessageText', 'sendPhoto', 'sendDocument'].includes(method)) {
        return { message_id: nextId++ }
      }
      return {}
    },
  })
}
mock.module('grammy', () => ({
  Bot: class {
    api = makeApi()
    constructor(_t: string) {}
    on(ev: string, h: Function) { cap.bot.set(ev, h) }
    command(n: string, h: Function) { cap.bot.set('cmd:' + n, h) }
    catch(h: Function) { cap.bot.set('catch', h) }
    async start(opts: any) { opts?.onStart?.({ username: 'testbot' }); return new Promise(() => {}) }
    async stop() {}
  },
  GrammyError: class extends Error {},
  InlineKeyboard,
  InputFile: class { constructor(public f: string) {} },
}))

beforeAll(async () => {
  await import('./server.ts')
})

// ---- helpers --------------------------------------------------------------
const reply = (args: any) => cap.call.get(CallToolRequestSchema)!({ params: { name: 'reply', arguments: args } })
const edit = (args: any) => cap.call.get(CallToolRequestSchema)!({ params: { name: 'edit_message', arguments: args } })
const lastSend = () => [...cap.api].reverse().find(c => c.method === 'sendMessage')!
function cbDataFrom(sendCall: { args: any[] }): string[] {
  const rm = sendCall.args[2]?.reply_markup
  const kb = rm?.inline_keyboard ?? rm?.toJSON?.()?.inline_keyboard ?? []
  return kb.flat().map((b: any) => b.callback_data).filter(Boolean)
}
function makeTapCtx(data: string, fromId: string, msgId = 1000) {
  const answers: any[] = []
  const ctx: any = {
    callbackQuery: { data, message: { message_id: msgId, date: 1_700_000_000 } },
    from: { id: Number(fromId), username: 'u' + fromId },
    answerCallbackQuery: async (opts?: any) => { answers.push(opts ?? null) },
    editMessageText: async () => {},
    editMessageReplyMarkup: async () => {},
    api: makeApi(),
  }
  return { ctx, answers }
}
const fireTap = (data: string, fromId: string, msgId = 1000) => {
  const { ctx, answers } = makeTapCtx(data, fromId, msgId)
  return cap.bot.get('callback_query:data')!(ctx).then(() => answers)
}

// ========================= SEND validation matrix =========================
test('reply with valid 2x callback row → sends with inline_keyboard, callback_data <=64B', async () => {
  const r: any = await reply({ chat_id: '111', text: 'pick', buttons: [[{ text: 'Yes', callback: 'yp' }, { text: 'No', callback: 'np' }]] })
  expect(r.isError).toBeFalsy()
  const datas = cbDataFrom(lastSend())
  expect(datas.length).toBe(2)
  for (const d of datas) { expect(d).toMatch(/^cb:[0-9a-f]{8}:[0-9a-f]{2}$/); expect(Buffer.byteLength(d)).toBeLessThanOrEqual(64) }
})
test('url + copy_text buttons accepted, no callback record needed', async () => {
  const r: any = await reply({ chat_id: '111', text: 'links', buttons: [[{ text: 'site', url: 'https://x.com' }, { text: 'copy', copy_text: 'ABC' }]] })
  expect(r.isError).toBeFalsy()
})
const bad = [
  ['empty grid', { buttons: [] }],
  ['empty row only', { buttons: [[]] }],
  ['row not array', { buttons: [{ text: 'x', callback: 'y' }] }],
  ['no action', { buttons: [[{ text: 'x' }]] }],
  ['two actions', { buttons: [[{ text: 'x', callback: 'a', url: 'https://x' }]] }],
  ['no text', { buttons: [[{ callback: 'a' }]] }],
  ['>8 per row', { buttons: [Array.from({ length: 9 }, (_, i) => ({ text: 't' + i, callback: 'c' + i }))] }],
  ['>100 total', { buttons: Array.from({ length: 101 }, (_, i) => [{ text: 't' + i, callback: 'c' + i }]) }],
  ['payload >4096', { buttons: [[{ text: 'x', callback: 'p'.repeat(4097) }]] }],
  ['copy_text >256', { buttons: [[{ text: 'x', copy_text: 'c'.repeat(257) }]] }],
  ['ack >200', { buttons: [[{ text: 'x', callback: 'a' }]], button_options: { ack: 'a'.repeat(201) } }],
] as const
for (const [name, extra] of bad) {
  test(`SEND rejects: ${name}`, async () => {
    const r: any = await reply({ chat_id: '111', text: 't', ...(extra as any) })
    expect(r.isError).toBe(true)
    expect(String(r.content?.[0]?.text)).toMatch(/reply failed/i)
  })
}
test('SEND rejects un-allowlisted chat', async () => {
  const r: any = await reply({ chat_id: '999', text: 't', buttons: [[{ text: 'x', callback: 'a' }]] })
  expect(r.isError).toBe(true)
})

// ========================= callback round-trip =========================
test('valid operator tap → forwards inbound with payload/message_id/mode, answers spinner', async () => {
  await reply({ chat_id: '111', text: 'q', buttons: [[{ text: 'Approve', callback: 'PAYLOAD-A' }]], button_options: { ack: 'noted' } })
  const data = cbDataFrom(lastSend())[0]
  const before = cap.notifications.length
  const answers = await fireTap(data, '111', 1000)
  const n = cap.notifications[cap.notifications.length - 1]
  expect(cap.notifications.length).toBe(before + 1)
  expect(n.params.meta.callback).toBe('true')
  expect(n.params.meta.callback_payload).toBe('PAYLOAD-A')
  expect(n.params.meta.button_text).toBe('Approve')
  expect(n.params.meta.message_id).toBe('1000')           // #2103: from callbackQuery.message
  expect(answers[0]).toEqual({ text: 'noted' })            // ack toast
})
test('operator-mode: non-allowlisted tapper rejected, no inbound forwarded', async () => {
  await reply({ chat_id: '111', text: 'q', buttons: [[{ text: 'x', callback: 'secret' }]] })
  const data = cbDataFrom(lastSend())[0]
  const before = cap.notifications.length
  const answers = await fireTap(data, '8675309', 1000)     // not in allowFrom
  expect(answers[0]).toEqual({ text: 'Not authorized.' })
  expect(cap.notifications.length).toBe(before)            // nothing forwarded
})
test('anyone-mode: non-allowlisted tapper allowed through', async () => {
  await reply({ chat_id: '111', text: 'poll', buttons: [[{ text: 'x', callback: 'v' }]], button_options: { who_may_tap: 'anyone' } })
  const data = cbDataFrom(lastSend())[0]
  const before = cap.notifications.length
  await fireTap(data, '8675309', 1000)
  expect(cap.notifications.length).toBe(before + 1)
})
test('once-mode: second tap rejected with "Already answered"', async () => {
  await reply({ chat_id: '111', text: 'q', buttons: [[{ text: 'x', callback: 'v' }]] }) // default once
  const data = cbDataFrom(lastSend())[0]
  const a1 = await fireTap(data, '111', 1000)
  const before = cap.notifications.length
  const a2 = await fireTap(data, '111', 1000)
  expect(a2[0]).toEqual({ text: 'Already answered.' })
  expect(cap.notifications.length).toBe(before)            // no second forward
})
test('persistent-mode: repeated taps keep forwarding', async () => {
  await reply({ chat_id: '111', text: 'menu', buttons: [[{ text: 'x', callback: 'v' }]], button_options: { mode: 'persistent' } })
  const data = cbDataFrom(lastSend())[0]
  const before = cap.notifications.length
  await fireTap(data, '111', 1000); await fireTap(data, '111', 1000); await fireTap(data, '111', 1000)
  expect(cap.notifications.length).toBe(before + 3)
})
test('unknown kbId → "expired" toast, no forward', async () => {
  const answers = await fireTap('cb:deadbeef:00', '111', 1000)
  expect(answers[0]).toEqual({ text: 'This button has expired.' })
})
test('TTL: tap after expiry → "expired"', async () => {
  await reply({ chat_id: '111', text: 'q', buttons: [[{ text: 'x', callback: 'v' }]], button_options: { ttl_seconds: 1 } })
  const data = cbDataFrom(lastSend())[0]
  await new Promise(r => setTimeout(r, 1100))
  const answers = await fireTap(data, '111', 1000)
  expect(answers[0]).toEqual({ text: 'This button has expired.' })
})
test('unknown (non-cb, non-perm) callback data → silent drop (bare answer)', async () => {
  const answers = await fireTap('garbage:data', '111', 1000)
  expect(answers[0]).toBeFalsy()                            // answerCallbackQuery() with no opts
})
test('perm: path still routes (regression — untouched)', async () => {
  // perm:more for an unknown request_id → answers "Details no longer available", not a cb drop
  const answers = await fireTap('perm:more:abcde', '111', 1000)
  expect(answers.length).toBeGreaterThan(0)                // perm branch handled it
})

// ========================= edit_message buttons =========================
test('edit_message with buttons attaches reply_markup; without → clears', async () => {
  const r1: any = await edit({ chat_id: '111', message_id: '500', text: 'upd', buttons: [[{ text: 'x', callback: 'v' }]] })
  expect(r1.isError).toBeFalsy()
  const ec = [...cap.api].reverse().find(c => c.method === 'editMessageText')!
  expect(ec.args[3]?.reply_markup).toBeTruthy()
  const r2: any = await edit({ chat_id: '111', message_id: '500', text: 'done' })
  expect(r2.isError).toBeFalsy()
  const ec2 = [...cap.api].reverse().find(c => c.method === 'editMessageText')!
  expect(ec2.args[3]?.reply_markup).toBeFalsy()            // no markup → keyboard cleared
})

// ========================= boundaries & odd inputs =========================
test('BOUNDARY: copy_text exactly 256 ok, payload exactly 4096 ok, 8/row ok, 100 total ok', async () => {
  const r1: any = await reply({ chat_id: '111', text: 't', buttons: [[{ text: 'x', copy_text: 'c'.repeat(256) }]] })
  expect(r1.isError).toBeFalsy()
  const r2: any = await reply({ chat_id: '111', text: 't', buttons: [[{ text: 'x', callback: 'p'.repeat(4096) }]] })
  expect(r2.isError).toBeFalsy()
  const r3: any = await reply({ chat_id: '111', text: 't', buttons: [Array.from({ length: 8 }, (_, i) => ({ text: 't' + i, callback: 'c' + i }))] })
  expect(r3.isError).toBeFalsy()
  const r4: any = await reply({ chat_id: '111', text: 't', buttons: Array.from({ length: 100 }, (_, i) => [{ text: 't' + i, callback: 'c' + i }]) })
  expect(r4.isError).toBeFalsy()
})
test('100-button grid: every callback_data unique and <=64B', async () => {
  await reply({ chat_id: '111', text: 't', buttons: Array.from({ length: 100 }, (_, i) => [{ text: 't' + i, callback: 'c' + i }]) })
  const datas = cbDataFrom(lastSend())
  expect(datas.length).toBe(100)
  expect(new Set(datas).size).toBe(100)                    // all distinct
  for (const d of datas) expect(Buffer.byteLength(d)).toBeLessThanOrEqual(64)
})
test('no-ack tap → bare spinner clear (answerCallbackQuery with no opts)', async () => {
  await reply({ chat_id: '111', text: 'q', buttons: [[{ text: 'x', callback: 'v' }]] })
  const data = cbDataFrom(lastSend())[0]
  const answers = await fireTap(data, '111', 1000)
  expect(answers[0]).toBeFalsy()                            // undefined, not {text:...}
})
test('unicode + emoji + newline payload round-trips verbatim', async () => {
  const payload = '✅ y\nés—{"k":"v"} 日本語'
  await reply({ chat_id: '111', text: 'q', buttons: [[{ text: '🆗', callback: payload }]] })
  const data = cbDataFrom(lastSend())[0]
  await fireTap(data, '111', 1000)
  const n = cap.notifications[cap.notifications.length - 1]
  expect(n.params.meta.callback_payload).toBe(payload)
  expect(n.params.meta.button_text).toBe('🆗')
})
test('multi-chunk text (>4096): buttons attach to LAST chunk only', async () => {
  const big = 'A'.repeat(9000)                              // 3 chunks at 4096
  await reply({ chat_id: '111', text: big, buttons: [[{ text: 'x', callback: 'v' }]] })
  const sends = cap.api.filter(c => c.method === 'sendMessage').slice(-3)
  expect(sends.length).toBe(3)
  expect(sends[0].args[2]?.reply_markup).toBeFalsy()
  expect(sends[1].args[2]?.reply_markup).toBeFalsy()
  expect(sends[2].args[2]?.reply_markup).toBeTruthy()      // only the last carries buttons
})
test('tap when callbackQuery.message absent → falls back to stored messageId (no crash)', async () => {
  await reply({ chat_id: '111', text: 'q', buttons: [[{ text: 'x', callback: 'v' }]] })
  const data = cbDataFrom(lastSend())[0]
  // ctx with message undefined (very old message) — must not throw, still forwards
  const answers: any[] = []
  const ctx: any = { callbackQuery: { data, message: undefined }, from: { id: 111, username: 'u' },
    answerCallbackQuery: async (o?: any) => { answers.push(o ?? null) } }
  const before = cap.notifications.length
  await cap.bot.get('callback_query:data')!(ctx)
  expect(cap.notifications.length).toBe(before + 1)        // still forwarded (no crash)
})
test('mixed row: callback + url + copy_text together; only callback gets callback_data', async () => {
  await reply({ chat_id: '111', text: 't', buttons: [[
    { text: 'cb', callback: 'p' }, { text: 'u', url: 'https://x.com' }, { text: 'cp', copy_text: 'Z' }]] })
  const rm = lastSend().args[2].reply_markup
  const row = (rm.inline_keyboard ?? rm.toJSON?.().inline_keyboard)[0]
  expect(row[0].callback_data).toMatch(/^cb:/)
  expect(row[1].url).toBe('https://x.com')
  expect(row[2].copy_text.text).toBe('Z')
})

// ========================= reply_markup size guard =========================
test('SIZE: keyboard whose serialized reply_markup exceeds the cap is rejected locally', async () => {
  // 50 buttons x 220-char labels -> serialized well over REPLY_MARKUP_MAX (9000)
  const rows = Array.from({ length: 50 }, (_, i) => [{ text: 'L'.repeat(220), callback: 'c' + i }])
  const r: any = await reply({ chat_id: '111', text: 't', buttons: rows })
  expect(r.isError).toBe(true)
  expect(String(r.content?.[0]?.text)).toMatch(/too large|bytes serialized/i)
})
test('SIZE: a generous-but-reasonable keyboard (under the cap) is accepted', async () => {
  // 40 buttons, ~24-char labels -> a few KB, well under the cap
  const rows = Array.from({ length: 20 }, (_, i) => [
    { text: 'Option number ' + i + ' label', callback: 'a' + i },
    { text: 'Other choice ' + i + ' label', callback: 'b' + i },
  ])
  const r: any = await reply({ chat_id: '111', text: 't', buttons: rows })
  expect(r.isError).toBeFalsy()
})

// ========================= targeted: url / whitespace / ttl =========================
test('URL: rejects no-scheme & disallowed schemes, accepts http(s)/tg', async () => {
  for (const u of ['example.com', 'javascript:alert(1)', 'ftp://x.com', 'http://', 'not a url', '', '//x.com', 'data:text/html,x']) {
    const r: any = await reply({ chat_id: '111', text: 't', buttons: [[{ text: 'x', url: u }]] })
    expect(r.isError).toBe(true)
  }
  for (const u of ['https://x.com', 'http://x.com/a?b=1#c', 'tg://user?id=1']) {
    const r: any = await reply({ chat_id: '111', text: 't', buttons: [[{ text: 'ok', url: u }]] })
    expect(r.isError).toBeFalsy()
  }
})
test('whitespace-only label rejected; padded real label kept', async () => {
  const bad: any = await reply({ chat_id: '111', text: 't', buttons: [[{ text: '   ', callback: 'a' }]] })
  expect(bad.isError).toBe(true)
  const ok: any = await reply({ chat_id: '111', text: 't', buttons: [[{ text: '  hi  ', callback: 'a' }]] })
  expect(ok.isError).toBeFalsy()
})
test('garbage ttl_seconds → keyboard still has a sane (non-NaN) expiry and taps work', async () => {
  for (const ttl of ['soon', NaN, Infinity, -5, 0, {}, null]) {
    const r: any = await reply({ chat_id: '111', text: 't', buttons: [[{ text: 'x', callback: 'v' }]], button_options: { ttl_seconds: ttl as any } })
    expect(r.isError).toBeFalsy()
  }
  const data = cbDataFrom(lastSend())[0] // last was ttl:null -> default
  const ans = await fireTap(data, '111', 1000)
  expect(ans[0]).not.toEqual({ text: 'This button has expired.' })
})

// ========================= FUZZ: random junk =========================
let _seed = 0x9e3779b9
const rnd = () => { _seed = (Math.imul(_seed, 1103515245) + 12345) & 0x7fffffff; return _seed / 0x7fffffff }
const pick = <T,>(a: T[]): T => a[Math.floor(rnd() * a.length)]
const ri = (n: number) => Math.floor(rnd() * n)
const hx = (n: number) => Array.from({ length: n }, () => '0123456789abcdef'[ri(16)]).join('')
// nasty values: wrong types, empties, control/null chars, huge, unicode, lone
// surrogate, injection-ish, RTL override, numbers, objects, a throwing toString.
const JUNK: any[] = [
  '', ' ', '   ', '\n\t\r', '\x00', '\x00\x01', 'x', 'A'.repeat(20000),
  '\u{1F916}\u{1F525}', 'foo', '\uD800', '\uDC00', '‮rev', 'á',
  '"; DROP TABLE--', '{"a":1}', '</script><b>', 'cb:deadbeef:00', 'perm:allow:abcde',
  'https://x.com', 'http://', 'tg://user?id=1', 'javascript:alert(1)', 'example.com', ' https://x.com ',
  0, 1, -1, 3.14, NaN, Infinity, -Infinity, 1e21, true, false, null, undefined,
  {}, [], [1, 2], { text: 'x' }, { toString() { throw new Error('evil') } },
]
const j = () => pick(JUNK)
function randButton(): any {
  if (rnd() < 0.05) return j() // sometimes not an object at all
  const b: any = {}
  if (rnd() < 0.9) b.text = j()
  const n = ri(4)
  for (let i = 0; i < n; i++) b[pick(['callback', 'url', 'copy_text'])] = j()
  if (rnd() < 0.15) b['extra' + ri(9)] = j()
  return b
}
function randGrid(): any {
  if (rnd() < 0.08) return pick([[], null, undefined, 'nope', 42, {}, [[]], [null], ['x'], [42]])
  return Array.from({ length: ri(13) }, () =>
    rnd() < 0.1 ? pick([null, 'x', 42, {}, undefined]) : Array.from({ length: ri(13) }, randButton))
}
function randOpts(): any {
  if (rnd() < 0.3) return undefined
  return {
    mode: pick(['once', 'persistent', 'weird', null, 42, undefined]),
    who_may_tap: pick(['operator', 'anyone', 'x', null, 7]),
    ack: j(),
    ttl_seconds: pick([60, 0, -5, NaN, Infinity, 'soon', null, 1e12, {}, 3.9]),
  }
}
const CB_RE = /^cb:[0-9a-f]{8}:[0-9a-f]{2}$/

test('FUZZ reply/edit: never throws uncaught; ok-or-clean-error; any emitted callback_data is legal', async () => {
  for (let i = 0; i < 4000; i++) {
    const args: any = { chat_id: pick(['111', '222', '-900', '999', j()]), text: pick(['hi', j()]),
      buttons: randGrid(), button_options: randOpts() }
    const useEdit = rnd() < 0.5
    if (useEdit) args.message_id = pick(['500', 123, j()])
    let res: any
    try { res = useEdit ? await edit(args) : await reply(args) }
    catch (e) {
      let dump = '<unserializable>'; try { dump = JSON.stringify(args).slice(0, 400) } catch {}
      throw new Error(`THREW (uncaught) i=${i}: ${e}\nargs=${dump}`)
    }
    expect(res && typeof res === 'object').toBe(true)
    if (res.isError) expect(typeof res.content?.[0]?.text).toBe('string')
    else {
      const send = [...cap.api].reverse().find(c => c.method === 'sendMessage' || c.method === 'editMessageText')
      const rm = send?.args?.[2]?.reply_markup ?? send?.args?.[3]?.reply_markup
      for (const b of (rm?.inline_keyboard ?? []).flat()) {
        if (b.callback_data != null) {
          expect(b.callback_data).toMatch(CB_RE)
          expect(Buffer.byteLength(b.callback_data)).toBeLessThanOrEqual(64)
        }
      }
    }
  }
})

test('FUZZ callback handler: never throws uncaught; always clears the spinner', async () => {
  const h = cap.bot.get('callback_query:data')!
  // callbackQuery.data is always a string in reality (Telegram serializes it);
  // a hostile client can still send arbitrary <=64B strings, so fuzz strings.
  const sj = () => { const v = j(); try { return typeof v === 'string' ? v : String(v) } catch { return 'badToString' } }
  for (let i = 0; i < 4000; i++) {
    const data = pick([
      sj(), 'cb:' + hx(ri(12)) + ':' + hx(ri(4)), 'cb:' + hx(8) + ':' + hx(2),
      'perm:' + pick(['allow', 'deny', 'more', 'x', '']) + ':' + Array.from({ length: ri(8) }, () => 'abcdefghijkmnopqrstuvwxyz'[ri(25)]).join(''),
      'cb::', 'cb:' + 'z'.repeat(8) + ':zz', '', ':::', 'cb:' + hx(8),
    ])
    const answers: any[] = []
    const ctx: any = {
      callbackQuery: { data: String(data), message: rnd() < 0.5 ? { message_id: ri(99999), date: ri(2_000_000_000) } : undefined },
      from: { id: pick([111, 222, 999, ri(1e9), 'weird']), username: pick(['u', undefined, 'z']) },
      answerCallbackQuery: async (o?: any) => { answers.push(o ?? null) },
      editMessageText: async () => ({ message_id: 1 }), editMessageReplyMarkup: async () => {},
    }
    try { await h(ctx) }
    catch (e) { throw new Error(`callback handler THREW i=${i} data=${JSON.stringify(String(data))} from=${JSON.stringify(ctx.from.id)}: ${e}`) }
    expect(answers.length).toBeGreaterThanOrEqual(1)
  }
})
