# math-proof

Two Claude Code skills for hard, research-level mathematics problems. Each
takes one problem stated in full, keeps everything it writes in a run folder,
switches Claude Code's web tools off for its run, and ends with a
self-contained `proof.md`.

**`/math-proof:solo`**: Claude works the problem itself, in your session, as
one long turn. It is instructed to write its plan and each intermediate result
to a notes file before reasoning further, so that a response cut off at the
output limit loses nothing already written. The lighter of the two; try it
first.

**`/math-proof:siege`** (multi-agent): your session does no mathematics itself;
for hours it runs rounds of sub-agents, each starting fresh. Each round a judge
writes a few self-contained questions, independent workers answer them in
parallel, and the judge keeps a ledger of what is proved, refuted and open.
When a worker's answer contains a complete proof (or disproof) of the goal the
judge set, two more workers check that exact text line by line before the judge
concludes; if the opening rounds do not get there, later rounds send more
workers per round, most of them at the one step the proof still lacks.
`proof.md` has a Status section saying plainly what is and is not proved.
Expect dozens of sub-agent runs, and well over a hundred if all fourteen rounds
run: check `/usage` before you start on a subscription, or cap the spend with
`--max-budget-usd` in the unattended form below on an API key.

![How a siege run unfolds](assets/how-a-run-unfolds.png)

Either way `proof.md` is the model's own account, and any result it cites from
the literature is quoted from memory: read it critically. Full instructions:
[skills/solo/SKILL.md](skills/solo/SKILL.md) and
[skills/siege/SKILL.md](skills/siege/SKILL.md); the sub-agents are defined in
[agents/](agents/).

## Install

```
/plugin install math-proof@claude-plugins-official
```

Needs Claude Code 2.1.280 or later and, for `siege`, Python 3.7 or later on
your PATH as `python3` or `python` (no extra packages). Then add this `"env"`
block once to `~/.claude/settings.json` (or to `.claude/settings.json` in the
directory you run from, to limit it to that directory). The three lines allow
long responses, keep sub-agents in the foreground by turning background tasks
off, and give a silent worker four hours before it is cut off; they affect every
session that reads the file, so remove them when you stop using the plugin.

```json
{
  "env": {
    "CLAUDE_CODE_MAX_OUTPUT_TOKENS": "128000",
    "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1",
    "CLAUDE_ASYNC_AGENT_STALL_TIMEOUT_MS": "14400000"
  }
}
```

## Use

In an empty working directory, one per problem and one run at a time:

```
claude --model claude-opus-5-5 --effort high
> /math-proof:solo <the complete problem statement, or the path of a file holding it>
```

or `/math-proof:siege <…>` likewise. `solo` writes under `./math-proof-solo/`,
`siege` under `./math-proof-run/`; the session says where `proof.md` is when it
finishes. In the default permission mode Claude Code asks you to approve file
writes and the `siege` judge's shell commands (short Python checks and file
copies), so stay within reach or use the unattended form below; other than
that, type nothing while it runs. While `siege` runs, `state.md` in the run
folder shows the current round, and if the judge proves its goal and goes
after a stronger one, the result already proved is copied to `result-so-far.md`.

If a run stops (an error, a closed terminal, a usage limit, Ctrl-C), give the
same `/math-proof:…` line again in the same directory, not a free-form message:
that reloads the skill's instructions and permissions, and the run continues
from its folder with the settings it started with.

Options go before the problem: `DIR=path` picks another run folder, and
`siege` takes settings such as `MAX_ROUNDS=8` (its SKILL.md lists them). To
change a sub-agent's thinking effort, copy its file from [agents/](agents/)
into `~/.claude/agents/`, leave its `name:` line unchanged, and edit the
`effort:` line; your copy takes precedence over the plugin's.

Unattended, with the problem in a file (likewise for `solo`):

```
claude -p "/math-proof:siege problem.md" --model claude-opus-5-5 --effort high \
  --dangerously-skip-permissions
```

With an API key, adding `--max-budget-usd <amount>` to that `-p` command stops
the run once that much has been spent; giving the command again resumes it.

**Caution:** `siege`'s judge runs model-written Python through Claude Code's
shell tool on your machine. Use `--dangerously-skip-permissions` only in a
disposable container or VM, as a non-root user; otherwise approve its commands
by hand.

## License

Apache-2.0; see [LICENSE](LICENSE).
