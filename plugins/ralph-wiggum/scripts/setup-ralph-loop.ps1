# Ralph Loop Setup Script (PowerShell version for Windows)
# Creates state file for in-session Ralph loop

param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

$MaxIterations = 0
$CompletionPromise = "null"
$PromptParts = @()

# Parse arguments
$i = 0
while ($i -lt $Arguments.Count) {
    $arg = $Arguments[$i]

    switch -Regex ($arg) {
        "^(-h|--help)$" {
            @"
Ralph Loop - Interactive self-referential development loop

USAGE:
  /ralph-loop [PROMPT...] [OPTIONS]

ARGUMENTS:
  PROMPT...    Initial prompt to start the loop (can be multiple words without quotes)

OPTIONS:
  --max-iterations <n>           Maximum iterations before auto-stop (default: unlimited)
  --completion-promise '<text>'  Promise phrase (USE QUOTES for multi-word)
  -h, --help                     Show this help message

DESCRIPTION:
  Starts a Ralph Wiggum loop in your CURRENT session. The stop hook prevents
  exit and feeds your output back as input until completion or iteration limit.

  To signal completion, you must output: <promise>YOUR_PHRASE</promise>

EXAMPLES:
  /ralph-loop Build a todo API --completion-promise 'DONE' --max-iterations 20
  /ralph-loop --max-iterations 10 Fix the auth bug
  /ralph-loop Refactor cache layer  (runs forever)
"@
            exit 0
        }
        "^--max-iterations$" {
            $i++
            if ($i -ge $Arguments.Count -or $Arguments[$i] -notmatch '^\d+$') {
                Write-Error "Error: --max-iterations requires a number argument"
                exit 1
            }
            $MaxIterations = [int]$Arguments[$i]
        }
        "^--completion-promise$" {
            $i++
            if ($i -ge $Arguments.Count) {
                Write-Error "Error: --completion-promise requires a text argument"
                exit 1
            }
            $CompletionPromise = $Arguments[$i]
        }
        default {
            $PromptParts += $arg
        }
    }
    $i++
}

$Prompt = $PromptParts -join " "

if ([string]::IsNullOrWhiteSpace($Prompt)) {
    Write-Error @"
Error: No prompt provided

Ralph needs a task description to work on.

Examples:
  /ralph-loop Build a REST API for todos
  /ralph-loop Fix the auth bug --max-iterations 20
"@
    exit 1
}

# Create .claude directory if it doesn't exist
$claudeDir = ".claude"
if (-not (Test-Path $claudeDir)) {
    New-Item -ItemType Directory -Path $claudeDir -Force | Out-Null
}

# Format completion promise for YAML
if ($CompletionPromise -ne "null") {
    $CompletionPromiseYaml = "`"$CompletionPromise`""
} else {
    $CompletionPromiseYaml = "null"
}

# Get current UTC timestamp
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

# Create state file
$stateContent = @"
---
active: true
iteration: 1
max_iterations: $MaxIterations
completion_promise: $CompletionPromiseYaml
started_at: "$timestamp"
---

$Prompt
"@

Set-Content -Path ".claude/ralph-loop.local.md" -Value $stateContent -NoNewline

# Output setup message
$maxIterDisplay = if ($MaxIterations -gt 0) { $MaxIterations } else { "unlimited" }
$promiseDisplay = if ($CompletionPromise -ne "null") { "$CompletionPromise (ONLY output when TRUE - do not lie!)" } else { "none (runs forever)" }

@"
Ralph loop activated in this session!

Iteration: 1
Max iterations: $maxIterDisplay
Completion promise: $promiseDisplay

The stop hook is now active. When you try to exit, the SAME PROMPT will be
fed back to you. You'll see your previous work in files, creating a
self-referential loop where you iteratively improve on the same task.

To monitor: Get-Content .claude/ralph-loop.local.md -Head 10

WARNING: This loop cannot be stopped manually! It will run infinitely
unless you set --max-iterations or --completion-promise.

$Prompt
"@
