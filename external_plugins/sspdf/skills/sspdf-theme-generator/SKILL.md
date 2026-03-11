---
name: sspdf-theme-generator
description: Generate custom sspdf theme files from brand specs — colors, fonts, and document type. Use when asked to create a theme, style a document, or design a PDF layout for sspdf.
---

# sspdf Theme Generator

Generate theme files for the sspdf PDF engine. A theme is a JS object that controls every visual decision in a document — page geometry, baseline state, and label styles. Themes produced here work on first render.

## Setup

Verify h17-sspdf is installed:

```bash
npx h17-sspdf --help
```

If this fails, install it:

```bash
npm install h17-sspdf
```

## How It Works

The sspdf engine takes two inputs: a theme (styling rules) and a source (content). The theme controls page geometry, baseline state, and label styles. The source references labels by name. If a label is missing, the engine throws.

Resolve the package location:

```bash
SSPDF_DIR=$(node -e "console.log(require.resolve('h17-sspdf').replace('/index.js',''))")
```

## Required Reading

Before generating a theme, always read the documentation:

```bash
cat $SSPDF_DIR/DOCUMENTATION.md
```

Read the full Theme section (page config, labels, customFonts, layout). This is your source of truth for every property name, type, and constraint.

Also check existing themes for patterns:

```bash
ls $SSPDF_DIR/examples/themes/
```

Read at least one existing theme to match the project's conventions.

## Theme Structure

```js
module.exports = {
  name: "Theme Name",

  page: {
    format: "a4",            // only a4
    orientation: "portrait",  // or "landscape"
    unit: "mm",              // only mm
    compress: true,

    // margins
    marginTopMm: 20,
    marginBottomMm: 20,
    marginLeftMm: 18,
    marginRightMm: 18,

    // background
    backgroundColor: [255, 255, 255],

    // baseline text state (required, every property)
    defaultText: {
      fontFamily: "helvetica",
      fontStyle: "normal",
      fontSize: 10,
      color: [0, 0, 0],
      lineHeight: 1.2,
    },

    // baseline stroke state (required)
    defaultStroke: {
      color: [0, 0, 0],
      lineWidth: 0.2,
      lineCap: "butt",
      lineJoin: "miter",
    },

    // baseline fill (required)
    defaultFillColor: [255, 255, 255],
  },

  labels: {
    // every label the source JSON will reference
  },
};
```

## Rules

1. Every label is self-contained. No inheritance between labels. If a label needs `fontFamily`, write `fontFamily`.
2. Colors are always `[R, G, B]` arrays, 0-255.
3. Only `"a4"` format and `"mm"` units are supported. The engine throws on anything else.
4. The `page` section must include `defaultText`, `defaultStroke`, and `defaultFillColor`, all fully specified. These reset after every operation to prevent style leaks.
5. Label names are arbitrary strings. Use a dot-namespace convention: `invoice.title`, `report.body`, `news.headline`.
6. Built-in font families: `helvetica`, `courier`, `times`. For anything else, embed TTF via `customFonts`.
7. Table labels need `cellPaddingMm`, border properties, and optionally `altRowColor`. Use the shared constants pattern from existing theme files if the document includes tables.
8. Do not hardcode positions or sizes in labels that belong in the source JSON.

## Label Property Quick Reference

**Text labels:** `fontFamily`, `fontStyle`, `fontSize`, `color`, `lineHeight`, `lineHeightMm`, `align`, `textTransform`

**Spacing:** `marginTopMm`, `marginTopPx`, `marginBottomMm`, `marginBottomPx`

**Padding:** `paddingMm`, `paddingPx`, `paddingTopMm`, `paddingBottomMm`, `paddingLeftMm`, `paddingRightMm` (and Px variants)

**Container:** `backgroundColor`, `borderWidthMm`, `borderColor`, `borderRadiusMm`

**Left border accent:** `leftBorder: { color, widthMm, gapMm, heightMm, topOffsetMm }`

**Divider labels:** `color`, `lineWidth`, `opacity`, `dashPattern`, spacing props

**Bullet marker:** `fontFamily`, `fontStyle`, `fontSize`, `color`, `lineHeight`, `marker`

**Spacer labels:** `spaceMm`, `spacePx`

**Table cell labels:** `fontFamily`, `fontStyle`, `fontSize`, `color`, `lineHeight`, `cellPaddingMm`, `backgroundColor`, `altRowColor`, `borderColor`, `borderTopMm`, `borderBottomMm`, `borderLeftMm`, `borderRightMm`, per-edge color overrides

## Workflow

1. Read `DOCUMENTATION.md` for the full property reference.
2. Read at least one existing theme in `examples/themes/` for conventions.
3. Ask the user what document type they need (or infer from context).
4. Identify every visual element the document will have. Each one needs a label.
5. Generate the theme file with all labels fully specified.
6. If the document uses tables, read an existing theme with tables and use the shared constants pattern.
7. Write the file to the specified path.

## Verification

If the user has a source JSON ready, render it:

```bash
npx h17-sspdf -s <source.json> -t <theme-path> -o output/test.pdf
```
