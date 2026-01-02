# Ralph Wiggum Stop Hook (PowerShell version for Windows)
# Prevents session exit when a ralph-loop is active
# Feeds Claude's output back as input to continue the loop

param()

$ErrorActionPreference = "Stop"

# Read hook input from stdin (advanced stop hook API)
$HookInput = $input | Out-String

# Check if ralph-loop is active
$RalphStateFile = ".claude/ralph-loop.local.md"

if (-not (Test-Path $RalphStateFile)) {
    # No active loop - allow exit
    exit 0
}

try {
    $stateContent = Get-Content $RalphStateFile -Raw
} catch {
    Write-Error "Failed to read state file: $_"
    exit 0
}

# Parse markdown frontmatter (YAML between ---) and extract values
$frontmatterMatch = [regex]::Match($stateContent, '(?s)^---\r?\n(.*?)\r?\n---')
if (-not $frontmatterMatch.Success) {
    Write-Host "Ralph loop: State file corrupted (no frontmatter found)" -ForegroundColor Yellow
    Remove-Item $RalphStateFile -Force
    exit 0
}

$frontmatter = $frontmatterMatch.Groups[1].Value

# Extract iteration
$iterationMatch = [regex]::Match($frontmatter, 'iteration:\s*(\d+)')
if (-not $iterationMatch.Success) {
    Write-Host "Ralph loop: State file corrupted" -ForegroundColor Yellow
    Write-Host "   File: $RalphStateFile"
    Write-Host "   Problem: 'iteration' field is not a valid number"
    Write-Host ""
    Write-Host "   This usually means the state file was manually edited or corrupted."
    Write-Host "   Ralph loop is stopping. Run /ralph-loop again to start fresh."
    Remove-Item $RalphStateFile -Force
    exit 0
}
$Iteration = [int]$iterationMatch.Groups[1].Value

# Extract max_iterations
$maxIterationsMatch = [regex]::Match($frontmatter, 'max_iterations:\s*(\d+)')
if (-not $maxIterationsMatch.Success) {
    Write-Host "Ralph loop: State file corrupted" -ForegroundColor Yellow
    Write-Host "   File: $RalphStateFile"
    Write-Host "   Problem: 'max_iterations' field is not a valid number"
    Write-Host ""
    Write-Host "   This usually means the state file was manually edited or corrupted."
    Write-Host "   Ralph loop is stopping. Run /ralph-loop again to start fresh."
    Remove-Item $RalphStateFile -Force
    exit 0
}
$MaxIterations = [int]$maxIterationsMatch.Groups[1].Value

# Extract completion_promise (may be quoted or null)
$completionPromiseMatch = [regex]::Match($frontmatter, 'completion_promise:\s*(?:"([^"]+)"|(\S+))')
if ($completionPromiseMatch.Success) {
    if ($completionPromiseMatch.Groups[1].Success) {
        $CompletionPromise = $completionPromiseMatch.Groups[1].Value
    } else {
        $CompletionPromise = $completionPromiseMatch.Groups[2].Value
    }
} else {
    $CompletionPromise = "null"
}

# Check if max iterations reached
if ($MaxIterations -gt 0 -and $Iteration -ge $MaxIterations) {
    Write-Host "Ralph loop: Max iterations ($MaxIterations) reached."
    Remove-Item $RalphStateFile -Force
    exit 0
}

# Get transcript path from hook input
try {
    $hookData = $HookInput | ConvertFrom-Json
    $TranscriptPath = $hookData.transcript_path
} catch {
    Write-Host "Ralph loop: Failed to parse hook input JSON" -ForegroundColor Yellow
    Write-Host "   Error: $_"
    Remove-Item $RalphStateFile -Force
    exit 0
}

if (-not (Test-Path $TranscriptPath)) {
    Write-Host "Ralph loop: Transcript file not found" -ForegroundColor Yellow
    Write-Host "   Expected: $TranscriptPath"
    Write-Host "   This is unusual and may indicate a Claude Code internal issue."
    Write-Host "   Ralph loop is stopping."
    Remove-Item $RalphStateFile -Force
    exit 0
}

# Read transcript and find last assistant message (JSONL format)
$transcriptContent = Get-Content $TranscriptPath -Raw
$lines = $transcriptContent -split "`r?`n" | Where-Object { $_.Trim() -ne "" }
$assistantLines = @($lines | Where-Object { $_ -match '"role"\s*:\s*"assistant"' })

if ($assistantLines.Count -eq 0) {
    Write-Host "Ralph loop: No assistant messages found in transcript" -ForegroundColor Yellow
    Write-Host "   Transcript: $TranscriptPath"
    Write-Host "   This is unusual and may indicate a transcript format issue"
    Write-Host "   Ralph loop is stopping."
    Remove-Item $RalphStateFile -Force
    exit 0
}

$lastAssistantLine = $assistantLines[-1]

try {
    $messageObj = $lastAssistantLine | ConvertFrom-Json
    $textParts = $messageObj.message.content | Where-Object { $_.type -eq "text" } | ForEach-Object { $_.text }
    $LastOutput = $textParts -join "`n"
} catch {
    Write-Host "Ralph loop: Failed to parse assistant message JSON" -ForegroundColor Yellow
    Write-Host "   Error: $_"
    Write-Host "   This may indicate a transcript format issue"
    Write-Host "   Ralph loop is stopping."
    Remove-Item $RalphStateFile -Force
    exit 0
}

if ([string]::IsNullOrWhiteSpace($LastOutput)) {
    Write-Host "Ralph loop: Assistant message contained no text content" -ForegroundColor Yellow
    Write-Host "   Ralph loop is stopping."
    Remove-Item $RalphStateFile -Force
    exit 0
}

# Check for completion promise (only if set)
if ($CompletionPromise -ne "null" -and -not [string]::IsNullOrEmpty($CompletionPromise)) {
    # Extract text from <promise> tags
    $promiseMatch = [regex]::Match($LastOutput, '(?s)<promise>(.*?)</promise>')
    if ($promiseMatch.Success) {
        $PromiseText = $promiseMatch.Groups[1].Value.Trim()
        # Normalize whitespace
        $PromiseText = $PromiseText -replace '\s+', ' '

        if ($PromiseText -eq $CompletionPromise) {
            Write-Host "Ralph loop: Detected <promise>$CompletionPromise</promise>"
            Remove-Item $RalphStateFile -Force
            exit 0
        }
    }
}

# Not complete - continue loop with SAME PROMPT
$NextIteration = $Iteration + 1

# Extract prompt (everything after the closing ---)
# Find the second --- and get everything after it
$promptMatch = [regex]::Match($stateContent, '(?s)^---\r?\n.*?\r?\n---\r?\n(.+)$')
if (-not $promptMatch.Success) {
    Write-Host "Ralph loop: State file corrupted or incomplete" -ForegroundColor Yellow
    Write-Host "   File: $RalphStateFile"
    Write-Host "   Problem: No prompt text found"
    Write-Host ""
    Write-Host "   This usually means:"
    Write-Host "     - State file was manually edited"
    Write-Host "     - File was corrupted during writing"
    Write-Host ""
    Write-Host "   Ralph loop is stopping. Run /ralph-loop again to start fresh."
    Remove-Item $RalphStateFile -Force
    exit 0
}

$PromptText = $promptMatch.Groups[1].Value.Trim()

# Update iteration in state file
$newStateContent = $stateContent -replace 'iteration:\s*\d+', "iteration: $NextIteration"
Set-Content -Path $RalphStateFile -Value $newStateContent -NoNewline

# Build system message with iteration count and completion promise info
if ($CompletionPromise -ne "null" -and -not [string]::IsNullOrEmpty($CompletionPromise)) {
    $SystemMsg = "Ralph iteration $NextIteration | To stop: output <promise>$CompletionPromise</promise> (ONLY when statement is TRUE - do not lie to exit!)"
} else {
    $SystemMsg = "Ralph iteration $NextIteration | No completion promise set - loop runs infinitely"
}

# Output JSON to block the stop and feed prompt back
$output = @{
    decision = "block"
    reason = $PromptText
    systemMessage = $SystemMsg
} | ConvertTo-Json -Compress

Write-Output $output

# Exit 0 for successful hook execution
exit 0
