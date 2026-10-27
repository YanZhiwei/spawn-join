#Requires -Version 7.0
<##
.SYNOPSIS
Exercise scripts/check-static.ps1 against isolated fixtures.
##>
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
$root = Split-Path -Parent $PSScriptRoot
$check = Join-Path $root 'scripts/check-static.ps1'
$parent = if ($env:SPAWN_JOIN_TEMP_DIR) {
    (Resolve-Path -LiteralPath $env:SPAWN_JOIN_TEMP_DIR).Path
} else { [IO.Path]::GetTempPath() }
# Spaces deliberately exercise argument handling on Windows and Linux.
$fixture = Join-Path $parent ('spawn join static fixture ' + [guid]::NewGuid().ToString('N'))
$workflow = Join-Path $fixture '.github/workflows/fixture.yml'
$script = Join-Path $fixture 'scripts/fixture.ps1'
$assertions = 0

function Write-FixtureFile {
    param([string]$Path, [string]$Content)
    $directory = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $directory)) {
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
    }
    Set-Content -LiteralPath $Path -Value $Content
}

function Test-StaticResult {
    param([string]$Label, [bool]$Success, [string]$Diagnostic)
    $output = & pwsh -NoProfile -File $check -Root $fixture 2>&1
    $code = $LASTEXITCODE
    $text = $output -join [Environment]::NewLine
    if (($Success -and $code -ne 0) -or (-not $Success -and $code -ne 1) -or
        ($Diagnostic -and $text -notmatch [regex]::Escape($Diagnostic))) {
        Write-Host $text
        throw "Unexpected static result for ${Label}: exit=$code"
    }
    $script:assertions++
    Write-Host "PASS: $Label (observed exit=$code)"
}

$validWorkflow = @"
name: Fixture
on: workflow_dispatch
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: echo ok
"@

New-Item -ItemType Directory -Path $fixture | Out-Null
try {
    Write-FixtureFile $workflow $validWorkflow
    Write-FixtureFile $script "Write-Host 'ok'`n"
    & git -C $fixture init --quiet
    & git -C $fixture config core.autocrlf false
    & git -C $fixture add -A
    Test-StaticResult 'valid workflow and script' $true ''

    Write-FixtureFile $workflow "name: Bad`non: push`njobs:`n  test:`n    runs-on: ubuntu-latest`n     bad-indent`n"
    Test-StaticResult 'invalid workflow YAML' $false ''

    Write-FixtureFile $workflow $validWorkflow
    Write-FixtureFile $script "Invoke-Expression 'Get-Date'`n"
    Test-StaticResult 'unapproved Invoke-Expression' $false 'AvoidUsingInvokeExpression'

    Write-Host "Static regression checks passed: $assertions scenarios."
} catch {
    Write-Error -Message $_ -ErrorAction Continue
    exit 1
} finally {
    Remove-Item -LiteralPath $fixture -Recurse -Force
}
# The last assertion expects a failing check; end explicitly for CI wrappers.
exit 0
