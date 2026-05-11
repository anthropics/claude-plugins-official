# Dashboard Template

*Referenced by the Dashboard offer guardrail. Keep dashboards simple and consistent — the value is speed of comprehension, not visual polish.*

## Structure (top to bottom)

1. **Title and metadata.** What this is, when it was generated, what it covers. One line.
2. **Summary stats.** The counts that matter, color-coded. "40 findings: 🔴 3 blocking · 🟠 8 high · 🟡 15 medium · 🟢 14 low — 6 due this week." This is the most valuable line. Make it scannable.
3. **The reviewer note.** Same one-block format as any output. Sources, scope, flags, before-relying. Dashboards don't skip the safety metadata.
4. **Chart(s).** One or two max. Pick the one that shows the shape:
   - **Risk distribution** (bar): counts by severity. Use for findings, issues, flags.
   - **Category breakdown** (pie or stacked bar): counts by type. Use for OSS licenses, contract types, matter categories.
   - **Timeline** (Gantt-lite or sorted table): dates in order. Use for renewal registers, deadline trackers, closing checklists.
   - Never more than two. A dashboard with five charts is a report, and reports are harder to read than the table.
5. **The table.** Sortable, filterable, color-coded by severity/status. Columns: the ones that were in the original output, trimmed to what fits on a screen. Put a "details" or "notes" column last — it's the one that gets truncated.
6. **The decision tree.** Same options as the text output. "What next?"

## Rendering by surface

- **Cowork / Claude Desktop:** HTML artifact. Self-contained, single file, inline CSS. No external dependencies, no CDN, no npm. Tables: HTML `<table>` with `data-sort` attributes and a small inline JS sorter. Charts: inline SVG or Unicode block chars for bar charts. Keep the JS minimal — sorting and filtering, nothing else.
- **Claude Code:** Write the same HTML file to the plugin's outputs folder (`~/.claude/plugins/config/claude-for-legal/<plugin>/outputs/dashboard-<topic>-<date>.html`) and tell the user to open it: `open <path>` on macOS, or "open in your browser." Also produce a markdown version with Unicode block charts for the summary stats so the user can see the shape without leaving the terminal.
- **Excel (optional, where it fits):** For `tabular-review`, `renewal-tracker`, `entity-compliance`, and anything the user will take into a meeting or share with a non-technical stakeholder. Use the existing Excel output spec. Apply the formula-injection defense.
- **Escape untrusted input (apply every dashboard, every time).** Every value that came from outside this session — OSS package/license fields from third-party manifests, counterparty contract text, diligence findings, vendor names, matter descriptions, any user- or VDR-supplied string — must be HTML-escaped before it lands in the document. Escape `&`, `<`, `>`, `"`, `'` into entities when writing into table cells, summary lines, chart labels, and tooltip text. In the inline JS sorter/filter, set cell text via `textContent`, never `innerHTML`. Do not emit `<script>` blocks whose contents interpolate untrusted strings. Do not render untrusted URLs into `href` or `src` without scheme-checking (`http:` / `https:` / `mailto:` only). This is the HTML-surface equivalent of the formula-injection defense on the Excel side — same threat (attacker-controlled cell content), different execution surface (browser JS instead of spreadsheet formula). A dashboard the reviewer opens in a browser is a trust boundary; treat it like one.

## Keep it boring

- **Color palette:** Red / orange / yellow / green for severity. Gray for neutral. Blue for status. Nothing else.
- **No animations, no frameworks, no external fonts.** A dashboard that breaks offline is a dashboard that breaks.
- **No clever layouts.** Summary, reviewer note, chart, table, decision tree. Top to bottom. Every dashboard looks the same so the reader knows where to look.
- **The markdown version matters.** Some users are in a terminal and won't open a browser. The summary stat line with Unicode bars (e.g., `🔴 ███ 3  🟠 ████████ 8  🟡 ███████████████ 15  🟢 ██████████████ 14`) gives them the shape.
