import { linesOf } from '../text'

/**
 * `analysis/<system>/MODERNIZATION_BRIEF.md`, read without a model: the
 * target stack, the phases, which modules each phase names, the exit
 * criteria boxes, and the approval block.
 *
 * The brief is prose an agent wrote, so every field is best-effort and a
 * field that cannot be read is absent, never guessed.
 */

export type Criterion = {
  /** The line as written, checkbox included. */
  line: string
  /** The criterion's text: the line without its checkbox and tick annotation. */
  text: string
  isTicked: boolean
}

export type Phase = {
  number: number
  title: string
  /** `S`, `M`, `L`, `XL`, when the heading says. */
  size?: string
  risk?: string
  /** Module ids (as the caller's `knownModules` names them) the phase's text mentions. */
  modules: string[]
  criteria: Criterion[]
}

export type Approval = {
  isSigned: boolean
  by?: string
  date?: string
  /** `phase-1`, `full`, or undefined when the block does not say. */
  covers?: 'phase-1' | 'full'
}

export type Brief = {
  target?: string
  phases: Phase[]
  approval: Approval
  /** Unticked `- [ ]` boxes under the Open Questions section. */
  openQuestions: number
}

const PHASE_HEADING = /^#{2,4}\s+Phase\s+(\d+)\s*[—–:.\-]\s*(.+?)\s*$/i
const CHECKBOX = /^\s*[-*]\s+\[( |x|X)\]\s+(.*)$/
const TICK_NOTE = /\s*\((?:[^()]*\d{4}-\d{2}-\d{2}[^()]*)\)\s*$/

const strip = (text: string) => text.replace(/\*\*/g, '').replace(/`/g, '').trim()

/** The criterion text of a checkbox line, its tick annotation `(who, date)` removed. */
export function criterionTextOf(line: string): string | null {
  const match = CHECKBOX.exec(line)

  if (match === null) {
    return null
  }

  return strip((match[2] ?? '').replace(TICK_NOTE, '')).replace(/\s+/g, ' ')
}

/**
 * Parses the brief.
 *
 * @param text the file
 * @param knownModules module ids from topology.json; a phase lists the ones
 *   its text mentions as whole words
 */
export function parseBrief(text: string, knownModules: readonly string[] = []): Brief {
  const lines = linesOf(text)

  const titleLine = lines.find(line => /^#\s+/.test(line)) ?? ''
  const arrow = /[→>]\s*(.+?)\s*$/.exec(titleLine.replace(/->/g, '→'))
  // The title may hold the arrow inside a parenthesis: `(COBOL/CICS → Java/Spring)`. The close is not part of the target.
  const fromTitle = arrow?.[1] !== undefined ? strip(arrow[1]).replace(/\)$/, m => (arrow[1]?.includes('(') === true ? m : '')) : undefined
  // The header's own `**Target stack:** `java-spring`` is the token the commands take: it wins when it is one plain token.
  const stackToken = /\*\*Target stack:?\*\*:?\s*`([A-Za-z0-9][\w.+/-]{0,59})`/i.exec(text)?.[1]
  const target = stackToken ?? fromTitle

  const phases: Phase[] = []
  let current: { phase: Phase; body: string[]; level: number } | null = null
  let section = ''
  let openQuestions = 0

  const closePhase = () => {
    if (current === null) {
      return
    }

    const body = current.body.join('\n')

    // The modules a phase names, the pilot's first and the rest in the order the phase
    // names them: the first one open is what the next step runs, and topology order
    // would put an identity screen ahead of a batch job the brief chose as its pilot.
    const wholeWord = (id: string) =>
      new RegExp(`(?<![A-Za-z0-9_])${id.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(?![A-Za-z0-9_])`)

    const pilotLine = /^.*\bpilot unit\b.*$/im.exec(body)?.[0] ?? ''

    current.phase.modules = knownModules
      .map(id => ({ id, at: body.search(wholeWord(id)), isPilot: wholeWord(id).test(pilotLine) }))
      .filter(entry => entry.at >= 0)
      .sort((a, b) => Number(b.isPilot) - Number(a.isPilot) || a.at - b.at)
      .map(entry => entry.id)

    phases.push(current.phase)
    current = null
  }

  for (const line of lines) {
    const heading = /^(#{1,6})\s+(.+?)\s*$/.exec(line)

    if (heading !== null) {
      const level = heading[1]?.length ?? 1
      const phase = PHASE_HEADING.exec(line)

      if (phase !== null) {
        closePhase()

        const parts = (phase[2] ?? '').split('·').map(part => strip(part))
        const size = parts.map(part => /^Size\s+(\w+)/i.exec(part)?.[1]).find(Boolean)
        const risk = parts.map(part => /^Risk\s+(\w+)/i.exec(part)?.[1]).find(Boolean)

        current = {
          level,
          body: [line],
          phase: {
            number: Number(phase[1]),
            title: parts[0] ?? '',
            ...(size !== undefined && { size: size.toUpperCase() }),
            ...(risk !== undefined && { risk }),
            modules: [],
            criteria: [],
          },
        }

        continue
      }

      if (current !== null && level <= current.level) {
        closePhase()
      }

      if (level <= 2) {
        section = strip(heading[2] ?? '').toLowerCase()
      }
    }

    if (current !== null) {
      current.body.push(line)

      const box = CHECKBOX.exec(line)
      const textOf = criterionTextOf(line)

      if (box !== null && textOf !== null) {
        current.phase.criteria.push({
          line,
          text: textOf,
          isTicked: box[1] !== ' ',
        })
      }

      continue
    }

    if (/open questions/.test(section) && /^\s*[-*]\s+\[ \]/.test(line)) {
      openQuestions += 1
    }
  }

  closePhase()

  const approvedLine = lines.find(line => /^\s*Approved by\s*:/i.test(line))
  const by = approvedLine?.replace(/^\s*Approved by\s*:/i, '').replace(/Date\s*:.*$/i, '').trim()
  const isSigned = by !== undefined && by !== '' && !/^_+$/.test(by.replace(/\s/g, ''))

  const dateLine = lines.find(line => /^\s*(?:Approved by\s*:.*)?Date\s*:\s*\S/i.test(line))
  const date = /Date\s*:\s*(\d{4}-\d{2}-\d{2}|[^\s_][^_\n]*?)\s*$/i.exec(dateLine ?? '')?.[1]

  const coversLine = lines.find(line => /Approval covers\s*:/i.test(line)) ?? ''
  const ticked = [...coversLine.matchAll(/\[\s*[xX]\s*\]\s*([^[\]|]+)/g)].map(m => (m[1] ?? '').trim())

  const plain = coversLine.replace(/^.*Approval covers\s*:/i, '').trim()

  const coversText = ticked[0] ?? (/\[/.test(coversLine) || /\|/.test(plain) ? '' : plain)

  const covers = /full/i.test(coversText)
    ? ('full' as const)
    : /phase\s*1/i.test(coversText)
      ? ('phase-1' as const)
      : undefined

  return {
    ...(target !== undefined && target !== '' && { target }),
    phases,
    approval: {
      isSigned,
      ...(isSigned && by !== undefined && { by }),
      ...(isSigned && date !== undefined && { date: date.trim() }),
      ...(isSigned && covers !== undefined && { covers }),
    },
    openQuestions,
  }
}
