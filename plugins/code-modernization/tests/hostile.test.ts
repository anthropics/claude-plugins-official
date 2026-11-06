import { describe, expect, test } from 'claude-code/testing'

import { parseBrief } from '../hooks/reader/brief'
import { readNotes, totalsOfJunitXml, totalsOfTrx } from '../hooks/reader/modernized'
import { parseRules } from '../hooks/reader/rules'
import { parseTopology } from '../hooks/reader/topology'
import { parseBaseline, parseCatalog } from '../hooks/reader/uplift'
import { parseVerification } from '../hooks/reader/verification'
import { parseLedger } from '../hooks/review/ledger'
import { signBrief } from '../hooks/sign'
import { linesOf, MAX_LINE } from '../hooks/text'
import { readTestRun } from '../hooks/tests-run'

/**
 * Every artifact the pane reads was written from an untrusted tree, sometimes by a model. A line of a million spaces
 * or digits must cost a moment, not minutes: a pattern that backtracks on it would freeze the hooks' environment.
 */
const N = 100_000

const SHAPES: Record<string, string> = {
  spaces: `${' '.repeat(N)}x`,
  hashes: '#'.repeat(N),
  'a heading and spaces': `## Phase 1 - a${' '.repeat(N)}x`,
  'a rule heading and spaces': `### RULE-001: a${' '.repeat(N)}x`,
  'a domain heading and spaces': `## a${' '.repeat(N)}x`,
  pipes: `|${' a |'.repeat(N / 4)}`,
  'table row': `| RULE-001 |${' x |'.repeat(N / 4)}\n|---|`,
  brackets: `${'['.repeat(N)}${']'.repeat(N)}`,
  backticks: '`'.repeat(N),
  checkbox: `- [ ] ${'a '.repeat(N / 2)}`,
  approval: `Approved by: ${' '.repeat(N)}\nDate: ${' '.repeat(N)}`,
  'rule number': `### RULE-${'1'.repeat(N)}`,
  citation: `x.cbl:${'1-'.repeat(N / 2)}`,
  'given and when': `Given ${'When '.repeat(N / 5)}`,
  xml: `<testsuite ${'tests="1" '.repeat(N / 10)}`,
  digits: '9'.repeat(N),
  'baseline table': `| a | pass | fail |\n|---|---|---|\n${'| x | 1 | 1 |\n'.repeat(N / 15)}`,
  'baseline totals': '| Passed | 1 |'.repeat(N / 12),
  'delta ids': `${'D-1 '.repeat(N / 4)}${'`a.b`'.repeat(N / 5)}`,
  'test run': `Tests run: ${'1, '.repeat(N / 3)}`,
  'notes phrases': `${'ported, not switched '.repeat(N / 20)}\n## Follow-ups\n${'- x\n'.repeat(N / 4)}`,
  json: `{"modules":[${'{"name":"a","track":"rewrite","verdict":"PROVEN"},'.repeat(N / 60)}]}`,
}

const PARSERS: Record<string, (text: string) => unknown> = {
  brief: text => parseBrief(text, ['A', 'B', 'C']),
  rules: text => parseRules(text),
  topology: text => parseTopology(text),
  baseline: text => parseBaseline(text),
  catalog: text => parseCatalog(text),
  verification: text => parseVerification(text),
  ledger: text => parseLedger(text),
  notes: text => readNotes(text),
  junit: text => totalsOfJunitXml(text),
  trx: text => totalsOfTrx(text),
  'a test run': text => readTestRun(text),
  sign: text => signBrief(text, 'Ana', '2026-09-24', 'full'),
}

describe('hostile text', () => {
  test('no reader takes long over a line of a hundred thousand characters, whatever it is made of', () => {
    const slow: string[] = []

    for (const [parserName, parse] of Object.entries(PARSERS)) {
      for (const [shapeName, text] of Object.entries(SHAPES)) {
        const started = Date.now()

        parse(text)

        const took = Date.now() - started

        if (took > 1_000) {
          slow.push(`${parserName} on ${shapeName}: ${took} ms`)
        }
      }
    }

    expect(slow).toEqual([])
  })

  test('a line is cut to what a reader looks at, and the text around it is read as before', () => {
    expect(linesOf(`a\n${'b'.repeat(MAX_LINE + 50)}\nc`).map(line => line.length)).toEqual([1, MAX_LINE, 1])

    const brief = parseBrief(`# Brief → Java\n\n## Phase 1 — Pilot\n\n- [ ] one\n${' '.repeat(50_000)}\n- [x] two\n`)

    expect(brief.phases[0]?.criteria.map(criterion => criterion.text)).toEqual(['one', 'two'])
  })
})
