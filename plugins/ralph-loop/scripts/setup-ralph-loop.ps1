# Ralph Loop Setup Script (PowerShell)
# Windows-native implementation for initializing Ralph loop state.
#
# Creates state file for in-session Ralph loop with YAML frontmatter.

param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

$ErrorActionPreference = "Stop"

# Parse arguments
$promptParts = @()
$maxIterations = 0
$completionPromise = "null"

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
  Starts a Ralph Loop in your CURRENT session. The stop hook prevents
  exit and feeds your output back as input until completion or iteration limit.

  To signal completion, you must output: <promise>YOUR_PHRASE</promise>

  Use this for:
  - Interactive iteration where you want to see progress
  - Tasks requiring self-correction and refinement
  - Learning how Ralph works

EXAMPLES:
  /ralph-loop Build a todo API --completion-promise 'DONE' --max-iterations 20
  /ralph-loop --max-iterations 10 Fix the auth bug
  /ralph-loop Refactor cache layer  (runs forever)
  /ralph-loop --completion-promise 'TASK COMPLETE' Create a REST API

STOPPING:
  Only by reaching --max-iterations or detecting --completion-promise
  No manual stop - Ralph runs infinitely by default!

MONITORING:
  # View current iteration:
  Select-String '^iteration:' .claude/ralph-loop.local.md

  # View full state:
  Get-Content .claude/ralph-loop.local.md -Head 10
"@
            exit 0
        }
        "^--max-iterations$" {
            $i++
            if ($i -ge $Arguments.Count -or [string]::IsNullOrEmpty($Arguments[$i])) {
                Write-Host "Error: --max-iterations requires a number argument" -ForegroundColor Red
                Write-Host ""
                Write-Host "   Valid examples:"
                Write-Host "     --max-iterations 10"
                Write-Host "     --max-iterations 50"
                Write-Host "     --max-iterations 0  (unlimited)"
                Write-Host ""
                Write-Host "   You provided: --max-iterations (with no number)"
                exit 1
            }
            $nextArg = $Arguments[$i]
            if ($nextArg -notmatch '^\d+$') {
                Write-Host "Error: --max-iterations must be a positive integer or 0, got: $nextArg" -ForegroundColor Red
                Write-Host ""
                Write-Host "   Valid examples:"
                Write-Host "     --max-iterations 10"
                Write-Host "     --max-iterations 50"
                Write-Host "     --max-iterations 0  (unlimited)"
                Write-Host ""
                Write-Host "   Invalid: decimals (10.5), negative numbers (-5), text"
                exit 1
            }
            $maxIterations = [int]$nextArg
        }
        "^--completion-promise$" {
            $i++
            if ($i -ge $Arguments.Count -or [string]::IsNullOrEmpty($Arguments[$i])) {
                Write-Host "Error: --completion-promise requires a text argument" -ForegroundColor Red
                Write-Host ""
                Write-Host "   Valid examples:"
                Write-Host "     --completion-promise 'DONE'"
                Write-Host "     --completion-promise 'TASK COMPLETE'"
                Write-Host "     --completion-promise 'All tests passing'"
                Write-Host ""
                Write-Host "   You provided: --completion-promise (with no text)"
                Write-Host ""
                Write-Host "   Note: Multi-word promises must be quoted!"
                exit 1
            }
            $completionPromise = $Arguments[$i]
        }
        default {
            # Non-option argument - collect as prompt part
            $promptParts += $arg
        }
    }
    $i++
}

# Join all prompt parts with spaces
$prompt = $promptParts -join " "

# Validate prompt is non-empty
if ([string]::IsNullOrWhiteSpace($prompt)) {
    Write-Host "Error: No prompt provided" -ForegroundColor Red
    Write-Host ""
    Write-Host "   Ralph needs a task description to work on."
    Write-Host ""
    Write-Host "   Examples:"
    Write-Host "     /ralph-loop Build a REST API for todos"
    Write-Host "     /ralph-loop Fix the auth bug --max-iterations 20"
    Write-Host "     /ralph-loop --completion-promise 'DONE' Refactor code"
    Write-Host ""
    Write-Host "   For all options: /ralph-loop --help"
    exit 1
}

# Create state file for stop hook (markdown with YAML frontmatter)
if (-not (Test-Path ".claude")) {
    New-Item -ItemType Directory -Path ".claude" -Force | Out-Null
}

# Quote completion promise for YAML if it contains special chars or is not null
if ($completionPromise -and $completionPromise -ne "null") {
    $completionPromiseYaml = "`"$completionPromise`""
} else {
    $completionPromiseYaml = "null"
}

# Get current UTC timestamp
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

# Create state file content
$stateContent = @"
---
active: true
iteration: 1
max_iterations: $maxIterations
completion_promise: $completionPromiseYaml
started_at: "$timestamp"
---

$prompt
"@

Set-Content -Path ".claude/ralph-loop.local.md" -Value $stateContent -NoNewline

# Output setup message
$maxIterDisplay = if ($maxIterations -gt 0) { $maxIterations } else { "unlimited" }
$promiseDisplay = if ($completionPromise -ne "null") { "$completionPromise (ONLY output when TRUE - do not lie!)" } else { "none (runs forever)" }

Write-Host "Ralph loop activated in this session!"
Write-Host ""
Write-Host "Iteration: 1"
Write-Host "Max iterations: $maxIterDisplay"
Write-Host "Completion promise: $promiseDisplay"
Write-Host ""
Write-Host "The stop hook is now active. When you try to exit, the SAME PROMPT will be"
Write-Host "fed back to you. You'll see your previous work in files, creating a"
Write-Host "self-referential loop where you iteratively improve on the same task."
Write-Host ""
Write-Host "To monitor: Get-Content .claude/ralph-loop.local.md -Head 10"
Write-Host ""
Write-Host "WARNING: This loop cannot be stopped manually! It will run infinitely" -ForegroundColor Yellow
Write-Host "    unless you set --max-iterations or --completion-promise." -ForegroundColor Yellow
Write-Host ""

# Output the initial prompt
if ($prompt) {
    Write-Host ""
    Write-Host $prompt
}

# Display completion promise requirements if set
if ($completionPromise -ne "null") {
    Write-Host ""
    Write-Host "======================================" -ForegroundColor Cyan
    Write-Host "CRITICAL - Ralph Loop Completion Promise" -ForegroundColor Cyan
    Write-Host "======================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To complete this loop, output this EXACT text:"
    Write-Host "  <promise>$completionPromise</promise>" -ForegroundColor Green
    Write-Host ""
    Write-Host "STRICT REQUIREMENTS (DO NOT VIOLATE):"
    Write-Host "  - Use <promise> XML tags EXACTLY as shown above"
    Write-Host "  - The statement MUST be completely and unequivocally TRUE"
    Write-Host "  - Do NOT output false statements to exit the loop"
    Write-Host "  - Do NOT lie even if you think you should exit"
    Write-Host ""
    Write-Host "IMPORTANT - Do not circumvent the loop:"
    Write-Host "  Even if you believe you're stuck, the task is impossible,"
    Write-Host "  or you've been running too long - you MUST NOT output a"
    Write-Host "  false promise statement. The loop is designed to continue"
    Write-Host "  until the promise is GENUINELY TRUE. Trust the process."
    Write-Host ""
    Write-Host "  If the loop should stop, the promise statement will become"
    Write-Host "  true naturally. Do not force it by lying."
    Write-Host "======================================" -ForegroundColor Cyan
}

exit 0
