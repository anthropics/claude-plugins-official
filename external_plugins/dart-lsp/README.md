# dart-lsp

Dart/Flutter language server for Claude Code, providing code intelligence features like go-to-definition, find references, hover information, and error checking.

## Supported Extensions

`.dart`

## Installation

The Dart language server is included with the Dart SDK. Ensure you have Dart or Flutter installed:

### Dart SDK

```bash
# macOS (Homebrew)
brew tap dart-lang/dart
brew install dart

# Windows (Chocolatey)
choco install dart-sdk

# Linux (apt)
sudo apt-get install dart
```

### Flutter SDK (includes Dart)

```bash
# macOS (Homebrew)
brew install flutter

# Or download from https://flutter.dev/docs/get-started/install
```

## Verification

Verify the language server is available:

```bash
dart language-server --help
```

## More Information

- [Dart SDK](https://dart.dev/get-dart)
- [Flutter SDK](https://flutter.dev/docs/get-started/install)
- [Dart Language Server Protocol](https://github.com/dart-lang/sdk/tree/main/pkg/analysis_server)
