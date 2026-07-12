import { describe, expect, test } from 'bun:test'

import { isPermissionReplyAuthorized } from './permission-auth.js'

describe('permission reply authorization', () => {
  test('accepts an exact top-level owner', () => {
    expect(isPermissionReplyAuthorized(['owner-1'], 'owner-1')).toBe(true)
  })

  test('rejects a group-admitted non-owner', () => {
    expect(isPermissionReplyAuthorized(['owner-1'], 'group-member')).toBe(false)
  })

  test('rejects everyone when no owner is paired', () => {
    expect(isPermissionReplyAuthorized([], 'group-member')).toBe(false)
  })

  test('uses exact identity matching', () => {
    expect(isPermissionReplyAuthorized(['owner-10'], 'owner-1')).toBe(false)
  })
})
