# jdtls-lsp

Java language server (Eclipse JDT.LS) for Claude Code, providing code intelligence and refactoring.

## Supported Extensions
`.java`

## Installation

### Via Homebrew (macOS)
```bash
brew install jdtls
```

### Via package manager (Linux)
```bash
# Arch Linux (AUR)
yay -S jdtls

# Other distros: manual installation required
```

### Manual Installation
1. Download from [Eclipse JDT.LS releases](https://download.eclipse.org/jdtls/snapshots/)
2. Extract to a directory (e.g., `~/.local/share/jdtls`)
3. Create a wrapper script named `jdtls` in your PATH

## Requirements
- Java 17 or later (JDK, not just JRE)

## More Information
- [Eclipse JDT.LS GitHub](https://github.com/eclipse-jdtls/eclipse.jdt.ls)
- [VSCode Java Extension](https://github.com/redhat-developer/vscode-java) (uses JDT.LS)
