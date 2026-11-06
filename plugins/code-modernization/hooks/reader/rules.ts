import { baseName } from '../paths'
import { linesOf } from '../text'

/**
 * `analysis/<system>/BUSINESS_RULES.md`, read into rule cards.
 *
 * The file is written by an agent, and the agent's layout varies between models and
 * runs. Three shapes are read: a card per rule under a `### <ID> · <title>` heading with
 * a header line (`P0 · Calculation · confidence High · file:line`), the same heading with
 * labelled fields (`**Category:**`, `**Priority:**`, `**Plain English:**`, a fenced
 * Given/When/Then block, `**Edge cases handled:**`, `**Suspected defect:**`), and table
 * rows for the lower priorities. Anything else is skipped, never thrown on.
 */

export type Citation = {
  /** The path as written (`legacy/x/app/cbl/A.cbl`, `A.cbl`, `app/cpy/B.cpy`). */
  path: string
  /** Lower-cased base name, the key the x-ray matches a read file by. */
  base: string
  from: number
  to: number
}

export type Rule = {
  /** `P0-052`, or `R-<hash>` of the title for a table row that carries no id. */
  id: string
  title: string
  /** `P0`, `P1`, `P2`, or `''` when the file does not say. */
  priority: string
  category?: string
  confidence?: string
  /** The rule's one-paragraph statement. */
  statement: string
  given?: string
  when?: string
  then?: string
  edgeCases: string[]
  defect?: string
  sme?: string
  /** Every `file:line` the card names; the first is the rule's own source. */
  citations: Citation[]
  /** The domain heading (`## D6 Interest & Fees`) the rule sits under. */
  domain?: string
}

export type RuleSet = {
  rules: Rule[]
  byId: Map<string, Rule>
  /** Lower-cased base name of a cited file, to the rules citing it. */
  byFileBase: Map<string, Rule[]>
}

const CITATION =
  /([A-Za-z0-9_][A-Za-z0-9_./-]*\.[A-Za-z][A-Za-z0-9]{0,7}):(\d+)(?:\s*[-–]\s*(\d+))?/g

/** `P0-052`, `RULE-001`, `BR-D7-09`: letters, optional segments (a domain), then the number. */
const ID = '[A-Z][A-Z0-9]*(?:-[A-Z][A-Z0-9]*)*-\\d+[a-z]?'

const CARD_HEADING = new RegExp(`^#{3,4}\\s+(${ID})\\s*[·:\\-–—]\\s*(.+?)\\s*$`)

/** Sections that describe or summarise the rules rather than hold them: a legend, a panel summary, appendices, provenance. */
const SKIPPED_SECTION =
  /\b(?:index|appendix|open questions|rejected|refuted|how to read|p0 confirmation|provenance)\b/i

const DOMAIN_HEADING = /^##\s+(.+?)\s*$/

const clean = (text: string) =>
  text
    .replace(/\*\*/g, '')
    .replace(/<br\s*\/?>(\s*)/gi, ' ')
    .replace(/\s+/g, ' ')
    .trim()

/** Every `file:line[-line]` in `text`, in order, without duplicates. */
export function citationsIn(text: string): Citation[] {
  const seen = new Set<string>()
  const out: Citation[] = []

  for (const match of text.matchAll(CITATION)) {
    const path = match[1] ?? ''
    const from = Number(match[2])
    const to = match[3] !== undefined ? Number(match[3]) : from
    const key = `${path}:${from}-${to}`

    if (path === '' || !Number.isFinite(from) || seen.has(key)) {
      continue
    }

    seen.add(key)

    out.push({
      path,
      base: baseName(path).toLowerCase(),
      from,
      to: Math.max(from, to),
    })
  }

  return out
}

const priorityOf = (id: string, body: string): string => {
  const fromId = /^(P\d)\b/.exec(id)?.[1]

  if (fromId !== undefined) {
    return fromId
  }

  const fromLabel = /\bPriority:?\s*\**\s*(P\d)\b/i.exec(body)?.[1]?.toUpperCase()

  if (fromLabel !== undefined) {
    return fromLabel
  }

  // `P0` · Calculation · confidence High · `app/cbl/A.cbl:10-20`
  const header = linesOf(body).find(line => line.trim() !== '') ?? ''

  return /^\s*`?\**(P\d)\**`?\s*(?:·|$)/.exec(header)?.[1] ?? ''
}

const gwtOf = (body: string, word: string): string | undefined => {
  const match = new RegExp(
    `\\*\\*${word}\\*\\*\\s*([\\s\\S]*?)(?=\\n[ \\t]*(?:[-*][ \\t]+)?>?\\s*\\*\\*(?:Given|When|Then)\\*\\*|\\n\\s*\\n|$)`,
    'i',
  ).exec(body)

  const text =
    match?.[1] !== undefined
      ? clean(match[1].replace(/\n>\s?/g, ' ')).replace(/^[—–:-]\s*/, '')
      : ''

  return text === '' ? undefined : text
}

const markedOf = (body: string, marker: RegExp): string | undefined => {
  for (const line of linesOf(body)) {
    if (marker.test(line)) {
      const text = clean(line.replace(/^>\s*/, '').replace(marker, ''))
        .replace(/^[—–-]\s*/, '')
        .trim()

      return text === '' ? undefined : text
    }
  }

  return undefined
}

/** The text after `**Name:**` (or `**Name**:`) on its own line, for the labelled-fields layout. */
const labelledOf = (body: string, name: string): string | undefined => {
  const match = new RegExp(`^[ \\t]*\\*\\*${name}:?\\*\\*:?[ \\t]*(.*)$`, 'im').exec(body)
  const text = match?.[1] !== undefined ? clean(match[1]) : ''

  return text === '' ? undefined : text
}

/**
 * Given/When/Then written as lines (`Given …`, `When …`, `Then …`, `And …`), usually inside a
 * fenced block under `**Specification:**`. `And` lines continue the clause before them.
 */
const specOf = (body: string): { given?: string; when?: string; then?: string } => {
  const block = /\*\*Specification:?\*\*:?\s*([\s\S]*?)(?=\n[ \t]*\*\*[A-Za-z][^*\n]*\*\*|$)/i.exec(body)?.[1] ?? ''
  const clauses: Record<'given' | 'when' | 'then', string[]> = { given: [], when: [], then: [] }
  let current: 'given' | 'when' | 'then' | undefined

  for (const raw of linesOf(block)) {
    const line = raw.trim().replace(/^```\w*$/, '').replace(/^[-*]\s+/, '')
    const match = /^(Given|When|Then|And)\s+(.*)$/.exec(line)

    if (match === null) {
      continue
    }

    const word = match[1] ?? ''
    const rest = clean(match[2] ?? '')

    if (word === 'And') {
      if (current !== undefined) {
        clauses[current].push(rest)
      }

      continue
    }

    current = word.toLowerCase() as 'given' | 'when' | 'then'
    clauses[current].push(rest)
  }

  const join = (parts: string[]) => (parts.length === 0 ? undefined : parts.join(' · '))

  return { given: join(clauses.given), when: join(clauses.when), then: join(clauses.then) }
}

function cardOf(
  id: string,
  title: string,
  body: string,
  domain: string | undefined,
): Rule {
  const lines = linesOf(body)
  const header = lines.find(line => line.trim() !== '') ?? ''
  const headerParts = header.split('·').map(part => clean(part))

  const category =
    headerParts
      .slice(1)
      .find(part => part !== '' && !/confidence/i.test(part) && !/`/.test(part)) ?? labelledOf(body, 'Category')

  const confidence =
    /confidence\s*:?\s*\**\s*(High|Medium|Low)\b/i.exec(body)?.[1] ?? undefined

  const statement =
    labelledOf(body, 'Plain English') ??
    lines
      .slice(lines.indexOf(header) + 1)
      .map(line => line.trim())
      .find(
        line =>
          line !== '' &&
          !line.startsWith('>') &&
          !line.startsWith('|') &&
          !line.startsWith('**') &&
          !line.startsWith('-') &&
          !line.startsWith('#') &&
          !line.startsWith('`'),
      ) ?? ''

  const edgeStart = lines.findIndex(line => /^\*\*Edge cases?[^*]*\*\*/i.test(line.trim()))

  const edgeCases: string[] = []

  if (edgeStart >= 0) {
    for (const line of lines.slice(edgeStart + 1)) {
      const trimmed = line.trim()

      if (trimmed.startsWith('- ')) {
        edgeCases.push(clean(trimmed.slice(2)))
      } else if (trimmed !== '' && edgeCases.length > 0) {
        break
      }
    }
  }

  const spec = specOf(body)
  const given = gwtOf(body, 'Given') ?? spec.given
  const when = gwtOf(body, 'When') ?? spec.when
  const then = gwtOf(body, 'Then') ?? spec.then
  const defect = markedOf(body, /(?:⚠️?\s*\**\s*Suspected defect\**|^\s*\*\*Suspected defect:?\*\*:?)/i)

  // `❓ **SME question** — …`, or `**Confidence:** Medium — SME question: …` on the confidence line.
  const smeInline = /\bSME questions?\s*:\s*(.+)$/im.exec(body)?.[1]

  const sme =
    markedOf(body, /❓\s*\**\s*SME(?:\s+questions?)?\**/i) ??
    (smeInline !== undefined && clean(smeInline) !== '' ? clean(smeInline) : undefined)

  return {
    id,
    title: clean(title),
    priority: priorityOf(id, body),
    ...(category !== undefined && { category }),
    ...(confidence !== undefined && {
      confidence: confidence[0]?.toUpperCase() + confidence.slice(1).toLowerCase(),
    }),
    statement: clean(statement),
    ...(given !== undefined && { given }),
    ...(when !== undefined && { when }),
    ...(then !== undefined && { then }),
    edgeCases,
    ...(defect !== undefined && { defect }),
    ...(sme !== undefined && { sme }),
    citations: citationsIn(body),
    ...(domain !== undefined && { domain }),
  }
}

/** A short stable id for a rule that carries none: a hash of its title, so a verdict survives the table being rewritten in another order. */
export function idOfTitle(title: string): string {
  let hash = 2166136261

  for (const char of title.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()) {
    hash = Math.imul(hash ^ char.charCodeAt(0), 16777619)
  }

  return `R-${(hash >>> 0).toString(16).padStart(8, '0').slice(0, 6)}`
}

function rowOf(
  line: string,
  domain: string | undefined,
): Rule | null {
  const cells = line
    .split('|')
    .slice(1, -1)
    .map(cell => cell.trim())

  const first = cells[0] ?? ''
  const titleMatch = /\*\*(.+?)\*\*/.exec(first)

  if (cells.length < 2 || titleMatch === null || /^-+$/.test(first)) {
    return null
  }

  const title = clean(titleMatch[1] ?? '')

  if (title === '' || /^rule$/i.test(title)) {
    return null
  }

  const idInTitle = new RegExp(`^(${ID})\\b`).exec(title)?.[1]
  const category = clean(first.replace(titleMatch[0], '').replace(/<br\s*\/?>/gi, ' '))
  const gwt = cells[1] ?? ''
  const part = (tag: string) =>
    clean(new RegExp(`\\*\\*${tag}\\*\\*\\s*(.*?)(?=\\*\\*[GWT]\\*\\*|$)`).exec(gwt)?.[1] ?? '')

  const given = part('G')
  const when = part('W')
  const then = part('T')
  const flags = cells.slice(3).join(' ')
  const priority = /\b(P\d)\b/.exec(`${flags} ${first}`)?.[1] ?? ''

  return {
    id: idInTitle ?? idOfTitle(title),
    title,
    priority,
    ...(category !== '' && { category }),
    statement: '',
    ...(given !== '' && { given }),
    ...(when !== '' && { when }),
    ...(then !== '' && { then }),
    edgeCases: [],
    ...(/⚠|defect/i.test(flags) && { defect: clean(flags) }),
    ...(/❓|SME/i.test(flags) && { sme: clean(flags) }),
    citations: citationsIn(line),
    ...(domain !== undefined && { domain }),
  }
}

/** Parses BUSINESS_RULES.md. Never throws; an unreadable file is no rules. */
export function parseRules(text: string): RuleSet {
  const lines = linesOf(text)
  const rules: Rule[] = []
  let domain: string | undefined
  /** Set by a top-level heading: `# P1 rules` gives its rows a priority, an index or appendix is skipped. */
  let sectionPriority = ''
  let isTopSkipped = false
  let isSectionSkipped = false

  let open: { id: string; title: string; start: number; domain: string | undefined } | null =
    null

  const close = (end: number) => {
    if (open !== null) {
      rules.push(
        cardOf(open.id, open.title, lines.slice(open.start, end).join('\n'), open.domain),
      )

      open = null
    }
  }

  lines.forEach((line, index) => {
    const isSkipped = isTopSkipped || isSectionSkipped
    const card = isSkipped ? null : CARD_HEADING.exec(line)

    if (card !== null) {
      close(index)
      open = { id: card[1] ?? '', title: card[2] ?? '', start: index + 1, domain }

      return
    }

    const top = /^#\s+(.+?)\s*$/.exec(line)

    if (top !== null) {
      close(index)
      sectionPriority = /\b(P\d)\b/.exec(top[1] ?? '')?.[1] ?? ''
      isTopSkipped = SKIPPED_SECTION.test(top[1] ?? '')
      isSectionSkipped = false
      domain = undefined

      return
    }

    const heading = DOMAIN_HEADING.exec(line)

    if (heading !== null && !line.startsWith('###')) {
      close(index)
      domain = clean(heading[1] ?? '')
      isSectionSkipped = SKIPPED_SECTION.test(heading[1] ?? '')

      return
    }

    if (/^#{1,4}\s/.test(line)) {
      close(index)

      return
    }

    if (open === null && !(isTopSkipped || isSectionSkipped) && line.startsWith('|')) {
      const row = rowOf(line, domain)

      if (row !== null) {
        rules.push(row.priority === '' ? { ...row, priority: sectionPriority } : row)
      }
    }
  })

  close(lines.length)

  const byId = new Map<string, Rule>()
  const byFileBase = new Map<string, Rule[]>()

  for (const rule of rules) {
    if (!byId.has(rule.id)) {
      byId.set(rule.id, rule)
    }

    for (const base of new Set(rule.citations.map(citation => citation.base))) {
      const bucket = byFileBase.get(base) ?? []

      bucket.push(rule)
      byFileBase.set(base, bucket)
    }
  }

  return { rules, byId, byFileBase }
}

/** The rules that need a person: a suspected defect, an SME note, or less than High confidence. */
export function needsReview(rule: Rule): boolean {
  return (
    rule.sme !== undefined ||
    rule.defect !== undefined ||
    (rule.confidence !== undefined && rule.confidence !== 'High')
  )
}
