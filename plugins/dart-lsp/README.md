# dart-lsp

Dart language server for Claude Code, providing code intelligence for Dart and Flutter projects.

## Supported Extensions
`.dart`

## Installation

The Dart language server is included with the Dart SDK. No separate installation is needed.

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

After installation, verify the language server is available:
```bash
dart language-server --help
```

## Version Managers (FVM, Puro)

If you use a version manager like [FVM](https://fvm.app/) or [Puro](https://puro.dev/), set the `DART_EXECUTABLE` environment variable in your Claude Code settings (`~/.claude/settings.json`):

```json
{
  "env": {
    "DART_EXECUTABLE": "/path/to/your/dart"
  }
}
```

Users with a standard Dart or Flutter installation do not need to change anything.

## More Information
- [Dart SDK](https://dart.dev/get-dart)
- [Flutter SDK](https://flutter.dev/docs/get-started/install)
- [Dart Language Server Protocol](https://github.com/dart-lang/sdk/tree/main/pkg/analysis_server)
