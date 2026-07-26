# Local patches

Personal fork of `anthropics/claude-plugins-official`, pruned to the telegram
plugin only. Everything that remains is upstream except the commits below.

| Commit subject | What it does |
| --- | --- |
| `marketplace: rename to centralhardware-plugins` | lets this fork be added alongside the upstream marketplace without an id collision |
| `telegram: surface quote-reply context in inbound channel meta` | adds `reply_to_message_id` / `reply_to_user` / `reply_to_text` to the `<channel>` tag so the model knows which message a quote-reply answers |
| `telegram: register extra bot-menu commands from local config` | feeds `{command, description}` entries from `$CLAUDE_CONFIG_DIR/telegram-commands.json` into `setMyCommands`, so hook-implemented commands (`/clr`, `/clr_status`, `/clear`) show up in the Telegram menu |
| `telegram: drop built-in start/help/status from the bot command menu` | the menu now lists only the local commands above; the upstream `/start`, `/help` and `/status` handlers still respond if typed |
| `telegram: keep "typing…" alive until the turn ends` | re-sends `sendChatAction` on an interval (upstream sends it once, so it expires after ~5s), stopping on `reply()`, a 10-minute cap, or the `$CLAUDE_CONFIG_DIR/telegram-turn-done` sentinel written by the local `/clr` and mail quick-action hooks |

## Syncing with upstream

```sh
git fetch upstream
git rebase upstream/main      # or: git merge upstream/main
git push --force-with-lease origin main   # only needed after a rebase
claude plugin marketplace update centralhardware-plugins
claude plugin update telegram@centralhardware-plugins
```

Conflicts should be limited to `external_plugins/telegram/server.ts` and
`.claude-plugin/marketplace.json`. Because the prune commit deletes every other
plugin and the rest of the catalog, an upstream sync will also surface newly
added upstream plugins as additions — delete them again (`git rm`) and keep the
manifest's `plugins` array at the single telegram entry.
