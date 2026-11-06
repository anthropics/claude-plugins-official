---
name: siege
description: "Work on one hard mathematics problem in rounds: each round a judge writes a few self-contained questions, independent workers answer them, and the judge keeps a ledger of what is proved, refuted and open, until the judge concludes or the rounds run out, and then a proof.md says plainly what is and is not proved. A run takes hours and dozens of worker runs. Usage: /math-proof:siege [NAME=value settings] <the problem, stated in full, or the path of a file holding it>."
argument-hint: "[NAME=value ...] [DIR=run-directory] <problem statement | problem-file>"
disable-model-invocation: true
disallowed-tools: WebSearch, WebFetch, AskUserQuestion
allowed-tools: Read, Write, Edit, Glob, Grep, Agent, Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/ledger.py *), Bash(python3 ${CLAUDE_PLUGIN_ROOT}/skills/siege/scripts/ledger.py *), Bash(python ${CLAUDE_SKILL_DIR}/scripts/ledger.py *), Bash(python ${CLAUDE_PLUGIN_ROOT}/skills/siege/scripts/ledger.py *), Bash(mkdir *), Bash(cp *), Bash(mv *), Bash(cat *), Bash(test *), Bash(ls *), Bash(wc *), Bash(cmp *), Bash(grep *), Bash(printf *), Bash(echo *)
---

# math-proof: siege

## The approach
The skill works on one problem in at most MAX_ROUNDS rounds. Each round a judge writes a few self-contained
questions, at most WAVE of them before round ESC_ROUND. The steps below call them queries. Each question goes
to a fresh worker that sees only that question and the problem statement. The judge reads the answers,
rewrites the running summary, and adds to a ledger of claims marked PROVED, REFUTED or OPEN. One claim is the
goal, set in round 1; the judge may set a new goal at a later round, and in particular may raise it to a more
significant statement once it is proved (the proved goal then stays in the ledger as the fallback result, to
which the judge returns if two waves bring the raised goal no nearer; when the goal is raised you tell the user and
copy the proved result to DIR/result-so-far.md). When an answer holds a complete written proof or disproof of the goal, two more workers check that exact text
line by line. Once both pass, the judge concludes or raises the goal. Before round MIN_ROUNDS, that is the only
way to conclude. From round ESC_ROUND on, if no complete proof or disproof is in hand, a round may
hold up to WAVE_DEEP questions for higher-effort workers. All but at most two of them aim at the one statement
still missing from the proof. After the rounds end, the judge writes a self-contained proof.md, a worker
checks it, and the judge finalizes it. Unless the goal the run ends on was both proved and checked twice during
the rounds, there are also extra revision passes and a last wave of full proof attempts before finalizing.
proof.md has a Status section that says plainly what is and is not proved. This section is only a summary: you do none of the mathematics
yourself, and you follow the steps below exactly, launching a fresh sub-agent for every judge step and every
worker.

You are the ORCHESTRATOR of this protocol. You do not do the mathematics yourself and you do not judge it:
the judging is done by fresh `math-proof-judge` subagents, one per step, and the reasoning by fresh `math-proof-worker` or
`math-proof-worker-deep` subagents, one per query (which of the two is fixed by the round number — see Rules). Your job is to run the steps below exactly, keep the files in order, act on the one
mechanical verdict the bookkeeping script prints, and never skip, merge or reorder steps because the problem
looks easy or hard. Do not read the workers' answer files yourself (use `test -s` to see whether one exists;
the bookkeeping script, not you, decides whether it is finished); do not summarize mathematics in your own words anywhere a judge will read it — pass files, not
paraphrases. Work unattended to the end: there is nobody to answer questions.

**Arguments.** The invoking message reads: $ARGUMENTS
It gives the problem and, optionally, settings. Read it this way. Tokens of the form NAME=value at its start,
where NAME is a word of two or more capital letters and underscores and value is a whole number (or, for DIR,
a path, quoted if it contains spaces), are settings (the seven below, or DIR, the run directory; any other such
NAME is an error, see Settings); remove them. If what remains is a single line that, taken as a whole —
surrounding whitespace and one pair of enclosing quotation marks removed, backslash-escaped spaces read as spaces
— is the path of an existing file (it may contain spaces; check with Read or Glob, not the shell), that file is
the problem file; if no such file exists and what remains can only be a file path — a single line ending in .md,
.txt or .tex, or a single token (no spaces once the quotes are removed) containing "/" or "\" — tell the user in
one sentence that no file exists at the absolute path you looked for (give it) and that the problem can instead
be given in full as text after the command, and stop; otherwise everything that remains, to the end of the
message, IS the problem statement, verbatim — mathematics, line breaks and all (MAX_ROUNDS=8 is a setting;
"n=3", "N=pq", "AB=AC" and "f(x)=…" are mathematics). The run directory DIR defaults to ./math-proof-run under the
current directory; use DIR's absolute path everywhere below. If the message holds neither a readable problem
file nor any problem text, say so in one or two sentences — with the usage, `/math-proof:siege [NAME=value …]
<problem statement, or the path of a file holding it>`, and that a stopped run is resumed by giving its
original line again in the same directory — and stop.
**Settings** (use these unless the invoking message overrides them by name): ESC_ROUND = 4 (the escalation
round: from round ESC_ROUND on, if the loop is still running, the wave cap rises, every worker is a
`math-proof-worker-deep`, and the plan brief carries its escalation clauses); WAVE = 4 queries per round at most in
rounds before ESC_ROUND and WAVE_DEEP = 10 queries per round at most from round ESC_ROUND on; MAX_ROUNDS = 14;
MIN_ROUNDS = 4 (the judge may conclude freely from round MIN_ROUNDS on, earlier only with an
audited chain in the ledger — the script decides); REFINE_STEPS = 2; MAX_COMMIT = 9 (both apply to the FULL proof tail; a run whose final goal was certified during the rounds gets the SHORT tail — see "The proof tail"). The invoking message may override any of these seven by
name, with tokens of the form NAME=value (for example MAX_ROUNDS=8 WAVE_DEEP=6) placed before the problem, at
the start of the invoking message: use the values as given, and treat such a token there (NAME a word of two or
more capitals and underscores, value a whole number) whose NAME is neither one of the seven nor DIR as an error — tell the user in one sentence
that NAME is not a setting of /math-proof:siege, that the accepted names are DIR, ESC_ROUND, WAVE, WAVE_DEEP,
MAX_ROUNDS, MIN_ROUNDS, REFINE_STEPS and MAX_COMMIT, and that if the token is part of the problem itself the
problem can be given as a file path instead — and stop before creating anything. (A leading token whose
left-hand side is a single letter or not all capitals, or whose right-hand side is not a whole number, and any
"=" further inside the problem statement, is mathematics, not a setting.)
Wherever a setting is named below, it means the value in force.
The bookkeeping script is scripts/ledger.py in this skill's own folder: `python3 ${CLAUDE_SKILL_DIR}/scripts/ledger.py`
(called SCRIPT below). If that placeholder was not filled in — the path before /scripts does not exist — use
`${CLAUDE_PLUGIN_ROOT}/skills/siege/scripts/ledger.py`, and if that one is unfilled too, Glob for
`**/skills/siege/scripts/ledger.py` under ~/.claude and use its absolute path (if several match, the newest); in
every case quote the script path in the command if it contains spaces. Before Setup, run SCRIPT once with no
further arguments: it should print a line beginning "usage:". If instead Python runs but says it cannot open the
script file, the path is wrong, not Python: resolve it again by the fallbacks above and run once more, and if no
ledger.py can be found tell the user the plugin's files are not where expected (reinstall math-proof from
`/plugin`) and stop. If instead the shell says python3 cannot be found, or anything else comes back that is not
the usage line (on Windows, a reply that Python "was not found" and can be installed from the Store is this
case), use `python` in place of `python3` in SCRIPT from then on and run it once more; if that fails too, tell
the user in one or two sentences that /math-proof:siege could not run its bookkeeping script — quote the command
and the shell's reply — that it needs Python 3.7 or later on the PATH as python3 or python, and that the same
line given again will work once that is fixed; then stop.

## Setup
1. If DIR/state.md already exists, this is a resume: check that the existing DIR/problem.md is the same problem
   you were given (compare the text, ignoring differences in whitespace and line endings; for a file, `cmp`) —
   if it differs, say in one sentence that DIR holds a run on a different problem and that `DIR=<another
   directory>` selects a fresh one, and stop; if it is the same and state.md records "phase: finished", that run
   is complete: say where DIR/proof.md is (and DIR/result-so-far.md, if it exists), that `DIR=<another
   directory>` starts a fresh run, and stop; otherwise Read DIR/problem.md in full, read state.md and
   resume from the phase it records instead of starting over, never redoing a step whose output files exist and
   never rewriting DIR/problem.md (if the invoking message gives settings that differ from those recorded in
   state.md, include one line saying the recorded ones govern this run in the same message as your next tool
   call — a notice, not a stop). If the phase recorded is a wave, start with `SCRIPT answers` on that wave's
   query stems (see the wave rule under Rules) and launch workers only for the queries the script does not report
   answered, each partial one with its {EARLIER} paragraph; that launch counts as the wave's first, so its one
   re-run still follows. A query already answered whose index line is missing gets the line
   "{Q} | answered | (finished before this session resumed)"; a query that already has an index line gets no
   second one — its new status is appended to that line as " | re-run: status | abstract" instead.
   Otherwise create DIR and DIR/judge/ (`mkdir -p`) and put the problem at DIR/problem.md: if
   it came as a file, copy that file there byte for byte with `cp`; if it came as text in the invoking message,
   Write exactly that text (nothing added, removed or reworded) to DIR/problem.md. Then, as your very next
   action, Read DIR/problem.md in full — you paste its text into every judge brief and every worker prompt (see
   Rules).
2. Write DIR/state.md (protocol math-proof siege, the seven settings with the values in force — marking any the invoking
   message overrode —, "phase: round 1 plan, attempt 1"). On a resume, the values recorded in state.md govern.

## The round loop — for r = 1, 2, …, MAX_ROUNDS
**(a) Plan.** Launch ONE `math-proof-judge` whose prompt is the PLAN BRIEF below with {r}, DIR and the round-dependent
slots filled in (and, on a retry, the correction paragraph the script gave you added at the top). The slots:
{CAP} is this round's cap on the number of queries — the Setting WAVE while r < ESC_ROUND, the Setting
WAVE_DEEP when r ≥ ESC_ROUND — and the same number goes into the check command of (b); {MAX_ROUNDS} is the MAX_ROUNDS setting, written as a number; {HORIZON}, {CONCLUDE_RULE}, {ESC_SUMMARY} and {ESC_WAVE} are the texts given
after the brief for this r (several are empty before round ESC_ROUND: an empty slot inserts nothing, not even
a space or a blank line). This is attempt 1 of round r.
**(b) Check.** First, if DIR/judge/screen_r{r-1}.md exists and round r−1's lines in DIR/index.md carry no screening verdict yet,
append each of its verdicts (" | OK" or " | DEGENERATE: …") to that query's index line — plain file handling; nothing is
re-run on a DEGENERATE verdict. Then run `SCRIPT check DIR {r} {CAP} {MIN_ROUNDS} {attempt}` ({CAP} = this round's cap, WAVE or WAVE_DEEP, exactly as in (a) —
passing WAVE in round ESC_ROUND or later would silently set part of the wave aside). It numbers and appends the round's
ledger lines to DIR/ledger.md itself and prints exactly one verdict line; act on its first word (if instead it prints a line
beginning `ERROR:`, the command itself was malformed — DIR first, as an absolute path, then the four numbers; correct
the command and run it again, which does not count as a plan attempt):
- `WAVE n FLOOR f …` — copy DIR/round{r}_summary.md over DIR/summary.md, note f (the fewest queries of this
  wave that may come back answered or partial, see Rules), give the goal-change notice below if one is due, then
  go to (c) with the query files DIR/round{r}_q1.md … DIR/round{r}_q{n}.md (the script has renumbered them
  consecutively if needed).
- `CONCLUDE …` — copy DIR/round{r}_summary.md over DIR/summary.md, record the verdict line in state.md as the
  reason the loop ended, give the goal-change notice below if one is due, and leave the loop for the proof tail.
- `RETRY: <correction>` — relaunch the plan step (a) as the next attempt, with the text after "RETRY: " as an
  added first paragraph of the brief; then run (b) again with the attempt number increased by one.
- `TAIL: <reason>` — the plan step failed three times; record the reason in state.md, copy
  DIR/round{r}_summary.md over DIR/summary.md if it exists and is non-empty, and leave the loop for the proof
  tail — unless no DIR/summary.md exists and no .answer.md or .partial.md file exists at all (nothing to draft
  from): then stop and report instead.
Goal-change notice: on a `WAVE` or `CONCLUDE` verdict, if the reply of the plan launch this verdict accepted (the
latest attempt) has a sentence beginning "Goal change:" (the judge replaced, raised or came back to a goal this
round — item 2 of the brief), give the user that sentence, quoted, as one line of text in the same message as your
next tool call (a notice, not a question: a message of text alone would end your turn — do not stop or wait), and
record the same line in state.md. If the sentence begins "Goal change: raised", first copy the file or files it
names as holding the earlier goal's proof (`test -s` each) to DIR/result-so-far.md — one file: `cp`; several: one
`cat <files in the order named> > DIR/result-so-far.md` (each ends with its own end line, which separates them)
— overwriting any earlier result-so-far.md, and end your line with "the proved result so far is in
DIR/result-so-far.md". If the sentence names no file, take `<stem>` from the locator after the final "—" of the last
line of the form "N. PROVED: [GOAL] …" in DIR/ledger.md (grep) and use `DIR/<stem>.answer.md`, or
`DIR/<stem>.partial.md` if only that exists; `test -s` each file first, and if none exists, skip the copy and say
so in your line. That file is for a user who stops the run here; nothing later reads it, and proof.md remains the
run's deliverable. (On a problem that fixes its claim a raise never happens — there is nothing to raise to — so
the file is never written; a replacement is still announced.)
In every case record in state.md the number R of the last round whose wave actually ran (R = r after (c)–(d)
complete; when the loop is left at round r before its wave, R = r−1; R = 0 if no wave ever ran). The DRAFT BRIEF
needs it.
**(c) Wave.** Run the wave of the round's query files (see Rules: one worker per file — `math-proof-worker` in rounds
before ESC_ROUND, `math-proof-worker-deep` from round ESC_ROUND on —, all in one message, the script's `answers` verdicts, index lines, one
re-run of the queries not answered, then the FLOOR stop rule).
**(d) Screen (no launch).** There is no separate screening step: the next round's plan judge screens this wave's
answers itself (PLAN BRIEF, item 0) and writes DIR/judge/screen_r{r}.md; step (b) of the next round copies its
verdicts into the index. Update state.md ("phase: round {r+1} plan, attempt 1"; R = r) and continue the loop.

## The proof tail (after the loop ends, by CONCLUDE, TAIL, or finishing round MAX_ROUNDS)
First fix the tail's shape: run `SCRIPT gate DIR`. If its output begins `CONCLUDE`, the claims ledger holds the
headline goal settled and certified by two separate verify queries, and the tail is SHORT: (e) draft, (f) no refine step, no select step — build DIR/r3_verify.md yourself by the shell concatenation described under (g) and
write no r3_q files —, (h) a commit wave consisting of DIR/r3_verify.md alone, (i) finalize. If it prints
anything else (normally `REJECT: …`), the tail is FULL: steps (e)–(i) exactly as written below — except that a line
beginning `ERROR:` means the gate command itself was malformed (DIR first, as an absolute path): correct it and run
it again before deciding. Record "tail: short" or "tail: full" and
the gate's line in state.md. Two fallbacks guard the short tail. If its verify-only wave ends, after the one re-run, with no
DIR/r3_verify.answer.md, switch to the FULL tail from (g) on (note "tail: short, then full — no verify answer"). And if the
FIRST finalize reply of the short tail begins "MAIN CLAIM: NOT PROVED" (check this before the stand-alone grep check of
step (i)), the certified chain did not survive the verify query — note "tail: short, then full" in state.md,
rename DIR/r3_verify.md and (if it exists) DIR/r3_verify.answer.md to DIR/r3_verify.first.md / DIR/r3_verify.first.answer.md,
and likewise any DIR/r3_verify.partial.md to DIR/r3_verify.first.partial.md (appending " | renamed r3_verify.first" to the r3_verify index line), and run (g), (h) and (i) once more as in the FULL tail (the select judge then sees the finalize judge's proof.md
and, by the name in the index, the first verify report); this fallback applies at most once, and the second pass carries
(i) to the end whatever its reply's first line says.
**(e) Draft.** One `math-proof-judge` with the DRAFT BRIEF ({R} from state.md; {PARTIALS} is the text given after the
DRAFT BRIEF when the tail is FULL and R ≥ ESC_ROUND, and empty otherwise — SHORT tail, or R < ESC_ROUND; if R = 0 replace the brief's "final round's
results" clause by "(no wave completed before the rounds ended — work from the summary and ledger)") →
DIR/proof.md. The extra-query rule applies (see Rules; that relaunch, if it happens, is part of this step). If
DIR/proof.md does not exist once the step is over, launch the draft judge one more time with the added first
paragraph "DIR/proof.md was not written; write it now from the material named below."; if it still does not
exist, stop and report.
**(f) Refine**, REFINE_STEPS times in the FULL tail (step names refine_2, refine_3, … in order, REFINE_STEPS of them), not at all in the SHORT
tail: one `math-proof-judge` each with the REFINE BRIEF (extra-query rule applies, once per step).
**(g) Select.** One `math-proof-judge` with the SELECT BRIEF → up to MAX_COMMIT files DIR/r3_q{k}.md and exactly one
DIR/r3_verify.md. If DIR/r3_verify.md does not exist afterwards, create it with the shell, without retyping
anything, as the concatenation of: the lines "The document below is a draft proof. Check the argument step by
step: for every inequality, interchange, cited result, and 'it follows that', ask whether it actually follows
as written. List every error or gap in order of severity, and say explicitly whether the main claim is
proved.", a blank line, the line "## The draft proof", a blank line, and the file DIR/proof.md.
**(h) Commit wave.** Run every DIR/r3_q{k}.md (there are none in the SHORT tail) plus DIR/r3_verify.md as one
wave (no screen step for this wave).
**(i) Finalize.** One `math-proof-judge` with the FINALIZE BRIEF ({PARTIALS_FIN}: the text given after the FINALIZE BRIEF
when the tail is FULL and R ≥ ESC_ROUND, empty otherwise) → the final DIR/proof.md. Then the stand-alone
check: run `grep -noE 'r[0-9]+_q[0-9]+|round[0-9]+_q[0-9]+|extra_q[0-9]+|r3_verify|[A-Za-z0-9_]+\.answer\.md|[A-Za-z0-9_]*summary\.md|synthesis\.md|ledger\.md|notes\.md|index\.md' DIR/proof.md || true`
(plain file handling; you are not reading the mathematics; no output means proof.md is clean). If it prints anything, proof.md still points at run
files a referee cannot open: launch the finalize judge ONCE more with the FINALIZE BRIEF preceded by the added
first paragraph "DIR/proof.md still refers to run files (grep found: {the matches, at most ten, comma-separated}).
A referee reads proof.md alone and cannot open them. Rewrite DIR/proof.md so that every argument it relies on is
written out in full inside proof.md itself, with no reference to any file in this directory.", note
"standalone-check: resent" in state.md, and accept whatever proof.md that launch leaves (do not repeat the check).
Update state.md ("phase: finished"). Reply to the user with: where proof.md is,
how many rounds ran and why the loop ended (the script's verdict line), how many worker queries ran, how
many were answered and how many ended partial, whether the goal was ever replaced or raised (one line, from
state.md; if DIR/result-so-far.md exists, say that it holds the earlier result as the worker wrote it, checked
only as far as the goal-change line recorded, and that proof.md and its Status section supersede it), and the judge's Status paragraph from its finalize reply, quoted. Do not
restate or assess the mathematics yourself.

## Rules that hold throughout
- Every judge step and every worker is a NEW subagent launch (the Agent tool) with `subagent_type` set
  explicitly; never omit it. The sub-agents ship with this plugin and your agent list normally shows them under
  plugin-scoped names — `math-proof:math-proof-judge`, `math-proof:math-proof-worker`, `math-proof:math-proof-worker-deep`.
  Decide the name seat by seat: for each of the three, use the bare name (`math-proof-judge`, `math-proof-worker`,
  `math-proof-worker-deep`) if your agent list offers it, otherwise the scoped name; mixing the two forms is fine (a
  bare-named copy in the user's or the project's agents directory is how a user changes that one seat's settings,
  and is meant to win). If one of the three is listed under neither name, tell the user that the math-proof
  plugin's sub-agents are not in this session's agent list — open `/plugin` to check that math-proof is installed
  and enabled, restart Claude Code, and give the same /math-proof:siege line again — and stop before round 1.
  Record in state.md the name used for each seat. Judge steps use `math-proof-judge`. Workers — round waves and their re-runs — use `math-proof-worker` in rounds
  before ESC_ROUND and `math-proof-worker-deep` in round ESC_ROUND and every later round; the workers of the proof
  tail (extra-query waves, the commit wave, r3_verify) use `math-proof-worker-deep` if a wave ran in round ESC_ROUND
  or later (R ≥ ESC_ROUND in state.md) and `math-proof-worker` otherwise. The choice is purely by round number, never
  by your own view of how the attempt is going. Never reuse, resume or send a message to an earlier subagent.
  Do not pass a `model` to the Agent tool: judges and workers run on this session's model.
  Launch a whole wave in ONE message so the workers run in parallel; never run a subagent in the background.
- In every brief and worker prompt below, DIR stands for the run directory's absolute path and the other
  {bracketed} slots for the values named; substitute them and send the text otherwise VERBATIM. Do not add
  encouragement, hints, opinions about the problem, deadlines, or summaries of results to any brief or prompt.
- One fixed addition to EVERY `math-proof-judge` launch: after the brief, append a blank line,
  the line "Problem statement (for reference — DIR/problem.md is the authoritative text; go by the file wherever
  this copy differs or looks garbled):" and then the complete contents of DIR/problem.md, byte for byte (you read
  it during setup). It is reference material so the judge's first request already contains
  the problem; it changes no instruction in the brief, and the briefs' rule that the judge must not copy the
  problem statement into query files still stands; DIR/problem.md, which every brief names, remains the authoritative
  text. (Worker prompts carry the same text, in the fixed form given below.) Paste it exactly: copy the text you
  read from DIR/problem.md character for character, never from memory and never retyped.
- You never write or edit query files, answer files (finished or partial), summaries, ledger files, notes.md or
  proof.md yourself. The only files you write are state.md, index.md, the problem copy, the fallback r3_verify.md
  and result-so-far.md (both by copying or concatenation only); beyond that you only copy or move files where a
  step says so (cp/mv: summary.md, and the r3_verify.first renames in the proof tail). You do not read answer files beyond confirming they exist (`test -s`);
  which of them are finished is decided by the bookkeeping script (`SCRIPT answers`, below), never by you.
- Worker prompts are always exactly this, with {Q} the query file stem (for example round2_q3, extra_q1,
  r3_q2, r3_verify), {PROBLEM} the complete contents of DIR/problem.md, byte for byte, and {EARLIER} an empty
  line — except when launching a query that this wave's latest `answers` run reported "partial", where {EARLIER} is the paragraph
  given after this prompt, with an empty line before it and after it:
  "Task file: DIR/{Q}.md — read it first; the task concerns the problem stated below (DIR/problem.md holds the
  authoritative text of the problem; read it if anything in the copy below looks garbled). Write your answer to
  DIR/{Q}.answer.md as you go, and when you have finished, whatever the outcome, make the file's last line this
  end line, exactly:
  === END OF ANSWER {Q} ===
  {EARLIER}
  Problem statement (verbatim, for reference):
  {PROBLEM}"
  {EARLIER}, when not empty, is exactly: "An earlier worker's attempt at this task was cut off part-way; its
  unfinished answer is DIR/{Q}.partial.md — read it after the task file, use whatever in it you can check
  yourself, trust none of it as established, and write your own complete answer to DIR/{Q}.answer.md, ending
  with the end line above."
  The end line is how a finished answer is told from one a worker was cut off in the middle of (by a usage
  limit, an error or its turn limit); the bookkeeping script checks for it, you never do.
- Running a wave of query files means: launch one worker of the type this wave uses (`math-proof-worker` or
  `math-proof-worker-deep`, see the first rule) per file, all in one message. When all have returned — never earlier: a worker still running is still
  writing its file — run `SCRIPT answers DIR {Q1} {Q2} …` with the stems of the wave's query files, as a
  command on its own, and read what it prints before you write any index line or launch anything. It decides,
  without your reading anything, which answer files are finished, and prints one line per query — "{Q}: answered" (DIR/{Q}.answer.md ends with that query's end line: its worker
  finished it), "{Q}: partial" (a worker wrote something but never finished; the script has moved that
  unfinished file to DIR/{Q}.partial.md, so that a .answer.md file always means a finished answer) or "{Q}: no
  answer" — and then a line "TOTAL (n queries): …" with the three counts (if it prints an ERROR line instead,
  it is safe to correct the command — DIR first, then stems such as round2_q1 — and run it again).
  Append to DIR/index.md ONE line per query: "{Q} | answered | ", "{Q} | partial | " or "{Q} | no answer | "
  as the script said, followed by the first 300 characters of the worker's reply to you (its abstract — not the
  answer file's contents), with newlines replaced by spaces so the entry stays on a single line. Then, if — and
  only if — some query of the wave is not answered, relaunch a fresh worker for each such query (once, all in
  one message; launch nothing for answered queries; a partial query's prompt carries the {EARLIER} paragraph,
  which hands the new worker the unfinished file), and when they have all returned run `SCRIPT answers` again
  with ALL the wave's stems (answered queries are unaffected), and append to the existing index line of each re-run
  query (with the Edit tool; no second line for the query)
  " | re-run: answered | ", " | re-run: partial | " or " | re-run: no answer | "
  as it now reports, followed by the first 300 characters of the new worker's reply as before (a query cut off twice stays partial; the script keeps the
  longer of its two unfinished files as DIR/{Q}.partial.md and the other beside it as DIR/{Q}.partial.prev.md).
  So an index line reads "{Q} | status | abstract", sometimes followed by " | re-run: status | abstract", and
  the re-run's status, when there is one, is the one in force; the plan, draft, refine and finalize briefs tell
  the judges what a partial file is. Never launch a worker for a query
  between a worker's return and the `answers` run that accounts for it. Note the TOTAL line of the last `answers` run for the wave — the one
  over all its stems, so its count n equals the wave's size: the FLOOR rule below and state.md use it.
- No user will answer you during this session: never end your turn to ask how to proceed, never wait for confirmation, and
  never stop early because something went wrong — decide by these rules and keep going until the protocol is
  finished or a rule below says to stop. A subagent that returns an error, an interrupted result or an empty
  reply is recorded in index.md / state.md and the protocol carries on; one lost worker is normal; a judge step
  that comes back errored or interrupted is relaunched once immediately. If the same judge step fails (errors out, or writes none of its files) twice in a
  row, stop and report where things stand. If, once a round's wave has ended after its one re-run,
  answered + partial on that last TOTAL line is smaller than the FLOOR number the script printed with its WAVE
  verdict (screening verdicts do not count against this), stop and report: something systematic is wrong and
  continuing would only spend judge steps on nothing — tell the user the likeliest cause is a usage limit or an
  outage that cut the workers off, that the run's files are intact, and that giving the same /math-proof:siege line
  again in this directory resumes the run once the cause has cleared. (If that TOTAL line's n is smaller than the wave, you ran
  `answers` on only some stems — run it on all of them first.) The extra-query and commit waves have no floor.
- Extra queries: when a draft or refine brief allows it, the judge may write up to 3 files named
  DIR/extra_q{k}.md using the next unused numbers k; the whole run has a budget of 10 (once DIR/extra_q10.md
  exists, no more may be written — the briefs say so). When a judge's reply says it wrote extra query files,
  confirm they exist, run them as a wave (their answers land in DIR/extra_q{k}.answer.md, or in
  DIR/extra_q{k}.partial.md for one cut off twice — the index says which), then relaunch that same step ONCE
  with this added first paragraph: "Your extra queries have been answered: read DIR/extra_q*.answer.md (the
  index says which exist). Finish the step now; do not write further extra queries in this step." A second
  batch of extra files from the relaunched step is left on disk unanswered.
- Rewrite DIR/state.md after every step: protocol, settings, current phase, attempt counters, and a growing
  one-line-per-step log; each round's plan line also records the wave cap passed to the check command and each
  wave's line the worker type launched and the last TOTAL line (e.g. "cap 10, math-proof-worker-deep ×9, answered 8,
  partial 1, no answer 0"). It is your only memory if this conversation is ever compacted; if you find yourself
  unsure where you are, read state.md and ${CLAUDE_SKILL_DIR}/SKILL.md again.

## PLAN BRIEF (round {r} of at most {MAX_ROUNDS}; {CAP}, {HORIZON}, {CONCLUDE_RULE}, {ESC_SUMMARY} and {ESC_WAVE} depend on r, see (a) and below)
> Step: plan round {r} of at most {MAX_ROUNDS}.{HORIZON} Files: the problem is DIR/problem.md; your running notes are
> DIR/notes.md; the running summary from the previous round is DIR/summary.md (absent in round 1); the claims
> ledger is DIR/ledger.md (absent or empty until something is recorded); the previous round's results are the
> files DIR/round{r-1}_q*.answer.md whose line in DIR/index.md gives the status "answered" (each line reads
> "query | status | abstract", sometimes followed by "| re-run: status | abstract", and then the re-run's
> status is the one that holds; none in round 1), plus DIR/extra_q*.answer.md if any exist. A query whose
> status is "partial" has instead a file DIR/round{r-1}_q{k}.partial.md: the notes of an engine that was cut
> off part-way. Read it too, for leads and for material to build new queries on, but nothing in it is
> established — it can prompt an OPEN line or a query, never by itself a PROVED line (one exception: if it
> holds a complete written proof or refutation of the [GOAL] claim, or of an earlier goal, since raised, that
> the audit rule below still covers, that proof counts as "in hand" for the audit rule exactly as if the file were
> finished — you also write the settled [GOAL] line that the audit and conclusion rules call for, with that
> query's stem (e.g. round3_q2) as its locator — and the verify queries then decide).
> (Every finished result file ends with a bookkeeping line "=== END OF ANSWER … ===": it is not part of the
> mathematics; leave it out of anything you splice or quote.) Read the problem, your notes, the summary, the
> ledger and the index first, then the previous round's result files — each file once, in full.
>
> 0. Screen first (rounds 2 and later). As you read the previous round's result files, check that each is a
> genuine attempt at its query — not a refusal, an empty or near-empty file, off-topic text, or work on a
> different problem. Write DIR/judge/screen_r{r-1}.md with one line per query of that round, exactly
> "round{r-1}_q{k}: OK" or "round{r-1}_q{k}: DEGENERATE: one-line reason" ("DEGENERATE: no answer" for a query
> whose status is no answer; a partial query's .partial.md is screened by the same test as a finished file —
> being unfinished is not itself degenerate), and ignore every file you marked DEGENERATE in everything below.
> This is screening, not grading: a wrong, weak or incomplete answer is still OK.
>
> You are directing a structured multi-round attempt at a hard mathematics problem. Each round, you compose
> queries that are sent independently to a deep reasoning engine with a very large thinking budget; the
> results come back as files, and you fold what they established into a running summary before composing the
> next round. This is round {r} of at most {MAX_ROUNDS}.{HORIZON} {CONCLUDE_RULE}
>
> Do these three things, in order.
>
> 1. Update the running summary. Rewrite it from scratch into DIR/round{r}_summary.md: it REPLACES the
> previous summary and is the only memory later rounds (and the final proof assembly) have of what came
> before, so carry forward everything still relevant. Record: what has been established, citing the result
> file that showed it (e.g. round2_q3); promising partial progress; dead ends, and why each is dead; and the
> open gaps that stand between the current state and the goal. Be honest — an overclaimed summary poisons
> every later round. Keep it under 6000 words. Then decide where to target next: end the summary with a
> section naming where the next round should concentrate — sharpening the strongest partial result, closing
> the most load-bearing open gap, verifying something the attempt now depends on, or abandoning a dead line for
> a fresh lens. Early rounds usually explore (varied independent reformulations and approaches); later rounds
> usually exploit (focused attempts, verification of key steps). The choice is yours each round.{ESC_SUMMARY}
>
> 2. Update the claims ledger. Alongside the summary, the run keeps a numbered ledger of claims, each marked
> PROVED, REFUTED, or OPEN. Unlike the summary, the ledger is never rewritten: the lines you write now are
> APPENDED verbatim (the numbering is added for you), and an existing entry is removed from force only by
> appending an explicit RETRACT line naming its number. Write DIR/round{r}_ledger_block.md containing ONLY this
> round's new lines, one per line, each of the form "PROVED: one-sentence claim — locator", "REFUTED:
> one-sentence claim — locator", "OPEN: one-sentence claim — locator" (locator = the result file stem, e.g.
> round2_q3), or "RETRACT 4: one-sentence reason entry 4 no longer stands". Append a line for every
> load-bearing claim this round settled or opened, a new line for any claim whose status changed (the newest
> line for a claim supersedes older ones), and a RETRACT line for anything now known wrong. Keep lines to one
> sentence: the full ledger is carried verbatim into every later round and into the final proof assembly — it
> is the one memory of this attempt that cannot fold away. Tag the line that states the headline goal with
> [GOAL] right after the status word ("PROVED: [GOAL] …", "OPEN: [GOAL] …"), and tag with [AUDIT] a PROVED
> line recording that a separate verify query checked a complete written proof chain (name that query's
> locator and cite the entry it certifies as "entry N" or "#N"). Tag lines as they arise. In round 1 write
> exactly one [GOAL] line. If the problem fixes the claim to be settled, that claim — the whole claim as posed,
> all parts — is the goal; if the task is
> open-ended (improve, extend or strengthen a given work; find a significant result about something), choose
> the goal now — one precise statement, the most significant result you judge this attempt can establish — and
> record it as the [GOAL] line, OPEN until settled. (i) Status lines. Write a further [GOAL] line for the same
> claim only when its status changes (OPEN → PROVED or REFUTED, or back to OPEN when a verify query finds a
> gap — then also RETRACT the PROVED line) — and then in the very round whose result files first contain the
> complete written proof, so that the verify queries you compose in the same step certify a line that is
> already numbered when their answers return — or to come back to it under (iv) below; never merely to re-word
> it, since only the newest [GOAL] line counts, and an [AUDIT] line must cite by number the [GOAL] entry it
> certifies, which is the newest one when the goal has not moved since (lines in your block are numbered on from
> the last entry of DIR/ledger.md, in file order). (ii) Changing the goal. The goal is not fixed: at any later plan step you may set a new goal by writing a new OPEN [GOAL] line, which is the
> goal from then on (this is no reason to aim low in round 1: choose the round-1 goal exactly as above);
> throughout this brief, "the [GOAL] line" and "the [GOAL] claim" mean the newest [GOAL] line in force and its
> claim. There are two reasons to set a new goal. Replace the goal (RETRACT the old [GOAL] line — if it was
> PROVED and the proof stands, re-enter what it proved as an ordinary untagged PROVED line — then write the new
> one) if it turned out false, ill-posed or already known, and also if you find it is narrower than, or
> different from, the claim the problem itself poses — then the posed claim is the new goal (a replacement, not
> a raise, even when the narrower goal was already PROVED: on a problem that fixes its claim the run's verdict is
> about that claim); for a goal you chose yourself in round 1 on an open-ended task, a refutation means replace it and continue (for a goal you raised to, see (iii)), and a
> REFUTED [GOAL] line ends the run only when the problem itself posed that claim. Or raise the goal: once the
> current goal is PROVED, if a more significant result now looks within reach of the rounds that remain — a
> stronger statement, or the general case of what was proved — write the new statement as an OPEN [GOAL] line
> (locator roundN_plan, N being this round's number), held to the same standard as the round-1 choice (one
> precise statement that you judge this attempt can establish, not one that as far as you can tell is false,
> ill-posed or already known). A raise is always an OPEN line: never write as a PROVED [GOAL] line a claim
> stronger than what the result files actually prove. When the problem itself posed the claim and it is proved
> as posed, there is nothing to raise to: conclude. (iii) What a raise leaves in place. When you raise, do not retract the proved goal or its
> [AUDIT] lines: they stay in force as ordinary entries, and that result is what the final document presents if
> the raised goal is not reached. If instead a verify query finds a gap in the proof of the goal you raised away
> from, RETRACT its PROVED [GOAL] line — never leave in force a PROVED [GOAL] line whose proof has failed its
> check — and decide afresh under (ii) which statement is the goal (to return to the earlier one, write it as the
> newest OPEN [GOAL] line and aim the wave at the gap). A REFUTED raised goal is not the run's verdict, and its
> refutation needs no verify queries (the audit rule below is for a goal the run may conclude on): record it as a
> "REFUTED: [GOAL] …" line naming the refuting file, then re-state the goal you proved below it, as (iv)
> describes, and conclude on that. Raising is a judgment, not a duty: if nothing clearly more significant looks
> within reach, conclude on the proved goal under the rule on concluding given earlier in this brief; and if the
> first two waves aimed at a raised goal (the raising round's own wave is the first) leave it no nearer — no
> proof of it, and no new route to one — then at the next plan step come back to the goal already proved and
> conclude. Coming back takes precedence over the summary's chain and progress rules and the escalation rule
> below, which direct a wave at a stalled statement only while it stays the goal: a step that comes back
> composes no queries other than any verify queries the audit rule still requires for the goal it returns to (one audit wave, then
> conclude). Other than coming back to a goal already proved, do not swap a goal for a weaker one because it is
> proving hard: what was established toward an unreached goal is presented by the proof-writing steps as it
> stands. Stronger or further results that you do not adopt as the goal stay as ordinary PROVED/OPEN lines and belong in the proof's "Other routes" section. (iv) Coming back. To come back to
> a goal proved earlier (the raised statement did not yield), re-state it in this round's block as a "PROVED:
> [GOAL] …" line citing its earlier entry as "entry N" or "#N", placed after any other [GOAL] line the block
> holds so that it is the newest (lines are numbered in file order), and below it re-state its certifications as
> [AUDIT] lines, each naming its verify query's locator as before and citing the new line's number in the same
> form (count it: if DIR/ledger.md ends at entry 23 and the re-stated goal is the second line of your block, it
> is entry 25) — one such line suffices when the re-stated goal line cites the earlier entry, otherwise two, from
> separate queries; then conclude under the rule on concluding. Leave the file empty if no claim was settled,
> opened, changed, or retracted.
>
> 3. Compose the next round's queries — or conclude. If and only if the material in hand fully establishes
> the goal, write DIR/round{r}_DONE.md containing one line naming where the material establishes it, and write
> no queries (if you raise the goal in this step, compose a wave for it instead — never write
> DIR/round{r}_DONE.md in the same step as a raise). Otherwise write between 1 and {CAP} query files DIR/round{r}_q1.md, DIR/round{r}_q2.md, …
> (consecutive numbers) aimed at the target you chose. While the [GOAL] line is OPEN, parallel queries are
> cheap and independent, so prefer using most of the budget; make them genuinely different attempts at the
> target, not rewordings of one attempt. Once a complete written proof (or refutation) of the [GOAL] claim is in
> hand, the wave shrinks: compose the verify queries the audit rule below requires plus at most 2 others, aimed
> at what the final proof document will need (a corollary's full write-up, the proof of a lemma that was only
> cited, an independent second proof). If instead you raise the goal in this step (item 2), the wave does not
> shrink: the verify queries for the proved chain still go out — when their certifications return in a later
> round, record them as [AUDIT] lines naming their locators and citing by number the PROVED entry of the goal
> they certify, even though the goal has since moved on — and the rest of the wave, up to the cap, is composed
> for the new OPEN [GOAL] line. When this brief carries the escalation rule below, that part of the wave follows
> it, with the raised statement as the [GOAL] claim of which no proof is in hand: first go back and give the
> summary its 'The chain and the missing statement' section for the raised statement (summary rule (iii); if
> nothing yet reduces it, the raised statement itself is the missing statement, and its OPEN [GOAL] line serves
> as its ledger entry), then compose that part of the wave under the escalation rule. Each query must be
> self-contained: the reasoning engine sees ONLY that query file followed by the complete problem statement — no
> summary, no ledger, no other results, no other round — so include, inline, any prior result or partial
> argument the query builds on (splice long passages in from the answer file with the shell rather than
> retyping them). Do NOT copy the problem statement itself into any query.
> Targeting rule (applies every round). Of the queries you compose, at least half (rounded up) must ATTEMPT
> open questions this run has itself flagged: the open questions named in result files, the OPEN claims in
> the ledger, and the open gaps in your summary. Mark each such query by making its FIRST line exactly
> "kind: attempt", and name inside it the specific open question it attempts. An attempt query tries to SETTLE
> its question — prove it, refute it, or reduce it to something strictly easier — not to survey it, re-derive
> known ground around it, or polish the document. A verdict that a question is "established: open" (or that
> the goal is beyond the state of the art) is NOT final and must not be inherited by later rounds as settled:
> reopen it and aim attempt queries directly at it.
> Audit rule (applies every round). Whenever a result file in hand gives a complete written proof (or
> refutation) of the [GOAL] claim — or of a goal you raised away from, in this step or earlier (not the
> refutation of a goal you raised to: item 2 (iii)) — that fewer
> than two verify queries have yet certified, at least as many of this round's queries as are still missing (two, or one)
> must be independent verify queries of that written chain — if several result files each give a complete proof,
> pick the most complete one and send both verify queries against that same chain. Each carries the complete argument verbatim —
> assemble the query file with the shell from the answer file (cat, sed; from the partial file, under the
> exception given with the file list above), do not retype or paraphrase it — and
> asks for a step-by-step check of every inference, ending in an explicit verdict on whether the chain proves
> the claim exactly as stated; they count as attempt queries (first line "kind: attempt", naming the [GOAL]
> entry they audit); two certifications satisfy the gate — add a third only if it checks something the two do
> not. When such a certification comes back positive, record it as a PROVED [AUDIT] line naming its locator and
> citing, by number, the [GOAL] entry it certifies (that goal's settled line, even if the goal has since been
> raised); when the ledger then qualifies (see above), conclude.{ESC_WAVE}
> Retrieval rule. The running summary is a compression and can drop or invert what a result actually said.
> Whenever you rely on or contradict a prior result — in the summary rewrite, in a ledger line, in your target
> choice, or in a decision to conclude — first read that result's answer file and work from what it actually
> says, not from the summary's paraphrase of it.
>
> Finally rewrite DIR/notes.md, and reply in under 150 words: concluded or not, how many query files and how
> many of them are attempt queries, and the target in one sentence. If you replaced, raised or came back to a
> goal this round (item 2), add one more sentence, not counted in the 150 words, beginning "Goal change:" —
> which of the three, what the goal was and what it is now (each in a short phrase), and the result already
> proved if one stands, with its ledger entry number and how many verify queries have certified it so far; for a
> raise, also name by full path the answer file or files that hold that result's complete proof (form: "Goal
> change: raised — entry N, proved in DIR/roundK_qJ.answer.md (certified by M verify queries so far), is …; the
> goal is now …").

{CONCLUDE_RULE} is, when r < MIN_ROUNDS, exactly: "You may conclude in this round, before round {MIN_ROUNDS},
as soon as the claims ledger holds the headline goal settled — a PROVED or REFUTED line tagged [GOAL] ("PROVED:
[GOAL] …") — and at least two PROVED lines tagged [AUDIT]. Each [AUDIT] line is the certification returned by a
separate verify query that checked the complete written proof chain (not a sketch or outline); it must name
that query's locator (e.g. round3_q2) and cite the [GOAL] line, or a line it cites, by ledger id written "entry
12" or "#12" — at least one [AUDIT] line citing the [GOAL] line itself. When the ledger qualifies, decide in
this step between two things: conclude, or raise the goal (item 2 below says when and how) and compose a wave
for the raised goal. Do not run further waves merely to reach round {MIN_ROUNDS} or to polish — the
proof-writing steps that follow do the polishing. Tag lines as they arise. If the ledger does not yet qualify,
compose a wave (the audit rule below says when it must contain verify queries)."
— and when r ≥ MIN_ROUNDS it is exactly: "From this round on you may conclude whenever the material in hand
fully establishes the [GOAL] claim — except that if a complete written proof is in hand that fewer than two verify queries
have yet certified, the audit rule below still applies this round (one audit wave, then conclude) — and when such a proof is in hand,
this round's ledger block must already carry the [GOAL] line settled, written in the ledger's ordinary form
"PROVED: [GOAL] …" (or "REFUTED: [GOAL] …") with nothing between the status word and the tag — that it is not
yet certified needs no mark of its own, the [AUDIT] lines record certification —, in the same step that composes
its verify queries. Once the [GOAL] claim is established you either conclude (after its audit wave, where the
audit rule applies) or raise the goal (item 2 below; a raise need not wait for the audits), never both in one
step: a step that raises the goal writes no DONE file, since a raised goal is settled by a wave, not by concluding. If you raised the goal in an earlier round and
the raised statement has not yielded, you may conclude on the goal already proved, re-stating it as the newest
[GOAL] line as item 2 (iv) describes. In the final round, do that rather than letting the rounds simply run out."

{HORIZON} is empty when r ≤ MAX_ROUNDS−2; when r = MAX_ROUNDS−1 it is exactly: " So at most one further round
can run after this one." and when r = MAX_ROUNDS exactly: " So this is the final round: whatever its queries
return goes straight to the proof-writing steps, with no further round to act on it." (Note the leading space.
{MAX_ROUNDS} in the brief is the MAX_ROUNDS setting written as a number, every round.)

{ESC_SUMMARY} is empty when r < ESC_ROUND; when r ≥ ESC_ROUND it is exactly (leading space included):
" From this round on four further rules govern the summary; because rule (iii) asks you for mathematics of your
own, write the summary file with its carried-forward material and (i)–(ii) before working (iii) out, then extend
it — a message spent only thinking can be cut off and what was not written is lost. (i) Standing results: keep a
section of that name listing every PROVED ledger line that is a theorem about the problem in general (all parameters), an exact
reformulation or reduction of the [GOAL] claim to a named simpler or classical statement, or a complete
solution of a natural special case — each with its locator — even when it cannot by itself finish the goal;
never drop an entry from this section (mark it 'not on the current line' instead), because if the goal is not
reached the final document is built around these. (ii) Dead ends: a route is dead only by a precise statement
that was REFUTED and the result file that refuted it, and is recorded in exactly that form. One result file
reporting an obstruction, a failed search inside one ansatz or one candidate, or that a route reaches only part
of the goal, closes that candidate, not the route: list such routes under the open gaps as 'set aside, not
refuted', open to re-attack. (iii) The chain and the missing statement. First decide whether a complete written
proof or refutation of the [GOAL] claim is in hand. A result file that proves last round's missing statement
exactly as stated, when that chain needs nothing further, IS one: in that case record the [GOAL] line PROVED (or
REFUTED, for a disproof) in this round's ledger block, citing by number the entries the chain uses and naming the
new proof's locator, and compose the audit rule's verify queries so that they carry the WHOLE chain — the cited
entries' arguments and the new proof, each spliced from its answer file, joined by the chain's derivation exactly
as last round's summary states it. If a complete written proof or refutation is in hand, that way or any other,
skip the rest of (iii) and all of (iv). Otherwise the summary carries a section headed exactly 'The chain and the
missing statement', rewritten every round, with four labeled parts. Chain: the derivation by which the [GOAL]
claim (or its negation, when the line pursued is a disproof — then read 'proof of the missing statement' below
accordingly) follows from results already PROVED — cited by ledger
number, statements only — together with exactly ONE further statement not yet proved; write the derivation out
step by step, so that a reader holding the cited entries and a proof of that one statement would hold a complete
proof. If the material does not yet reduce the goal to a single statement, take as the missing statement the
strongest intermediate claim the main line needs next, and say in the chain what would still remain after it.
Missing statement: that one statement written out in full and self-contained — every quantifier, every object
defined, and every hypothesis of the problem it may use stated with it (a statement stripped of a hypothesis it
actually needs becomes false, and its refutation then discredits a sound line). It may carry hypotheses of its
own — a restriction to some of the objects or to part of the parameter range — only if the chain shows, citing
PROVED entries, that everything outside those hypotheses is already settled; a statement whose proof would still
leave some of the objects the problem admits unsettled is a special case, not the missing statement. Among
statements that would complete the chain prefer the simplest and most concrete. Enter it in the ledger as an
OPEN line (as locator write roundN_plan, N being this round's number) the first time you state it and whenever
its wording changes — and then also RETRACT the OPEN line of the wording it replaces — so that later rounds and
queries can refer to it. Why it should hold: your own sketch, in at most fifteen lines, of why you believe it and
by what kind of argument it could be proved — do this mathematics yourself: if you can see a candidate mechanism,
of whatever kind, that would give it, state it precisely; a conjecture of yours that the engines then prove or
refute is among the most useful things this step produces. Tried so far: one line per query already spent on
this statement or an earlier wording of it — locator, the approach it took, and what it yielded (a proof of a
special case, an equivalent reformulation, an obstruction, nothing); identical copies of one task share a line;
an approach so listed counts as tried. (iv) Progress test. Open the target section by saying whether the last two
rounds produced progress on the chain, counting as progress ONLY: a proof of the missing statement; a proof of the
[GOAL] claim; a new PROVED result that holds for every object the hypotheses admit and shortens the chain; or the
replacement of the missing statement by a strictly simpler one (simpler, not merely narrower), with the chain
re-derived. Settling a further part of the objects while the hard part of the missing statement stays open — so
that the statement merely narrows — or an equivalent reformulation of it, is recorded under (i) but is not
progress in this sense. If there was none, write 'main line stalled — no universal progress', say in one line
what in your sketch or decomposition differs from last round's, and do not respond by opening another special
case or by turning to other routes for breadth: the wave (unless item 2 (iii) now has you come back to a goal
already proved and conclude) goes to the missing statement itself under the Closing rule below, and what must change is your own sketch in (iii) — a different mechanism for the same statement, or
a different decomposition of the chain with a different missing statement. If a result file REFUTED the missing
statement exactly as stated, do not rescue it merely by excluding the counterexample's class (unless a PROVED
entry already settles that class, and the chain says so): either state a corrected missing statement and
re-derive the chain for it in full, or record the line as dead under (ii) and build the chain of the next most
promising line. From this round on, 'verifying' as a target means only the audit rule's goal audits and the one
chain check the Closing rule's item (c) allows."

{ESC_WAVE} is empty when r < ESC_ROUND; when r ≥ ESC_ROUND it is exactly (leading space included; {CAP} substituted
as elsewhere):
" Escalation rule (this round and every later one, for as long as no complete written proof or refutation of
the [GOAL] claim is in hand — once one is, including the case summary rule (iii) describes of a proved missing
statement that completes the chain, the audit rule and the shrunken wave above take over, and (a)–(c) below are
then ignored). The engines answering this round have a much larger thinking budget than those of the opening
rounds, and the wave may hold up to {CAP} queries: use most of it, and spend it on the missing statement of your
chain, stated in full — not on surveys, and not on breadth for its own sake. (a) Every query attacks: it attempts
the missing statement, the [GOAL] claim itself, or a question whose answer would settle or strictly reduce one of
them (settling it for part of the objects only is not a reduction). Do not spend queries on writing up,
polishing, re-deriving or verifying results that do not complete the [GOAL] chain — the proof-writing steps
after the rounds do that, with their own query budget — so the only verify queries in a round are the audit
rule's (the verify queries certifying a goal that was proved and then raised count as the audit rule's) and
the one chain check item (c) allows. Do not spend a query asking an engine to recall or reconstruct a
proof from the literature, of the [GOAL] claim or of anything else: the engines have no library to consult, and
such a task gives them nothing to reason with (invoking known theorems inside an attack is another matter, and
fine). (Only in the final two rounds — this brief's opening 'Step: plan round …' line will then say so
explicitly, in the words "one further round" or "the final round"; if it carries neither, this is not one of
them — up to two queries may instead verify, or write up in full, the standing results the final document will
present.) (b) Closing rule.
Write ONE task file that asks for a complete proof of exactly the missing statement of your chain — or else an
explicit counterexample to it — and that contains: the statement, verbatim as the summary states it; every prior
result it may rest on, spliced in full with its proof from the answer files (cat, sed — never paraphrased); the
chain's derivation of the [GOAL] from it, so that the engine sees what the statement is for and can say so if
that derivation is itself flawed; your sketch of why it should hold, offered as a suggestion the engine is free
to discard; and the explicit sentence that a proof of the statement for only some of the cases it covers — a
sub-class of its objects or a sub-range of its parameters — does not answer the question, though it should be
reported if it is all that was found. Save it as this round's query file q1 (the first of the files named above)
and copy it byte for byte (cp) to q2 and q3: three engines attempt the same statement independently —
independent attempts at one well-posed statement are worth more here than one attempt each at three statements.
These identical copies are intended (the instruction above against rewordings of one attempt does not apply to
them), and all three are attempt queries (first line 'kind: attempt', naming the missing statement as the open
question they attempt). (c) The remaining queries — use most of the cap — also go to the missing statement, each
self-contained (carrying the same splices unless said otherwise below), and each is either a further
byte-for-byte copy of the closing task (allowed: it is one more independent attempt) or genuinely different from
it: an attack by a named approach that does not appear under 'Tried so far' (name it in the task; the engine may
depart from it if it says why); or a listed approach continued from the partial result it returned, with that
result spliced in; or the hardest single step of your own sketch, cut out and posed as a self-contained claim; or
the one obstruction a result file raised against the statement, posed as the thing to overcome or to sharpen into
a counterexample. In the first round a missing statement is posed, and again whenever its wording has changed,
one of these queries instead tries to REFUTE it exactly as stated — by an explicit construction, or by deriving
from it something known to be false. When the same missing statement has already been attacked in two earlier
rounds, one of these queries is given only the statement and the cited entries' statements (no proofs, no
sketch), and is asked first to derive for itself that the statement would complete the [GOAL] and then to attack
it by a first move none of the listed attempts used — an engine that finds the derivation does not go through,
or the statement implausible, says so, and that is a result to act on under summary rule (iv). At most TWO
queries of the wave may go elsewhere: to routes the main line does not descend from (set aside, not refuted,
under summary rule (ii)), or —
at most one of them — to checking one PROVED step the chain rests on that no separate query has yet checked. All
of these are attempt queries (first line 'kind: attempt')."

## DRAFT BRIEF
> Step: proof draft. Files: the problem is DIR/problem.md; your running notes are DIR/notes.md; your running
> summary of everything the attempt established is DIR/summary.md; the claims ledger is DIR/ledger.md; the
> final round's results are the newest DIR/round{R}_q*.answer.md files marked answered and not DEGENERATE in
> DIR/index.md; every earlier round's result files and DIR/extra_q*.answer.md are there to consult by name (a
> DIR/…_q{k}.partial.md file, where the index marks a query partial, is the unfinished and unverified notes of
> an engine that was cut off: leads only, nothing in it is established; and the "=== END OF ANSWER … ===" line
> that closes each finished file is bookkeeping, not mathematics).
> Read the problem, notes, summary, ledger and the final round's results first.
>
> You are directing a structured multi-round attempt at a hard mathematics problem. The rounds have concluded.
> Your job now: write DIR/proof.md containing the strongest route to the goal — the most complete argument the
> attempt found — with its full argument spelled out,{PARTIALS} plus a short note on every other route worth recording,
> and an honest statement of anything that remains a gap — a clearly-marked gap is worth more than a
> papered-over one. If the newest [GOAL] line is not PROVED — or is PROVED but not certified by two [AUDIT]
> lines and its written proof does not survive your own check — and the ledger holds, in force, a PROVED [GOAL]
> line for a different claim (a goal that was reached and then raised; if several, the most recent), then that
> proved goal is proof.md's main claim. State it as the document's theorem and write its complete argument out
> in full from the result files the ledger names for it (where the file the ledger names is a .partial.md file,
> take the text from the verify query files that carried it and whose answers certified it); it is not one of the
> lesser results. The raised goal
> comes after it, as a statement that was attempted, with whatever was established toward it, and the Status
> section says which is which. Use python3 whenever a concrete computation would confirm or kill a step: check a
> candidate identity on examples, verify a constant, test a claimed counterexample numerically. Checking beats
> believing. If one or a few targeted deep-reasoning queries would settle a load-bearing point, you may write
> them as the next unused DIR/extra_q{k}.md files (at most 3 in this step; none once DIR/extra_q10.md exists),
> each self-contained — the engine sees only that file followed by the problem statement, so include inline
> whatever it builds on and do not copy the problem into it — and say in your reply that you did; they will be
> answered and you will be invoked once more. Write DIR/proof.md in this step regardless. Rewrite
> DIR/notes.md. Reply in under 150 words.

{PARTIALS} is empty in the SHORT tail and whenever R < ESC_ROUND; in the FULL tail with R ≥ ESC_ROUND it is
exactly (leading space included): " and — because
the newest [GOAL] line is not certified — also written out in full with their proofs, in the body (after the
theorem of an earlier proved goal, when the sentence below about a raised goal applies) and ahead of the statement
of what remains open: every PROVED result in the ledger or summary that settles a natural special case, gives an exact reformulation or reduction of the goal (state it as a theorem: 'the claim holds for all …
provided …'), or identifies the goal or its open core with a named known statement, the most general first —
for a goal the attempt did not settle, a referee judges it by the reductions and partial results it
actually establishes, so these are the document, not side notes;"

## REFINE BRIEF (step name {S} = refine_2, refine_3, … in order)
> Step: {S}. Files: the problem is DIR/problem.md; your running notes are DIR/notes.md; the current draft is
> DIR/proof.md; the result files are DIR/round*_q*.answer.md (every round's results) and DIR/extra_q*.answer.md,
> listed with their status in DIR/index.md (a query whose status there is "partial" has instead a
> DIR/…_q{k}.partial.md, the unfinished and unverified notes of an engine that was cut off: leads, not results;
> and the "=== END OF ANSWER … ===" line that closes each finished file is bookkeeping, not mathematics); the
> claims ledger is DIR/ledger.md and the running summary DIR/summary.md.
> Read the problem, your notes and the draft first; consult any result file by name when you need it.
>
> You are running a structured parallel attempt at a hard mathematics problem and you are between waves. Your
> job this step: make proof.md strictly better. Re-derive the weakest steps, hunt for errors as a hostile
> referee would, and use python3 to check every concrete computational claim you rely on. If one targeted
> deep-reasoning query would settle a load-bearing gap, you may write it as the next unused DIR/extra_q{k}.md
> (at most 3 in this step; none once DIR/extra_q10.md exists), self-contained — the engine sees only that file
> followed by the problem statement, so include inline whatever it builds on and do not copy the problem into
> it — and say in your reply that you did. Then rewrite DIR/proof.md in full, first saving the incoming draft as
> DIR/judge/{S}_previous_proof.md. Be honest about what remains a gap — a clearly-marked gap is worth more than
> a papered-over one. Rewrite DIR/notes.md. Reply in under 150 words.

## SELECT BRIEF
> Step: select routes for the commit wave. Files: the problem is DIR/problem.md; your running notes are
> DIR/notes.md; the draft proof is DIR/proof.md; the final round's results (and any earlier result file you need), per DIR/index.md (a query marked "partial" there has only unverified notes in a DIR/…_q{k}.partial.md, from an engine cut off part-way); the claims ledger DIR/ledger.md.
>
> You are running a structured parallel attempt at a hard mathematics problem; you have a draft proof document
> and the full results of the pursuit. Your job is the commit step of the protocol: any result with a concrete
> route (a named lemma chain, a specific construction) toward the goal gets a commit query at the full thinking
> budget: "Route: [the route]. Write the full rigorous proof." Plus one verify query that checks the draft
> proof's argument step by step. (If a goal was proved and a later, raised goal was not, the draft's main claim
> is the proved goal; concrete routes toward the raised goal may still be committed.)
> Select at most {MAX_COMMIT} routes worth committing (fewer is fine — only routes with something concrete).
> For each, write the query as DIR/r3_q1.md, DIR/r3_q2.md, …, with the route's actual content included (not a
> reference to it — the engine sees nothing but the query file followed by the problem statement). Do NOT copy
> the problem statement into any query. Also write exactly one DIR/r3_verify.md containing the complete
> current draft proof (copied in full from DIR/proof.md with the shell — cat —, not retyped) and asking for a step-by-step check: for every
> inequality, interchange, cited result and "it follows that", does it actually follow as written; list every
> error or gap in order of severity and say explicitly whether the main claim is proved.
> Use python3 if a quick computation would settle which routes are real. Rewrite DIR/notes.md. Reply in under
> 100 words with the list of files written.

## FINALIZE BRIEF
> Step: finalize. Files: the problem is DIR/problem.md; your running notes are DIR/notes.md; the draft proof
> that went into the commit wave is DIR/proof.md; the commit-wave results are DIR/r3_q*.answer.md and the
> verify query's report is DIR/r3_verify.answer.md (DIR/index.md says which exist; if none exist, finalize from
> the draft; a query the index marks "partial" has instead a DIR/r3_q{k}.partial.md or DIR/r3_verify.partial.md,
> the unfinished notes of an engine that was cut off — unverified, so a proof in one is a lead to check, not a
> result, and the gaps a cut-off verify report lists are still worth checking, though the absence of its final
> verdict tells you nothing either way; the "=== END OF ANSWER … ===" line closing each finished file is bookkeeping); the claims ledger is
> DIR/ledger.md. Read all of these.
>
> You are running a structured parallel attempt at a hard mathematics problem. The commit wave has returned.
> Your job is the final step of the protocol: assemble the final proof.md from the best commit result (or from
> the draft if no commit query produced better). Iterate: if the verify query found gaps, repair what is
> repairable from the material you have; use python3 to check every concrete computational claim you rely on.
> Be honest in the final document about anything that remains a gap — a clearly-marked gap is worth more than a
> papered-over one. The final document must state the problem's answer and give the complete argument, then a
> short section "Status" saying plainly whether the main claim is fully proved and listing anything that
> remains a gap, and a short section "Other routes" on anything else worth recording{PARTIALS_FIN}. If the
> newest [GOAL] line is not PROVED — or is PROVED but not certified by two [AUDIT] lines and its written proof
> does not survive the verify report and your repairs — and the ledger holds, in force, a PROVED [GOAL] line for
> a different claim (the goal was raised after being reached; if several, the most recent), then the main claim
> is that proved goal, stated and proved as the document's theorem, not presented as a lesser result. The raised
> goal is reported after it as attempted, not as a gap in the main claim, and the Status section says plainly
> which claim is the main claim and that the raised goal was not reached. proof.md is read on its
> own by a referee who cannot open any other file in this directory: never cite run files (r*_q*, extra_q*,
> *.answer.md, the verify report, notes, scripts) in it; write every relied-on argument out in full in
> proof.md, rewriting it from the worker files if needed. Save the incoming draft
> as DIR/judge/finalize_previous_proof.md first, then write the final DIR/proof.md. Rewrite DIR/notes.md. Reply
> in under 200 words: first a line beginning exactly "MAIN CLAIM: PROVED" or "MAIN CLAIM: NOT PROVED" (your
> Status section's verdict on proof.md's main claim as defined above; PROVED here means the document's main
> result — a proof, or a disproof, of that claim — is complete), then on the same line a dash and that main
> claim in one clause, then that Status paragraph.

{PARTIALS_FIN} is empty in the SHORT tail and whenever R < ESC_ROUND; in the FULL tail with R ≥ ESC_ROUND it is
exactly (leading space included): " (routes
only sketched or not pursued — whereas every PROVED reduction, reformulation or special case that bears on the
goal belongs in the body, written out in full, the most general first)"
