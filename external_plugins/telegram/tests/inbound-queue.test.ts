// Regression tests for inbound message pairing. A single "latest inbound"
// pointer used to answer the wrong message whenever a second one arrived while
// the assistant was still working on the first.
import { readFileSync, writeFileSync } from 'fs'

const EXTRACTED = '/tmp/tg-inbound-extracted.ts'
const src = readFileSync(new URL('../server.ts', import.meta.url), 'utf8')

function grab(header: string): string {
  const start = src.indexOf(header)
  if (start < 0) throw new Error(`missing: ${header}`)
  // The body brace is the last one on the signature line.
  const open = src.lastIndexOf('{', src.indexOf('\n', start))
  let depth = 0
  for (let j = open; j < src.length; j++) {
    if (src[j] === '{') depth++
    else if (src[j] === '}' && --depth === 0) return src.slice(start, j + 1)
  }
  throw new Error(`unbalanced: ${header}`)
}

writeFileSync(EXTRACTED, [
  src.match(/^const pendingInbound = .*$/m)![0],
  src.match(/^const MAX_PENDING_INBOUND = .*$/m)![0],
  grab('function pushInbound('),
  grab('function peekInbound('),
  grab('function takeInbound('),
  'export { pushInbound, peekInbound, takeInbound, pendingInbound, MAX_PENDING_INBOUND }',
].join('\n\n'))

const q = await import(EXTRACTED)
const { pushInbound, peekInbound, takeInbound, pendingInbound, MAX_PENDING_INBOUND } = q as {
  pushInbound: (c: string, m: number) => void
  peekInbound: (c: string) => number | undefined
  takeInbound: (c: string, m: number | undefined) => void
  pendingInbound: Map<string, number[]>
  MAX_PENDING_INBOUND: number
}

let fails = 0
const ok = (cond: boolean, msg: string) => {
  console.log(`${cond ? 'PASS' : 'FAIL'}  ${msg}`)
  if (!cond) fails++
}
const reset = () => pendingInbound.clear()

reset()
ok(peekInbound('c') === undefined, 'empty chat has nothing to answer')

reset()
pushInbound('c', 10)
ok(peekInbound('c') === 10, 'single message is the answer target')

// The actual bug: two messages in flight, the answer must go to the first.
reset()
pushInbound('c', 10)
pushInbound('c', 11)
ok(peekInbound('c') === 10, 'second message does not steal the answer target')
takeInbound('c', 10)
ok(peekInbound('c') === 11, 'answering the first moves on to the second')
takeInbound('c', 11)
ok(peekInbound('c') === undefined, 'queue empties once both are answered')

// An explicit reply_to may address a message out of order.
reset()
pushInbound('c', 10)
pushInbound('c', 11)
pushInbound('c', 12)
takeInbound('c', 11)
ok(peekInbound('c') === 10, 'answering out of order retires only that message')
takeInbound('c', 10)
ok(peekInbound('c') === 12, 'remaining messages keep their order')

reset()
pushInbound('a', 1)
pushInbound('b', 2)
ok(peekInbound('a') === 1 && peekInbound('b') === 2, 'chats are independent')

reset()
pushInbound('c', 10)
takeInbound('c', 999)
ok(peekInbound('c') === 10, 'retiring an unknown id leaves the queue alone')
takeInbound('c', undefined)
ok(peekInbound('c') === undefined, 'no id retires the oldest')

reset()
for (let i = 0; i < MAX_PENDING_INBOUND + 5; i++) pushInbound('c', i)
ok(pendingInbound.get('c')!.length === MAX_PENDING_INBOUND, 'queue is bounded')
ok(peekInbound('c') === 5, 'overflow drops the oldest, not the newest')

console.log(fails ? `\n${fails} FAILURE(S)` : '\nall green')
process.exit(fails ? 1 : 0)
