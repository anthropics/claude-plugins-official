# Cancel Ralph Loop Script (PowerShell version for Windows)
# Removes the state file to stop an active Ralph loop

param()

$StateFile = ".claude/ralph-loop.local.md"

if (Test-Path $StateFile) {
    try {
        $content = Get-Content $StateFile -Raw
        $iterationMatch = [regex]::Match($content, 'iteration:\s*(\d+)')

        if ($iterationMatch.Success) {
            $iteration = $iterationMatch.Groups[1].Value
        } else {
            $iteration = "unknown"
        }

        Remove-Item $StateFile -Force
        Write-Output "Cancelled Ralph loop (was at iteration $iteration)"
    } catch {
        Write-Error "Failed to cancel loop: $_"
        exit 1
    }
} else {
    Write-Output "No active Ralph loop found."
}

exit 0
