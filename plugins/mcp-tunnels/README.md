# mcp-tunnels

Connect Claude to an MCP server running inside your private network through an
Anthropic [**MCP tunnel**](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/overview)
— no inbound ports, no public exposure, no IP allowlisting on your origin.
Traffic flows over an outbound-only connection.

> **Research preview.** MCP tunnels is provided "as-is" with no uptime or
> support commitment and depends on a third-party transport provider
> (Cloudflare). Review the
> [security model](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/security)
> before sending anything sensitive.

## Commands

### `/create-docker-mcp-tunnel [deployment-dir]`

Drives the MCP tunnels
[**quickstart**](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/quickstart)
end to end on your machine, using Docker
Compose with manually supplied credentials (the shortest path for local
testing). It walks you through the parts only you can do in the Claude Console
and runs everything else for you:

1. **Preflight** — checks Docker, Docker Compose, OpenSSL, and outbound
   connectivity.
2. **Create the tunnel** (Console) — you create it and copy the domain; the
   token stays out of the chat and goes into a locked-down, gitignored `.env`.
3. **Certificates** — generates a CA and a server certificate with OpenSSL,
   with the exact extensions the tunnel requires.
4. **Register the CA** (Console) — you upload `ca.crt`; the tunnel goes Active.
5. **Upstream** — scaffolds a verifiable FastMCP sample server, or wires up an
   MCP server you already have.
6. **Proxy config + Compose** — writes `mcp-proxy.yaml` and a
   `docker-compose.yaml` with digest-pinned images and the cloudflared agent.
7. **Start and verify** — brings the stack up and checks the proxy and tunnel
   logs.
8. **Call it from Claude** — shows you how to reach the server from Managed
   Agents and the Messages API.

It also carries a troubleshooting matrix (TLS handshake failures, the
`routes`-must-be-a-map gotcha, the `tls.key` permission issue, the
config-is-not-hot-reloaded trap, upstream IP validation) and the operational
basics for token rotation and certificate renewal.

**Usage:**

```
/create-docker-mcp-tunnel
/create-docker-mcp-tunnel ~/work/my-tunnel
```

### Copying the CA certificate to another machine

You register the CA in the Console from a browser, which is often a different
machine than the one running the stack (for example, the tunnel runs in a
remote homespace but you upload `ca.crt` from your laptop or devbox). Only the
**certificate** (`<deployment-dir>/data/ca.crt`, ~1 KB PEM) leaves the host —
never `data/ca.key` or `data/tls.key`.

For a file this small, the simplest path is to print it and paste it into the
Console's certificate field directly:

```bash
cat <deployment-dir>/data/ca.crt   # default: ~/mcp-tunnel/data/ca.crt
```

To copy it as a file with `scp`, run the command from whichever machine can
SSH to the other (`scp` can't relay between two remotes). Pulling from a
homespace onto your devbox — if you've run `coder config-ssh`, the host is
`coder.<workspace>`:

```bash
scp coder.<workspace>:<deployment-dir>/data/ca.crt .
# generic form: scp <homespace-ssh-host>:~/mcp-tunnel/data/ca.crt .
```

Or push from the host to the devbox, if the host can reach it:

```bash
scp <deployment-dir>/data/ca.crt <user>@<devbox-host>:~/
```

## What gets built

A small container stack on your host:

| Container | Role |
|---|---|
| **mcp-proxy** | Anthropic's proxy. Terminates inner TLS with a cert you control, validates upstream IPs, routes by hostname. |
| **cloudflared** | The tunnel agent. Outbound-only to the Anthropic tunnel edge; shares the proxy's network namespace. |
| **hello-mcp** *(optional)* | A FastMCP sample server, only if you don't have an MCP server to expose yet. |

When it's running, the routed server is reachable from Claude at
`https://<subdomain>.<your-tunnel-domain>/<path>` with nothing listening on a
public port.

## Requirements

- Docker and Docker Compose.
- OpenSSL 1.1.1 or newer.
- A Claude Console role that can manage MCP tunnels.
- Outbound access to `api.anthropic.com:443` and the tunnel edge on 7844
  TCP/UDP. No inbound ports are opened.

## Scope and next steps

This plugin targets the **manual-credentials, single-host, local-testing**
path. For a hardened single-host deployment (non-root, read-only rootfs,
dropped capabilities), a Kubernetes deployment, or programmatic access via
[Workload Identity Federation](https://platform.claude.com/docs/en/manage-claude/workload-identity-federation),
see the official deployment guides:
[Deploy with Docker Compose](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/deploy-compose) /
[Deploy with Helm](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/deploy-helm).

## Author

Anthropic (support@anthropic.com)

## License

See `LICENSE`.
