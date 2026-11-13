import { describe, expect, test } from 'claude-code/testing'

import { buildItems, countHits, splitHits, wrapLines } from '../hooks/register'

const SECTIONS = [
  { id: 'intro', scope: 'shared', text: 'You are an interactive agent.' },
  { id: 'memory', scope: 'session', text: 'Remember the project rules.' },
]
const TOOLS = [
  { name: 'Read', description: 'Reads a file from disk.', mcp: false },
  { name: 'Grep', description: 'Searches files.', mcp: false },
]
const TURN_1 = [
  {
    role: 'user',
    content: [
      { type: 'text', text: '<system-reminder>\n# Environment\nPrimary working directory: /home/jordan/trailmix\n</system-reminder>' },
      { type: 'text', text: "Why does parseDuration('90m') return NaN?" },
    ],
  },
]
const TURN_2 = [
  ...TURN_1,
  {
    role: 'assistant',
    content: [
      { type: 'text', text: 'Let me look at the parser.' },
      { type: 'tool_use', id: 'toolu_1', name: 'Read', input: { file_path: '/home/jordan/trailmix/src/duration.ts' } },
    ],
  },
  {
    role: 'user',
    content: [{ type: 'tool_result', tool_use_id: 'toolu_1', content: 'const UNITS = { s: 1000, h: 3600000 }\nreturn Number(amount) * UNITS[unit]' }],
  },
]

describe('buildItems', () => {
  test('labels every piece and marks what a request added', () => {
    const first = buildItems(SECTIONS, TOOLS, TURN_1 as never, () => false, undefined)
    expect(first.items.map(i => i.kind)).toEqual(['section', 'section', 'tool', 'tool', 'reminder', 'prompt'])
    expect(first.items[4]?.label).toBe('Environment')

    const second = buildItems(SECTIONS, TOOLS, TURN_2 as never, () => false, first.items)
    const added = second.items.filter(i => i.isNew)
    expect(added.map(i => i.kind)).toEqual(['assistant', 'tool_use', 'tool_result'])
    expect(added[1]?.label).toBe('Read src/duration.ts')
    expect(added[2]?.label).toBe('Read src/duration.ts → 2 lines')
    expect(second.texts.get(added[2]?.hash ?? '')).toContain('UNITS[unit]')
  })
})

describe('buildItems on repeats', () => {
  test('a block identical to an earlier one is still new where it lands', () => {
    const two = buildItems(SECTIONS, TOOLS, TURN_2 as never, () => false, undefined)
    const again = [...TURN_2, TURN_2[1], TURN_2[2]]
    const three = buildItems(SECTIONS, TOOLS, again as never, () => false, two.items)
    expect(three.items.filter(i => i.isNew).map(i => i.kind)).toEqual(['assistant', 'tool_use', 'tool_result'])
  })
})

describe('buildItems without sections', () => {
  test('shows the system prompt by its size when its text was not reported', () => {
    const none = buildItems([], TOOLS, TURN_1 as never, () => false, undefined, 3200)
    const sys = none.items.filter(i => i.group === 'system')
    expect(sys.length).toBe(1)
    expect(sys[0]?.estTokens).toBe(3200)
  })
})

describe('text helpers', () => {
  test('counts and splits hits case-insensitively', () => {
    expect(countHits('Units and UNITS', 'units')).toBe(2)
    expect(splitHits('a UNITS b', 'units')).toEqual([
      { text: 'a ', isHit: false },
      { text: 'UNITS', isHit: true },
      { text: ' b', isHit: false },
    ])
  })
  test('wraps long lines and keeps line numbers on the first piece', () => {
    const rows = wrapLines('x'.repeat(25) + '\nshort', 10)
    expect(rows.map(r => r.n)).toEqual([1, 0, 0, 2])
  })
})

function stubEngine(on: any, messages: { current: unknown[] }) {
  on('prompt.compose', () => ({ sections: SECTIONS }))
  on('tool.list', () => ({ value: TOOLS }))
  on('session.messages', () => ({ value: messages.current }))
  on('session.usage', () => ({
    value: {
      startedAt: 0,
      context: {
        window: 200000,
        breakdown: {
          categories: [
            { name: 'System prompt', tokens: 6900, kind: 'used' },
            { name: 'System tools', tokens: 12000, kind: 'used' },
            { name: 'Messages', tokens: 900, kind: 'used' },
            { name: 'Free space', tokens: 180200, kind: 'free' },
          ],
          totalTokens: 19800,
          rawMaxTokens: 200000,
        },
      },
      rateLimits: [],
      cost: { usd: 0 },
    },
  }))
  on('clock.now', () => ({ value: 1 }))
  on('turn.step', async function* (_$: unknown, e: { turnId: string; index: number }) {
    return { turnId: e.turnId, index: e.index, answer: '', toolUses: [], stopReason: 'end_turn', usage: null }
  })
}

const PANE_PROPS = { title: 'Context lens', isFocused: true, bodyColumns: 90, placement: 'dock', scroll: { offset: 0, bodyRows: 40, rows: 40 }, view: {} }

const BAND_PROPS = { hasSurvey: false, isWorking: false, maxRows: 6, bodyColumns: 100, scroll: { offset: 0, bodyRows: 6, rows: 6 }, view: {} }

describe('band', () => {
  for (const surface of ['terminal', 'desktop'] as const) {
    test('sums up what the latest request added on ' + surface, async ($, on) => {
      const messages = { current: TURN_1 as unknown[] }
      stubEngine(on, messages)
      on('ui.open', () => ({ value: { isPlaced: true } }))
      on('ui.render', { component: 'AbovePrompt' }, ($: any, e: any) => {
        const { Box } = $.ui.resolve(e)
        return <Box />
      })
      const band = await $.ui.mount({ plugin: 'context-lens', surface, component: 'AbovePrompt', props: BAND_PROPS as never })
      expect(await band.find({ key: 'open' })).toBeUndefined()

      await $.prompt.compose({ model: 'm', promptModel: 'm', surfaces: [surface], tools: ['Read', 'Grep'], outputStyle: null, traits: [] })
      for await (const _ of $.turn.step({ turnId: 't1', index: 0, model: 'm', messageCount: 1 })) void _
      messages.current = TURN_2
      for await (const _ of $.turn.step({ turnId: 't1', index: 1, model: 'm', messageCount: 3 })) void _

      expect(await band.find({ type: 'Text', text: /request 2 added 3 items/ })).toBeDefined()
      expect(await band.find({ type: 'Text', text: /last: result Read src\/duration.ts/ })).toBeDefined()
      await band.press({ key: 'hide' })
      expect(await band.find({ key: 'open' })).toBeUndefined()
      await band.unmount()
    })
  }
})

describe('pane', () => {
  for (const surface of ['terminal', 'desktop'] as const) {
    test('browses, filters and searches a captured request on ' + surface, async ($, on) => {
      const messages = { current: TURN_1 as unknown[] }
      stubEngine(on, messages)

      await $.prompt.compose({ model: 'm', promptModel: 'm', surfaces: [surface], tools: ['Read', 'Grep'], outputStyle: null, traits: [] })
      for await (const _ of $.turn.step({ turnId: 't1', index: 0, model: 'm', messageCount: 1 })) void _
      messages.current = TURN_2
      await $.prompt.compose({ model: 'm', promptModel: 'm', surfaces: [surface], tools: ['Read', 'Grep'], outputStyle: null, traits: [] })
      for await (const _ of $.turn.step({ turnId: 't1', index: 1, model: 'm', messageCount: 3 })) void _

      const ui = await $.ui.mount({ plugin: 'context-lens', surface, component: 'Pane', requestId: 'context-lens', props: PANE_PROPS as never, viewport: { columns: 100, rows: 48 } as never })
      expect(await ui.find({ type: 'Text', text: /Request 2\/2/ })).toBeDefined()
      expect(await ui.find({ type: 'Button', text: /Read src\/duration.ts → 2 lines/ })).toBeDefined()

      await ui.press({ key: 'f-new' })
      const rows = async () => (await ui.findAll({ type: 'Button' })).filter(b => b.key?.startsWith('i-'))
      expect((await rows()).map(b => b.text)).toEqual(['Let me look at the parser.', 'Read src/duration.ts', 'Read src/duration.ts → 2 lines'])

      await ui.press({ key: 'f-all' })
      await ui.input({ key: 'search', text: 'units' })
      expect(await ui.find({ type: 'Text', text: /2 matches in 1 of/ })).toBeDefined()

      const row = await ui.find({ type: 'Button', text: /Read src\/duration.ts → 2 lines/ })
      await ui.press({ key: row?.key ?? '' })
      expect(await ui.find({ type: 'Button', text: /next match/ })).toBeDefined()
      expect(await ui.find({ type: 'Text', text: 'UNITS' })).toBeDefined()

      await ui.press({ key: 'prev' })
      expect(await ui.find({ type: 'Text', text: /Request 1\/2/ })).toBeDefined()
      // request 1 has no tool result, so the reader falls back to the list
      expect(await ui.find({ key: 'back' })).toBeUndefined()
      await ui.input({ key: 'search', text: '' })
      await ui.press({ key: 'f-new' })
      // the first request is all new: two sections, two tools, the reminder and the prompt
      expect((await ui.findAll({ type: 'Button' })).filter(b => b.key?.startsWith('i-')).length).toBe(6)
      await ui.unmount()
    })
  }
})
