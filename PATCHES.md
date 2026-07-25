# Local patches

Personal fork of `anthropics/claude-plugins-official`. Everything here is
upstream except the commits below and the marketplace rename.

| Commit subject | What it does |
| --- | --- |
| `marketplace: rename to centralhardware-plugins` | lets this fork be added alongside the upstream marketplace without an id collision |
| `telegram: surface quote-reply context in inbound channel meta` | adds `reply_to_message_id` / `reply_to_user` / `reply_to_text` to the `<channel>` tag so the model knows which message a quote-reply answers |
| `telegram: keep "typing…" alive until the turn ends` | re-sends `sendChatAction` on an interval (upstream sends it once, so it expires after ~5s), stopping on `reply()`, a 10-minute cap, or the `$CLAUDE_CONFIG_DIR/telegram-turn-done` sentinel written by the local `/clr` and mail quick-action hooks |

## Syncing with upstream

```sh
git fetch upstream
git rebase upstream/main      # or: git merge upstream/main
git push --force-with-lease origin main   # only needed after a rebase
claude plugin marketplace update centralhardware-plugins
claude plugin update telegram@centralhardware-plugins
```

Conflicts should be limited to `external_plugins/telegram/server.ts` and the
`name`/`description` lines at the top of `.claude-plugin/marketplace.json`.
