import type { RenderInput, SessionStartInput } from 'claude-code'

export const SESSION: SessionStartInput = { surface: 'terminal', isInteractive: true, cwd: '/work' }

export const HINT: RenderInput<'PromptHint'> = {
  component: 'PromptHint',
  surface: 'terminal',
  requestId: 'hint',
  viewport: { columns: 180, rows: 48, isFullscreen: true },
  props: { isDraft: false, isWorking: false, hint: '' },
}

export const MAIN_SCREEN_HINT: RenderInput<'PromptHint'> = {
  ...HINT,
  viewport: { columns: 180, rows: 48, isFullscreen: false },
}

export const PANE: RenderInput<'Pane'> = {
  component: 'Pane',
  surface: 'terminal',
  requestId: 'modernize',
  viewport: { columns: 180, rows: 48, isFullscreen: true },
  props: {
    title: 'Modernization',
    isFocused: false,
    bodyColumns: 72,
    placement: 'dock',
    scroll: { offset: 0, bodyRows: 44 },
    view: {},
  },
}

export const SIGN_PANE: RenderInput<'Pane'> = { ...PANE, requestId: 'modernize-sign', props: { ...PANE.props, placement: 'inline' } }

export const BAND: RenderInput<'AbovePrompt'> = {
  component: 'AbovePrompt',
  surface: 'terminal',
  requestId: 'band',
  viewport: { columns: 180, rows: 48, isFullscreen: true },
  props: {
    hasSurvey: false,
    isWorking: false,
    maxRows: 20,
    bodyColumns: 100,
    scroll: { offset: 0, bodyRows: 19 },
    view: {},
  },
}

export const command = (name: string, args = '') => ({
  command: name,
  args,
  origin: { kind: 'composer' as const },
  presentation: { isFullscreen: true, columns: 180 },
})
