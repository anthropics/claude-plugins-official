# ballerina-lsp

Ballerina language server for Claude Code, providing code intelligence features like go-to-definition, find references, diagnostics, and type information.

## Supported Extensions
`.bal`

## Prerequisites

This plugin requires the Ballerina language distribution to be installed on your machine.

**Minimum Requirements:**
- Ballerina >= 2201.12.0 (Swan Lake Update 12 or later)
- The `bal` command must be available in your system PATH
- Java 21 (bundled with Ballerina distribution)

## Installation

### Install Ballerina

1. Download and install Ballerina from [https://ballerina.io/downloads/](https://ballerina.io/downloads/)
2. Follow the installation instructions for your platform (macOS, Linux, or Windows)
3. Verify the installation:
   ```bash
   bal version
   ```

You should see output similar to:
```
Ballerina 2201.13.1 (Swan Lake Update 13)
Language specification 2024R1
Update Tool 1.5.1
```

**Verify Installation:**
```bash
# Check Ballerina is in PATH
bal version

# Check Ballerina home
bal home
```

## More Information
- [Ballerina Official Website](https://ballerina.io)
- [Ballerina Language Server Repository](https://github.com/ballerina-platform/ballerina-lang)
- [Ballerina Documentation](https://ballerina.io/learn/)
