# purescript-lsp

PureScript language server for Claude Code, providing type checking, diagnostics, go-to-definition, find references, and code intelligence for `.purs` files.

## Supported Extensions

`.purs`

## Installation

Install the PureScript language server globally via npm:

```bash
npm install -g purescript-language-server
```

The language server also requires the PureScript compiler and spago:

```bash
npm install -g purescript spago
```

## Requirements

- A PureScript project with `spago.yaml` (or `spago.dhall`)
- Run `spago build` at least once to generate the `output/` directory, which the language server uses for IDE features
