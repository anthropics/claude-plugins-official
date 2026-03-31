# claude-hwp-plugin

> Control Korean HWP/HWPX documents with natural language in Claude Code.

## Overview

A Claude Code plugin that lets you read, fill forms, create, compare, and batch-process
Korean HWP/HWPX documents using natural language commands.
Built on the [kordoc](https://github.com/chrisryugj/kordoc) library via MCP Server.

## Features

| Tool | Description |
|------|-------------|
| hwp_parse | Read HWP/HWPX/PDF → Markdown |
| hwp_detect_format | Detect file format via magic bytes |
| hwp_extract_form | Extract form fields from templates |
| hwp_fill_form | Fill form templates with data |
| hwp_batch_fill | Batch fill (up to 500 records) |
| hwp_create | Create new HWPX from Markdown |
| hwp_compare | Compare two documents (diff) |
| hwp_metadata | Extract metadata quickly |

## Installation

### Requirements
- Node.js >= 18

### Install via Claude Code


### Manual setup (for development)

added 274 packages, and audited 275 packages in 21s

68 packages are looking for funding
  run `npm fund` for details

6 moderate severity vulnerabilities

To address all issues (including breaking changes), run:
  npm audit fix --force

Run `npm audit` for details.

> claude-hwp-plugin-mcp@0.1.0 build
> tsc

## Repository

https://github.com/hyunmin625/claude-hwp-plugin

## License

MIT
