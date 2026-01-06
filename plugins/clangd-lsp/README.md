# clangd-lsp

C/C++ language server (clangd) for Claude Code, providing code intelligence, diagnostics, and formatting.

## Supported Extensions
`.c`, `.h`, `.cpp`, `.cc`, `.cxx`, `.hpp`, `.hxx`, `.C`, `.H`

## Installation

### Via Homebrew (macOS)
```bash
brew install llvm
# Add to PATH: export PATH="/opt/homebrew/opt/llvm/bin:$PATH"
```

### Via package manager (Linux)
```bash
# Ubuntu/Debian
sudo apt install clangd

# Fedora
sudo dnf install clang-tools-extra

# Arch Linux
sudo pacman -S clang
```

### Windows
Download from [LLVM releases](https://github.com/llvm/llvm-project/releases) or install via:
```bash
winget install LLVM.LLVM
```

## More Information
- [clangd Website](https://clangd.llvm.org/)
- [Getting Started Guide](https://clangd.llvm.org/installation)
