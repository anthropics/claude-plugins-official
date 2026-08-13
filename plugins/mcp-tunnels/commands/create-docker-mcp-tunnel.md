---
description: Stand up an Anthropic MCP tunnel locally with Docker Compose so Claude can call a private MCP server (manual-credentials quickstart).
argument-hint: "[deployment-dir] (default: ./mcp-tunnel)"
allowed-tools: [Bash, Read, Write, Edit, AskUserQuestion]
---

# Create a Docker MCP tunnel

Drive the
[**MCP tunnels quickstart**](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/quickstart)
end to end: from zero to Claude calling a private MCP server through an
Anthropic-operated tunnel, using Docker Compose with manually supplied
credentials (the shortest path for local testing).

> MCP tunnels is in **research preview**. It is provided "as-is" with no uptime
> or support commitment and depends on a third-party transport (Cloudflare).
> Do not put production traffic through this without reading the
> [security model](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/security).

You are guiding the user through a mix of **local commands you run** and
**Console actions only they can do** (creating the tunnel, uploading the CA).
Be a careful operator: explain each step briefly, run the commands, check the
output, and stop with a clear diagnosis if something fails.

Deployment directory: use `$ARGUMENTS` if the user passed a path, otherwise
default to `./mcp-tunnel`. Refer to it below as `$DIR`.

## What you'll build

A container stack on the user's machine:

- **mcp-proxy** — Anthropic's proxy. Terminates the inner TLS handshake using
  a certificate the user controls, validates upstream IPs, routes by hostname.
- **cloudflared** — the tunnel agent. Outbound-only connection to the Anthropic
  tunnel edge; shares the proxy's network namespace.
- **hello-mcp** *(optional)* — a sample FastMCP server, only if the user has no
  MCP server of their own to expose yet.

When it's up, the routed server is reachable from Claude at
`https://<subdomain>.<tunnel-domain>/<path>` with nothing listening on a public
port.

## Step 0 — Preflight

Run these and report what's missing before going further:

```bash
docker --version && docker compose version && openssl version
```

- Docker + Docker Compose are required. `openssl` 1.1.1+ is required (the
  commands below use `-addext`, available in 1.1.1+).
- Confirm the host has **outbound** access to `api.anthropic.com:443` and the
  tunnel edge (`198.41.192.0/19`, `2606:4700:a0::/44`) on **7844 TCP and UDP**.
  No inbound ports are opened.

If `docker compose` (v2) is unavailable but `docker-compose` (v1) exists, use
that and tell the user; the compose file is v2-compatible.

## Step 1 — Create the tunnel (Console — user action)

Tell the user to do this in the [Claude Console](https://console.anthropic.com)
(see [Create a tunnel](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/console#create-a-tunnel)):

1. Sidebar → **Manage → MCP tunnels** → **New tunnel**. Give it a name.
2. Leave **Set up programmatic access** **off** — this quickstart uses manual
   credentials.
3. Open the tunnel. From the **Connection** section copy two values:
   - **Domain** — looks like `abcd1234.tunnel.anthropic.com`
   - **Token** — click the eye icon, then copy

Then ask the user, via AskUserQuestion or a direct prompt, for the **Domain**.
**Do not ask them to paste the Token into the chat.** The token is a secret
that authenticates the outbound tunnel connection; keep it out of the
transcript. Instead, tell them you will create a `$DIR/.env` file and they
should paste the token into it themselves (Step 3), or have them export it:
`export TUNNEL_TOKEN='eyJ...'` in the shell you'll run compose from.

Record the domain as `TUNNEL_DOMAIN` for the steps below.

## Step 2 — Deployment directory

```bash
mkdir -p "$DIR"/{config,data}
cd "$DIR"
```

## Step 3 — Credentials file

Create `$DIR/.env` (compose auto-loads it; this survives reboots, unlike a
shell `export`). Write `TUNNEL_DOMAIN` yourself; leave a placeholder for the
secret and have the **user** fill it in:

```
TUNNEL_DOMAIN=<the domain from step 1>
TUNNEL_TOKEN=PASTE_TUNNEL_TOKEN_HERE
```

Then lock it down and make sure it never gets committed:

```bash
chmod 600 "$DIR/.env"
printf '.env\ndata/\n' > "$DIR/.gitignore"
```

Pause and have the user replace `PASTE_TUNNEL_TOKEN_HERE` with the real token
(tell them the exact file path). Verify it's set without printing it:

```bash
cd "$DIR" && grep -q '^TUNNEL_TOKEN=eyJ' .env && echo "token looks set" || echo "token NOT set — edit .env"
```

Load it for the openssl/config steps in this shell:

```bash
cd "$DIR" && set -a && . ./.env && set +a && echo "domain: $TUNNEL_DOMAIN"
```

## Step 4 — Generate the CA and server certificate

The proxy terminates an inner TLS handshake using a certificate signed by a CA
the user controls. Generate both (Linux/macOS shown; the
[quickstart](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/quickstart)
also has a Windows PowerShell variant — offer it if the user is on Windows):

```bash
cd "$DIR"

openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout data/ca.key -out data/ca.crt \
  -days 3650 -subj "/CN=mcp-tunnel-ca" \
  -addext "basicConstraints=critical,CA:TRUE" \
  -addext "keyUsage=critical,keyCertSign,cRLSign" \
  -addext "subjectKeyIdentifier=hash"

cat > data/tls.ext <<EOF
subjectAltName = DNS:${TUNNEL_DOMAIN},DNS:*.${TUNNEL_DOMAIN}
authorityKeyIdentifier = keyid,issuer
extendedKeyUsage = serverAuth
EOF

openssl req -newkey rsa:2048 -nodes \
  -keyout data/tls.key -out /tmp/server.csr \
  -subj "/CN=${TUNNEL_DOMAIN}"
openssl x509 -req -in /tmp/server.csr \
  -CA data/ca.crt -CAkey data/ca.key -CAcreateserial \
  -out data/tls.crt -days 90 -extfile data/tls.ext

chmod 644 data/tls.key
```

Why these flags: the explicit `-addext` extensions make the CA satisfy the
tunnel's [certificate requirements](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/reference#certificate-requirements)
regardless of distro `openssl.cnf` defaults;
`-extfile` (not `-copy_extensions`, which is OpenSSL 3.0+ only) keeps this
working on OpenSSL 1.1.x and adds the `AuthorityKeyIdentifier` the proxy
requires. `chmod 644 data/tls.key` is **required**: openssl writes the key
`0600` but the proxy container runs as a non-root user and must read it.

`data/tls.key` and `data/ca.key` are sensitive — they live under `data/`,
which the `.gitignore` from Step 3 already excludes.

## Step 5 — Register the CA (Console — user action)

Have the user, on the tunnel detail page, scroll to **Certificates** →
**Add certificate**
(see [Add a CA certificate](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/console#add-a-ca-certificate)),
and upload `$DIR/data/ca.crt` (or paste its contents —
print it with `cat data/ca.crt` so they can copy it). The tunnel status flips
to **Active** once a certificate is registered. The tunnel will not appear in
the agent picker until this is done.

Wait for the user to confirm the tunnel shows **Active** before continuing.

## Step 6 — Choose the upstream MCP server

Ask the user (AskUserQuestion):

- **"I have an MCP server already"** — get its reachable address as
  `scheme://host:port` (port mandatory, no path — the proxy rejects a path in
  the upstream value at config load). It must be reachable from the proxy
  container and resolve to an RFC1918 private address (`10/8`, `172.16/12`,
  `192.168/16`); the proxy refuses public/loopback upstreams by default
  (SSRF protection). If it runs as a Compose service, add it to the compose
  file so it shares the network. If it runs on the host, see Troubleshooting
  ("host process"). Pick a route subdomain with the user (e.g. `wiki`).
- **"Use the sample server"** — scaffold the FastMCP `hello-server` below as a
  Compose service `hello-mcp` and route subdomain `echo`.

### Sample server (only if chosen)

Write `$DIR/hello_server.py`:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("hello-server", host="0.0.0.0", port=9000)


@mcp.tool()
def hello(name: str = "world") -> str:
    """Say hello to someone."""
    return f"Hello, {name}!"


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
```

## Step 7 — Proxy config

Write `$DIR/config/mcp-proxy.yaml`. `tunnel_domain` is **required** (the
proxy strips it from the incoming hostname to find the subdomain in `routes`).
`routes` is a **flat map** subdomain → upstream URL, *not* a list:

```yaml
listen_addr: ":8080"
log_level: info
tunnel_domain: <TUNNEL_DOMAIN>
tls:
  cert_file: /data/tls.crt
  key_file: /data/tls.key
routes:
  echo: http://hello-mcp:9000
```

Substitute the real `TUNNEL_DOMAIN`. Replace the `routes:` block with the
user's chosen subdomain → upstream if they brought their own server (e.g.
`wiki: http://wiki-mcp.internal:8080`). You can keep multiple routes.

## Step 8 — Compose file

Write `$DIR/docker-compose.yaml`. Images are pinned by digest:

```yaml
services:
  mcp-proxy:
    image: us-docker.pkg.dev/anthropic-public-registry/images/mcp-proxy@sha256:6b9adedbf2763143ec72f106ecaf0ce7fd3294e89b208f54a1db97a33d14c5ba
    command: ["-config", "/etc/mcp-proxy/config.yaml"]
    volumes:
      - ./config/mcp-proxy.yaml:/etc/mcp-proxy/config.yaml:ro
      - ./data:/data:ro
    restart: unless-stopped

  cloudflared:
    image: cloudflare/cloudflared@sha256:6b599ca3e974349ead3286d178da61d291961182ec3fe9c505e1dd02c8ac31b0
    command: tunnel --no-autoupdate run --url http://localhost:8080
    environment:
      - TUNNEL_TOKEN
    network_mode: "service:mcp-proxy"
    restart: unless-stopped
```

`--url http://localhost:8080` is **required** in the manual flow: no ingress
rules are pushed server-side, so without it cloudflared 503s every request.
`network_mode: "service:mcp-proxy"` shares the proxy's netns so
`localhost:8080` reaches it. `environment: - TUNNEL_TOKEN` (no value) passes
the variable through from `.env`.

If the sample server was chosen, append the service:

```yaml
  hello-mcp:
    image: python:3.13-slim
    working_dir: /app
    volumes:
      - ./hello_server.py:/app/hello_server.py:ro
    command: sh -c "pip install --quiet mcp && python hello_server.py"
    restart: unless-stopped
```

If the user brought their own server *and* it's containerized, add its service
here too so it shares the Compose network with the proxy.

(For a hardened single-host deployment — non-root user, read-only rootfs,
`cap_drop: ALL`, `no-new-privileges` — point the user at
[Deploy with Docker Compose](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/deploy-compose);
this quickstart keeps it minimal for fast local testing.)

## Step 9 — Start and verify

```bash
cd "$DIR" && docker compose up -d
sleep 5
docker compose logs mcp-proxy | grep -i "route configured"
docker compose logs cloudflared | grep -i "Registered tunnel connection"
```

Expect one `route configured` line per route and **four**
`Registered tunnel connection` lines. Containers take a few seconds; rerun the
log greps if they come back empty (don't conclude failure on the first empty
result). If they stay empty, go to Troubleshooting.

## Step 10 — Call it from Claude

Tell the user both options:

**Managed Agents (Console):** **Managed Agents → Sessions** → new session →
agent picker **Create new agent** → **+ MCP Server** → select the tunnel →
**Subdomain** = the route (`echo`), **Path** = `mcp` (FastMCP
`streamable-http` serves at `/mcp`). Then ask: *"Use the hello tool to greet
tunnel."* — expect a tool call and its result.

**Messages API:** the host is `<subdomain>.<tunnel-domain>`; the path is
whatever the upstream serves (`/mcp` for FastMCP). Use an API key for the
workspace the tunnel was created in.

```bash
curl https://api.anthropic.com/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: mcp-client-2025-11-20" \
  -d "{
    \"model\": \"claude-opus-4-7\",
    \"max_tokens\": 1024,
    \"mcp_servers\": [{\"type\": \"url\", \"name\": \"echo\", \"url\": \"https://echo.${TUNNEL_DOMAIN}/mcp\"}],
    \"tools\": [{\"type\": \"mcp_toolset\", \"mcp_server_name\": \"echo\"}],
    \"messages\": [{\"role\": \"user\", \"content\": \"call hello with name=tunnel\"}]
  }"
```

The tunnel carries encrypted traffic but does **not** authenticate to the
upstream. If the upstream MCP server requires its own auth, the user supplies
it the same as for any other MCP server.

## Troubleshooting (diagnose in this order)

| Symptom | Cause | Fix |
|---|---|---|
| Caller sees HTTP 500; cloudflared logs `No ingress rules were defined` | cloudflared has no local target | Ensure `--url http://localhost:8080` and `network_mode: "service:mcp-proxy"` are both present, then `docker compose up -d` |
| Proxy exits `cannot unmarshal !!seq into map[string]string` | `routes` written as a YAML list | Use `routes: { name: http://host:port }`, not a list of objects |
| Proxy exits `open /data/tls.key: permission denied` | key is `0600`, proxy runs non-root | `chmod 644 data/tls.key` |
| Proxy logs `no route for host` (caller gets `502 No route configured for host`) | `tunnel_domain` missing or wrong | Set it to the exact domain on the tunnel detail page; then **restart the proxy** (next row) |
| Edited config but nothing changed | proxy does **not** hot-reload `config.yaml` (only `tls.cert_file`) | `docker compose restart mcp-proxy` — `up -d` alone won't recreate it on a file-content change |
| `tls handshake failed ... unknown certificate authority` | CA not registered/revoked on this tunnel | Re-upload `data/ca.crt` in the Console (Step 5) |
| `tls handshake failed ... bad certificate` | server cert SAN ≠ `*.<tunnel-domain>`, or expired | Regenerate the server cert (Step 4) with the correct `TUNNEL_DOMAIN` |
| `IP validation failed: <ip> is not a private address` | upstream resolves outside RFC1918 (e.g. `127.0.0.1`, public IP) | Run the upstream as a Compose service on the proxy's network; or narrow `upstream.allowed_ips` deliberately (avoid `0.0.0.0/0` outside local testing) |
| `dial tcp ...: connect: connection refused` for `host.docker.internal` | rootless Docker can't reach the host netns | Run the MCP server as a Compose service instead of a host process |
| HTTP 502, no `request started` in proxy log | cloudflared hadn't finished registering, or rolling update | Wait for ×4 `Registered tunnel connection` and retry |
| Tunnel missing from agent **+ MCP Server** picker | no active certificate, or wrong workspace | Register a CA cert (Step 5); open the session in the tunnel's workspace |
| `curl https://<proxy>:8080` fails `wrong version number` | expected — listener is plaintext WS, TLS is inside the WS stream | Don't curl the proxy directly; verify via Managed Agent or Messages API |

`docker compose logs cloudflared` (token/edge reachability) and
`docker compose logs mcp-proxy` (config/cert/routing) are the two primary
diagnostics. Check the outbound connection first, then the inner TLS handshake,
then upstream routing. See
[Troubleshooting](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/troubleshooting)
for additional cases.

## Operational notes (mention briefly, don't run unprompted)

- **Token rotation:** Console → **Rotate token** invalidates the old token
  immediately. Update `TUNNEL_TOKEN` in `.env` and
  `docker compose up -d cloudflared`.
- **Cert renewal:** the server cert is valid 90 days. Re-sign with the same CA
  (the registered CA doesn't change) and replace `data/tls.crt`; the proxy
  polls and reloads it, no restart needed.
- **Config changes always need** `docker compose restart mcp-proxy`.

## Wrap up

Summarize: deployment dir, route(s) configured, tunnel domain, and the exact
URL Claude reaches the server at. Remind the user the token is a live secret in
`$DIR/.env` (chmod 600, gitignored) and that this is a research-preview,
local-testing setup — point them at
[Deploy with Docker Compose](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/deploy-compose) /
[Deploy with Helm](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/deploy-helm)
for a hardened or programmatic-access deployment.
