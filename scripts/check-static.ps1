#Requires -Version 7.0
<##
.SYNOPSIS
Run workflow and PowerShell static analysis without modifying the repository.

.DESCRIPTION
Runs actionlint against .github/workflows and PSScriptAnalyzer against scripts/
using the committed high-signal rule set. Missing tools fail visibly instead of
being skipped.

.PARAMETER Root
Repository root. Defaults to the parent directory of this script.
##>
[CmdletBinding()]
param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

$rootPath = [IO.Path]::GetFullPath($Root)
if (-not (Test-Path -LiteralPath $rootPath -PathType Container)) {
    throw "Repository root does not exist: $rootPath"
}
$settingsPath = Join-Path $PSScriptRoot 'PSScriptAnalyzerSettings.psd1'
$actionlintVersion = '1.7.12.25'
$failures = 0

$actionlintExit = 0
Push-Location $rootPath
try {
    $actionlint = Get-Command actionlint -ErrorAction SilentlyContinue
    if ($actionlint) {
        & $actionlint.Source -no-color
        $actionlintExit = $LASTEXITCODE
    } else {
        $uvx = Get-Command uvx -ErrorAction SilentlyContinue
        if ($uvx) {
            & uvx --from "actionlint-py==$actionlintVersion" actionlint -no-color
            $actionlintExit = $LASTEXITCODE
        } else {
            Write-Host 'ERROR: actionlint is unavailable; install actionlint or uv (uvx).'
            $actionlintExit = 1
        }
    }
} finally {
    Pop-Location
}
if ($actionlintExit -ne 0) {
    $failures++
}

$module = @(Get-Module -ListAvailable PSScriptAnalyzer |
        Sort-Object Version -Descending) | Select-Object -First 1
if (-not $module) {
    Write-Host ('ERROR: PSScriptAnalyzer is unavailable; run ' +
        'Install-Module PSScriptAnalyzer -RequiredVersion 1.25.0 -Scope CurrentUser -Force.')
    $failures++
} else {
    Import-Module $module.Path -Force
    $findings = @(Invoke-ScriptAnalyzer -Path (Join-Path $rootPath 'scripts') -Recurse `
            -Settings $settingsPath -Severity Warning, Error)
    foreach ($finding in $findings) {
        $relative = [IO.Path]::GetRelativePath($rootPath, $finding.ScriptPath).Replace('\', '/')
        Write-Host "ERROR: ${relative}:$($finding.Line): [$($finding.RuleName)] $($finding.Message)"
    }
    if ($findings.Count -gt 0) {
        $failures++
    }
}

Write-Host "Static analysis: $failures failing check(s)."
if ($failures -gt 0) {
    exit 1
}
exit 0
