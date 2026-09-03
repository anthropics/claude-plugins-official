// Tests for the Details helpers. Run: bun test
// The helpers are pure; the Discord-facing parts (send/edit/interaction) are exercised live at rollout.
import { describe, expect, test } from 'bun:test'
import { composeDetails, loadDetails, saveDetails, splitDetails } from './details.ts'

const MARK = '\n▾ **Details**\n'

describe('details helpers', () => {
  test('store round-trips by message id and refuses bad ids', () => {
    const dir = `/tmp/details-test-${process.pid}`
    saveDetails(dir, '1788406933', '• a\n• b\n')
    expect(loadDetails(dir, '1788406933')).toBe('• a\n• b')
    expect(loadDetails(dir, '999')).toBe('')
    expect(() => saveDetails(dir, '../x', 'y')).toThrow()
  })
  test('compose adds the marker + text only when expanded and non-empty', () => {
    expect(composeDetails('sum', 'more', false)).toBe('sum')
    expect(composeDetails('sum', '', true)).toBe('sum')
    expect(composeDetails('sum', 'more', true)).toBe('sum' + MARK + 'more')
  })
  test('split recovers the summary and the expanded state', () => {
    expect(splitDetails('sum')).toEqual({ summary: 'sum', expanded: false })
    expect(splitDetails('sum' + MARK + 'more\nlines')).toEqual({ summary: 'sum', expanded: true })
  })
  test('round trip survives a result line appended while expanded', () => {
    const expanded = composeDetails('line1\nline2', '• fact', true)
    const { summary, expanded: ex } = splitDetails(expanded)
    const again = composeDetails(summary + '\n✅ done', '• fact', ex)
    expect(again.startsWith('line1\nline2\n✅ done' + MARK)).toBe(true)
    expect(again.endsWith('• fact')).toBe(true)
  })
  test('a summary that merely mentions the word Details is not treated as expanded', () => {
    expect(splitDetails('see Details below').expanded).toBe(false)
  })
})
