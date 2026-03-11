---
description: Generate a PDF document from a description — invoices, reports, tear sheets, articles, or any printable deliverable
argument-hint: "<what to generate> (e.g. 'quarterly earnings summary for AAPL', 'invoice for $7,250')"
---

# Generate PDF

> This command uses the sspdf engine (`h17-sspdf` npm package) to render PDF documents. No external dependencies beyond Node.js and the canvas native addon.

Generate a publication-ready PDF from a natural language description. Builds the source JSON, selects or creates a theme, and renders the output.

See the **sspdf** skill for the full operation reference and rendering workflow.

## Workflow

### 1. Determine the Document

Ask the user what they need if not already clear from the argument. Identify:
- Document type (report, invoice, tear sheet, article, program, etc.)
- Content to include
- Any brand preferences (colors, fonts)

### 2. Read Documentation

```bash
SSPDF_DIR=$(node -e "console.log(require.resolve('h17-sspdf').replace('/index.js',''))")
cat $SSPDF_DIR/DOCUMENTATION.md
```

### 3. Select or Create Theme

Check built-in themes: `default`, `editorial`, `newsprint`, `corporate`, `ceremony`, `program`, `financial`.

```bash
ls $SSPDF_DIR/examples/themes/
```

If none fits, create a custom theme using the **sspdf-theme-generator** skill.

### 4. Build Source JSON

Construct the source JSON with operations matching the document structure. Every label must exist in the chosen theme.

### 5. Render

```bash
npx h17-sspdf -s <source.json> -t <theme> -o output/<name>.pdf
```

### 6. Verify

Confirm the PDF exists and open it for the user.
