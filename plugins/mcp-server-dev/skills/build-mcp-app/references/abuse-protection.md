# Abuse protection for authless hosted servers

An authless StreamableHTTP server is reachable by anything on the internet.
There are three resources to protect: your compute, any upstream API quota
your tools consume, and egress bandwidth for large `callServerTool` payloads.

## You don't get a per-user identity

In authless mode there is no token and stateless transport gives no session
ID. Traffic from claude.ai is proxied through Anthropic's egress — every web
user arrives from the same small set of IPs:

```
160.79.104.0/21
2607:6bc0::/48
```

(See https://platform.claude.com/docs/en/api/ip-addresses.)

Claude Desktop, Claude Code, and other hosts connect **directly from the
user's machine**, so those *do* have distinct per-user IPs. Per-IP limiting
therefore works for direct-connect clients; for claude.ai you can only limit
the aggregate Anthropic pool. If true per-user limits matter, that's the
trigger to add OAuth.

## Tiered token-bucket (per-replica backstop)

```ts
const ANTHROPIC_CIDRS = ["160.79.104.0/21", "2607:6bc0::/48"];
const TIERS = {
  anthropic: { capacity: 600, refillPerSec: 100 }, // shared pool
  other:     { capacity: 30,  refillPerSec: 2   }, // per-IP
};
```

Match `req.ip` against the CIDRs, pick a bucket (`"anthropic"` or
`"ip:<addr>"`), 429 + `Retry-After` on exhaust. This is a per-replica
backstop — cross-replica enforcement belongs at the edge (Cloudflare, Cloud
Armor), which keeps the containers stateless.

## `trust proxy` must match your topology

`req.ip` only honours `X-Forwarded-For` if `app.set('trust proxy', N)` is
set. `true` trusts every hop, which lets a direct client send
`X-Forwarded-For: 160.79.108.42` and claim the Anthropic tier. Set it to the
exact number of trusted hops (e.g. `1` behind a single LB, `2` behind
Cloudflare → origin LB) and **never `true` in production**.

## Hard-allowlisting Anthropic IPs is a product decision

Blocking everything outside `160.79.104.0/21` locks out Desktop, Claude Code,
and every other MCP host. Use the CIDRs to **tier** rate limits, not to gate
access, unless claude.ai-only is an explicit goal.

## Cache upstream responses

For tools that wrap a third-party API, an in-process LRU keyed on the
normalized query (TTL hours, no secrets in the key) is the primary cost
control — repeat queries become free and absorb thundering-herd. Rate limits
are the safety net, not the first line.
