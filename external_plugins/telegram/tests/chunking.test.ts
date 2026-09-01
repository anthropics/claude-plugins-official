const EXTRACTED = '/tmp/tg-extracted.ts'
import { readFileSync, writeFileSync } from 'fs'
const src = readFileSync(new URL('../server.ts', import.meta.url), 'utf8')

// Pull the real definitions out of server.ts (which has boot side effects) into
// a standalone module so bun transpiles and tests the actual source.
function grab(header: string): string {
  const start = src.indexOf(header)
  if (start < 0) throw new Error(`missing: ${header}`)
  // The body brace is the last one on the signature line — an object return
  // type like { safe: number[] } would otherwise be matched instead.
  const open = src.lastIndexOf('{', src.indexOf('\n', start))
  let depth = 0
  for (let j = open; j < src.length; j++) {
    if (src[j] === '{') depth++
    else if (src[j] === '}' && --depth === 0) return src.slice(start, j + 1)
  }
  throw new Error(`unbalanced: ${header}`)
}
const consts = src.match(/^const FENCE_RE = .*$/m)![0] + '\n' + src.match(/^const FENCE_RESERVE = .*$/m)![0]
writeFileSync(EXTRACTED, [
  consts,
  grab('function cutPoints('),
  grab('function healFences('),
  grab('function chunkRich('),
  'export { chunkRich, healFences, cutPoints }',
].join('\n\n'))

const { chunkRich } = await import(EXTRACTED)

let fails = 0
const ok = (cond: boolean, msg: string) => { console.log(`${cond ? 'PASS' : 'FAIL'}  ${msg}`); if (!cond) fails++ }
const fenceBalanced = (parts: string[]) => parts.every(p => (p.match(/^\s{0,3}(```|~~~)/gm) ?? []).length % 2 === 0)
const stripped = (s: string) => s.replace(/```\w*|~~~\w*/g, '').replace(/\s+/g, ' ').trim()

ok(chunkRich('hello', 100).length === 1, 'short text stays one chunk')

const fence = 'intro para\n\n```python\n' + 'x = 1\n'.repeat(40) + '```\n\ntail para\n'
const parts = chunkRich(fence, 120)
ok(parts.length > 1, `oversized code block splits (${parts.length} parts)`)
ok(fenceBalanced(parts), 'every part has balanced fences')
ok(parts.every(p => p.length <= 120), 'every part respects the limit')
ok(parts.filter(p => p.includes('x = 1')).every(p => p.startsWith('```python')), 'reopened fences keep the language tag')
ok(stripped(parts.join('\n')) === stripped(fence), 'no code lines lost or duplicated')

const doc = Array.from({ length: 60 }, (_, i) => `paragraph number ${i} with filler words`).join('\n\n')
const dp = chunkRich(doc, 200)
ok(dp.every(p => p.length <= 200), 'prose respects the limit')
ok(dp.join('\n\n').replace(/\s+/g, ' ') === doc.replace(/\s+/g, ' '), 'prose content preserved exactly')
ok(dp.every(p => !p.endsWith('para') || p.endsWith('words')), 'prose cuts land on paragraph boundaries')

const oneLine = 'z'.repeat(500)
const ol = chunkRich(oneLine, 100)
ok(ol.every(p => p.length <= 100) && ol.join('') === oneLine, 'a single overlong line hard-cuts without loss')

const table = 'head\n\n| a | b |\n| - | - |\n' + '| 1 | 2 |\n'.repeat(30)
ok(chunkRich(table, 150).every(p => p.length <= 150), 'tables split without exceeding the limit')

ok(chunkRich('', 100).length === 1, 'empty string is one chunk')

console.log(fails ? `\n${fails} FAILURE(S)` : '\nall green')
process.exit(fails ? 1 : 0)
