# mdshare plugin for Claude Code

Wraps the [mdshare-mcp](https://www.npmjs.com/package/mdshare-mcp) server as a Claude Code plugin so Claude can share markdown documents to [mdshare.live](https://mdshare.live) without copy-pasting walls of text into the conversation.

## What it does

Adds 14 MCP tools for uploading, reading, editing, commenting on, and versioning markdown documents. Claude calls them automatically when you ask things like:

- "share this markdown with my team"
- "publish these notes as a link"
- "give me a comment-only link for this doc"
- "what versions does this doc have?"

The MCP server uses `file_path` arguments so large markdown files don't burn conversation tokens — disk → mdshare.live, never through the model context.

## Install

```
/plugin install mdshare@claude-plugins-official
```

Or browse `/plugin > Discover` and search for `mdshare`.

## Permissions model

Every document gets four kinds of share links:

- **admin** — full control (rename, regenerate keys, delete)
- **edit** — modify content
- **comment** — add inline-anchored comments without editing
- **view** — read-only

No accounts. The link is the auth. Don't paste anything sensitive.

## Underlying MCP server

`npx -y mdshare-mcp` — published to npm, registered in the official MCP Registry as `io.github.sathya-sankaran/mdshare`.

## Links

- mdshare.live — https://mdshare.live
- GitHub — https://github.com/urbanmorph/mdshare
- npm — https://www.npmjs.com/package/mdshare-mcp
- MCP Registry — `io.github.sathya-sankaran/mdshare`

## License

MIT
