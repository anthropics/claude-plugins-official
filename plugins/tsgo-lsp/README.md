# tsgo-lsp

TypeScript native language server for Claude Code using [tsgo](https://github.com/microsoft/typescript-go) - Microsoft's native Go port of TypeScript.

## Features

- **10x faster** type checking compared to the traditional TypeScript language server
- Full LSP support including go-to-definition, find references, hover, and diagnostics
- Drop-in replacement for typescript-language-server

## Supported File Extensions

| Extension | Language |
|-----------|----------|
| `.ts` | TypeScript |
| `.tsx` | TypeScript React |
| `.js` | JavaScript |
| `.jsx` | JavaScript React |
| `.mts` | TypeScript (ESM) |
| `.cts` | TypeScript (CJS) |
| `.mjs` | JavaScript (ESM) |
| `.cjs` | JavaScript (CJS) |

## Installation

Install the TypeScript native preview package globally:

```bash
npm install -g @typescript/native-preview
```

Or with other package managers:

```bash
# yarn
yarn global add @typescript/native-preview

# pnpm
pnpm add -g @typescript/native-preview

# bun
bun install -g @typescript/native-preview
```

Verify the installation:

```bash
tsgo --version
```

## Requirements

- Node.js 18+ (for npm installation)
- The `tsgo` binary must be available in your PATH

## Resources

- [TypeScript Native Previews Announcement](https://devblogs.microsoft.com/typescript/announcing-typescript-native-previews/)
- [Progress on TypeScript 7 - December 2025](https://devblogs.microsoft.com/typescript/progress-on-typescript-7-december-2025/)
- [@typescript/native-preview on npm](https://www.npmjs.com/package/@typescript/native-preview)

## Notes

This plugin uses the native TypeScript 7 language server which implements the standard LSP protocol (unlike the legacy TSServer protocol). Some behavior may differ slightly from the traditional typescript-language-server.
