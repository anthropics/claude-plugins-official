import { expect, test } from 'bun:test'
import './harness'
import { TOOLS, client } from '../server'

test('importing the server does not open a gateway connection', () => {
  expect(client.isReady()).toBe(false)
  expect(client.token).toBeNull()
})

test('every tool declares a name, a description and an object schema', () => {
  expect(TOOLS.length).toBeGreaterThan(0)
  for (const t of TOOLS) {
    expect(typeof t.name).toBe('string')
    expect(t.description.length).toBeGreaterThan(0)
    expect(t.inputSchema.type).toBe('object')
    for (const req of t.inputSchema.required) {
      expect(Object.keys(t.inputSchema.properties)).toContain(req)
    }
  }
})
