/**
 * Busy-gate for Discord channel delivery (JP-44).
 *
 * Inbound IM + scheduler messages reach the Claude TUI via MCP
 * notification, a path that does NOT enroll in Claude's pty type-ahead
 * queue. Delivered mid-turn, the text orphans in the input box and is
 * never submitted (the "wedge"). This module gates delivery: every
 * payload is enqueued and a drain loop flushes it FIFO, one per tick,
 * only when the tmux pane is idle.
 */
import { execFile } from 'node:child_process'
import { promisify } from 'node:util'

const execFileAsync = promisify(execFile)

/** Substring present in the Claude TUI footer only while a turn is generating. */
export const BUSY_MARKER = 'esc to interrupt'

/** tmux target (session:window) to inspect. Configurable for non-a1-b hosts. */
export const TMUX_TARGET = process.env.TMUX_TARGET ?? 'claude-tg-agent:0'

/** Max queued payloads before the oldest is evicted to bound memory. */
export const QUEUE_MAX_SIZE = 100

/**
 * Drain-loop tick interval.
 *
 * 500ms keeps queued-message latency imperceptible while serializing all
 * delivery through the drain loop. Correctness under bursts does NOT depend
 * on this interval: the FOOTER_SETTLE_MS cooldown (below) holds the queue
 * across the footer's busy-lag window regardless of how often the loop ticks.
 */
export const QUEUE_DRAIN_INTERVAL_MS = 500

/**
 * Post-deliver settle cooldown.
 *
 * `tmux capture-pane` reflects the footer's busy marker ~1s AFTER the agent
 * actually goes busy on a freshly delivered message. With a 500ms tick this
 * lag is wider than one tick, so re-probing right after a delivery would read
 * a not-yet-settled (still "idle") footer and flush the next payload into the
 * previous message's lag window — re-wedging it. After each delivery the gate
 * refuses to flush again until FOOTER_SETTLE_MS has elapsed, giving the footer
 * time to settle so the next busy probe is truthful. This makes correctness
 * independent of tick frequency (see plan doc, "cooldown design").
 */
export const FOOTER_SETTLE_MS = 1500

/**
 * Hard cap on a single `tmux capture-pane` shell-out.
 *
 * Kept short: the probe should return in low single-digit milliseconds; a
 * hung tmux must not stall the drain loop. On timeout the capture fails
 * open (idle), so a brief cap only risks an extra-fast retry, never a wedge.
 */
const CAPTURE_TIMEOUT_MS = 1000

/** Number of trailing capture lines that may contain the TUI footer marker. */
const FOOTER_TAIL_LINES = 5

/**
 * Decide whether the Claude pane is mid-turn from a captured pane snapshot.
 *
 * Tests only the last FOOTER_TAIL_LINES lines for the busy marker. The marker
 * lives in the TUI footer; scanning the whole capture would read busy forever
 * if agent output happened to contain the literal marker string.
 *
 * Args:
 *   pane: stdout of `tmux capture-pane -p`.
 * Returns:
 *   True when the busy marker is present in the footer region, else False.
 */
export function isPaneBusy(pane: string): boolean {
  const footer = pane.split('\n').slice(-FOOTER_TAIL_LINES).join('\n')
  return footer.includes(BUSY_MARKER)
}

/**
 * Capture the configured tmux pane and report busy state.
 *
 * Shells out asynchronously to `tmux capture-pane -p -t <TMUX_TARGET>` so a
 * slow or hung tmux never blocks the event loop. On any failure (tmux
 * missing, target gone, non-zero exit, timeout) resolves False — fail-open so
 * a broken capture never wedges delivery permanently.
 *
 * Args:
 *   target: tmux session:window to inspect. Defaults to TMUX_TARGET.
 * Returns:
 *   Promise resolving True when the footer shows the busy marker, False on
 *   idle or on error.
 */
export async function capturePaneBusy(target: string = TMUX_TARGET): Promise<boolean> {
  try {
    const { stdout } = await execFileAsync('tmux', ['capture-pane', '-p', '-t', target], {
      encoding: 'utf8',
      timeout: CAPTURE_TIMEOUT_MS,
    })
    return isPaneBusy(stdout)
  } catch (err) {
    process.stderr.write(`discord busy-gate: capture-pane failed (treating as idle): ${err}\n`)
    return false
  }
}

/**
 * Dependencies a BusyGate needs, injected for testability.
 *
 * isBusy: busy probe (production: capturePaneBusy). May be sync or async;
 *   drainOnce awaits it either way.
 * deliver: async delivery of one payload (production: mcp.notification wrapper).
 * now: wall-clock reader in ms (production: Date.now). Injected so tests can
 *   drive the settle cooldown deterministically.
 */
export type BusyGateDeps<T> = {
  isBusy: () => boolean | Promise<boolean>
  deliver: (payload: T) => Promise<void>
  now?: () => number
}

/**
 * FIFO busy-gated delivery queue.
 *
 * Every payload is enqueued by submit(); nothing is ever delivered
 * synchronously from submit(). A drain loop flushes ONE payload per tick
 * while idle. Two layered holds keep bursts from re-wedging the agent:
 *   - a post-deliver settle cooldown (FOOTER_SETTLE_MS) that ignores the
 *     lagging footer right after a delivery, and
 *   - a steady-state busy probe (isBusy) for the footer once it has settled.
 * A re-entrancy guard (draining) prevents a slow deliver() from letting the
 * next tick concurrently shift+deliver a second payload with unordered writes.
 */
export class BusyGate<T> {
  private readonly queue: T[] = []
  private readonly deps: BusyGateDeps<T>
  private readonly now: () => number
  private timer: ReturnType<typeof setInterval> | null = null
  private lastDeliverAt = 0
  private draining = false

  constructor(deps: BusyGateDeps<T>) {
    this.deps = deps
    this.now = deps.now ?? Date.now
  }

  /** Current queue depth. */
  get size(): number {
    return this.queue.length
  }

  /** Oldest queued payload without removing it (test/inspection aid). */
  peekOldest(): T | undefined {
    return this.queue[0]
  }

  /**
   * Enqueue a payload for delivery. Always enqueued; the drain loop
   * delivers it when the pane is next idle. On overflow the oldest queued
   * payload is evicted (newest is most relevant; an over-cap backlog
   * signals a stuck agent).
   *
   * Args:
   *   payload: the {content, meta} channel-notification body.
   * Returns:
   *   None.
   */
  submit(payload: T): void {
    if (this.queue.length >= QUEUE_MAX_SIZE) {
      this.queue.shift()
      process.stderr.write(`discord busy-gate: queue full (${QUEUE_MAX_SIZE}), dropped oldest\n`)
    }
    this.queue.push(payload)
  }

  /**
   * Flush at most one payload if it is safe to do so.
   *
   * Hold checks run cheapest-first, shelling out only when needed:
   *   1. re-entrant call (a prior drainOnce still awaiting) -> hold
   *   2. empty queue -> nothing to do
   *   3. settle cooldown not elapsed since the last delivery -> hold
   *   4. footer reports busy -> hold
   * Only when all pass is one payload shifted and delivered; lastDeliverAt is
   * stamped on success to open the next settle window.
   *
   * Returns:
   *   None.
   */
  async drainOnce(): Promise<void> {
    if (this.draining) return
    if (this.queue.length === 0) return
    this.draining = true
    try {
      if (this.now() - this.lastDeliverAt < FOOTER_SETTLE_MS) return
      if (await this.deps.isBusy()) return
      const payload = this.queue.shift()!
      try {
        await this.deps.deliver(payload)
        this.lastDeliverAt = this.now()
      } catch (err) {
        // deliver failed; payload already shifted -> dropped, no retry. lastDeliverAt
        // is NOT stamped, so the next tick proceeds immediately.
        process.stderr.write(`discord busy-gate: flush deliver failed: ${err}\n`)
      }
    } finally {
      this.draining = false
    }
  }

  /**
   * Start the background drain loop. Idempotent. The interval is unref'd so
   * it never blocks process exit.
   *
   * Returns:
   *   None.
   */
  start(): void {
    if (this.timer) return
    this.timer = setInterval(() => {
      void this.drainOnce()
    }, QUEUE_DRAIN_INTERVAL_MS)
    // bun's setInterval Timer exposes unref; the optional chain is a defensive
    // guard for any runtime whose timer object lacks it.
    this.timer.unref?.()
  }

  /**
   * Stop the drain loop and drop any queued payloads.
   *
   * Returns:
   *   None.
   */
  stop(): void {
    if (this.timer) {
      clearInterval(this.timer)
      this.timer = null
    }
    this.queue.length = 0
  }
}
