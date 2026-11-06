/**
 * Text that came from the legacy tree, or from an analysis of it, and is about to go in front of the model or into
 * the prompt box: a node name, a rule title, a module id, a delta id. Such text can hold words written for a model,
 * so it is not passed on as it is. Control, format (zero-width, bidirectional and tag) and line-separator characters are
 * replaced too, so nothing in the value is invisible to a person reading the same line.
 *
 * `plain` keeps a value to one short line of ordinary characters. Control and invisible characters, backticks,
 * angle and square brackets and double quotes are replaced, so the value cannot start a new line, open a fence, forge
 * a note's own header or end line, or hide from a person reading it. `isToken` says whether a name is safe to place in
 * a command line: no whitespace, quote, `$`, backtick or shell separator, and a letter or digit first.
 */

const INVISIBLE = /[\p{Cc}\p{Cf}\p{Zl}\p{Zp}]/gu

export function plain(value: unknown, max = 80): string {
  if (typeof value !== 'string') {
    return ''
  }

  const flat = value
    .replace(INVISIBLE, ' ')
    .replace(/[`<>[\]]/g, '_')
    .replace(/"/g, "'")
    .replace(/\s+/g, ' ')
    .trim()

  return flat.length <= max ? flat : `${flat.slice(0, Math.max(1, max - 1)).trimEnd()}…`
}

const TOKEN = /^[A-Za-z0-9][A-Za-z0-9._:/#@+-]{0,79}$/

/** The names the plugin's own workflows accept for a system: letters, digits, hyphen and underscore. */
const SYSTEM_NAME = /^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$/

export const isToken = (value: string): boolean => TOKEN.test(value)

export const isSystemName = (value: string): boolean => SYSTEM_NAME.test(value)

/** The longest line a reader looks at. A line of a table or a heading is a few hundred characters; a longer one is not a card, and a pattern run over a million characters of it is what a hostile file is for. */
export const MAX_LINE = 4_000

/** `text` as lines, each cut to what a reader looks at. */
export const linesOf = (text: string): string[] => text.split('\n').map(line => (line.length > MAX_LINE ? line.slice(0, MAX_LINE) : line))
