/* @jsxRuntime classic */
/* @jsx h */
/* @jsxFrag Fragment */
import type { RenderChildren, RenderElement } from 'claude-code'

import type { ReviewVerdict } from '../reader/progress'
import { tallyOf } from '../review/deck'
import type { DeckState, SignState } from '../state'
import type { Kit } from './pane'
import { BAD, GOOD, HEAD, WARN } from './palette'

export type DeckActions = {
  decide: (verdict: ReviewVerdict) => void
  undo: () => void
  prev: () => void
  next: () => void
  source: () => void
  close: () => void
}

const SCOPE_WORDS = { flagged: 'high-priority rules a person should check', p0: 'all high-priority rules', all: 'all rules' }
const SCOPE_SHORT = { flagged: 'flagged', p0: 'high-priority', all: 'all' }

const VERDICT_COLORS: Record<ReviewVerdict, string> = {
  confirmed: GOOD,
  wrong: BAD,
  discuss: WARN,
}

/** `text` word-wrapped to `width` cells, at most `maxLines` rows, the last ending in an ellipsis when cut. */
export function wrapLines(text: string, width: number, maxLines: number): string[] {
  const out: string[] = []
  const limit = Math.max(8, width)
  let line = ''

  const push = (value: string) => {
    out.push(value)
  }

  for (const word of text.split(/\s+/).filter(part => part !== '')) {
    let rest = word

    while (rest.length > limit) {
      if (line !== '') {
        push(line)
        line = ''
      }

      push(rest.slice(0, limit))
      rest = rest.slice(limit)
    }

    if (line === '') {
      line = rest
    } else if (line.length + 1 + rest.length <= limit) {
      line = `${line} ${rest}`
    } else {
      push(line)
      line = rest
    }
  }

  if (line !== '') {
    push(line)
  }

  if (out.length <= maxLines) {
    return out
  }

  const kept = out.slice(0, Math.max(1, maxLines))
  const last = kept[kept.length - 1] ?? ''

  kept[kept.length - 1] = `${last.slice(0, Math.max(0, limit - 1))}…`

  return kept
}

/**
 * The review deck's body: one rule card, its verdict, and the keys.
 *
 * It draws in the band above the prompt, where a bare digit presses a Button
 * from an empty composer. A tree taller than the band scrolls and disarms the
 * digits, so the card wraps its own text into counted rows and never exceeds
 * `maxRows`.
 */
export function deckView(
  kit: Kit,
  deck: DeckState,
  columns: number,
  maxRows: number,
  actions: DeckActions,
): RenderElement {
  const { Box, Text, Button, Code } = kit
  const width = Math.max(30, columns - 2)
  const rule = deck.queue[deck.index]
  const tally = tallyOf(deck.queue, deck.ledger)

  if (rule === undefined) {
    return (
      <Box flexDirection="column">
        <Text bold color={HEAD}>Rule review</Text>
        <Text dimColor wrap="truncate-end">
          {`Nothing to review among ${SCOPE_WORDS[deck.scope]}${deck.filter !== '' ? ` matching "${deck.filter}"` : ''}. Try /modernize-review-pane all.`}
        </Text>
        <Button key="close" hotkey="0" plain onPress={actions.close}>close</Button>
      </Box>
    )
  }

  const verdict = deck.ledger[rule.id]
  const first = rule.citations[0]
  const shownSource = deck.isSourceShown && deck.source !== null && deck.source.ruleId === rule.id ? deck.source : null

  const meta = [
    rule.domain,
    rule.category !== undefined && rule.category.toLowerCase() === rule.domain?.toLowerCase() ? undefined : rule.category,
    rule.confidence !== undefined ? `confidence ${rule.confidence}` : undefined,
    first !== undefined ? `${first.path.split('/').pop()}:${first.from}${first.to !== first.from ? `-${first.to}` : ''}` : undefined,
  ].filter((part): part is string => part !== undefined && part !== '')

  const keys = (
    <Box columnGap={2}>
      <Button key="confirm" hotkey="1" plain onPress={() => actions.decide('confirmed')}>confirm</Button>
      <Button key="wrong" hotkey="2" plain onPress={() => actions.decide('wrong')}>wrong</Button>
      <Button key="discuss" hotkey="3" plain onPress={() => actions.decide('discuss')}>discuss</Button>
      <Button key="prev" hotkey="4" plain onPress={actions.prev}>back</Button>
      <Button key="skip" hotkey="5" plain onPress={actions.next}>skip</Button>
      <Button key="source" hotkey="6" plain onPress={actions.source}>{deck.isSourceShown ? 'hide source' : 'source'}</Button>
      {verdict !== undefined ? <Button key="undo" hotkey="7" plain onPress={actions.undo}>undo</Button> : null}
      <Button key="close" hotkey="0" plain onPress={actions.close}>close</Button>
    </Box>
  )

  const verdictLine =
    verdict !== undefined ? (
      <Text color={VERDICT_COLORS[verdict.verdict]} bold>{`Your verdict: ${verdict.verdict} (${verdict.at.slice(0, 10)})`}</Text>
    ) : (
      <Text dimColor>Is this rule right? No verdict yet.</Text>
    )

  // The reviewer's own words, when they gave any (the review command records them): one line, cut short.
  const noteLine =
    verdict?.note !== undefined ? (
      <Text wrap="truncate-end">
        <Text dimColor>Note: </Text>
        <Text>{verdict.note}</Text>
      </Text>
    ) : null

  const noteRows = noteLine === null ? 0 : 1

  const headline = (
    <Text wrap="truncate-end">
      <Text bold color={HEAD}>Rule review</Text>
      <Text bold>{` ${deck.index + 1} of ${tally.total}`}</Text>
      <Text dimColor>{' · '}</Text>
      <Text color={GOOD}>{`${tally.confirmed} confirmed`}</Text>
      <Text dimColor>{' · '}</Text>
      <Text color={BAD}>{`${tally.wrong} wrong`}</Text>
      <Text dimColor>{' · '}</Text>
      <Text color={WARN}>{`${tally.discuss} to discuss`}</Text>
      <Text dimColor>{` · ${tally.open} open · ${width < 96 ? SCOPE_SHORT[deck.scope] : SCOPE_WORDS[deck.scope]}${deck.filter !== '' ? ` · "${deck.filter}"` : ''}`}</Text>
    </Text>
  )

  // With the source open the code gets the room: the rule in one line, no blank rows, and as many
  // cited lines as the band holds. Seven rows are spoken for: headline, title, meta, statement,
  // path, verdict, keys.
  if (shownSource !== null && Code !== undefined) {
    const codeRows = Math.max(3, Math.min(24, maxRows - 8 - noteRows))
    const gist = rule.statement !== '' ? rule.statement : (rule.then ?? rule.given ?? '')

    return (
      <Box flexDirection="column" width={width}>
        {headline}
        <Text bold wrap="truncate-end">{`${rule.id.startsWith('R-') ? rule.priority : rule.id} · ${rule.title}`}</Text>
        <Text dimColor wrap="truncate-end">{meta.join(' · ')}</Text>
        <Text wrap="truncate-end">{wrapLines(gist, width, 1)[0] ?? ''}</Text>
        <Text dimColor wrap="truncate-end">{`${shownSource.path}:${shownSource.startLine}`}</Text>
        <Code
          source={shownSource.text.split('\n').slice(0, codeRows).join('\n')}
          path={shownSource.path}
          startLine={shownSource.startLine}
          wrap="truncate-end"
        />
        {verdictLine}
        {noteLine}
        {keys}
      </Box>
    )
  }

  // Rows that are always there: header, blank, title, meta, blank, [body], blank, verdict, keys.
  const fixed = 8
  // One row of slack: a band exactly full still scrolls on some layouts.
  const isTight = maxRows < 16
  const room = Math.max(1, maxRows - (isTight ? fixed - 3 : fixed) - 1 - noteRows)
  const prose = Math.max(1, room)

  // Share the prose rows: flags one row each, the statement up to two, the rest split over Given/When/Then.
  const flagRows = (rule.defect !== undefined ? 1 : 0) + (rule.sme !== undefined ? 1 : 0)
  const statementRows = rule.statement !== '' ? Math.min(2, Math.max(0, prose - flagRows - 3)) : 0
  const parts = [rule.given, rule.when, rule.then].filter(part => part !== undefined).length
  const each = parts > 0 ? Math.max(1, Math.floor((prose - flagRows - statementRows) / parts)) : 0

  type Row = { text: string; color?: string; label?: string }
  const rows: Row[] = []

  for (const line of wrapLines(rule.statement, width, statementRows)) {
    rows.push({ text: line })
  }

  const block = (label: string, text: string | undefined) => {
    if (text === undefined) {
      return
    }

    wrapLines(`${label} ${text}`, width, each).forEach((line, index) => {
      rows.push(index === 0 ? { label, text: line.slice(label.length + 1) } : { text: line })
    })
  }

  block('Given', rule.given)
  block('When', rule.when)
  block('Then', rule.then)

  if (rule.defect !== undefined) {
    rows.push({ text: wrapLines(`! Suspected defect: ${rule.defect}`, width, 1)[0] ?? '', color: WARN })
  }

  if (rule.sme !== undefined) {
    rows.push({ text: wrapLines(`? For an SME: ${rule.sme}`, width, 1)[0] ?? '', color: HEAD })
  }

  return (
    <Box flexDirection="column" width={width}>
      {headline}
      <Box marginTop={isTight ? 0 : 1} flexDirection="column">
        <Text bold wrap="truncate-end">{`${rule.id.startsWith('R-') ? rule.priority : rule.id} · ${rule.title}`}</Text>
        <Text dimColor wrap="truncate-end">{meta.join(' · ')}</Text>
      </Box>
      <Box marginTop={isTight ? 0 : 1} flexDirection="column">
        {rows.slice(0, prose).map(row => (
          <Text wrap="truncate-end" color={row.color}>
            {row.label !== undefined ? <Text bold color={HEAD}>{`${row.label} `}</Text> : null}
            {row.text}
          </Text>
        ))}
      </Box>
      <Box marginTop={isTight ? 0 : 1}>{verdictLine}</Box>
      {noteLine}
      {keys}
    </Box>
  )
}

export type SignActions = {
  name: (value: string) => void
  covers: (value: 'phase-1' | 'full') => void
  sign: () => void
  cancel: () => void
}

/** The sign-off dialog: a person's name, what the approval covers, and the button that writes it. */
export function signView(
  kit: Kit,
  sign: SignState,
  system: string,
  openQuestions: number,
  columns: number,
  actions: SignActions,
): RenderElement {
  const { Box, Text, Button, Input } = kit
  const width = Math.max(30, columns)

  return (
    <Box flexDirection="column" width={width}>
      <Text bold color={HEAD}>Sign the brief</Text>
      <Text dimColor wrap="wrap">
        {`Records who approved the plan in analysis/${system}/MODERNIZATION_BRIEF.md, and how much of it. Nothing is built until it is signed.`}
      </Text>
      {openQuestions > 0 ? (
        <Text color={WARN} wrap="wrap">{`${openQuestions} open question${openQuestions === 1 ? '' : 's'} in the brief ${openQuestions === 1 ? 'is' : 'are'} still unticked.`}</Text>
      ) : null}
      <Box marginTop={1} flexDirection="column">
        {Input !== undefined ? (
          <Input
            key="signer"
            label="Approved by"
            placeholder="name, role"
            value={sign.name}
            submitLabel="sign"
            autoFocus
            onInput={actions.name}
            onSubmit={value => {
              actions.name(value)
              actions.sign()
            }}
          />
        ) : (
          <Text>{`Approved by: ${sign.name}`}</Text>
        )}
      </Box>
      <Box marginTop={1} columnGap={2}>
        <Text dimColor>Covers:</Text>
        <Button key="phase1" plain onPress={() => actions.covers('phase-1')}>
          {`${sign.covers === 'phase-1' ? '◉' : '○'} Phase 1 only`}
        </Button>
        <Button key="full" plain onPress={() => actions.covers('full')}>
          {`${sign.covers === 'full' ? '◉' : '○'} Full plan`}
        </Button>
      </Box>
      {sign.error !== null ? <Text color={BAD} wrap="wrap">{sign.error}</Text> : null}
      <Box marginTop={1} columnGap={2}>
        <Button key="do-sign" onPress={actions.sign}>sign</Button>
        <Button key="cancel" dimColor onPress={actions.cancel}>cancel</Button>
      </Box>
      <Box>
        <Text dimColor>enter signs · tab moves · esc cancels</Text>
      </Box>
    </Box>
  )
}
