# Stagehand Browser Automation Plugin

Browser automation skill for Claude Code using [Stagehand](https://github.com/browserbase/stagehand). This plugin enables Claude to automate web browser interactions, extract data, and navigate websites using natural language.

## Installation

Install the plugin from the Claude Code marketplace:

```bash
/plugin install stagehand@claude-plugin-directory
```

## Prerequisites

This plugin requires the browser automation CLI tools to be installed separately. The CLI tools are available from the GitHub marketplace.

### Step 1: Add the GitHub Marketplace

```bash
/plugin marketplace add browserbase/agent-browse
```

### Step 2: Install the Browser Automation CLI Plugin

```bash
/plugin install browser-automation@browser-tools
```

### Step 3: Set Up the CLI Tools

After installing the browser-automation plugin, you need to set up the CLI tools:

1. Navigate to the plugin directory (typically `~/.claude/plugins/browser-automation/`)
2. Install dependencies and build:
   ```bash
   npm install
   ```
3. Link the browser command globally:
   ```bash
   npm link
   ```
4. Configure your Anthropic API key:
   ```bash
   export ANTHROPIC_API_KEY="your-api-key-here"
   ```
   Or use Claude Code's subscription token (recommended if you have Claude Pro/Max):
   ```bash
   claude setup-token
   ```

### Step 4: Verify Installation

Test that the browser command is available:

```bash
browser navigate https://example.com
```

## Usage

Once installed and configured, you can use natural language to automate browser tasks:

- *"Go to Hacker News, get the top post comments, and summarize them"*
- *"QA test http://localhost:3000 and fix any bugs you encounter"*
- *"Extract product information from example.com/products"*

Claude will automatically use the browser automation skill when you ask for web-related tasks.

## Features

- **Natural Language Control**: Describe browser actions in plain English
- **Data Extraction**: Extract structured data from web pages
- **Screenshot Capture**: Take screenshots for visual verification
- **Persistent Sessions**: Browser state persists between commands
- **Chrome Profile Integration**: Uses your Chrome profile for cookies and sessions

## Troubleshooting

### Chrome not found

Install Chrome for your platform:
- **macOS** or **Windows**: https://www.google.com/chrome/
- **Linux**: `sudo apt install google-chrome-stable`

### Browser command not found

Make sure you've run `npm link` in the browser-automation plugin directory after installing it.

### API Key Issues

- If you have Claude Pro/Max, use `claude setup-token` (recommended)
- Otherwise, export `ANTHROPIC_API_KEY` in your terminal
- Or create a `.env` file in the plugin directory with your API key

## Resources

- [Stagehand Documentation](https://github.com/browserbase/stagehand)
- [GitHub Marketplace](https://github.com/browserbase/agent-browse)
- [Claude Code Skills Documentation](https://code.claude.com/docs/en/plugins)

## Support

For issues or questions, please visit the [GitHub repository](https://github.com/browserbase/agent-browse).

