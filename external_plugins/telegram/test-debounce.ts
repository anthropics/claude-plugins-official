/**
 * Tests for debounce v9 — everything in ONE notification.
 * Run: bun test-debounce.ts
 */

type MediaRef = { kind: string; file_id: string; file_unique_id?: string; size?: number; mime?: string; name?: string }
type BufferedMessage = { text: string; chatId: string; messageId: number | undefined; user: string; userId: string; ts: string; media: MediaRef | undefined }
type PendingBatch = { messages: BufferedMessage[]; timer: ReturnType<typeof setTimeout> }

const pendingBatches = new Map<string, PendingBatch>()
const emitted: { content: string; meta: Record<string, string> }[] = []

function emitNotification(content: string, meta: Record<string, string>): void {
  emitted.push({ content, meta })
}

function buildMeta(msg: BufferedMessage, extra?: Record<string, string>): Record<string, string> {
  return { chat_id: msg.chatId, ...(msg.messageId != null ? { message_id: String(msg.messageId) } : {}), user: msg.user, user_id: msg.userId, ts: msg.ts, ...extra }
}

function debounceMessage(msg: BufferedMessage, delayMs: number): void {
  const chatId = msg.chatId
  const existing = pendingBatches.get(chatId)
  if (existing) { clearTimeout(existing.timer); existing.messages.push(msg); existing.timer = setTimeout(() => flushBatch(chatId), delayMs) }
  else { const timer = setTimeout(() => flushBatch(chatId), delayMs); pendingBatches.set(chatId, { messages: [msg], timer }) }
}

async function downloadPhoto(fileId: string, fileUniqueId: string): Promise<string | undefined> {
  return `/tmp/inbox/${fileUniqueId}.jpg`
}

async function flushBatch(chatId: string): Promise<void> {
  const batch = pendingBatches.get(chatId)
  if (!batch) return
  pendingBatches.delete(chatId)

  const parts: string[] = []
  const meta = buildMeta(batch.messages[0])
  const attachments: { kind: string; file_id: string; size?: number; mime?: string; name?: string }[] = []

  for (const msg of batch.messages) {
    meta.ts = msg.ts
    if (msg.media) {
      if (msg.media.kind === 'photo' && msg.media.file_unique_id) {
        const path = await downloadPhoto(msg.media.file_id, msg.media.file_unique_id)
        if (msg.text && msg.text !== '(photo)') parts.push(msg.text)
        if (path) { parts.push(`[image: ${path}]`); if (!meta.image_path) meta.image_path = path }
      } else {
        if (msg.text) parts.push(msg.text)
        attachments.push({ kind: msg.media.kind, file_id: msg.media.file_id, size: msg.media.size, mime: msg.media.mime, name: msg.media.name })
      }
    } else {
      parts.push(msg.text)
    }
  }

  if (attachments.length > 0) {
    const first = attachments[0]
    meta.attachment_kind = first.kind; meta.attachment_file_id = first.file_id
    if (first.size != null) meta.attachment_size = String(first.size)
    if (first.mime) meta.attachment_mime = first.mime; if (first.name) meta.attachment_name = first.name
  }
  emitNotification(parts.join('\n'), meta)
}

function msg(chatId: string, text: string, ts: string, media?: MediaRef): BufferedMessage {
  return { text, chatId, messageId: undefined, user: 'test', userId: '123', ts, media }
}
function sleep(ms: number): Promise<void> { return new Promise(r => setTimeout(r, ms)) }
const D = 500

async function test1_textOnly() {
  console.log('\n=== TEST 1: 3 text → 1 notification ===')
  emitted.length = 0
  debounceMessage(msg('c1', 'привет', '1'), D)
  debounceMessage(msg('c1', '3 сообщения', '2'), D)
  debounceMessage(msg('c1', 'вот', '3'), D)
  await sleep(D + 100)
  const pass = emitted.length === 1 && emitted[0].content === 'привет\n3 сообщения\nвот'
  console.log(`  ${emitted.length} notif (exp 1) ${pass ? '✅' : '❌'}`)
  return pass
}

async function test2_textPhotoText() {
  console.log('\n=== TEST 2: text + photo + text → 1 notification ===')
  emitted.length = 0
  debounceMessage(msg('c2', 'вот фото', '1'), D)
  debounceMessage(msg('c2', '(photo)', '2', { kind: 'photo', file_id: 'f1', file_unique_id: 'u1' }), D)
  debounceMessage(msg('c2', 'и ещё текст', '3'), D)
  await sleep(D + 100)
  const pass = emitted.length === 1
    && emitted[0].content === 'вот фото\n[image: /tmp/inbox/u1.jpg]\nи ещё текст'
    && emitted[0].meta.image_path === '/tmp/inbox/u1.jpg'
  console.log(`  ${emitted.length} notif (exp 1) content: "${emitted[0]?.content}" ${pass ? '✅' : '❌'}`)
  if (!pass) console.log(`  meta: ${JSON.stringify(emitted[0]?.meta)}`)
  return pass
}

async function test3_threePhotos() {
  console.log('\n=== TEST 3: 3 photos → 1 notification with 3 image paths ===')
  emitted.length = 0
  debounceMessage(msg('c3', '(photo)', '1', { kind: 'photo', file_id: 'f1', file_unique_id: 'u1' }), D)
  debounceMessage(msg('c3', '(photo)', '2', { kind: 'photo', file_id: 'f2', file_unique_id: 'u2' }), D)
  debounceMessage(msg('c3', '(photo)', '3', { kind: 'photo', file_id: 'f3', file_unique_id: 'u3' }), D)
  await sleep(D + 100)
  const pass = emitted.length === 1
    && emitted[0].content.includes('[image: /tmp/inbox/u1.jpg]')
    && emitted[0].content.includes('[image: /tmp/inbox/u2.jpg]')
    && emitted[0].content.includes('[image: /tmp/inbox/u3.jpg]')
    && emitted[0].meta.image_path === '/tmp/inbox/u1.jpg'
  console.log(`  ${emitted.length} notif (exp 1) ${pass ? '✅' : '❌'}`)
  if (!pass) console.log(`  content: "${emitted[0]?.content}"`)
  return pass
}

async function test4_complexMix() {
  console.log('\n=== TEST 4: text text photo text text photo text → 1 notification ===')
  emitted.length = 0
  debounceMessage(msg('c4', 'a', '1'), D)
  debounceMessage(msg('c4', 'b', '2'), D)
  debounceMessage(msg('c4', '(photo)', '3', { kind: 'photo', file_id: 'f1', file_unique_id: 'u1' }), D)
  debounceMessage(msg('c4', 'c', '4'), D)
  debounceMessage(msg('c4', 'd', '5'), D)
  debounceMessage(msg('c4', '(photo)', '6', { kind: 'photo', file_id: 'f2', file_unique_id: 'u2' }), D)
  debounceMessage(msg('c4', 'e', '7'), D)
  await sleep(D + 100)
  const pass = emitted.length === 1
    && emitted[0].content === 'a\nb\n[image: /tmp/inbox/u1.jpg]\nc\nd\n[image: /tmp/inbox/u2.jpg]\ne'
  console.log(`  ${emitted.length} notif (exp 1) ${pass ? '✅' : '❌'}`)
  if (!pass) console.log(`  content: "${emitted[0]?.content}"`)
  return pass
}

async function test5_voiceAttachment() {
  console.log('\n=== TEST 5: text + voice + text → 1 notification ===')
  emitted.length = 0
  debounceMessage(msg('c5', 'послушай', '1'), D)
  debounceMessage(msg('c5', '(voice message)', '2', { kind: 'voice', file_id: 'vf1', mime: 'audio/ogg', size: 12345 }), D)
  debounceMessage(msg('c5', 'ну как?', '3'), D)
  await sleep(D + 100)
  const pass = emitted.length === 1
    && emitted[0].content === 'послушай\n(voice message)\nну как?'
    && emitted[0].meta.attachment_kind === 'voice'
    && emitted[0].meta.attachment_file_id === 'vf1'
  console.log(`  ${emitted.length} notif (exp 1) ${pass ? '✅' : '❌'}`)
  if (!pass) console.log(`  content: "${emitted[0]?.content}" meta: ${JSON.stringify(emitted[0]?.meta)}`)
  return pass
}

async function test6_textThenDocument() {
  console.log('\n=== TEST 6: text + doc → 1 notification ===')
  emitted.length = 0
  debounceMessage(msg('c6', 'вот доки', '1'), D)
  debounceMessage(msg('c6', '(document: file.pdf)', '2', { kind: 'document', file_id: 'df1', mime: 'application/pdf', name: 'file.pdf', size: 99999 }), D)
  await sleep(D + 100)
  const pass = emitted.length === 1
    && emitted[0].content === 'вот доки\n(document: file.pdf)'
    && emitted[0].meta.attachment_kind === 'document'
  console.log(`  ${emitted.length} notif (exp 1) ${pass ? '✅' : '❌'}`)
  return pass
}

async function test7_metaPreservation() {
  console.log('\n=== TEST 7: merged text keeps first message_id, latest ts ===')
  emitted.length = 0
  debounceMessage({ text: 'first', chatId: 'c7', messageId: 100, user: 'u', userId: '1', ts: 'early', media: undefined }, D)
  debounceMessage({ text: 'second', chatId: 'c7', messageId: 200, user: 'u', userId: '1', ts: 'latest', media: undefined }, D)
  await sleep(D + 100)
  const pass = emitted.length === 1 && emitted[0].meta.message_id === '100' && emitted[0].meta.ts === 'latest'
  console.log(`  msg_id: ${emitted[0]?.meta.message_id} (exp 100) ts: ${emitted[0]?.meta.ts} (exp latest) ${pass ? '✅' : '❌'}`)
  return pass
}

async function test8_differentChats() {
  console.log('\n=== TEST 8: different chats independent ===')
  emitted.length = 0
  debounceMessage(msg('cA', 'hello A', '1'), D)
  debounceMessage(msg('cB', 'hello B', '1'), D)
  debounceMessage(msg('cA', 'more A', '2'), D)
  await sleep(D + 100)
  const a = emitted.filter(e => e.meta.chat_id === 'cA')
  const b = emitted.filter(e => e.meta.chat_id === 'cB')
  const pass = a.length === 1 && a[0].content === 'hello A\nmore A' && b.length === 1 && b[0].content === 'hello B'
  console.log(`  total: ${emitted.length} (exp 2) ${pass ? '✅' : '❌'}`)
  return pass
}

async function test9_realWorld() {
  console.log('\n=== TEST 9: real scenario — text + 3 photos + text → 1 notification ===')
  emitted.length = 0
  debounceMessage(msg('c9', 'ПРОВЕРКА', '1'), D)
  debounceMessage(msg('c9', 'Длинный текст поста', '2', { kind: 'photo', file_id: 'p1', file_unique_id: 'pu1' }), D)
  debounceMessage(msg('c9', '(photo)', '3', { kind: 'photo', file_id: 'p2', file_unique_id: 'pu2' }), D)
  debounceMessage(msg('c9', '(photo)', '4', { kind: 'photo', file_id: 'p3', file_unique_id: 'pu3' }), D)
  debounceMessage(msg('c9', 'Лидерборд: Gemini 0.2%', '5'), D)
  await sleep(D + 100)
  const pass = emitted.length === 1
    && emitted[0].content.includes('ПРОВЕРКА')
    && emitted[0].content.includes('Длинный текст поста')
    && emitted[0].content.includes('[image: /tmp/inbox/pu1.jpg]')
    && emitted[0].content.includes('[image: /tmp/inbox/pu2.jpg]')
    && emitted[0].content.includes('[image: /tmp/inbox/pu3.jpg]')
    && emitted[0].content.includes('Лидерборд: Gemini 0.2%')
    && emitted[0].meta.image_path === '/tmp/inbox/pu1.jpg'
  console.log(`  ${emitted.length} notif (exp 1) ${pass ? '✅' : '❌'}`)
  if (!pass) console.log(`  content: "${emitted[0]?.content}"`)
  return pass
}

async function test10_photoWithCaption() {
  console.log('\n=== TEST 10: photo with caption (not "(photo)") preserved ===')
  emitted.length = 0
  debounceMessage(msg('c10', 'Красивый закат', '1', { kind: 'photo', file_id: 'f1', file_unique_id: 'u1' }), D)
  await sleep(D + 100)
  const pass = emitted.length === 1
    && emitted[0].content === 'Красивый закат\n[image: /tmp/inbox/u1.jpg]'
    && emitted[0].meta.image_path === '/tmp/inbox/u1.jpg'
  console.log(`  ${emitted.length} notif (exp 1) content: "${emitted[0]?.content}" ${pass ? '✅' : '❌'}`)
  return pass
}

;(async () => {
  const results = [
    await test1_textOnly(), await test2_textPhotoText(), await test3_threePhotos(),
    await test4_complexMix(), await test5_voiceAttachment(), await test6_textThenDocument(),
    await test7_metaPreservation(), await test8_differentChats(), await test9_realWorld(),
    await test10_photoWithCaption(),
  ]
  const passed = results.filter(Boolean).length
  console.log(`\n${'='.repeat(50)}`)
  console.log(`Results: ${passed}/${results.length} passed`)
  console.log(passed === results.length ? '🎉 All tests passed!' : '💀 Some tests failed')
  if (passed !== results.length) process.exit(1)
})()
