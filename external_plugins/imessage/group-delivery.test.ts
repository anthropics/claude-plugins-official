// bun test — the group-delivery decisions. Run: bun test group-delivery.test.ts
import { expect, test } from 'bun:test'
import { fromMeGroupAction, passesGroupAllowFrom } from './group-delivery'

// --- fromMeGroupAction: when is the owner's own message delivered? ---

test('opted-in group, owner typed it (not an echo) -> delivered as owner', () => {
  expect(fromMeGroupAction(true, true, false)).toBe('deliver-as-owner')
})

test("opted-in group, but it's the assistant's own recent send (echo) -> dropped", () => {
  // This is the guarantee that the feature never echoes the assistant's own sends.
  expect(fromMeGroupAction(true, true, true)).toBe('drop')
})

test('group but NOT opted in -> dropped (default behavior unchanged)', () => {
  expect(fromMeGroupAction(true, false, false)).toBe('drop')
})

test('not a group (a DM/self-chat from-me row) -> dropped here regardless of flag', () => {
  // self-chat delivers the owner via the is_from_me=0 loopback copy, never this path.
  expect(fromMeGroupAction(false, true, false)).toBe('drop')
})

// --- passesGroupAllowFrom: the owner is always admitted; others obey the allowlist ---

test('owner (fromMe) is always admitted, even against a non-empty member allowlist', () => {
  expect(passesGroupAllowFrom(['+15550001111'], '+15559998888', true)).toBe(true)
})

test('empty member allowlist admits anyone', () => {
  expect(passesGroupAllowFrom([], '+15559998888', false)).toBe(true)
})

test('non-empty member allowlist admits a listed member', () => {
  expect(passesGroupAllowFrom(['+15550001111'], '+15550001111', false)).toBe(true)
})

test('non-empty member allowlist rejects an unlisted non-owner', () => {
  expect(passesGroupAllowFrom(['+15550001111'], '+15559998888', false)).toBe(false)
})
