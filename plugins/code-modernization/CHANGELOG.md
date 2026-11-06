# Changelog

Each release gets a new number in `.claude-plugin/plugin.json`; Claude Code only offers an update when that number changes.

## 1.0.0

- **A front door.** `/code-modernization:modernize` asks what you want done (once), records it in `analysis/<system>/INTENT.md`, shows the road and gives the exact first command. `--source <path>` links the code so nothing has to be copied.
- **Same-stack version moves.** `modernize-uplift` catalogs what changes between two versions of the same technology, records a measured baseline, migrates one pilot unit and then the rest by playbook.
- **Independent proof.** `modernize-verify` re-runs the tests from clean, re-runs your own canary, tries inputs nobody used and gives each module one verdict, PROVEN, PARTLY PROVEN or NOT PROVEN, computed by a script from files it parses itself.
- **People decide what only they can.** `modernize-review` records a person's verdict on each flagged rule; the plan, the build and the tests read it. A difference the proof finds is accepted once per input by a person, never by the tool.
- **Comparison that fits real output.** Floating-point output can be compared within a declared, justified tolerance; masks and approvals are listed in the result.
- **Proportional rule extraction.** The same rule found in several files is folded into one, and the number of rules follows the size of the code.
- **A one-page report** (`REPORT.html`, works offline) with the proof, the rules, the map and a next step you can copy.
- **A live progress pane** (early access, terminal): the estate map, the rule review deck, the sign-off dialog and the proof at a glance.
- **Usage counts** (whole numbers only, off by switch): which commands run, how far a system gets, what the plugin runs on (operating system, python status, path problems on Windows), and which kinds of failure happen (python missing, blocked by a permission rule, model errors, the plugin's own script errors). Once per version and machine at session start it also says what it runs on. See the Telemetry section of the README.
