# Local MCP Security

**MCPB provides no sandbox.** There's no `permissions` block in the manifest, no filesystem scoping, no network allowlist enforced by the platform. The server process runs with the user's full privileges — it can read any file the user can, spawn any process, hit any network endpoint.

Claude drives it. That combination means: **tool inputs are untrusted**, even though they come from an AI the user trusts. A prompt-injected web page can make Claude call your `delete_file` tool with a path you didn't intend.

Your tool handlers are the only defense. Everything below is about building that defense yourself.

---

## Path traversal

The #1 bug in local MCP servers. If you take a path parameter and join it to a root, **resolve and check containment**.

```typescript
import { resolve, relative, isAbsolute } from "node:path";

function safeJoin(root: string, userPath: string): string {
  const full = resolve(root, userPath);
  const rel = relative(root, full);
  if (rel.startsWith("..") || isAbsolute(rel)) {
    throw new Error(`Path escapes root: ${userPath}`);
  }
  return full;
}
```

`resolve` normalizes `..`, symlink segments, etc. `relative` tells you if the result left the root. Don't just `String.includes("..")` — that misses encoded and symlink-based escapes.

**Python equivalent:**

```python
from pathlib import Path

def safe_join(root: Path, user_path: str) -> Path:
    full = (root / user_path).resolve()
    if not full.is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes root: {user_path}")
    return full
```

---

## Roots — ask the host, don't hardcode

Before hardcoding `ROOT` from a config env var, check if the host supports `roots/list`. This is the spec-native way to get user-approved workspace boundaries.

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

const server = new McpServer({ name: "...", version: "..." });

let allowedRoots: string[] = [];
server.server.oninitialized = async () => {
  const caps = server.getClientCapabilities();
  if (caps?.roots) {
    const { roots } = await server.server.listRoots();
    allowedRoots = roots.map(r => new URL(r.uri).pathname);
  } else {
    allowedRoots = [process.env.ROOT_DIR ?? process.cwd()];
  }
};
```

```python
# fastmcp — inside a tool handler
async def my_tool(ctx: Context) -> str:
    try:
        roots = await ctx.list_roots()
        allowed = [urlparse(r.uri).path for r in roots]
    except Exception:
        allowed = [os.environ.get("ROOT_DIR", os.getcwd())]
```

If roots are available, use them. If not, fall back to config. Either way, validate every path against the allowed set.

---

## Command injection

If you spawn processes, **never pass user input through a shell**.

```typescript
// ❌ catastrophic
exec(`git log ${branch}`);

// ✅ array-args, no shell
execFile("git", ["log", branch]);
```

If you're wrapping a CLI, build the full argv as an array. Validate each flag against an allowlist if the tool accepts flags at all.

---

## Read-only by default

Split read and write into separate tools. Most workflows only need read. A tool that's read-only can't be weaponized into data loss no matter what Claude is tricked into calling it with.

```
list_files   ← safe to call freely
read_file    ← safe to call freely
write_file   ← separate tool, separate scrutiny
delete_file  ← consider not shipping this at all
```

Pair this with tool annotations — `readOnlyHint: true` on every read tool, `destructiveHint: true` on delete/overwrite tools. Hosts surface these in permission UI (auto-approve reads, confirm-dialog destructive). See `../build-mcp-server/references/tool-design.md`.

If you ship write/delete, consider requiring explicit confirmation via elicitation (see `../build-mcp-server/references/elicitation.md`) or a confirmation widget (see `build-mcp-app`) so the user approves each destructive call.

---

## Resource limits

Claude will happily ask to read a 4GB log file. Cap everything:

```typescript
const MAX_BYTES = 1_000_000;
const buf = await readFile(path);
if (buf.length > MAX_BYTES) {
  return {
    content: [{
      type: "text",
      text: `File is ${buf.length} bytes — too large. Showing first ${MAX_BYTES}:\n\n`
            + buf.subarray(0, MAX_BYTES).toString("utf8"),
    }],
  };
}
```

Same for directory listings (cap entry count), search results (cap matches), and anything else unbounded.

---

## Secrets

- **Config secrets** (`sensitive: true` in manifest `user_config`): host stores in OS keychain, delivers via env var. Don't log them. Don't include them in tool results.
- **Never store secrets in plaintext files.** If the host's keychain integration isn't enough, use `keytar` (Node) / `keyring` (Python) yourself.
- **Tool results flow into the chat transcript.** Anything you return, the user (and any log export) can see. Redact before returning.

---

## Checklist before shipping

- [ ] Every path parameter goes through containment check
- [ ] No `exec()` / `shell=True` — `execFile` / array-argv only
- [ ] Write/delete split from read tools; `readOnlyHint`/`destructiveHint` annotations set
- [ ] Size caps on file reads, listing lengths, search results
- [ ] Secrets never logged or returned in tool results
- [ ] Tested with adversarial inputs: `../../etc/passwd`, `; rm -rf ~`, 10GB file
