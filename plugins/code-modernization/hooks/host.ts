import type {
  CommandSpec,
  PaneCloseArgs,
  PaneOpenArgs,
  PromptFillArgs,
  PromptSubmitArgs,
  TimerCall,
  UiBlitArgs,
  UiBlitResult,
} from 'claude-code'

import type { ReaderFs } from './reader/fs'

/**
 * What `$.ui.open` answers: drawn, or open but held back undrawn (unasked, on a terminal narrower than the engine docks a
 * pane on) with the reason. A build that answers nothing has drawn it, as far as anyone can tell.
 */
export type OpenResult = { isPlaced: boolean; reason?: string } | void

/**
 * The engine as `session.start` bound it from its `$`: every later hook,
 * timer and button press reaches the engine through this, so the rest of
 * the module is plain functions over a small interface a test can stand in for.
 */
export type Host = {
  fs: ReaderFs & { write: (path: string, text: string) => Promise<void> }
  now: () => Promise<number>
  after: TimerCall
  every: TimerCall
  storeGet: (key: string) => Promise<unknown>
  storeSet: (key: string, value: unknown) => Promise<void>
  invalidate: () => void
  blit: (args: UiBlitArgs) => Promise<UiBlitResult>
  status: (text: string | undefined) => void
  toast: (text: string, timeoutMs?: number) => void
  log: (text: string) => void
  openPane: (pane: PaneOpenArgs) => Promise<OpenResult>
  closePane: (pane: PaneCloseArgs) => Promise<void>
  registerCommand: (spec: CommandSpec) => Promise<unknown>
  fillPrompt: (input: PromptFillArgs) => Promise<{ isFilled: boolean }>
  submitPrompt: (input: PromptSubmitArgs) => Promise<unknown>
  abortTurn: (turnId: string) => Promise<void>
}
