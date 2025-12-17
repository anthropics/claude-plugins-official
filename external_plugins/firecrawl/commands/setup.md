---
description: Set up Firecrawl API key and verify configuration
allowed-tools: firecrawl_scrape, Read
---

# Firecrawl Setup

Help the user configure their Firecrawl API key.

**IMPORTANT: Only use `firecrawl_scrape` and `Read` tools. Do NOT use any other MCP tools like PostHog, docs-search, etc.**

## Steps:

1. **Check if Firecrawl is working** by calling the `firecrawl_scrape` tool directly on https://firecrawl.dev with formats: ["summary"]

2. **If it fails or the tool isn't available**, detect where the plugin is installed and guide the user:

   Use the Read tool to check these files for `"firecrawl@"` in `enabledPlugins`:
   - `~/.claude/settings.json` (user/global scope)
   - `.claude/settings.json` (project scope)
   - `.claude/settings.local.json` (local scope)

3. **Guide the user based on what you found:**

   If you found the settings file with the plugin enabled, tell them:

   "To use Firecrawl, add your API key to `[THE FILE YOU FOUND]`:

   ```json
   {
     "env": {
       "FIRECRAWL_API_KEY": "fc-YOUR-API-KEY"
     }
   }
   ```

   If the file already has other settings, just add the `env` section (or add `FIRECRAWL_API_KEY` to existing `env`).

   **Get your API key at:** https://firecrawl.dev/app/api-keys

   **After adding the API key, you MUST restart Claude Code** to load the Firecrawl MCP server, then run `/firecrawl:setup` again to verify."

4. **If you can't find the plugin in any settings file:**

   "Could not detect where Firecrawl is installed.

   First, install the plugin, then restart Claude Code:
   ```
   /plugin install firecrawl@<marketplace>
   ```

   Then add your API key to one of these files:
   - `~/.claude/settings.json` - Global (all projects)
   - `.claude/settings.json` - Project (shared with team)
   - `.claude/settings.local.json` - Local (gitignored, personal)

   **Important:** After installing the plugin OR adding the API key, you must restart Claude Code."

5. **If it works**, confirm:
   "Firecrawl is configured correctly! You can now use:
   - `/firecrawl:scrape` - Scrape a single page
   - `/firecrawl:crawl` - Crawl an entire website
   - `/firecrawl:search` - Search the web
   - `/firecrawl:map` - Discover URLs on a site"
