# Data Explorer Template

Use this template when the playground is about data queries, APIs, pipelines, or structured configuration: SQL builders, API designers, regex builders, pipeline visuals, cron schedules.

## Layout

```
+-------------------+----------------------+
|                   |                      |
|  Controls         |  Formatted output    |
|  grouped by:      |  (syntax-highlighted |
|  • Source/tables  |   code, or a         |
|  • Columns/fields |   visual diagram)    |
|  • Filters        |                      |
|  • Grouping       |                      |
|  • Ordering       |                      |
|  • Limits         |                      |
|                   +----------------------+
|                   |  Prompt output       |
|                   |  [ Copy Prompt ]     |
+-------------------+----------------------+
```

## Control types by decision

| Decision | Control | Example |
|---|---|---|
| Select from available items | Clickable cards/chips | table names, columns, HTTP methods |
| Add filter/condition rows | Add button → row of dropdowns + input | WHERE column op value |
| Join type or aggregation | Dropdown per row | INNER/LEFT/RIGHT, COUNT/SUM/AVG |
| Limit/offset | Slider | result count 1–500 |
| Ordering | Dropdown + ASC/DESC toggle | order by column |
| On/off features | Toggle | show descriptions, include header |

## Preview rendering

Render syntax-highlighted output using `<span>` tags with color classes:

```javascript
function renderPreview() {
  const el = document.getElementById('preview');
  // Color-code by token type
  el.innerHTML = sql
    .replace(/\b(SELECT|FROM|WHERE|JOIN|ON|GROUP BY|ORDER BY|LIMIT)\b/g, '<span class="kw">$1</span>')
    .replace(/\b(users|orders|products)\b/g, '<span class="tbl">$1</span>')
    .replace(/'[^']*'/g, '<span class="str">$&</span>');
}
```

For pipeline-style playgrounds, render a horizontal or vertical flow diagram using positioned divs with arrow connectors.

## Prompt output for data

Frame it as a specification of what to build, not the raw query itself:

> "Write a SQL query that joins orders to users on user_id, filters for orders after 2024-01-01 with total > $50, groups by user, and returns the top 10 users by order count."

Include the schema context (table names, column types) so the prompt is self-contained.

## Example topics

- SQL query builder (tables, joins, filters, group by, order by, limit)
- API endpoint designer (routes, methods, request/response field builder)
- Data transformation pipeline (source → filter → map → aggregate → output)
- Regex builder (sample strings, match groups, live highlight)
- Cron schedule builder (visual timeline, interval, day toggles)
- GraphQL query builder (type selection, field picker, nested resolvers)
