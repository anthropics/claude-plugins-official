import { describe, expect, mock, test } from 'claude-code/testing'

import { BAND, command, PANE, SESSION, SIGN_PANE } from './fixtures/inputs'
import { MAVEN_UPLIFT, REIMAGINE, LEGACY_ONLY } from './fixtures/stacks'
import { worldOf } from './fixtures/world'
import { FULL, UNSIGNED } from './fixtures/workspace'

const PLUGIN = 'code-modernization'

type Mounted = { surface: string; unmount: () => Promise<void> }

/**
 * `$.ui.mount` is newer than the declarations `tsc` reads (`.claude/types`), so it is reached through a cast. A mount is held
 * to the terminal's element table and then let go, so the next one is a fresh instance of the same pane.
 */
const accepted =
  ($: unknown) =>
  async (input: Record<string, unknown>): Promise<string> => {
    const mounted = await ($ as { ui: { mount: (target: unknown) => Promise<Mounted> } }).ui.mount(input)

    await mounted.unmount()

    return mounted.surface
  }

/**
 * `$.ui.render` hands back what the plugin drew; `$.ui.mount` also holds it to the terminal's element table, as the screen
 * does: a prop or an element the surface refuses means the engine draws its own and the pane never shows.
 */
describe('what the plugin draws is accepted by the terminal', () => {
  const pack = JSON.stringify({
    modules: [{ name: 'INTCALC', track: 'rewrite', verdict: 'NOT PROVEN', reasons: ['Tests ran: 2 tests failed.'], verifiedAt: '2026-09-24 20:31 UTC' }],
  })

  const cases: [string, Record<string, string>][] = [
    ['a finished rewrite', FULL],
    ['a rewrite with a failed proof', { ...FULL, 'analysis/billing/VERIFICATION.json': pack }],
    ['an unsigned brief', UNSIGNED],
    ['a Maven uplift', MAVEN_UPLIFT],
    ['a reimagine', REIMAGINE],
    ['a legacy tree', LEGACY_ONLY],
    ['a workspace with nothing', { 'README.md': 'x' }],
  ]

  for (const [name, files] of cases) {
    test(`the pane for ${name}, docked at three widths and inline`, async ($, on) => {
      worldOf(on, files)
      mock.clock(on)
      on('ui.render', () => ({ type: 'Text', children: [''] }))
      await $.session.start(SESSION)
      await $.command.run(command('modernize-panel'))

      for (const bodyColumns of [26, 48, 72]) {
        expect(await accepted($)({ ...PANE, plugin: PLUGIN, props: { ...PANE.props, bodyColumns, scroll: { offset: 0, bodyRows: 40 } } })).toBe('terminal')
      }

      expect(await accepted($)({ ...PANE, plugin: PLUGIN, props: { ...PANE.props, placement: 'inline', bodyColumns: 100, scroll: { offset: 0, bodyRows: 8 } } })).toBe('terminal')
    })
  }

  test('the show bar, the review deck with and without source, and the sign-off dialog', async ($, on) => {
    const world = worldOf(on, {
      ...UNSIGNED,
      'analysis/billing/RULE_REVIEWS.json': JSON.stringify({ reviews: { 'P0-002': { verdict: 'discuss', at: '2026-09-16', note: 'a question for the owner' } } }),
    })

    const clock = mock.clock(on)

    void world
    on('ui.render', () => ({ type: 'Text', children: [''] }))
    await $.session.start(SESSION)

    expect(await accepted($)({ ...BAND, plugin: PLUGIN })).toBe('terminal')

    await $.command.run(command('modernize-review-pane', 'all'))
    await $.ui.render(BAND)
    await $.ui.press({ plugin: PLUGIN, key: 'prev' })

    for (const maxRows of [8, 12, 16, 30]) {
      expect(await accepted($)({ ...BAND, plugin: PLUGIN, props: { ...BAND.props, maxRows, scroll: { offset: 0, bodyRows: maxRows - 1 } } })).toBe('terminal')
    }

    await $.ui.render(BAND)
    await $.ui.press({ plugin: PLUGIN, key: 'source' })
    await clock.settle()
    expect(await accepted($)({ ...BAND, plugin: PLUGIN })).toBe('terminal')
    await $.ui.render(BAND)
    await $.ui.press({ plugin: PLUGIN, key: 'close' })

    await $.command.run(command('modernize-sign'))
    expect(await accepted($)({ ...SIGN_PANE, plugin: PLUGIN })).toBe('terminal')
  })
})
