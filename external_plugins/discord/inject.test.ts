import { describe, expect, test } from 'bun:test'
import { parseInjectBody } from './inject'

describe('parseInjectBody', () => {
  test('parses a valid body into a scheduler channel delivery', () => {
    const r = parseInjectBody('{"text":"hi","chat_id":"123"}')
    expect(r.ok).toBe(true)
    if (!r.ok) return
    expect(r.delivery.content).toBe('hi')
    expect(r.delivery.meta.chat_id).toBe('123')
    expect(r.delivery.meta.user).toBe('scheduler')
    expect(r.delivery.meta.user_id).toBe('scheduler')
    expect(typeof r.delivery.meta.ts).toBe('string')
  })

  test('rejects invalid JSON with 400', () => {
    const r = parseInjectBody('not-json')
    expect(r).toEqual({ ok: false, status: 400, message: 'invalid json' })
  })

  test('rejects a missing chat_id with 400', () => {
    const r = parseInjectBody('{"text":"hi"}')
    expect(r).toEqual({ ok: false, status: 400, message: 'missing text or chat_id' })
  })

  test('rejects a missing text with 400', () => {
    const r = parseInjectBody('{"chat_id":"123"}')
    expect(r).toEqual({ ok: false, status: 400, message: 'missing text or chat_id' })
  })

  test('rejects an empty text with 400', () => {
    const r = parseInjectBody('{"text":"","chat_id":"123"}')
    expect(r).toEqual({ ok: false, status: 400, message: 'missing text or chat_id' })
  })

  test('rejects a non-string chat_id with 400', () => {
    const r = parseInjectBody('{"text":"hi","chat_id":123}')
    expect(r).toEqual({ ok: false, status: 400, message: 'missing text or chat_id' })
  })
})
