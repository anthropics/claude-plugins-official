---
description: Create a custom sspdf theme from brand specs — colors, fonts, and document type
argument-hint: "<brand specs> (e.g. 'navy headers, Helvetica, financial tear sheet')"
---

# Create Theme

> This command uses the sspdf engine (`h17-sspdf` npm package). See the **sspdf-theme-generator** skill for the full property reference.

Create a custom theme file for the sspdf PDF engine from brand specifications.

## Workflow

### 1. Gather Brand Specs

Ask the user for:
- Primary and accent colors
- Font preferences (built-in: helvetica, courier, times — or TTF for custom)
- Document type the theme targets
- Any reference materials or existing brand guidelines

### 2. Read Documentation

```bash
SSPDF_DIR=$(node -e "console.log(require.resolve('h17-sspdf').replace('/index.js',''))")
cat $SSPDF_DIR/DOCUMENTATION.md
```

Read the Theme section for the complete property reference.

### 3. Study Existing Themes

```bash
ls $SSPDF_DIR/examples/themes/
```

Read at least one theme to match conventions.

### 4. Generate Theme

Write a `.js` file exporting a valid theme object with all required labels fully specified. See the **sspdf-theme-generator** skill for the schema, rules, and label property reference.

### 5. Test Render

If the user has a source JSON ready:

```bash
npx h17-sspdf -s <source.json> -t <theme-path> -o output/test.pdf
```
