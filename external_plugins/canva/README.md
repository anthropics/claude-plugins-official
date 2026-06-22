# Canva

[Canva](https://www.canva.com) is an online design and communication platform. This plugin connects Claude Code to your Canva account via the Canva MCP server, letting you create, edit, and manage Canva designs directly from your terminal.

## Features

- **Generate designs** — Create AI-powered presentations, social media posts, flyers, docs, whiteboards, and more
- **Edit designs** — Update text, colors, images, and layouts in existing designs
- **Resize for social media** — Automatically resize a design into all major social media formats (Facebook, Instagram, LinkedIn) and export as PNG
- **Implement feedback** — Apply comment-based feedback to designs programmatically
- **Brand check** — Verify designs conform to your brand kit guidelines
- **Bulk create** — Generate multiple design variants from a data set
- **Export** — Export designs as PNG, PDF, or other formats with direct download links

## Setup

### 1. Connect your Canva account

When you first use this plugin, Claude Code will prompt you to authenticate with Canva. Follow the OAuth flow to grant access.

### 2. Install the plugin

```
/plugin install canva@claude-plugins-official
```

## Available Skills

| Skill | Slash command | Description |
|-------|--------------|-------------|
| Resize for Social Media | `/canva:resize-for-social-media` | Resize a design for all social platforms and export PNGs |
| Edit Design | `/canva:edit-design` | Make targeted edits to an existing design |
| Implement Feedback | `/canva:implement-feedback` | Apply review comments to a design |
| Get Design Feedback | `/canva:get-design-feedback` | Analyze a design and surface improvement suggestions |
| Brand Check | `/canva:brand-check` | Check a design against your brand kit |
| Bulk Create | `/canva:bulk-create` | Generate multiple design variants from a data set |

## Example Usage

Ask Claude Code to:
- "Create a 5-slide presentation about our Q3 roadmap"
- "Resize my latest design for all social media platforms"
- "Apply the feedback comments on design DAXM81pHA-w"
- "Check if this design follows our brand guidelines"
- "Generate 10 variants of this flyer using names from this CSV"

## Documentation

- [Canva Developer Platform](https://www.canva.dev)
- [Canva MCP documentation](https://www.canva.dev/docs/mcp)
