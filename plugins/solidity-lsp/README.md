# solidity-lsp

Solidity language server for Claude Code, providing code intelligence, diagnostics, and analysis for smart contract development.

## Supported Extensions
`.sol`

## Installation

### Via npm (recommended)
```bash
npm install -g @nomicfoundation/solidity-language-server
```

Ensure your npm global bin directory is on your PATH:
- **macOS/Linux**: `export PATH="$(npm bin -g):$PATH"`
- **Windows**: `%APPDATA%\npm` is usually added automatically

## Requirements
- Node.js 16.0 or later
- npm 7.0 or later

## Features
- Real-time diagnostics and error highlighting
- Go-to-definition for contracts, functions, and state variables
- Hover documentation
- Code completion (triggered by `.`, `/`, `"`, `'`)
- Find all references across `.sol` files
- Rename symbol
- Document formatting
- Semantic syntax highlighting
- Signature help for function calls

## More Information
- [Nomic Foundation Hardhat VSCode](https://github.com/NomicFoundation/hardhat-vscode)
- [Solidity Documentation](https://docs.soliditylang.org/)
- [Foundry Book](https://book.getfoundry.sh/)
