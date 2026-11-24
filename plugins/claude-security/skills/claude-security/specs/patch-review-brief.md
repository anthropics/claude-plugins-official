# The patch review's brief

Your dispatch names this file, and it is part of your dispatch.

**The one question:** what can an attacker do with this change in place that they should not be able to — a path the change opens, or the finding's own exploit still reachable by another route?

A pre-existing weakness unrelated to this finding is a matter for a scan, not an objection to this patch.

**What to report, as the last lines of your reply:** one numbered line for each concrete attack path you find (a route that you found closed is not one), `1 | <kind> | <the request and the code it reaches>`, and always a last line `PATHS: <how many>`. If you found none, your last line is `PATHS: 0`, with no numbered line above it. One exception: if the `STAGED` command is refused before the script runs, you have not seen the change, so give no `PATHS:` line, and say that the call was refused. `<kind>` is one word: `opened` for a path that the change opens, `still_reachable` for the finding's exploit by another route, or `set_aside` for one that is pre-existing and unrelated to the finding. Only these lines reach the user, so each concrete attack path that your reply tells of has its line, a `set_aside` one too. Name a credential by its file and line, never by its value.
