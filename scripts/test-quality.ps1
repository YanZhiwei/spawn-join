#Requires -Version 7.0
<##
.SYNOPSIS
Exercise the real gate in an isolated fixture, including expected failures.
##>
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
$root = Split-Path -Parent $PSScriptRoot
$parent = if ($env:SPAWN_JOIN_TEMP_DIR) {
    (Resolve-Path -LiteralPath $env:SPAWN_JOIN_TEMP_DIR).Path
} else { [IO.Path]::GetTempPath() }
# Spaces deliberately exercise native argument handling on Windows and Linux.
$fixture = Join-Path $parent ('spawn join gate fixture ' + [guid]::NewGuid().ToString('N'))
$core = Join-Path $fixture 'packages/core/spawn-join-core'
$runner = Join-Path $fixture 'scripts/quality.ps1'
$probe = Join-Path $core 'tests/test_probe.py'
$assertions = 0

function Assert-GateResult {
    param([string]$Label, [string]$Check, [bool]$Success, [string]$Diagnostic)
    $before = if (Test-Path -LiteralPath $probe) { (Get-FileHash -LiteralPath $probe).Hash }
    $output = & pwsh -NoProfile -File $runner -Package spawn-join-core -Check $Check 2>&1
    $code = $LASTEXITCODE
    $text = $output -join [Environment]::NewLine
    if (($Success -and $code -ne 0) -or (-not $Success -and $code -ne 1) -or
        ($Diagnostic -and $text -notmatch [regex]::Escape($Diagnostic))) {
        Write-Host $text
        throw "Unexpected gate result for ${Label}: exit=$code"
    }
    if ($before -and $before -ne (Get-FileHash -LiteralPath $probe).Hash) {
        throw "Read-only check changed $probe"
    }
    $script:assertions++
    Write-Host "PASS: $Label (observed gate exit=$code)"
}

New-Item -ItemType Directory -Path $fixture | Out-Null
try {
    New-Item -ItemType Directory -Path "$fixture/scripts", "$core/src", "$core/tests",
        "$fixture/.specify/memory" | Out-Null
    Copy-Item -LiteralPath "$root/pyproject.toml" -Destination "$fixture/pyproject.toml"
    Copy-Item -LiteralPath "$root/scripts/quality.ps1" -Destination $runner
    $originalCore = Join-Path $root 'packages/core/spawn-join-core'
    foreach ($name in @('pyproject.toml', 'uv.lock')) {
        Copy-Item -LiteralPath (Join-Path $originalCore $name) -Destination $core
    }
    Copy-Item -LiteralPath "$originalCore/src/spawn_join_core" -Destination "$core/src" -Recurse
    Copy-Item -LiteralPath "$originalCore/tests/test_package.py" -Destination "$core/tests"
    foreach ($file in @('README.md', 'AGENTS.md', '.specify/memory/constitution.md')) {
        Set-Content -LiteralPath (Join-Path $fixture $file) -Value '# Fixture'
    }
    & git -C $fixture init --quiet
    if ($LASTEXITCODE -ne 0) { throw 'Could not initialize fixture Git repository.' }
    Assert-GateResult 'clean full pipeline, including isolated wheel install' all $true ''

    Set-Content -LiteralPath $probe -Value "value=1`n" -NoNewline
    Assert-GateResult 'Black rejects bad formatting without rewriting' format $false 'would reformat'

    Set-Content -LiteralPath $probe -Value "import sys`nimport os`n`n__all__ = [`"os`", `"sys`"]`n" -NoNewline
    Assert-GateResult 'isort rejects unordered imports' format $false 'Imports are incorrectly sorted'

    Set-Content -LiteralPath $probe -Value "unknown_name`n" -NoNewline
    Assert-GateResult 'Ruff rejects undefined names' lint $false 'F821'

    Set-Content -LiteralPath $probe -Value "value: int = `"wrong`"`n" -NoNewline
    Assert-GateResult 'Pyright rejects incompatible types' type $false 'reportAssignmentType'

    Set-Content -LiteralPath $probe -Value "def test_failure() -> None:`n    assert False`n" -NoNewline
    Assert-GateResult 'pytest failure propagates' test $false 'FAILED'
    Remove-Item -LiteralPath $probe

    $init = Join-Path $core 'src/spawn_join_core/__init__.py'
    Set-Content -LiteralPath $init -Value "raise RuntimeError('wheel-import-probe')`n" -NoNewline
    Assert-GateResult 'installed wheel import failure propagates' build $false 'wheel-import-probe'
    Copy-Item -LiteralPath "$originalCore/src/spawn_join_core/__init__.py" -Destination $init

    Remove-Item -LiteralPath "$core/tests/test_package.py"
    Assert-GateResult 'zero tests are not success' test $false 'exit_code=5'

    Set-Content -LiteralPath "$fixture/README.md" -Value '[missing](missing-target.md)'
    Assert-GateResult 'missing Markdown target propagates' docs $false 'Missing Markdown target'
    foreach ($forbidden in @('.venv', 'uv.lock', 'build', 'dist')) {
        if (Test-Path -LiteralPath (Join-Path $fixture $forbidden)) {
            throw "Forbidden root artifact: $forbidden"
        }
    }
    Write-Host "Gate regression checks passed: $assertions scenarios; no root project artifacts."
} catch {
    Write-Error -Message $_ -ErrorAction Continue
    exit 1
} finally {
    # Only remove the exact fixture directory created above, never the supplied parent.
    Remove-Item -LiteralPath $fixture -Recurse -Force
}
# The last assertion runs an intentionally failing gate, so $LASTEXITCODE is still 1.
# GitHub appends `exit $LASTEXITCODE` to pwsh steps, so a successful run must end explicitly.
exit 0
