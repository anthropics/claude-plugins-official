# sspdf — PDF Generation Plugin

Generate publication-ready PDF documents directly from Claude — financial reports, tear sheets, invoices, articles, and branded deliverables — with deterministic, math-first rendering.

## What This Plugin Does

This plugin gives Claude the ability to produce PDF documents from natural language descriptions. Instead of generating HTML and converting it, or relying on LibreOffice, sspdf renders PDFs directly via jsPDF with precise mathematical layout. The output is deterministic: same input, same PDF, every time.

The engine separates content from styling completely. A **source** JSON describes what to render (text, tables, charts, dividers, blocks). A **theme** JS file controls how it looks (fonts, colors, spacing, page geometry). Claude builds both from a description and renders the final PDF.

## Skills

| Skill | What It Does |
|-------|-------------|
| `sspdf` | Builds source JSON and renders PDF documents. Knows all operation types (text, tables, charts, rows, bullets, blocks, quotes, dividers) and the complete rendering pipeline. |
| `sspdf-theme-generator` | Creates custom theme files from brand specs. Knows the full label property schema — page config, text styling, spacing, containers, table formatting, dividers. |

## Commands

| Command | Description |
|---------|-------------|
| `/generate-pdf` | Generate a PDF from a natural language description |
| `/create-theme` | Create a custom theme from brand specifications |

## What It Can Render

- **Text** — wrapped paragraphs, headings, captions with full font/style control
- **Tables** — column alignment, alternating row shading, borders, header repetition on page breaks
- **Charts** — bar, line, pie, stacked bar, grouped bar — rendered as embedded images via canvas
- **Rows** — left/right aligned pairs (ideal for invoice line items, key-value data)
- **Blocks** — grouped content with background, border, and keep-together pagination
- **Quotes** — blockquotes with optional attribution
- **Bullets** — custom markers with wrapped text
- **Page templates** — repeating headers and footers with `{{page}}` token
- **Hidden text** — invisible text layer for ATS keyword injection

Built-in themes: `default`, `editorial`, `newsprint`, `corporate`, `ceremony`, `program`, `financial`.

## Installation

```bash
npm install h17-sspdf
```

Requires Node.js and the `canvas` native addon (automatically installed as a dependency).

## Quick Start

```bash
# CLI
npx h17-sspdf -s source.json -t financial -o output/report.pdf

# Programmatic
const { renderDocument } = require("h17-sspdf");
renderDocument({ source, theme, outputPath: "output/report.pdf" });
```

## Why sspdf

- **No LibreOffice** — Renders PDFs directly via jsPDF. No headless browsers, no OS-level dependencies beyond Node.js.
- **Deterministic** — Math-first layout engine. Same input produces identical output on any machine.
- **Charts and tables out of the box** — Native table operation with page-break header repetition. Chart plugin renders bar, line, pie charts as embedded images.
- **Content/style separation** — Source JSON never contains colors, fonts, or sizes. The theme controls all visual decisions. Swap themes without touching content.
- **Pagination built in** — Automatic page breaks, keep-together blocks, orphan prevention, header/footer templates.

## Requirements

- Node.js 18+
- npm (for h17-sspdf package installation)

## License

[Apache License 2.0](../../LICENSE)
