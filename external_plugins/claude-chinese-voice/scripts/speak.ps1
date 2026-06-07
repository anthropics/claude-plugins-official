# ============================================================
# Claude Code TTS
# Usage:
#   speak.ps1 -File "tts.txt"                    (default Huihui)
#   speak.ps1 -File "tts.txt" -Voice "Kangkang"  (male voice)
#   speak.ps1 -File "tts.txt" -Voice "Zira"      (English)
# ============================================================

param([string]$File, [string]$Voice = "Huihui")

$lockFile = "$env:TEMP\claude_tts.lock"

$waited = 0
while ((Test-Path $lockFile) -and ($waited -lt 15)) {
    Start-Sleep -Milliseconds 200
    $waited += 0.2
}
" " | Out-File $lockFile -Force

try {
    if (-not $File -or -not (Test-Path $File)) {
        Write-Host "ERR: file not found: $File"
        exit 1
    }

    $speakText = (Get-Content $File -Raw -Encoding UTF8).Trim()
    if ([string]::IsNullOrWhiteSpace($speakText)) { Write-Host "ERR: empty"; exit 1 }
    if ($speakText.Length -gt 5000) { $speakText = $speakText.Substring(0, 5000) }

    $spVoice = New-Object -ComObject SAPI.SpVoice

    # Select voice by name match
    $found = $false
    foreach ($token in $spVoice.GetVoices()) {
        $name = $token.GetAttribute("Name")
        if ($name -like "*$Voice*") {
            $spVoice.Voice = $token
            $found = $true
            Write-Host ("VOICE: " + $name)
            break
        }
    }
    if (-not $found) {
        Write-Host ("WARN: voice '$Voice' not found, using default")
    }

    $spVoice.Rate = 1
    $spVoice.Volume = 100
    $spVoice.Speak("", 2) | Out-Null
    $spVoice.Speak($speakText, 0) | Out-Null
    $spVoice.WaitUntilDone(-1)

    Write-Host "OK"

} catch {
    Write-Host ("ERR: " + $_.Exception.Message)
    exit 1
} finally {
    Remove-Item $lockFile -Force -ErrorAction SilentlyContinue
}
