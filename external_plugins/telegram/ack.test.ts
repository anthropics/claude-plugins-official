import { test, expect, mock } from 'bun:test'
import { deliverAndAck } from './ack'

// MERT TENY: server.ts korabban a Telegram-nyugtazast (emoji-reakcio) a Claude
// fele valo kezbesites eredmenyetol FUGGETLENUL kuldte -- MCP-kiesesnel a
// felhasznalo "kezbesitve" jelzest kapott egy olyan uzenetre, ami sosem jutott
// el Claude-hoz. Ez a teszt bizonyitja, hogy a nyugtazas most a kezbesites
// sikeretol fugg.

test('ack fires only after delivery succeeds', async () => {
  const ack = mock(() => {})
  const onFailure = mock(() => {})

  const delivered = await deliverAndAck(async () => {}, ack, onFailure)

  expect(delivered).toBe(true)
  expect(ack).toHaveBeenCalledTimes(1)
  expect(onFailure).not.toHaveBeenCalled()
})

test('ack is withheld when delivery fails (MCP outage)', async () => {
  const ack = mock(() => {})
  const onFailure = mock(() => {})
  const err = new Error('MCP disconnected')

  const delivered = await deliverAndAck(async () => {
    throw err
  }, ack, onFailure)

  expect(delivered).toBe(false)
  expect(ack).not.toHaveBeenCalled()
  expect(onFailure).toHaveBeenCalledWith(err)
})
