/**
 * Writing a person's signature into the brief's approval block. The block
 * comes in a few shapes (one line or several, checkboxes or a choice in
 * words); each is filled in where it stands, and nothing else is touched.
 */

const COVER_WORDS = { 'phase-1': 'Phase 1 only', full: 'Full plan' } as const

/**
 * The brief with its approval block signed; null when it has no `Approved by:` line.
 *
 * @param text the brief
 * @param name who approves
 * @param date `YYYY-MM-DD`
 * @param covers what the approval covers
 */
export function signBrief(
  text: string,
  name: string,
  date: string,
  covers: 'phase-1' | 'full',
): string | null {
  const lines = text.split('\n')
  const at = lines.findIndex(line => /^\s*Approved by\s*:/i.test(line))

  if (at < 0) {
    return null
  }

  const who = name.replace(/\s+/g, ' ').trim()
  const line = lines[at] ?? ''
  const indent = /^\s*/.exec(line)?.[0] ?? ''
  const hasInlineDate = /\bDate\s*:/i.test(line)

  lines[at] = hasInlineDate ? `${indent}Approved by: ${who}  Date: ${date}` : `${indent}Approved by: ${who}`

  // The block ends at a blank-line-separated heading or code fence; look a short way down.
  const end = Math.min(lines.length, at + 12)

  if (!hasInlineDate) {
    const dateAt = lines.findIndex((candidate, index) => index > at && index < end && /^\s*Date\s*:/i.test(candidate))

    if (dateAt >= 0) {
      const head = /^(\s*Date\s*:\s*)/i.exec(lines[dateAt] ?? '')?.[1] ?? 'Date: '

      lines[dateAt] = `${head}${date}`
    } else {
      lines.splice(at + 1, 0, `${indent}Date:        ${date}`)
    }
  }

  const coversAt = lines.findIndex(
    (candidate, index) => index >= at && index < end + 1 && /Approval covers\s*:/i.test(candidate),
  )

  if (coversAt >= 0) {
    const current = lines[coversAt] ?? ''

    if (/\[[ xX]?\]/.test(current)) {
      lines[coversAt] = current.replace(/\[[ xX]?\](\s*)([^[\]|]+)/g, (_match, gap: string, label: string) => {
        const isFull = /full/i.test(label)
        const isPhase = /phase\s*1/i.test(label)
        const isChosen = covers === 'full' ? isFull : isPhase

        return `[${isChosen ? 'X' : ' '}]${gap}${label}`
      })
    } else {
      const head = /^(.*Approval covers\s*:\s*)/i.exec(current)?.[1] ?? 'Approval covers: '

      lines[coversAt] = `${head}${COVER_WORDS[covers]}`
    }
  } else {
    lines.splice(at + (hasInlineDate ? 1 : 2), 0, `${indent}Approval covers: ${COVER_WORDS[covers]}`)
  }

  return lines.join('\n')
}
