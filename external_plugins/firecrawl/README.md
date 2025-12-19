# Firecrawl Plugin for Claude Code

Turn any website into clean, LLM-ready markdown or structured data with Firecrawl.

## Features

- **Scrape**: Extract content from any webpage as clean markdown
- **Crawl**: Automatically discover and extract content from entire websites
- **Search**: Search the web and get scraped results
- **Map**: Discover all URLs on a website

All features include automatic JavaScript rendering, anti-bot handling, and proxy rotation.

## Installation

### 1. Install the Plugin

```
/plugin install firecrawl@claude-plugins-official
```

**Important:** After installing, restart Claude Code to load the Firecrawl MCP server.

### 2. Set Up Your API Key

Run `/firecrawl:setup` to configure your API key. It will detect where the plugin is installed and guide you.

Or manually add your API key using one of these methods:

**Option A: Claude Code Settings (Recommended)**

Add to the same settings file where the plugin is enabled:
```json
{
  "env": {
    "FIRECRAWL_API_KEY": "fc-YOUR-API-KEY"
  }
}
```

File locations by scope:
- `~/.claude/settings.json` - Global (all projects)
- `.claude/settings.json` - Project (shared with team)
- `.claude/settings.local.json` - Local (gitignored, personal)

**Option B: Shell Profile**
```bash
# Add to ~/.zshrc or ~/.bashrc
export FIRECRAWL_API_KEY=fc-YOUR-API-KEY
```
Note: Running `export` directly in terminal only lasts for that session. Add it to your profile file for persistence.

**Get your free API key at:** https://firecrawl.dev/app/api-keys

### 3. Verify Setup

Restart Claude Code, then run `/firecrawl:setup` to confirm everything is working.

## Usage

### Slash Commands

| Command | Description |
|---------|-------------|
| `/firecrawl:setup` | Configure API key and verify setup |
| `/firecrawl:scrape` | Scrape a single webpage to markdown |
| `/firecrawl:crawl` | Crawl an entire website |
| `/firecrawl:search` | Search the web and scrape results |
| `/firecrawl:map` | Discover all URLs on a website |

### Available Formats

When scraping, you can request different output formats:
- `markdown` - Clean markdown content (default)
- `html` - Raw HTML content
- `screenshot` - Screenshot of the page
- `links` - Extract all links
- `summary` - AI-generated summary

### Direct Tool Usage

The plugin exposes Firecrawl's MCP tools directly:

- `firecrawl_scrape` - Single page scraping
- `firecrawl_batch_scrape` - Multiple URL scraping
- `firecrawl_crawl` - Website crawling
- `firecrawl_check_crawl_status` - Check crawl progress
- `firecrawl_map` - URL discovery
- `firecrawl_search` - Web search with scraping

### Examples

**Scrape a documentation page:**
```
Scrape https://docs.firecrawl.dev/introduction and summarize the key points
```

**Get a summary of a page:**
```
Scrape https://firecrawl.dev with summary format
```

**Research a topic:**
```
Search for "best practices for React testing" and compile the key recommendations
```

**Crawl a documentation site:**
```
Crawl the entire documentation at https://docs.firecrawl.dev and create a summary
```

**Discover site structure:**
```
Map all URLs on https://firecrawl.dev
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FIRECRAWL_API_KEY` | Yes | Your Firecrawl API key |
| `FIRECRAWL_API_URL` | No | Custom API endpoint (for self-hosted) |
| `FIRECRAWL_RETRY_MAX_ATTEMPTS` | No | Max retry attempts (default: 3) |
| `FIRECRAWL_RETRY_INITIAL_DELAY` | No | Initial retry delay in ms (default: 1000) |
| `FIRECRAWL_CREDIT_WARNING_THRESHOLD` | No | Credit warning threshold (default: 1000) |

## Self-Hosted Deployment

Firecrawl can be self-hosted. Set `FIRECRAWL_API_URL` to point to your instance:

```bash
export FIRECRAWL_API_URL=https://your-firecrawl-instance.com
```

See [Firecrawl documentation](https://docs.firecrawl.dev) for self-hosting instructions.

## Resources

- [Firecrawl Documentation](https://docs.firecrawl.dev)
- [API Reference](https://docs.firecrawl.dev/api-reference)
- [GitHub Repository](https://github.com/mendableai/firecrawl)
- [Get API Key](https://firecrawl.dev)

## License

This plugin is licensed under AGPL-3.0, consistent with Firecrawl's open-source license.

## Support

- [Firecrawl Discord](https://discord.gg/gSmWdAkdwd)
- [GitHub Issues](https://github.com/mendableai/firecrawl/issues)
- Email: hello@firecrawl.dev
