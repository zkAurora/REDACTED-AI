# REDACTED AI Swarm — run terminal (Windows PowerShell)
# Usage: .\run.ps1   or   pwsh -File run.ps1

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

# Optional: install minimal deps for cloud terminal (skip if already installed)
# pip install openai requests python-dotenv --quiet

& python run.py
exit $LASTEXITCODE
