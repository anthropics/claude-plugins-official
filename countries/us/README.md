# United States Country Plugin (`countries-us`)

This is the **retroactively-extracted** package that proves the country
architecture reconstructs today's default behavior. It is not a new product —
it is `employment-legal`'s existing US content, moved into the Provider/
Registry system so the same vertical can also serve `countries-tr` (and, in
future, `countries-de`, `countries-fr`, `countries-uk`, `countries-ae`,
`countries-sa`) without a rewrite.

## Install

```
/plugin install countries-us@claude-for-legal
/plugin install employment-legal@claude-for-legal
```

**Not required for existing users.** `employment-legal`'s skills carry an
embedded US-default fallback (see the `<details>` blocks in
`wage-hour-qa/SKILL.md` and the equivalent in `worker-classification`,
`termination-review`, `leave-tracker.md`) that activates automatically when
no country plugin is installed or active. Installing `countries-us`
explicitly is only useful once multiple country plugins are installed side
by side and you want the active-country pointer to be explicit rather than
implicit.

## What this package provides

See `capabilities.yaml` — `employment-legal` coverage is `full` across all
three Providers, backed by real, already-operational MCP servers
(CourtListener, Trellis, Federal Register API, DocuSign, iManage — see
`mcp/mcp-tool-registry.us.yaml`).

## Reference implementation

New country plugins (starting with `countries/tr`) are modeled on this
package's structure. If you're building a new country plugin, read this
one first.
