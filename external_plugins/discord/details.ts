// "▸ Details" helpers for the Discord channel plugin.
// Discord has no collapsible text. A reply may carry `details`; the message goes out with a
// "▸ Details" button and the text is stored on disk keyed by message id (survives a restart of
// this server). A press edits the message in place to append the text and flips the label to
// "▾ Hide"; a second press collapses it. Anyone may press — it reveals text the bot already posted.
import { ActionRowBuilder, ButtonBuilder, ButtonStyle } from 'discord.js'
import { mkdirSync, readFileSync, writeFileSync } from 'fs'
import { join } from 'path'

export const DETAIL_MARK = '\n▾ **Details**\n'

function detailsPath(dir: string, messageId: string): string {
  if (!/^[0-9]{5,30}$/.test(messageId)) throw new Error('bad message id')
  return join(dir, `${messageId}.txt`)
}
export function saveDetails(dir: string, messageId: string, text: string): void {
  mkdirSync(dir, { recursive: true })
  writeFileSync(detailsPath(dir, messageId), text.trimEnd() + '\n')
}
export function loadDetails(dir: string, messageId: string): string {
  try {
    return readFileSync(detailsPath(dir, messageId), 'utf8').trimEnd()
  } catch {
    return ''
  }
}
export function splitDetails(content: string): { summary: string; expanded: boolean } {
  const i = content.indexOf(DETAIL_MARK)
  return i < 0 ? { summary: content, expanded: false } : { summary: content.slice(0, i), expanded: true }
}
export function composeDetails(summary: string, details: string, expanded: boolean): string {
  return expanded && details ? summary + DETAIL_MARK + details : summary
}
export function detailsRow(expanded: boolean) {
  return new ActionRowBuilder<ButtonBuilder>().addComponents(
    new ButtonBuilder()
      .setCustomId(expanded ? 'details:hide' : 'details:show')
      .setLabel(expanded ? '▾ Hide' : '▸ Details')
      .setStyle(ButtonStyle.Secondary),
  )
}
