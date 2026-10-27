#Requires -Version 7.0
<##
.SYNOPSIS
Exercise scripts/check-governance.ps1 against isolated fixtures, including expected failures.
##>
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
$root = Split-Path -Parent $PSScriptRoot
$check = Join-Path $root 'scripts/check-governance.ps1'
$parent = if ($env:SPAWN_JOIN_TEMP_DIR) {
    (Resolve-Path -LiteralPath $env:SPAWN_JOIN_TEMP_DIR).Path
} else { [IO.Path]::GetTempPath() }
# Spaces deliberately exercise argument handling on Windows and Linux.
$fixture = Join-Path $parent ('spawn join governance fixture ' + [guid]::NewGuid().ToString('N'))
$evidence = Join-Path $fixture 'harness/evidence/phase-01-fixture.md'
$spec = Join-Path $fixture 'specs/003-fixture/spec.md'
$tasks = Join-Path $fixture 'specs/003-fixture/tasks.md'
$readme = Join-Path $fixture 'README.md'
$assertions = 0

function Write-FixtureFile {
    param([string]$Path, [string]$Content)
    $directory = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $directory)) {
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
    }
    Set-Content -LiteralPath $Path -Value $Content
}

function Test-GovernanceResult {
    param([string]$Label, [bool]$Success, [string]$Diagnostic,
        [string]$AbsentDiagnostic)
    $output = & pwsh -NoProfile -File $check -Root $fixture 2>&1
    $code = $LASTEXITCODE
    $text = $output -join [Environment]::NewLine
    if (($Success -and $code -ne 0) -or (-not $Success -and $code -ne 1) -or
        ($Diagnostic -and $text -notmatch [regex]::Escape($Diagnostic)) -or
        ($AbsentDiagnostic -and $text -match [regex]::Escape($AbsentDiagnostic))) {
        Write-Host $text
        throw "Unexpected governance result for ${Label}: exit=$code"
    }
    $script:assertions++
    Write-Host "PASS: $Label (observed exit=$code)"
}

New-Item -ItemType Directory -Path $fixture | Out-Null
try {
    Write-FixtureFile (Join-Path $fixture '.gitignore') "/specs/`n"
    Write-FixtureFile $readme "# Fixture`n"
    Write-FixtureFile (Join-Path $fixture 'harness/build-log.md') @"
# Build Log

Evidence: ``harness/evidence/phase-01-fixture.md``
"@
    Write-FixtureFile $evidence @"
# Evidence

- feature_id: fixture
- phase_id: phase-01-fixture
- base_revision: working-tree
- head_revision: working-tree
- working_directory: fixture
- recorded_at: 2026-10-27
- result: pass

## Limitations

None.
"@
    Write-FixtureFile (Join-Path $fixture 'docs/decisions/README.md') @"
# Decisions

| ID | 领域 | 决策 | 状态 |
|---|---|---|---|
| ADR-0001 | engineering | [Fixture](engineering/0001-fixture.md) | Accepted |
"@
    Write-FixtureFile (Join-Path $fixture 'docs/decisions/engineering/0001-fixture.md') @"
# ADR-0001: Fixture

- Status: Accepted
- Superseded by: 无
"@
    Write-FixtureFile $spec "**Status**: In Progress`n"
    Write-FixtureFile $tasks "- [ ] T001 First task.`n- [ ] T002 Second task.`n"

    & git -C $fixture init --quiet
    if ($LASTEXITCODE -ne 0) { throw 'Could not initialize fixture Git repository.' }
    & git -C $fixture config core.autocrlf false
    & git -C $fixture add -A
    if ($LASTEXITCODE -ne 0) { throw 'Could not stage fixture files.' }
    & git -C $fixture -c user.name=fixture -c user.email=fixture@example.invalid `
        commit -m 'fixture baseline' --quiet
    if ($LASTEXITCODE -ne 0) { throw 'Could not commit fixture baseline.' }

    Test-GovernanceResult 'valid structure' $true ''

    $baseCommit = (& git -C $fixture rev-parse HEAD).Trim()
    $originalEvidence = Get-Content -LiteralPath $evidence -Raw
    Set-Content -LiteralPath $evidence -Value ($originalEvidence -replace
        'head_revision: working-tree', "head_revision: $baseCommit")
    Add-Content -LiteralPath $readme -Value 'docs-only follow-up'
    & git -C $fixture add README.md
    & git -C $fixture -c user.name=fixture -c user.email=fixture@example.invalid `
        commit -m 'docs-only follow-up' --quiet
    Test-GovernanceResult 'docs-only follow-up keeps freshness warning quiet' `
        $true '' -AbsentDiagnostic 'WARN:'

    New-Item -ItemType Directory -Path (Join-Path $fixture 'scripts') -Force | Out-Null
    Set-Content -LiteralPath (Join-Path $fixture 'scripts/probe.ps1') -Value '# probe'
    & git -C $fixture add scripts/probe.ps1
    & git -C $fixture -c user.name=fixture -c user.email=fixture@example.invalid `
        commit -m 'material change' --quiet
    Test-GovernanceResult 'material change after evidence head warns' `
        $true 'material paths changed'
    Set-Content -LiteralPath $evidence -Value $originalEvidence

    $original = Get-Content -LiteralPath $evidence -Raw
    Set-Content -LiteralPath $evidence -Value ($original -replace '- result: pass\r?\n', '')
    Test-GovernanceResult 'missing result field' $false 'missing field: result'
    Set-Content -LiteralPath $evidence -Value $original

    Set-Content -LiteralPath $evidence -Value ($original -replace '- result: pass', '- result: ok')
    Test-GovernanceResult 'invalid result vocabulary' $false 'invalid result: ok'
    Set-Content -LiteralPath $evidence -Value $original

    $extraAdr = Join-Path $fixture 'docs/decisions/engineering/0002-fixture.md'
    Write-FixtureFile $extraAdr "# ADR-0002: Extra`n`n- Status: Accepted`n- Superseded by: 无`n"
    Test-GovernanceResult 'unindexed ADR' $false 'file exists but is not indexed'
    Remove-Item -LiteralPath $extraAdr

    $originalReadme = Get-Content -LiteralPath $readme -Raw
    Write-FixtureFile (Join-Path $fixture 'specs/hidden.md') "# Hidden`n"
    Set-Content -LiteralPath $readme -Value ($originalReadme + "`n[hidden](specs/hidden.md)`n")
    Test-GovernanceResult 'link to local-only spec' $false 'links to local-only path: specs/hidden.md'
    Set-Content -LiteralPath $readme -Value $originalReadme
    Remove-Item -LiteralPath (Join-Path $fixture 'specs/hidden.md')

    $extraEvidence = Join-Path $fixture 'harness/evidence/phase-02-fixture.md'
    Write-FixtureFile $extraEvidence @"
# Evidence

- feature_id: fixture
- phase_id: phase-02-fixture
- base_revision: working-tree
- head_revision: working-tree
- working_directory: fixture
- recorded_at: 2026-10-27
- result: pass

## Limitations

None.
"@
    Test-GovernanceResult 'evidence missing from build log' $false 'not referenced from harness/build-log.md'
    Remove-Item -LiteralPath $extraEvidence

    $buildLog = Join-Path $fixture 'harness/build-log.md'
    $originalLog = Get-Content -LiteralPath $buildLog -Raw
    Remove-Item -LiteralPath $buildLog
    Test-GovernanceResult 'missing evidence build log' $false 'missing or empty evidence build log'
    Set-Content -LiteralPath $buildLog -Value $originalLog

    $originalSpec = Get-Content -LiteralPath $spec -Raw
    Set-Content -LiteralPath $spec -Value '**Status**: Implemented'
    Test-GovernanceResult 'implemented spec with unchecked tasks' $false 'Status is Implemented but tasks.md has unchecked items'
    Set-Content -LiteralPath $spec -Value $originalSpec

    Set-Content -LiteralPath $tasks -Value "- [ ] T001 First task.`n- [ ] T001 Duplicate.`n"
    Test-GovernanceResult 'duplicate task IDs' $false 'duplicate task IDs'
    Set-Content -LiteralPath $tasks -Value "- [ ] T001 First task.`n- [ ] T002 Second task.`n"

    Write-Host "Governance regression checks passed: $assertions scenarios."
} catch {
    Write-Error -Message $_ -ErrorAction Continue
    exit 1
} finally {
    Remove-Item -LiteralPath $fixture -Recurse -Force
}
# The last assertion intentionally expects a failing check; end explicitly for CI wrappers.
exit 0
