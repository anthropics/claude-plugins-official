#!/bin/sh
# claude-code-action starts this file as Claude Code and puts this folder on PATH, so the folder contains no other file.
# Says why no session was started, and stops. The reason also goes to the job summary, which renders Markdown, so each reason is fixed text.
refuse() {
  echo "claude-security: $1" >&2
  { printf '\n**The Claude Security plugin stopped:** %s\n' "$1" >> "$GITHUB_STEP_SUMMARY"; } 2> /dev/null
  exit 1
}
[ -n "${GITHUB_TOKEN-}" ] || refuse "found no GITHUB_TOKEN to take out of the session, so no session was started"
# The checks below look for the token in what the scan would get.
scan_token=$GITHUB_TOKEN
# ALL_INPUTS: claude-code-action's inputs as JSON, the token among them.
unset GITHUB_TOKEN GH_TOKEN OVERRIDE_GITHUB_TOKEN DEFAULT_WORKFLOW_TOKEN ALL_INPUTS
unset ACTIONS_RUNTIME_TOKEN ACTIONS_ID_TOKEN_REQUEST_TOKEN ACTIONS_ID_TOKEN_REQUEST_URL
# Claude Code keeps its files in a folder used only by this scan, which action.yml makes, instead of the runner's ~/.claude.
export CLAUDE_CONFIG_DIR="$RUNNER_TEMP/claude-security-work/home"
# Asks Claude Code to load no user, project or local CLAUDE.md, AGENTS.md or rules file, and to keep no auto memory, so that no instruction file that the scan writes is loaded.
export CLAUDE_CODE_DISABLE_CLAUDE_MDS=1 CLAUDE_CODE_DISABLE_AUTO_MEMORY=1
# Each Bash command of the main session starts in the checkout: a cd does not carry over to the next.
export CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR=1
# On the Claude API, with the job's own value here, the sandbox's relay would send the credential as a bearer token, and the session would get its stand-in under that name.
unset ANTHROPIC_AUTH_TOKEN
# Beside a bearer key on Bedrock the relay signs with no AWS key, so the job's keys stay out of it.
[ -z "${AWS_BEARER_TOKEN_BEDROCK-}" ] || unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
# With one of these set, the checks below would read other settings than git reads without it.
unset GIT_CONFIG GIT_CONFIG_GLOBAL GIT_CONFIG_SYSTEM GIT_CONFIG_PARAMETERS GIT_DIR GIT_COMMON_DIR GIT_WORK_TREE XDG_CONFIG_HOME
git remote set-url origin "$GITHUB_SERVER_URL/$GITHUB_REPOSITORY.git" ||
  refuse "git could not set the checkout's origin to the repository's plain address, so no session was started; the reason is in the log of the scan's step"
# git exits with 1 where no key matches. Any other failure must not count as no saved credential.
git config --get-regexp '^http\.(.*\.)?extraheader$' > /dev/null
case $? in
  0) refuse "git has a saved credential, so no session was started; remove it (for actions/checkout, set persist-credentials: false)" ;;
  1) ;;
  *) refuse "git could not read its settings, and the check for a saved credential needs them, so no session was started; the reason is in the log of the scan's step" ;;
esac
case "$(env) $* $(git config --list) $(cat "$RUNNER_TEMP/claude-security-token/token" 2> /dev/null)" in *"$scan_token"*)
  refuse "the job's token is still in the session's variables, arguments, git settings or model credential, so no session was started; look in the workflow's env:, in claude_args, in the key or token that the job gives this action and in git config --list" ;;
esac
# Claude Code loads no settings, hook, skill, agent, workflow or MCP server from the checkout. It takes the last --setting-sources.
set -- "$@" --setting-sources=user
# On a pull request, claude-code-action has put the base branch's copies of these paths in the checkout, and kept the pull request's in .claude-pr. The scan must read those in their places. A .git there is a note in a submodule's place, on which git would stop.
case ${GITHUB_EVENT_NAME-} in pull_request*)
  for path in .claude .claude.json .gitmodules .husky .mcp.json .ripgreprc AGENTS.md CLAUDE.local.md CLAUDE.md .claude-pr; do
    rm -rf -- "$path" && { [ ! -e ".claude-pr/$path" ] || { find ".claude-pr/$path" -name .git -delete && mv -- ".claude-pr/$path" .; }; } ||
      refuse "the pull request's copies of the files that claude-code-action replaces could not be put back, so no session was started; the reason is in the log of the scan's step"
  done ;;
esac
# The sandbox does not hide the checkout. Root searches it, because the job's user cannot read every file there. The token goes in on standard input, because other users can read a command line.
if ! printf %s "$scan_token" | sudo -n python3 -I -S "${0%/*}/../saved_credentials.py" "$PWD"; then
  refuse "the search of the checkout for a saved credential found a file that may hold one, or did not finish, so no session was started; the reason is in the log of the scan's step"
fi
# Asks Claude Code to run each Bash command of the session in this shell, which reads no startup file.
export CLAUDE_CODE_SHELL="${0%/*}/../shell/bash"
# action.yml stops the job after the scan step if this file is missing.
true > "$RUNNER_TEMP/claude-security-session-started"
# Each program on the line below becomes the next by exec: the sandbox lets only the process that it started call the relay.
# GIT_CONFIG_GLOBAL and PYTHONNOUSERSITE keep git and Python from running what a file in the sandbox's home names or holds.
# They are set on the inner command: the sandbox passes in only the names on its list, and here they replace any value that the job gives.
# CLAUDE_CODE_USE_COWORK_PLUGINS is empty here and in action.yml's --settings, so that the job cannot set it.
# CLAUDE_SECURITY_ROOT_ELSEWHERE lets the plugin's scripts run git outside the checkout: the reports, with each fix's workspace, lie under the runner's temp folder.
set -- "$RUNNER_TEMP/claude-security-work" -- env GIT_CONFIG_GLOBAL=/dev/null PYTHONNOUSERSITE=1 CLAUDE_CODE_USE_COWORK_PLUGINS= CLAUDE_SECURITY_ROOT_ELSEWHERE=1 sh -c 'cd "$1" && shift && exec "$@"' sh "$PWD" "$HOME/.local/bin/claude" "$@"
# On Bedrock the relay takes the credential from the variables.
# Elsewhere the relay reads the token file, and reads it again as the credential ages. A missing file stops the start, because with no command sandbox.py runs gcloud as root on Google Cloud.
# With ANTHROPIC_API_KEY set on the Claude API, the relay sends the file's text as x-api-key, not as a bearer token, so that variable keeps only action.yml's stand-in for an API key.
if [ "${CLAUDE_CODE_USE_BEDROCK-}" != 1 ]; then
  [ "${ANTHROPIC_API_KEY-}" = a-stand-in-for-an-api-key ] || unset ANTHROPIC_API_KEY
  set -- "--credential-command=/usr/bin/cat $RUNNER_TEMP/claude-security-token/token" "$@"
fi
exec python3 -I -S "${0%/*}/../scan_user.py" session "$RUNNER_TEMP/claude-security-firewall" -- "$@"
