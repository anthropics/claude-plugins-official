# Claude History - Automatic Transcript Backup
# Runs on UserPromptSubmit and Stop hooks
# Creates: exports/{date}/{summary}_{shortId}.jsonl + .meta.json + index.json

param()

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

try {
    # Get project root from environment or current directory
    $projectRoot = if ($env:CLAUDE_PROJECT_DIR) { $env:CLAUDE_PROJECT_DIR } else { (Get-Location).Path }

    # Create exports directory at project root
    $exportDir = Join-Path $projectRoot "exports"
    if (-not (Test-Path $exportDir)) {
        New-Item -ItemType Directory -Path $exportDir -Force | Out-Null
    }

    # Setup debug logging (optional - in exports folder)
    $logFile = Join-Path $exportDir ".debug.log"

    # Convert project path to Claude projects format
    # Example: E:\SAS\Project -> E--SAS-Project
    $projectPath = $projectRoot -replace ':\\', '--' -replace '\\', '-'

    # Find Claude projects directory
    $claudeProjectsDir = Join-Path $env:USERPROFILE ".claude\projects\$projectPath"

    if (-not (Test-Path $claudeProjectsDir)) {
        exit 0
    }

    # Find most recent transcript file (not in subagents folder)
    $transcriptFile = Get-ChildItem $claudeProjectsDir -Filter "*.jsonl" -File |
        Where-Object { $_.Directory.Name -ne "subagents" } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    if (-not $transcriptFile) {
        exit 0
    }

    # Read first 100 lines to find metadata
    $lines = Get-Content $transcriptFile.FullName -First 100

    # Get LATEST summary entry (best describes current session context)
    $summaryLines = $lines | Where-Object { $_ -match '"type":"summary"' }
    $latestSummary = $summaryLines | Select-Object -Last 1

    # Get first user message for session metadata
    $firstUserMsg = $lines | Where-Object { $_ -match '"type":"user"' } | Select-Object -First 1

    if ($firstUserMsg) {
        try {
            $msgData = $firstUserMsg | ConvertFrom-Json

            # Extract metadata
            $sessionId = $msgData.sessionId
            $shortId = $sessionId.Substring(0, 8)
            $sessionTimestamp = [DateTime]::Parse($msgData.timestamp)
            $dateFolder = $sessionTimestamp.ToString("yyyy-MM-dd")

            # Get session description from LATEST summary (or fall back to first prompt)
            $sessionDesc = ""
            if ($latestSummary) {
                try {
                    $summaryData = $latestSummary | ConvertFrom-Json
                    $sessionDesc = $summaryData.summary
                } catch {
                    $sessionDesc = ""
                }
            }

            # Fall back to first user message if no summary
            if (-not $sessionDesc) {
                $sessionDesc = $msgData.message.content
                if ($sessionDesc.Length -gt 200) {
                    $sessionDesc = $sessionDesc.Substring(0, 200) + "..."
                }
            }
            # Clean up for JSON
            $sessionDesc = $sessionDesc -replace "`r`n", " " -replace "`n", " " -replace '"', "'"

            # Create filename-safe version of summary
            $safeDesc = $sessionDesc -replace '[^\w\s-]', '' -replace '\s+', '-'
            if ($safeDesc.Length -gt 50) {
                $safeDesc = $safeDesc.Substring(0, 50)
            }
            $safeDesc = $safeDesc.Trim('-')

            # Build filename: date_summary_shortId
            $baseFilename = "${dateFolder}_${safeDesc}_${shortId}"

            # Create date folder
            $datePath = Join-Path $exportDir $dateFolder
            if (-not (Test-Path $datePath)) {
                New-Item -ItemType Directory -Path $datePath -Force | Out-Null
            }

            # Copy transcript to dated folder
            $sessionFile = Join-Path $datePath "$baseFilename.jsonl"
            Copy-Item -Path $transcriptFile.FullName -Destination $sessionFile -Force

            # Get line count
            $lineCount = (Get-Content $transcriptFile.FullName | Measure-Object -Line).Lines

            # Write metadata file
            $metaFile = Join-Path $datePath "$baseFilename.meta.json"
            $metaContent = @{
                sessionId = $sessionId
                shortId = $shortId
                startTime = $msgData.timestamp
                summary = $sessionDesc
                cwd = $msgData.cwd
                gitBranch = $msgData.gitBranch
                lastUpdate = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
                sizeBytes = $transcriptFile.Length
                messageCount = $lineCount
            }
            $metaContent | ConvertTo-Json -Depth 3 | Set-Content $metaFile -Encoding UTF8

            # Update index.json
            $indexFile = Join-Path $exportDir "index.json"
            $index = @{ sessions = @(); lastUpdated = "" }

            if (Test-Path $indexFile) {
                try {
                    $index = Get-Content $indexFile -Raw | ConvertFrom-Json
                    if (-not $index.sessions) {
                        $index = @{ sessions = @(); lastUpdated = "" }
                    }
                } catch {
                    $index = @{ sessions = @(); lastUpdated = "" }
                }
            }

            # Create session entry
            $sessionEntry = @{
                id = $shortId
                fullId = $sessionId
                date = $dateFolder
                startTime = $sessionTimestamp.ToString("HH:mm:ss")
                lastUpdate = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
                summary = $sessionDesc
                sizeBytes = $transcriptFile.Length
                messageCount = $lineCount
                path = "$dateFolder/$baseFilename.jsonl"
            }

            # Update or add session in index
            $sessions = [System.Collections.ArrayList]@()
            $found = $false
            foreach ($s in $index.sessions) {
                if ($s.id -eq $shortId) {
                    $sessions.Add($sessionEntry) | Out-Null
                    $found = $true
                } else {
                    $sessions.Add($s) | Out-Null
                }
            }
            if (-not $found) {
                $sessions.Add($sessionEntry) | Out-Null
            }

            # Sort by lastUpdate descending
            $sortedSessions = $sessions | Sort-Object { $_.lastUpdate } -Descending

            $newIndex = @{
                sessions = @($sortedSessions)
                lastUpdated = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
            }
            $newIndex | ConvertTo-Json -Depth 4 | Set-Content $indexFile -Encoding UTF8

        } catch {
            # Silent failure
        }
    }

    # Output for CLI feedback
    Write-Output "[OK] Transcript backed up"

} catch {
    # Silent failure - hooks should never break the user experience
    exit 0
}
