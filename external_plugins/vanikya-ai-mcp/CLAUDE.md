# Vanikya AI MCP

The Vanikya MCP server provides AI-powered tools for image generation, SEO analysis, creative insights, and credits management. It is available at `https://prod.vanikya.com/mcp` when the user has connected it.

## Available Skills

Use the appropriate skill when the user's request matches:

- **vanikya-setup** — user wants to connect, configure, or troubleshoot the Vanikya MCP connection
- **imagine** — user wants to generate images, videos, vectors (SVG), or lottie animations; edit images; enhance prompts; browse generations or assets
- **seo-analysis** — user wants to analyze SEO of a URL or run batch SEO audits
- **creative-insights** — user wants creative/visual analysis of images, branding feedback, or batch analysis of multiple images
- **credits** — user asks about their credit balance, available packages, or wants to buy credits

Before using any Vanikya tool, confirm the user is connected (`claude mcp list` should show `vanikya`). If not, use the vanikya-setup skill first.

> Most Vanikya tools consume credits. If the user seems surprised by credit usage, use the credits skill to check their balance.
