# Marketplace Configuration Reference

This document covers the `marketplace.json` file used for registering plugins in Claude Code marketplaces.

## Overview

A marketplace is a collection of plugins that can be installed together. The `marketplace.json` file defines the marketplace metadata and lists all plugins it contains.

**Location**: `.claude-plugin/marketplace.json`

## Schema

```json
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "name": "marketplace-name",
  "description": "Brief description of the marketplace",
  "owner": {
    "name": "Owner Name",
    "email": "owner@example.com"
  },
  "plugins": [
    {
      "name": "plugin-name",
      "description": "Plugin description",
      "version": "1.0.0",
      "author": {
        "name": "Author Name",
        "email": "author@example.com"
      },
      "source": "./",
      "category": "productivity"
    }
  ]
}
```

## Required Fields

### Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique marketplace identifier (kebab-case) |
| `owner` | object | Yes | Marketplace owner information |
| `plugins` | array | Yes | List of plugins in this marketplace |

### Owner Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Owner's display name |
| `email` | string | Yes | Owner's contact email |

### Plugin Entry Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Plugin identifier (kebab-case) |
| `source` | string | Yes | Relative path to plugin directory |
| `description` | string | No | Brief plugin description |
| `version` | string | No | Semantic version (e.g., "1.0.0") |
| `author` | object | No | Plugin author information |
| `category` | string | No | Plugin category for organization |

## Source Path Format

**Critical**: The `source` field must follow specific formatting rules.

### Valid Formats

```json
// Single plugin at marketplace root
"source": "./"

// Plugin in subdirectory
"source": "./plugins/my-plugin"

// Nested path
"source": "./category/subcategory/plugin"
```

### Invalid Formats

```json
// Missing trailing slash for root
"source": "."  // INVALID - will cause schema error

// Absolute path
"source": "/Users/name/plugins/my-plugin"  // INVALID

// Missing leading ./
"source": "plugins/my-plugin"  // INVALID
```

### Common Error

**Error**: `Invalid schema: plugins.0.source: Invalid input`

**Cause**: Using `"source": "."` instead of `"source": "./"`

**Fix**: Always include the trailing slash for root-level plugins:
```json
// Wrong
"source": "."

// Correct
"source": "./"
```

## Optional Fields

### Top-Level Optional Fields

```json
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "description": "Marketplace description for discovery",
  "metadata": {
    "description": "Additional metadata",
    "version": "1.0.0"
  }
}
```

### Plugin Optional Fields

```json
{
  "license": "MIT",
  "category": "development",
  "keywords": ["testing", "automation"],
  "strict": false
}
```

**Categories**: `development`, `productivity`, `documentation`, `testing`, `integration`, `utilities`

## Examples

### Single Plugin Marketplace (Local Development)

For a single plugin developed locally:

```json
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "name": "my-plugin-local",
  "description": "Local marketplace for my plugin",
  "owner": {
    "name": "Developer Name",
    "email": "dev@example.com"
  },
  "plugins": [
    {
      "name": "my-plugin",
      "description": "What my plugin does",
      "version": "1.0.0",
      "author": {
        "name": "Developer Name",
        "email": "dev@example.com"
      },
      "source": "./",
      "category": "productivity"
    }
  ]
}
```

### Multi-Plugin Marketplace

For a marketplace containing multiple plugins:

```json
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "name": "company-plugins",
  "description": "Internal company plugins collection",
  "owner": {
    "name": "Company Name",
    "email": "plugins@company.com"
  },
  "plugins": [
    {
      "name": "code-review",
      "description": "Automated code review tools",
      "version": "2.0.0",
      "source": "./plugins/code-review",
      "category": "development"
    },
    {
      "name": "deployment",
      "description": "Deployment automation",
      "version": "1.5.0",
      "source": "./plugins/deployment",
      "category": "integration"
    }
  ]
}
```

## Registration in Claude Code

### Method 1: settings.json (extraKnownMarketplaces)

Add to `~/.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "my-marketplace-local": {
      "source": {
        "source": "directory",
        "path": "/path/to/marketplace"
      }
    }
  },
  "enabledPlugins": {
    "plugin-name@my-marketplace-local": true
  }
}
```

### Method 2: known_marketplaces.json

The system maintains `~/.claude/plugins/known_marketplaces.json` for installed marketplaces:

```json
{
  "my-marketplace-local": {
    "source": {
      "source": "directory",
      "path": "/path/to/marketplace"
    },
    "installLocation": "/path/to/marketplace",
    "lastUpdated": "2025-01-27T00:00:00.000Z"
  }
}
```

## Troubleshooting

### "Invalid schema: owner: Invalid input"

**Cause**: Missing `owner` field or incorrect format

**Fix**: Ensure owner object has both `name` and `email`:
```json
"owner": {
  "name": "Your Name",
  "email": "your@email.com"
}
```

### "Invalid schema: plugins.0.source: Invalid input"

**Cause**: Invalid source path format

**Fix**: Use `"./"` for root-level plugins, not `"."`

### Plugin not appearing after registration

**Checklist**:
1. Verify marketplace.json is in `.claude-plugin/` directory
2. Check plugin.json exists and has valid `name` field
3. Confirm `source` path points to correct location
4. Restart Claude Code after changes
5. Run `claude --debug` to see loading errors

### Marketplace loading errors

Run Claude Code with debug flag to see detailed errors:
```bash
claude --debug
```

Look for lines containing "Failed to load marketplace" for specific error messages.

## Best Practices

1. **Always include $schema**: Enables IDE validation and autocomplete
2. **Use descriptive names**: Make marketplace and plugin names clear
3. **Include contact info**: Both owner and author emails help with support
4. **Version consistently**: Follow semantic versioning for plugins
5. **Test locally first**: Verify marketplace loads before sharing
6. **Document dependencies**: Note any required tools or configurations
