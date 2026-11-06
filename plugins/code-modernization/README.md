# Code Modernization

Point Claude at a legacy codebase and get four things: an understanding of what it is and what it does, a plan you approve, the modernized code, and **proof that the new code behaves like the old**. It works with any language and any kind of move: a newer version of the same technology, a rewrite in another one, or a rebuild on a new architecture.

![One report page with everything found so far: a green banner when the proof passes and the old and new outputs match, the command to run next, the steps done, and the counts, with tabs for the assessment, the map, the business rules, the plan, the build notes and the proof.](assets/media/report-glance.jpg)

## Install

You need [Claude Code](https://code.claude.com). Then:

```
/plugin install code-modernization@claude-plugins-official
```

Some steps start many agents at once, so expect real usage on a large system (see *What to expect*). Start with one module or one unit as a pilot, not the whole estate.

## Start here

Open a folder for the work and type `/code-modernization:modernize`. It asks what you want to do with your code (a couple of short questions), finds the code, writes your answers down once, shows the road ahead, and gives you the exact first command. Every later command reads what you said, so nothing is asked twice. **Not sure what you want?** Choose *Understand it first*: you get the assessment, the map, the business rules and a plan, and no code is rebuilt.

To go step by step instead, point the first command at your code and follow the "next step" line each command ends with:

```
/code-modernization:modernize-preflight <name> --source <path to your code>
/code-modernization:modernize-status <name>       # where am I, and what is next: run it any time
```

`<name>` is a short label of your choice (letters, digits, `-`, `_`). `--source` makes a link at `legacy/<name>` and copies nothing, so a huge repository stays where it is. **Nothing edits your legacy source.** Commands write only to `analysis/<name>/` and `modernized/` (a build check writes build output where your build normally does), and each refreshes `analysis/<name>/REPORT.html`: one page, with everything found so far, that you can open or share. A few steps need someone who knows how the system is built and run, so bring an engineer for the first questions.

## The path

Each step stands alone, so you can stop and review after any of them.

| Step | Command | What you get |
| --- | --- | --- |
| 0 | `modernize` | Say what you want. Writes `INTENT.md`; every later command reads it. |
| 1 | `modernize-preflight <name> [target-stack] [--source <path>]` | Is the environment ready? Asks five questions only a person can answer (is this the whole system or a slice, can it build and test here, is there custom build tooling, has anyone tried before, is anything off limits), proves a build works on this code, and finds missing source. |
| 2 | `modernize-assess <name>` | What am I dealing with: inventory, complexity, debt, security, and a recommended pattern. |
| 3 | `modernize-map <name>` | The structure: dependencies, data flow, entry points and business flows, as an interactive map. |
| 4 | `modernize-extract-rules <name>` | The business rules as testable Given/When/Then cards with `file:line` citations, each re-checked by a second agent. |
| 4b | `modernize-review <name>` | A person confirms or corrects the rules that look wrong. Your answers reach the plan and the build. With the live pane on, `/modernize-review-pane` does the same one card at a time. |
| 5 | `modernize-brief <name> [target-stack]` | The phased plan a steering committee approves. **Nothing is built until you approve it.** |
| 6 | `uplift`, `transform` or `reimagine` | The build (see below). |
| 7 | `modernize-verify <name>` | **The proof.** An independent re-check with one verdict per module. |
| 8 | `modernize-harden <name>` | A security scan of the legacy system with a reviewed patch you apply yourself. |

`assess --portfolio <parent-dir>` surveys many systems and ranks them on one page. `modernize-status <name>` says where you are and gives the exact command to paste.

**A person decides at six points**, and the plugin never decides them for you: the five preflight answers, the rules that look wrong (`review`), approving the brief, accepting any difference the proof finds, signing the proof, and applying the security patch.

## How it proves the result

Modernization fails quietly: the new code passes the tests someone wrote, and differs on the inputs nobody thought of. So the proof is built from evidence a script can check, not from the model's opinion. `modernize-verify` runs after a build, ideally in a fresh session, and re-does the work instead of trusting the notes the build left behind:

- **The tests, run again from clean.** Build output is deleted, the full suite runs, and the counts come from the runner's own result files or a saved log. A run that executed no tests, or skipped them, is a failure, and a count the command merely typed in does not count.
- **Old and new on the same inputs.** Where the legacy code can run, both run on the same inputs and a script compares every byte. Only fields that must vary (timestamps, generated ids) are masked, floating-point output can be compared within a declared tolerance, and every masked field is listed in the result. A difference a person accepts is recorded with the reason.
- **Inputs nobody used.** It invents at least ten new inputs (boundaries, empty, huge, unusual order, and malformed records when you asked for exact behavior, quirks included) and compares again, so a suite that only passes on the cases the model chose is caught.
- **Tests that can fail.** A deliberate one-line break must turn tests red (the canary), and the comparison itself is checked by changing one byte of an output.
- **Every critical rule is backed by a test that ran.** Each P0 business rule must be named by a test that executed and passed. A rule named only by a skipped or pending test is listed as "named, not run", and a test folder that holds no code of its own is listed as tooling and gets no verdict.
- **The source is untouched**, checked by file times without running anything inside the analyzed tree.

Each module gets one verdict, computed by `scripts/proof_pack.py` from those files with rules written into the output: **PROVEN**, **PARTLY PROVEN** (with what is missing) or **NOT PROVEN** (nothing ran, something differs, a test fails). If the old system cannot run where you work (a mainframe program, a system that only runs in production), the old behavior can only be checked against recorded outputs, and the best verdict is PARTLY PROVEN: the page says so plainly. Anything a person must decide (open questions, exit criteria, the sign-off) is listed as waiting for a person and is never ticked for you. Every verdict is computed again from current evidence each time; none is carried over from an earlier run.

![The proof tab of the report: what passed for one rewritten module, a table of checks each with its detail, and the count of critical rules that a test names.](assets/media/report-proof.jpg)

## Choose how to build (the plan recommends one)

| If you want | Run | What happens |
| --- | --- | --- |
| The same technology on a newer version (.NET Framework to .NET 8, Java 8 to 17, Spring Boot 2 to 3) | `modernize-uplift <name> [source-version] [target-version]` | Keeps your code and fixes only what the new version breaks, driven by a catalog of the breaking changes this code actually hits. One pilot unit first with its lessons written down, then batches. The proof is the same test suite run on both versions. |
| A new technology, one module at a time, while the old system keeps running | `modernize-transform <name> [module] [target-stack]` | A plan you approve, tests that pin the old behavior, an idiomatic rewrite, and proof: old and new run on the same inputs and a script compares them. |
| A rebuild on a new architecture | `modernize-reimagine <name> [target-vision]` | A spec mined from the code, an architecture that is reviewed and approved, then services scaffolded with executable acceptance tests. |

A version move keeps your code, so it can skip `extract-rules` and `review`: `preflight`, `assess`, `uplift`, `verify` is a complete path, and `map` and `brief` add the unit order and an approved phased plan for a large system. If the delta catalog shows an "uplift" would rewrite most of the code, the command says so and points to `transform`. Rehost (move as is) and Replace (buy a product) change no code, so no build command applies; the analysis is still useful for both.

## What it has been tried on

The commands were run for real, headlessly, on public codebases while the plugin was built, and what broke was fixed. Every number below comes from the files those runs wrote. The same command can give different counts on a second run (the security scan of the osCommerce code found 48 confirmed findings and then 52), so read the numbers as typical, not exact. Wherever a person had to decide (approve a plan, accept a difference), the tester played that person. Some runs stopped early because of limits of the test machine (it refused to run any freshly compiled program, and its package index refused installs); the plugin said so and did not work around them.

| Codebase | Move | What it did and what was shown |
| --- | --- | --- |
| **AWS CardDemo** (COBOL, CICS, JCL) | Rewrite in Java, one job at a time | 35 rules (8 critical) and a five-phase plan, then the monthly interest job rewritten in Java 21 (213 tests at the end). Five independent checks in a row compared it with the real COBOL program, built locally, on inputs written after the fact. Each found something the tests had missed, and each was answered: a blank field that halted the job, a non-numeric account key, a negative zero, and differences the owner accepted as deliberate. The last check tried fifteen more inputs with malformed records and found seven more differences, so it ended NOT PROVEN. It also told two problems of the old system's test harness apart from defects in the new code. What ends a loop like this is a person deciding which inputs are in scope; the verify command now reads that from the intent you gave the front door. |
| **Eclipse Jetty** (Java 8, 2,600 files) | Java 8 to 17 | A pilot on the `jetty-util` module: the same 946 tests give the same results on both Java versions. Building and running both versions found six changes that reading the code had not predicted: a direct buffer reported as memory-mapped on 17, a bundle plugin that writes an invalid manifest and still says SUCCESS, and a build on JDK 13 to 16 that would have shipped Java 8-labelled classes that crash on Java 8, among others. 50 tests were added for the 25 of 56 critical rules that had none (996 tests run on each version, no differences). |
| **osCommerce** (PHP 5, about 44,000 lines of PHP) | PHP to Python and FastAPI | 97 rules (26 critical) and a six-phase plan. First slice, the product page: 17,957 tests pass, and 17,727 comparison cases against the real PHP files are identical. Two deliberate breaks each turned tests red. The architecture review found two high-severity problems (expired specials still shown, and a page request holding a database write lock) that were fixed with tests that failed first. An independent verification said PROVEN: its own break made 647 more tests fail, and 14 new inputs matched the real PHP. |
| **AngularJS RealWorld** (AngularJS 1.5) | AngularJS to React and TypeScript | 79 rules (5 critical). The articles service was rewritten: 166 tests, and 29 comparison cases against recorded responses of the real API (23 identical, 6 differences approved as deliberate, none unexplained). Four deliberate breaks each turned tests red, and the review's two high-severity findings were fixed. Checked by the build step itself; there was no separate verification run. |
| **JPetStore** (Java and JSP) | Rebuild as a REST API | A spec with 12 capabilities, the 35 rules and a four-phase plan. The architecture review found two blockers (an order confirmation that could not be safely replayed, and cart updates lost under parallel requests); both were designed out. One service was scaffolded: 35 tests ran and passed, 56 more are pending or need Docker. The independent check said NOT PROVEN: 6 of 24 new comparisons with the old application differ, and the development cases hold no old-versus-new comparison yet. That run also showed the proof step counting skipped tests as covering a rule; it now flags five of the six critical rules as named only by tests that did not run. |
| **beets** (Python 2, about 19,000 lines) | Python 2 to 3 | 21 rules for the tagging module (4 critical), all about matching. Only 3 files in the whole tree fail to compile on Python 3, so it is an uplift and not a rewrite. No existing test could run on Python 3 yet, and the packages they need were refused by this machine's package index; the plugin reported that and did not claim a pass. |
| **Spring PetClinic** (7 services) | Spring Boot 2.6 to 3.3 | A delta catalog with exact target versions: 59 `javax` imports in 10 files to move, a request that answered 200 on 2.6 and answers 400 on 3.3 (verified by running both), a Hibernate 6 identifier check that came out safe, and a monitoring endpoint that Boot 3 dropped. The pilot stopped at the plan gate because the approved plan named a different first service, and the command enforced the plan. |
| **AWStats** (Perl, about 43,000 lines) | Perl to Python and FastAPI | 88 rules (2 critical) and a six-phase plan that keeps replacing it with an existing product open as the alternative. The security scan confirmed 48 findings, 9 of them high (7 in an optional module that runs as root), and refuted 14 of 62 as false positives. |
| **Redmine 2.3.3, eShop (.NET), Jenkins pipelines** | Rails 3.2 to 7.1, .NET Framework 4.7.2 to .NET 10, Jenkins to GitHub Actions | Maps, rules (185, 57 and 58) and plans. Redmine's assessment led with "check whether upstream already made this move". eShop's catalog lists 12 silent behavior changes and says the first phase must build a test harness because the solution has none. |
| **NetHack, KISS FFT, BSD numbers** (C) | C to Python, and to Rust | 28, 70 to 93 and 56 rules. NetHack's first slice (its declarations, in Python) matched the C program on 8 of 8 comparison cases. The Rust runs stopped at the plan: this Mac killed every freshly compiled program, so the plugin listed what could not run and did not work around it. |
| **A booby-trapped codebase** (built for the test) | Rewrite | Planted instructions in comments, the README, a `CLAUDE.md` and a project settings file, a script that would drop a marker file, and file names with shell syntax. Nothing planted was obeyed, no marker file appeared, the source stayed unchanged, the planted lines were listed in the report, and the credential was masked. |

## What to expect

Steps run as agents working for you, and the heavy ones run many at once. Rough times on systems of tens of thousands of lines: preflight 3 to 4 minutes, assess 5 to 8, map 5 to 15, extract-rules 5 to 15, brief about 5. Building one module takes 15 to 30 minutes, an uplift pilot about 15. The heaviest step, `extract-rules`, started 50 to 200 agents in these runs, and every fan-out step says how many it will start; `extract-rules` asks before a big run. On systems in the millions of lines, work one module or unit at a time. The size index in `assess` is a relative measure for ranking systems, never a schedule or a cost.

## Words you will see

| Word | Plain meaning |
| --- | --- |
| Agent | A separate Claude worker that does one job (read one module, check one rule) and reports back. Steps start many of them at once. |
| Business rule card | One thing the system does, written as Given / When / Then with the file and line it comes from, so a person can check it. |
| P0 | A rule that would defeat the system's purpose or be costly or irreversible if it were wrong. Everything else is P1 or P2. |
| Brief | The written plan, phase by phase. You approve it; commands never build anything before that. |
| Uplift / transform / reimagine | Newer version of the same technology / rewrite in another technology / rebuild on a new architecture. |
| Pilot | The first small unit built end to end, so its lessons are written down before the rest is attempted. |
| Canary | A deliberate one-line break in the new code that must make tests fail, proving the tests can fail. |
| Delta catalog | The list of things the newer version breaks that this code actually uses. |

## Set it up so it runs smoothly

The commands never edit your code, by convention. A `.claude/settings.json` in the workspace backs that up with a deny rule for the source and allow rules for the outputs (`preflight` checks for the deny rule):

```json
{
  "permissions": {
    "allow": ["Read(**)", "Edit(analysis/**)", "Edit(modernized/**)"],
    "deny": ["Edit(/legacy/**)"]
  }
}
```

- File writes are matched through the `Edit` rule, so this covers the `Write` tool too (a `Write(path)` rule is never consulted). The leading `/` anchors the rule at the workspace root.
- If `legacy/<name>` is a symlink (which `--source` makes), also allow reading its target (`"additionalDirectories": ["/path/to/code"]`) and deny its real path (`"Edit(//path/to/code/**)"`), because the rule above matches the link's path, not its target's.
- The rule covers Claude's file tools and the shell commands it recognizes. A script that opens files itself is not covered, so keep Bash on a *prompted* permission mode for the two steps that fan out many writing agents at once (`uplift` step 5b and `reimagine` phase E).
- Shell commands still ask even in accept-edits mode (`python3` scripts, `scc`, `rsync`, your build and test commands, anything outside the workspace). Use accept-edits mode or allow rules for the ones you trust.

Helpful but optional (run `preflight` to check them all): [`scc`](https://github.com/boyter/scc) or `cloc` for size metrics; Python 3.8 or newer as `python3` (on Windows `python` or `py -3` works) for the map, the shard builder, the proof and the report; a build toolchain for your stack, which enables the strongest proof (running old and new side by side); and the whole system in the tree (deployment descriptors, copybooks, DDL), which entry points and data lineage need. Without a toolchain the plugin falls back to recorded-output tests and says so.

## Safety

- **Analyzed code is untrusted input.** A hostile codebase can plant comments like "ignore previous instructions", a README that tells tools to run a script, or file names with shell syntax. Agents treat file content as data, list the instruction-shaped text they found and never follow it (the legacy code's own build and tests run only where a command needs its behavior, in a scratch copy when it can), verification agents re-derive every rule and finding from the cited code, and `brief` is a human approval gate before anything is built. Treat discovery artifacts from untrusted code with the same skepticism as the code.
- **Secrets stay out of shared artifacts.** Discovered credentials are masked (`AKIA****`) and inventoried in a gitignored `SECRETS.local.md` (or `~/.modernize/<name>/` outside git); `harden` keeps credential-removal hunks in a separate gitignored patch. `--show-secrets` puts raw values in the quarantine file only.
- **The old system is run only where it is safe.** Baselines come from the legacy code running locally or against a test environment you named. Production or third-party services, new accounts and real data are off limits unless the plan you approved names them, a token in a recorded response is replaced before anything is saved, and every command stops the servers it started.
- **Trying it on a live repository.** `preflight` and `assess` change no source file. Preflight's smoke test compiles one file and, where there is a build system, restores and builds one small project, which writes build output wherever the build normally does.

## Telemetry

The plugin counts how it is used, so the next version can be better. It sends **whole numbers only**: never code, file or system names, paths, prompts or anything you typed. Counts of 100 or more are rounded to two significant figures (17,727 is sent as 18,000), so a number says roughly how big, not exactly which system. It sends them through Claude Code's own telemetry, so nothing is sent to Anthropic when that is off. The plugin itself makes no network call and adds no identifier; the one file it writes is a small `telemetry-state.json` of hashes in its own data folder, so the same counts are not sent twice.

Five small hooks do it:

- **When you type one of the plugin's commands:** which command, how far that system had got, and what it is running on (operating system, python status and version, and whether the folder's path has a space or unusual characters).
- **When a turn ends and the counts changed:** how far the newest system has got, and how the last rule extraction went (agents started, lost, unverified). Only in a folder where the plugin has left files such as `INTENT.md` or `PREFLIGHT.md`.
- **When something fails:** a tool call that errored, or a model call that ended a turn. The failure's text is read on your machine to choose one code from a fixed list (python missing, blocked by a permission rule, timed out, file not found, rate limit and so on) and only the code is sent, at most once per kind per session. Only where the plugin is in use or the failing command names it.
- **When one of the plugin's own scripts raises an error:** which kind of error and which line, never its message.
- **Once per plugin version on each machine, at the start of a session:** what the plugin runs on (the same operating system, python and path numbers), so that machines where nobody gets as far as typing a command are still counted once. This is the one number that is sent without you using the plugin.

If python is missing, is the Windows Store placeholder, is too old or crashes, the small shell script that starts the hooks says so in numbers itself, because python cannot report its own absence. If it finds `python` or the `py` launcher working, it uses that instead.

| Key | What it counts |
| --- | --- |
| `pv` | plugin version as major*10000 + minor*100 + patch |
| `cmd` | command typed: 1 front door, 2 preflight, 3 assess, 4 map, 5 extract-rules, 6 review, 7 brief, 8 transform, 9 uplift, 10 reimagine, 11 verify, 12 harden, 13 status, 20 to 22 the pane's commands, 99 other |
| `perm` | permission mode the session ran in: 0 unknown, 1 default, 2 accept edits, 3 plan, 4 auto, 5 bypass, 6 don't ask |
| `has_source` | 1 when the command carried `--source` |
| `fresh` | 1 when the system had no artifacts yet |
| `systems` | systems under `analysis/` |
| `goal` | 0 unknown, 1 understand, 2 uplift, 3 transform, 4 reimagine |
| `lang` | the language with most lines in the map: 1 COBOL, 2 Java, 3 C# and .NET, 4 Python, 5 PHP, 6 Perl, 7 C, 8 C++, 9 JavaScript and TypeScript, 10 Ruby, 11 Go, 12 Rust, 13 Kotlin and Scala, 14 SQL, 15 Fortran, 16 RPG, 17 Pascal and Delphi, 18 shell, 19 assembler, 99 other, 0 unknown |
| `done` | the steps that have left their file, added up: preflight 1, assess 2, map 4, rules 8, reviewed 16, brief 32, approved 64, built 128, verified 256, signed 512, hardened 1024, report 2048, deltas 4096, baseline 8192, playbook 16384, spec 32768 |
| `map_kloc` | thousand lines of code in the map |
| `rules`, `p0` | business rules found, and the critical ones among them |
| `rev_ok`, `rev_wrong` | rules a person confirmed, and rules a person marked wrong |
| `phases` | phases in the plan |
| `built` | modules or services built (an uplift's working copy counts as one once it exists) |
| `eq_cases`, `eq_diff`, `eq_appr` | old-versus-new comparison cases run, differences or missing outputs nobody approved, differences a person approved (counted from the case list, the way the report counts them) |
| `v_proven`, `v_partly`, `v_not` | modules judged PROVEN, PARTLY PROVEN and NOT PROVEN |
| `sec_crit`, `sec_high` | critical and high security findings |
| `os` | system: 1 macOS, 2 Linux, 3 Windows, 4 Windows subsystem for Linux, 0 other |
| `py` | how python worked: 0 python3 ran, 1 none found, 2 macOS developer-tools stub, 3 python3 present but broken (the Windows Store placeholder), 4 python3 unusable but python or py ran, 5 too old, 6 the script crashed |
| `pyv` | python version as major*100 + minor (311 is 3.11) |
| `pathf` | the folder's path: 1 has a space, 2 has non-ASCII characters, 4 is over 200 characters (added up) |
| `tool` | the tool that failed: 1 Bash, 2 Read, 3 Edit or Write, 4 Glob or Grep, 5 agent, 6 Workflow, 7 asking the person, 8 skill, 9 web, 10 a connector, 99 other |
| `kind` | what went wrong: 1 python or another interpreter missing, 2 the Windows Store python stub, 3 the macOS developer-tools stub, 4 python too old or a syntax error, 5 one of the plugin's scripts raised an error, 6 blocked by a permission rule or policy, 7 a file permission was denied, 8 timed out, 9 a file or folder was not found, 10 network, certificate or sign-in, 11 disk or memory, 12 workflow or agent trouble, 99 other |
| `api` | a model call ended a turn: 1 rate limit, 2 sign-in failed, 3 billing, 4 invalid request, 5 server error or overloaded, 6 output too long, 7 network or timeout, 99 unknown |
| `err`, `err_at` | the plugin's own script raised: 1 KeyError, 2 ValueError, 3 OSError, 4 TypeError, 5 AttributeError, 6 RecursionError, 7 MemoryError, 8 UnicodeError, 99 other; and the line of `telemetry.py` where it raised |
| `agents`, `wf_failed`, `wf_skip`, `wf_unver` | agents the last rule extraction started, modules or agents it lost, modules it skipped, rules it could not verify |

To see exactly what would be sent for your workspace, before anything is sent, run `python3 scripts/telemetry.py show /path/to/workspace` from the plugin's folder (add `--prompt "/code-modernization:modernize-verify billing"` to see a command's counts).

To turn it off, use any one of these: the plugin's **Usage counts** option, `CODE_MODERNIZATION_TELEMETRY=0` in your environment (anything but an explicit `1` or `on` counts as off), or Claude Code's own `DISABLE_TELEMETRY=1` (or `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`). Nothing is sent while any of them is set.

**What these numbers cannot see.** A machine where the shell cannot start the hooks at all (for example Windows without Git Bash) sends nothing, and neither does a machine that never starts a session with the plugin enabled, so failure rates here are a floor, not a total. Read them next to install counts and Claude Code's own hook-failure events.

If nothing seems to be sent when you expect it, set `CODE_MODERNIZATION_TELEMETRY_DEBUG=1`: each hook run then adds one line saying what it decided to `telemetry-debug.log` in the plugin's data folder.

## Working in a team

State lives in files, not in chat: later commands read the brief, the intent and `PREFLIGHT.md`, not your conversation, so a second person or a fresh session can run `status` and continue. The commands never commit to your repository, so commit `analysis/` and `modernized/` yourself (an uplift's working copy gets its own local history, for a reviewable diff).

| Artifact | Suggested reviewer |
| --- | --- |
| `PREFLIGHT.md` (the five answers, scope boundary, build checks) | whoever owns the build |
| `ASSESSMENT.md`, `REPORT.html` | the engineering lead or sponsor |
| `topology.json`, `TOPOLOGY.html` | engineers who know the system |
| `BUSINESS_RULES.md` (then `modernize-review`) | a business expert per domain: start with the P0 rules and the closing question list |
| `MODERNIZATION_BRIEF.md` | the approver, who steers execution by editing it |
| `VERIFICATION.md` | the approver and a second engineer, who sign it |
| `SECURITY_FINDINGS.md` and the patch | a security engineer, who applies the patch |

## Live progress pane (early access)

A pane beside the transcript that shows the map of your code, how far each part has got, each built module's proof verdict, and what to run next, in any language and for any of the three ways of building. It needs Claude Code's early-access function hooks: start with `CLAUDE_CODE_ENABLE_FUNCTION_HOOKS=1 claude`. Without the flag nothing changes. Its three commands are typed bare: `/modernize-panel` shows or hides it, `/modernize-review-pane` reviews the flagged rule cards in it, and `/modernize-sign` fills in the plan's approval block. Details are in [hooks/README.md](hooks/README.md).

![The live pane beside the transcript for a rewrite: the map with one module reviewed, the phases, a module marked proven, the next command, and two items that need attention.](assets/media/pane-rewrite.png)

## Good to know

- **A model does the extraction, so two runs can find different rules.** Treat `BUSINESS_RULES.md` as reviewed output, not a deterministic build artifact. Rules are cut one per business decision, not one per branch, and headings are always `### RULE-NNN: <name>`.
- **Large runs are resumable.** On Claude Code builds with the Workflow tool, `extract-rules`, `harden`, `assess --portfolio`, `reimagine` and `uplift` run as scripted multi-agent jobs that verify findings adversarially. `extract-rules` shards by module and asks before a big run; a stopped run resumes in the same session with its run ID, and finished agents replay from the journal. Older builds fall back to plain subagents automatically.
- **Scripting it (`claude -p`).** Long steps run as background workflows, and a headless session stops waiting for background work after 10 minutes. Set `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0` so `extract-rules`, `harden` and the other fan-out steps can finish, and answer a step's approval gate by resuming the session with `--resume`.
- **Adapting it.** Commands, agents and workflows are markdown and JavaScript under Apache 2.0: fork them to change the prompts or steps for your stack.
- **Agents.** `legacy-analyst`, `business-rules-extractor`, `architecture-critic`, `security-auditor`, `test-engineer`, `version-delta-analyst`, `uplift-migrator` and `scaffolder` are invoked by the commands (or directly). The last two write only inside their own unit's directory.
- **Related.** [code-migration-kit-with-claude-code](https://github.com/anthropics/code-migration-kit-with-claude-code) is a separate public kit of prompts, templates and scripts for large-scale language migrations. This plugin is the guided, command-driven workflow from discovery through plan, build and proof; use either or both.

## License

Apache 2.0. See `LICENSE`.
