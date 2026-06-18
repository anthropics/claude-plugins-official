/**
 * Scheduler /inject request parsing for the Discord channel server.
 *
 * Split out from server.ts (which has top-level side effects: token check,
 * MCP connect, gateway login) so the HTTP contract is unit-testable in
 * isolation — same pattern as busy-gate.ts / busy-gate.test.ts.
 */

/** Synthetic channel message handed to the busy-gate for delivery. */
export type ChannelDelivery = {
  content: string
  meta: Record<string, string>
}

/** Outcome of parsing a raw /inject request body. */
export type InjectParse =
  | { ok: true; delivery: ChannelDelivery }
  | { ok: false; status: number; message: string }

/**
 * Parse and validate a raw /inject request body into a channel delivery.
 *
 * The scheduler POSTs `{ text, chat_id }`; this turns it into the synthetic
 * `scheduler` channel message handed to the busy-gate. Kept pure (no I/O) so
 * the HTTP contract is unit-testable without booting the MCP server.
 *
 * @param raw - Raw request body, expected to be JSON `{ text, chat_id }`.
 * @returns `{ ok: true, delivery }` on success, else `{ ok: false, status, message }`
 *   carrying the HTTP status (400) and reason to write back.
 */
export function parseInjectBody(raw: string): InjectParse {
  let body: { text?: unknown; chat_id?: unknown }
  try {
    body = JSON.parse(raw)
  } catch {
    return { ok: false, status: 400, message: 'invalid json' }
  }
  if (typeof body.text !== 'string' || !body.text || typeof body.chat_id !== 'string' || !body.chat_id) {
    return { ok: false, status: 400, message: 'missing text or chat_id' }
  }
  return {
    ok: true,
    delivery: {
      content: body.text,
      meta: {
        chat_id: body.chat_id,
        user: 'scheduler',
        user_id: 'scheduler',
        ts: new Date().toISOString(),
      },
    },
  }
}
