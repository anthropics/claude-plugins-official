# Live progress pane (early access)

While the commands run, the plugin can draw a live pane beside the transcript, for a system in any language: a map of the
code, the steps done, each module and how far it has come, and the next command to run. It is built on Claude Code's
function hooks, which are early access and off by default. Turn them on with the flag:

```sh
CLAUDE_CODE_ENABLE_FUNCTION_HOOKS=1 claude
```

![About twelve seconds of the pane while the verify command runs on a COBOL system: agents read the code and the tiles they touch light up, then the module's verdict appears and the next step changes](../assets/media/pane-live.gif)

*The agent activity in this recording is scripted for the illustration, so its timing is illustrative. The workspace is a finished run of the plugin on AWS CardDemo, and the verdict it ends on is the one the plugin's proof script wrote for that run.*

Without the flag nothing changes: the commands, agents and workflows behave the same and the pane never loads. Everything
the pane shows is read from the files the commands write under `analysis/<system>/` and `modernized/<system>/`, and from the
legacy code itself. Nothing is guessed by a model, and a fact that is not on disk is shown as missing. The pane has been run
on Claude Code 2.1.280, and its tests run on the engine's own test kit (`claude plugin test .`); the hooks are written against
a feature that may change between releases.

The pictures on this page are the pane's own drawing, taken from finished runs of the plugin on open-source code (AWS CardDemo,
a COBOL credit-card system, and Eclipse Jetty, a Java web server). Where a picture shows something typed or scripted for it,
the line under the picture says so.

## What you see

<picture>
  <source media="(prefers-color-scheme: light)" srcset="../assets/media/pane-rewrite-light.png">
  <img alt="The pane for a COBOL rewrite: the system and its steps, the map of the code with the reviewed module's tile green and marked as proven, the phases of the plan, the built module with its PROVEN chip, the next command, and what needs attention" src="../assets/media/pane-rewrite.png">
</picture>

From the top: the system and the way it is being modernized, the steps done, what the code is made of and how much of it is
done, the map, the phases of the plan, the modules built so far, the **Next** command with its buttons, what needs
attention, and what Claude is doing right now (**Session**).

- **The map.** One tile per module, sized by its lines of code and grouped by business area (or by directory, when no map has
  been made yet). A tile's colour says how far its module has come; the legend under the map names the colours in use.
  A tile lights up for a few seconds when Claude or one of its agents reads it (blue) or writes to it (yellow), so a fan-out
  is something you watch move across the system.
- **Any language.** The pane reads no language of its own. The map comes from `topology.json` once
  `/code-modernization:modernize-map` has run. Until then it is read off the legacy tree: one tile per build module where the
  tree has build files (Maven, Gradle, npm, .NET projects, Go, Cargo, Python packages, Composer and more), one per source
  file for a tree without them, one per directory for a tree too big for that. The header names the languages by their
  share of the code and how many units it found.
- **Any way of working.** The pane follows the way whose files are newest: a **rewrite** (map, rules, brief, transform), a
  same-stack **uplift** (delta catalog, baseline, playbook, working copy) or a **reimagine** (spec, architecture, services).
  Each has its own steps, its own next command and its own words. Set `track` to pin one.

  <picture>
    <source media="(prefers-color-scheme: light)" srcset="../assets/media/pane-uplift-light.png">
    <img alt="The pane for a Java 8 to 17 uplift at the pilot stage: the first module matches its baseline and is green, the others are not migrated" src="../assets/media/pane-uplift.png">
  </picture>

  In an uplift a module is set against the baseline (what the tests did on the old runtime): *matches baseline* means every
  test that passed there still passes and none is missing; *worse than baseline* means more failures than it had. Failures
  the baseline already had are not called worse.
- **Any test runner.** A module's tests come from the reports it left (JUnit XML in the usual places, Visual Studio `.trx`, or
  `.modernize/test-report.json`) and, where a runner leaves none, from a test command run in the module's directory during
  the session (Maven, Gradle, pytest, Jest, dotnet, go, cargo, rspec, phpunit and more).
- **A verdict on every built module.** Once `/code-modernization:modernize-verify` has run, each built module carries one chip
  in the module list and one mark on its tile: `PROVEN`, `PARTLY PROVEN` or `NOT PROVEN`, as
  `analysis/<system>/VERIFICATION.json` says. A module that is built and that nothing has checked reads `not verified yet`;
  one whose notes or test reports changed after its check reads `changed since verified`. The next step is the verify command
  for such a module, before the next module is started. A `NOT PROVEN` or `PARTLY PROVEN` module says its first reason in one
  line. The pane only shows the verdicts: a script computes them, and a verdict that is not exactly one of the three words is
  ignored. An uplift has one verdict, for the whole upgrade.
- **Next.** One command, with the reason it comes next, and a **put in prompt** button that types it into the prompt box for
  you. It never runs it: a person presses Enter. In a workspace nobody has started, the next step is the front door,
  `/code-modernization:modernize <name>`, which asks what you want to do and gives the first step; while the brief is unsigned it is a
  **sign the brief** button.
- **Colours for a light or a dark terminal.** Text is drawn in Claude Code's own theme colours, which follow your theme, and
  the map's tiles are mid-tones that show on either background.

### Hide it, show it

The pane opens by itself under the fullscreen layout, on a terminal at least 144 columns wide, once the workspace has an
`analysis/` directory. The **hide** button at the top closes it. Whenever the pane is not on screen (hidden, or held back
because the terminal is narrower than 144 columns), one row above the prompt says where the workspace stands and holds a
**show pane** button; pressing it seats the pane at any width.

![The one-row bar that stands where a hidden pane was: a summary of where the workspace stands and a show pane button, above the prompt](../assets/media/pane-hidden-bar.png)

*The rules and the prompt mark around the bar are drawn for the picture; the bar is the pane's.*

`/modernize-panel` does the same from the keyboard, and shows the pane for a legacy tree nothing has analysed yet. In a
workspace with nothing to show the pane says so and names the one command to type, `/code-modernization:modernize`. Set
`panel` to `command` to have the pane open only on request, or `off` for no pane and no bar.

## X-ray reads

![The session block after Claude read a legacy file: the read is listed with the number of rules that cite the file, and a count of reads that carried notes from the analysis](../assets/media/pane-xray.png)

*The session activity in this picture is scripted for the illustration.*

When Claude reads a file in the system's code (`legacy/<system>/`, followed through a symlink), what the analysis already
established about that file rides along as context only the model sees: the map's callers, callees and data stores, the
business flows through it, the rules in `BUSINESS_RULES.md` that cite it (narrowed to the lines just read when the read was a
window), any rule a reviewer disputed, and whether it has already been transformed. In an uplift it carries the module's
baseline (what fails on the source runtime is part of the oracle, so it is reproduced, not fixed), where the module stands
in the working copy, and the deltas the catalog cites the file under. The model stops re-deriving what three stages already
worked out, and stops calling code dead that the map knows is reached. A read that misses because a cited path was taken from
the workspace root is told where the file is under the legacy root. The pane lists each such read with a short note.

## A review deck for business rules

![A rule card in the review deck: the rule, its citation, Given / When / Then, the suspected defect, the reviewer's verdict and note, and the keys](../assets/media/pane-review-deck.png)

*The reviewer's note and the verdicts on this card are samples typed for the picture.*

`/modernize-review-pane [flagged|p0|all] [filter]` pages through rule cards in the band above the prompt: the rule, its citation,
Given / When / Then, the suspected defect, the question for an SME, and, once a rule has a verdict, the verdict and the
reviewer's note. From an empty prompt: `1` confirms, `2` marks the rule wrong, `3` sends it to discussion, `4` goes back,
`5` skips, `6` shows the cited legacy lines, `7` takes a verdict back and `0` closes the deck.

Verdicts go to `analysis/<system>/RULE_REVIEWS.json` and a readable `RULE_REVIEWS.md` (`Rule | Verdict | When | Title |
Note`); the agent-written `BUSINESS_RULES.md` is never edited. **The plugin's own command
`/code-modernization:modernize-review <system> [flagged|p0|all]` writes the same two files** for people without the pane: it
asks the same questions in pop-ups and can keep a reviewer's own words as a `note`. The deck shows the note on the card, keeps
it when it records a new verdict, and reads the file again before it writes, so what the command recorded meanwhile is not
lost. A rule marked wrong is not used as a test oracle, and a high-priority rule under discussion stops the build commands
until it is settled; the pane lists both under **Attention**, and later x-ray notes mention them.

## A sign-off dialog

![The sign-off dialog: who approves, whether the approval covers Phase 1 only or the full plan, and the sign and cancel buttons](../assets/media/pane-sign.png)

*The approver's name is a sample typed for the picture.*

`/modernize-sign [name, role]`, or the **sign the brief** button, fills in the brief's approval block: who, when, and whether
it covers Phase 1 or the full plan. It changes nothing else in the file.

## A fleet view

![A fan-out in progress: the map lit where agents are reading, and under Attention the shared failure four agents hit](../assets/media/pane-fleet.png)

*The agent activity in this picture is scripted for the illustration.*

Every agent loop that makes a tool call is counted, including a workflow's agents, which the engine does not list by name.
The pane shows how many are active and done, and what the most recent are doing. When agents fail the same way (paths, numbers
and quoted values folded out, and one cause that words itself differently per command folded together), the pane lists it
with an example of what the failing calls were aimed at. The transcript says so once it is a pattern for a fleet that size
(three agents, or one in twenty), and once more if it spreads fivefold: one cause across agents belongs in the playbook, not
in each agent. A bare exit code or a malformed call is not a cause and is not counted as one.

## Buttons

| Button | What it does |
|---|---|
| **put in prompt** | Puts the step under **Next** in the prompt box. It never runs it: a person presses Enter. |
| **sign the brief** | Shown while the brief is unsigned: opens the sign-off dialog. |
| **review rules** | Opens the rule review deck. |
| **stop the run** | Shown while agents are working: interrupts the turn. |
| **hide** / **show pane** | Closes the pane / brings it back. |
| **system 1/2** | Shown when the workspace holds more than one system: follows the next one. |

There is no refresh button: the pane reads the files again by itself after a command writes, when a turn ends, and every 20
seconds while idle.

## Pane commands

| | |
|---|---|
| `/modernize-panel [open\|close\|json]` | Show or hide the pane (the same switch as its **hide** and **show pane** buttons); `json` prints the reading it draws from. |
| `/modernize-review-pane [flagged\|p0\|all] [filter]` | The review deck. `flagged` (default) is the P0 rules with a defect, an SME note or less than High confidence. The filter matches an id, a domain, a title or a cited file. Not the same as `/code-modernization:modernize-review`, the plugin command that asks in pop-ups and works without the pane. |
| `/modernize-sign [name, role]` | Sign the brief's approval block. |

## Pane options

Set in `/config`, or under `pluginConfigs` in settings.

| Option | Default | |
|---|---|---|
| `system` | first under `analysis/`, else under `legacy/` | The system to follow (a name of letters, digits, `-` and `_`). |
| `track` | `auto` | `auto` follows whichever way the commands are working on the system; `transform`, `uplift` or `reimagine` pins one. |
| `panel` | `auto` | `auto` opens the pane by itself and draws the show bar while it is hidden; `command` opens it only when the button or `/modernize-panel` asks; `off` neither opens it nor draws the bar. |
| `xray` | on | Attach analysis context to legacy reads. |
| `commandPrefix` | `/code-modernization:modernize-` | How the pane writes the plugin's commands. |
| `legacyDir` | `legacy` | The read-only tree. |

## Pane keys

Hotkeys work in the band above the prompt (the review deck's digits, from an empty prompt). A pane's buttons are pressed by
clicking, or `ctrl+x tab` to give the pane the keyboard, then Tab and Enter. Where the terminal is tall enough the pane prints
this as a hint under its buttons.

## What the pane does not do

- An uplift's changed modules are found by comparing the working copy with the legacy tree by file name and size, with the
  file API alone: the pane runs no program inside either tree. An edit that keeps a file exactly the same size is not seen by
  that comparison, but a test run in the module, or a write during the session, shows it.
- Sizes are lines where the map gave them and bytes of source where the units were read off the tree; a single file counts for
  at most 400 KB, so a binary in a test folder is not a system's bulk.
- It never runs a command by itself. The **put in prompt** button puts the command in the prompt box; a person presses Enter.
- It does not call a model. The brief's phases and approval are read by pattern from the file, and the verdicts from
  `VERIFICATION.json` as its script wrote them; what cannot be read that way is shown as unknown, not guessed.
- It only watches. It does not block or rewrite any edit or command; the workspace's own permission rules
  (`Edit(/legacy/**)` denied, see "Set it up so it runs smoothly" in the plugin README) are what keep the source read-only.
- The cut-over console (live legacy-versus-modern traffic diff with automatic fallback) and approvals from a phone are not
  built: both need an environment this repository cannot test.

To work on the pane, `hooks/register.ts` is the module: it binds the engine at `session.start` and wires the hooks, and
everything it calls is a plain function under `hooks/`. `claude plugin test .` runs the tests in `tests/` (parsers, layout,
estates in eight stacks, and the hooks through the engine's own `$`); `tsc -p .` typechecks them against the
declaration file `/plugin-types` writes into `.claude/types/`.
