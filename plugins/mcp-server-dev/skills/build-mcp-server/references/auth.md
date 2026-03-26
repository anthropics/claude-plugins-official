# Auth for MCP Servers

Auth is the reason most people end up needing a **remote** server even when a local one would be simpler. OAuth redirects, token storage, and refresh all work cleanly when there's a real hosted endpoint to redirect back to.

---

## The three tiers

### Tier 1: No auth / static API key

Server reads a key from env. User provides it once at setup. Done.

```typescript
const apiKey = process.env.UPSTREAM_API_KEY;
if (!apiKey) throw new Error("UPSTREAM_API_KEY not set");
```

Works for local stdio, MCPB, and remote servers alike. If this is all you need, stop here.

### Tier 2: OAuth 2.0 via CIMD (preferred per spec 2025-11-25)

**Client ID Metadata Document.** The MCP host publishes its client metadata at an HTTPS URL and uses that URL *as* its `client_id`. Your authorization server fetches the document, validates it, and proceeds with the auth-code flow. No registration endpoint, no stored client records.

Spec 2025-11-25 promoted CIMD to SHOULD (preferred). Advertise support via `client_id_metadata_document_supported: true` in your OAuth AS metadata.

**Server responsibilities:**

1. Serve OAuth Authorization Server Metadata (RFC 8414) at `/.well-known/oauth-authorization-server` with `client_id_metadata_document_supported: true`
2. Serve an MCP-protected-resource metadata document pointing at (1)
3. At authorize time: fetch `client_id` as an HTTPS URL, validate the returned client metadata, proceed
4. Validate bearer tokens on incoming `/mcp` requests

```
┌─────────┐  client_id=https://...  ┌──────────────┐   upstream OAuth   ┌──────────┐
│ MCP host│ ──────────────────────> │ Your MCP srv │ ─────────────────> │ Upstream │
└─────────┘ <─── bearer token ───── └──────────────┘ <── access token ──└──────────┘
```

### Tier 3: OAuth 2.0 via Dynamic Client Registration (DCR)

**Backward-compat fallback** — spec 2025-11-25 demoted DCR to MAY. The host discovers your `registration_endpoint`, POSTs its metadata to register itself as a client, gets back a `client_id`, then runs the auth-code flow.

Implement DCR if you need to support hosts that haven't moved to CIMD yet. Same server responsibilities as CIMD, but instead of fetching the `client_id` URL you run a registration endpoint that stores client records.

**Client priority order:** pre-registered → CIMD (if AS advertises `client_id_metadata_document_supported`) → DCR (if AS has `registration_endpoint`) → prompt user.

---

## Hosting providers with built-in DCR/CIMD support

Several MCP-focused hosting providers handle the OAuth plumbing for you — you implement tool logic, they run the authorization server. Check their docs for current capabilities. If the user doesn't have strong hosting preferences, this is usually the fastest path to a working OAuth-protected server.

---

## Local servers and OAuth

Local stdio servers **can** do OAuth (open a browser, catch the redirect on a localhost port, stash the token in the OS keychain). It's fragile:

- Breaks in headless/remote environments
- Every user re-does the dance
- No central token refresh or revocation

If OAuth is required, lean hard toward remote HTTP. If you *must* ship local + OAuth, the `@modelcontextprotocol/sdk` includes a localhost-redirect helper, and MCPB is the right packaging so at least the runtime is predictable.

---

## Token storage

| Deployment | Store tokens in |
|---|---|
| Remote, stateless | Nowhere — host sends bearer each request |
| Remote, stateful | Session store keyed by MCP session ID (Redis, etc.) |
| MCPB / local | OS keychain (`keytar` on Node, `keyring` on Python). **Never plaintext on disk.** |

---

## Token audience validation (spec MUST)

Validating "is this a valid bearer token" isn't enough. The spec requires validating "was this token minted *for this server*" — RFC 8707 audience. A token issued for `api.other-service.com` must be rejected even if the signature checks out.

**Token passthrough is explicitly forbidden.** Don't accept a token, then forward it upstream. If your server needs to call another service, exchange the token or use its own credentials.

---

## SDK helpers — don't hand-roll

`@modelcontextprotocol/sdk/server/auth` ships:
- `mcpAuthRouter()` — Express router for the full OAuth AS surface (metadata, authorize, token)
- `bearerAuth` — middleware that validates bearer tokens against your verifier
- `proxyProvider` — forward auth to an upstream IdP

If you're wiring auth from scratch, check these first.
