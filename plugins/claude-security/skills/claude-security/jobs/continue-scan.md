# Continue a scan that stopped

Ask no question and make no new report directory. For the stop that you continue from, this recipe takes the place of your role's three choices: write a report only where it says so. If the call of step 7 fails or is stopped, that is a new stop, and your role's section applies.

1. Find the `args` and the Run ID of the scan's last `Workflow` call in this conversation, at the call or in the notice of its stop. If you cannot see both whole, say that you cannot see the scan here, that only the session that ran it can continue it, and that `claude --resume` reopens a closed session, and stop.
2. Read `scan-meta.json` in the call's `runDir`. If it is gone, say that nothing is left to continue, and stop.
3. If it holds a `revision.commit`, run `GIT_TERMINAL_PROMPT=0 git rev-parse HEAD` from the call's `scanRoot`, which reads the same git settings as the script that recorded the commit. When `pwd` does not print that folder, add `-C '<the call's scanRoot>'`; Claude Code may ask the user's approval there, which is expected. If git prints another commit, tell the user that commit, which commit was scanned, that `/claude-security continue the scan` works again once HEAD is that commit, and, if `runDir` holds `votes.json`, that the findings verified so far are kept until then, and stop. If git fails, tell the user what it printed and that `/claude-security continue the scan` works again once git can read the repository, and stop. If Claude Code refuses the git command, tell the user so, and that `/claude-security continue the scan` works again once they allow it, and stop. Never add a `safe.directory` entry, not even for one call: it makes git apply that owner's `.git/config`, which can run commands. Name it only with the words "if you trust that owner".
4. Read that scan's recipe again, beside this file: `scan-codebase.md` if the call's `mode` is `scan`, else `scan-changes.md`. Its wait, `save_result.py`, Delivery and delivery message apply from here. Its rule for a refused step 6 call does not.
5. If the call's result has arrived, go on from the recipe's `save_result.py` step, and skip steps 6 to 8.
6. If the notice of its stop said that safeguards stopped an agent, make no call, and end as "No way on" says.
7. Make the call again with the same `name` and `args`, and add `resumeFromRunId: "<its Run ID>"`. If the call's `mode` is not `scan`, and `pwd` does not print its `scanRoot`, hand on `gitFromCwd: false`: the agents' plain git would read another folder. Never pass `scriptPath`, though a notice offers it: that runs the session's copy of the script, not the plugin's own.
8. Wait for the result as the recipe says. If Claude Code refuses the call instead, follow none of the refusal's advice:
   - because the run is still running, stop nothing, and wait for its result in the same way;
   - because the run has not exited yet, tell the user to type the command again in a minute, and stop;
   - because the run's journal is not on disk, say what step 1 says, and stop;
   - because the user, the permission mode or the classifier did not allow it, remove nothing, say that the scan can still be continued once that call is allowed, and stop;
   - for any other reason, end as "No way on" says.

In every delivery message under this recipe, say that the duration includes any time the scan sat stopped.

If the scan's step 5 ran a `cd` into its `scanRoot` and the working folder now lies above that root, run that `cd` again, unless a `.claude/workflows` or `.claude/output-styles` entry, or a `.claude` that is a link, now stands in that root or a folder between: then name it, say that this command can go on here only once it is gone, and stop. Run it as a Bash call of its own before step 3. Before any stop after it, run the `cd` back.

## No way on

Tell the user in your own words why the scan cannot continue. If `runDir` holds `votes.json`, earlier runs are recorded: follow the recipe's Delivery for that run directory, and relay the render's line on the candidates that were left. If not, name the report directory and say that it holds no report.
