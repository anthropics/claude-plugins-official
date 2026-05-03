---
name: mdshare-tools
description: Use this skill when the user wants to share, publish, or send a markdown file to a teammate; needs a hosted URL for markdown content; wants to collaborate on markdown with comments or real-time editing; or asks about mdshare-specific operations like generating share links, managing permissions, or document versions. Activates on phrases like "share this markdown", "publish my notes", "give me a link for this doc", "let me comment on the markdown", or any direct mention of mdshare.
version: 1.4.0
license: MIT
---

# mdshare — markdown sharing via MCP

mdshare is a free, no-login markdown sharing service at mdshare.live. This skill orchestrates 14 MCP tools that let Claude upload, read, edit, comment on, and version markdown documents.

## When to use

- The user has a markdown file or just-generated markdown content they want to share
- The user wants link-based collaboration (comments, edit permissions, real-time sync)
- The user mentions mdshare specifically

## When NOT to use

- The user wants Claude to read or edit local markdown files (use the standard file tools)
- The user wants to configure Claude with markdown context (CLAUDE.md / AGENTS.md territory — different concept)
- The content is sensitive — share links are the only auth; warn the user instead

## Core conventions

- **All arguments are literal strings.** Shell substitution like `$(cat file)` does NOT work.
- **For files on disk, prefer `file_path` / `output_path`.** Inline content over ~1KB burns tokens unnecessarily.
- **`key` is OPTIONAL on tools addressed by `document_id`** — admin keys are looked up automatically from the local credential store.
- **Never surface admin URLs to the user** unless they explicitly ask. `upload_markdown` returns only `share_url` by design.
- **For small edits, prefer `patch_document` over `update_document`** — keeps version history granular.

## Tool reference

### Sharing a new document
- `upload_markdown(file_path)` — preferred; pass disk path so content never enters conversation context
- `upload_markdown(content)` — fallback for inline content under ~1KB

Returns `share_url`. Admin URL is stored locally; surface only if explicitly asked via `get_admin_url(document_id)`.

### Editing an existing document
- `patch_document(document_id, operations)` — preferred for small edits (find/replace operations)
- `update_document(document_id, file_path)` — for whole-doc rewrites; pass file_path not content

### Generating links with specific permissions
- `generate_link(document_id, permission)` — `permission` is one of `admin`, `edit`, `comment`, `view`
- `revoke_link(token)` — invalidate a specific link
- `list_links(document_id)` — see all active links

### Comments
- `post_comment(document_id, content, anchor_text?)` — `anchor_text` creates an inline-anchored comment
- `list_comments(document_id)` — read the thread
- `resolve_comment(comment_id)` — mark resolved (drops the in-document highlight)

### Discovery
- `list_my_documents()` — all documents uploaded via this MCP server
- `register_document(admin_url)` — import an admin URL from elsewhere
- `read_document(document_id, output_path?)` — fetch content; pass `output_path` for documents over 10KB

### Versions
- `get_versions(document_id)` — see edit history

## Caveats

- Documents expire after 90 days
- Anyone with a share link can access at the link's permission tier — don't paste sensitive content
- Free service with no accounts; not a Google Docs replacement
