# centralhardware-plugins

Personal fork of [`anthropics/claude-plugins-official`](https://github.com/anthropics/claude-plugins-official),
pruned to the one plugin this marketplace actually serves: the **telegram**
channel plugin in `external_plugins/telegram`, carrying the local patches
listed in [`PATCHES.md`](PATCHES.md).

Everything else from upstream — the other marketplace entries, `/plugins`, and
the upstream CI workflows — has been removed, and
`.claude-plugin/marketplace.json` lists telegram only.

## Installation

```sh
claude plugin marketplace add centralhardware/claude-plugins-official
claude plugin install telegram@centralhardware-plugins
```

## Updating

```sh
claude plugin marketplace update centralhardware-plugins
claude plugin update telegram@centralhardware-plugins
```

See `PATCHES.md` for the upstream-sync flow.

## License

See [`LICENSE`](LICENSE) and the plugin's own `external_plugins/telegram/LICENSE`.
