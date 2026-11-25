#Requires -Version 7.0
<#
.SYNOPSIS
Exercise publication checks against a private Git object database.
#>
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true
$check = Join-Path $PSScriptRoot 'check-pr-evidence.ps1'
$runtime = Join-Path (Split-Path -Parent $PSScriptRoot) '.specify/extensions/delivery/scripts/delivery_runtime.py'
$python = 'python3'
if ($IsWindows) {
    $python = 'python'
    if (Get-Command py -CommandType Application -ErrorAction SilentlyContinue) {
        # A Windows launcher can exist even when only the PATH interpreter is usable.
        $registered = & {
            $PSNativeCommandUseErrorActionPreference = $false
            py -3 -c 'import sys; print(sys.executable)' 2>$null
        }
        if ($registered) { $python = $registered }
    }
}
$fixture = Join-Path ([IO.Path]::GetTempPath()) ('spawn join pr evidence ' + [guid]::NewGuid().ToString('N'))
$path = '.specify/delivery/fixture/evidence.md'
$evidence = Join-Path $fixture $path
$eventPath = Join-Path $fixture '.git/pr-event.json'
$single = "Delivery-Evidence: $path`n`nDelivery-Stack: single"
$stack = $single.Replace('Stack: single', 'Stack: stacked')
$map = Join-Path (Split-Path -Parent $evidence) 'publication-branches.txt'
$count = 0

function New-TestRevision {
    param([string]$Parent)
    & git -C $fixture add -A
    $tree = & git -C $fixture write-tree
    $parents = if ($Parent) { @('-p', $Parent) } else { @() }
    return (& git -C $fixture commit-tree $tree @parents -m fixture)
}

function Test-Publication {
    param([string]$Label, [string]$Body, [string]$Base, [string]$Head, [string]$ErrorText,
        [string]$Branch = 'topic/final')
    @{
        action = 'edited'
        repository = @{ full_name = 'example/repo' }
        pull_request = @{ body = $Body; number = 42; base = @{ sha = $Base }; head = @{ sha = $Head; ref = $Branch } }
    } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $eventPath
    $caught = ''
    try { & $check -EventPath $eventPath -Root $fixture }
    catch { $caught = $_.Exception.Message }
    if (($ErrorText -and -not $caught.Contains($ErrorText)) -or (-not $ErrorText -and $caught)) {
        throw "Unexpected publication result for $Label. Expected '$ErrorText', observed '$caught'."
    }
    $script:count++
    Write-Host "PASS: $Label"
}

$null = [IO.Directory]::CreateDirectory((Split-Path -Parent $evidence))
try {
    & git -C $fixture init --quiet
    & git -C $fixture config user.name fixture
    & git -C $fixture config user.email fixture@example.invalid
    & git -C $fixture config core.autocrlf false
    Set-Content -LiteralPath "$fixture/README.md" -Value '# Fixture'
    $base = New-TestRevision
    & git -C $fixture update-ref HEAD $base
    & $python -B $runtime init --root $fixture --run fixture --lane lightweight | Out-Null
    Add-Content -LiteralPath "$fixture/README.md" -Value 'Change under review'
    $unmapped = New-TestRevision $base
    Set-Content -LiteralPath $map -Value @('topic/first', 'topic/final')
    $missing = New-TestRevision $unmapped
    $record = @"
# Fixture evidence

- **delivery_run**: fixture
- **lane**: lightweight
- **evidence_path**: $path
- **base_revision**: $base
- **reviewed_head**: $missing
- **original_pr_head**: pending
- **content_fingerprint**: sha256:$('a' * 64)
- **requirements_fingerprint**: sha256:$('b' * 64)
- **method_identity**: builtin
- **pull_request**: pending

## 限制与未验证项

CI pending at review time.
"@
    Set-Content -LiteralPath $evidence -Value $record
    Test-Publication 'a local-only file cannot satisfy a single PR' $single $base $missing 'Missing regular evidence'
    Test-Publication 'a PR body alone cannot opt into deferral' $stack $base $unmapped 'Missing approved publication branches' 'topic/first'
    Test-Publication 'intermediate layer can defer final evidence' $stack $base $missing '' 'topic/first'
    Test-Publication 'last layer cannot defer final evidence' $stack $base $missing 'Missing regular evidence'
    Test-Publication 'actual source must appear in the stack' $stack $base $missing 'actual PR source branch' 'unlisted'
    Set-Content -LiteralPath $map -Value @('topic/first', 'topic/final', 'topic/final')
    Test-Publication 'duplicate layers' $stack $base (New-TestRevision $missing) 'distinct source branch'
    Set-Content -LiteralPath $map -Value @('topic/first', 'bad..branch')
    Test-Publication 'invalid branch' $stack $base (New-TestRevision $missing) 'distinct source branch'
    Set-Content -LiteralPath $map -Value @('topic/first', 'topic/final', 'topic/later')
    Test-Publication 'a final layer cannot extend the published map to defer' $stack $missing (New-TestRevision $missing) 'previously published branch order'
    Set-Content -LiteralPath $map -Value @('topic/first', 'topic/final')
    Test-Publication 'invalid publication mode' ($stack.Replace('stacked', 'skip')) $base $missing 'single or stacked'
    Test-Publication 'missing declaration' 'Delivery-Stack: single' $base $missing 'Missing Delivery-Evidence'
    Test-Publication 'empty PR body' '' $base $missing 'Missing Delivery-Evidence'
    Test-Publication 'template placeholder' ($single.Replace('/fixture/', '/<run-id>/')) $base $missing 'canonical Delivery or Harness'
    Test-Publication 'duplicate declarations on body edit' ($single + "`n`nDelivery-Stack: single") $base $missing 'Duplicate Delivery-Stack'
    Test-Publication 'commented declarations' "<!--`n$single`n-->" $base $missing 'Missing Delivery-Evidence'
    Test-Publication 'code examples are not declarations' ("~~~text`n" + $single + "`n~~~") $base $missing 'Missing Delivery-Evidence'
    Test-Publication 'quotations are not declarations' ($single -replace '(?m)^Delivery-', '> Delivery-') $base $missing 'Missing Delivery-Evidence'
    Test-Publication 'path traversal' ($single.Replace('/fixture/', '/../')) $base $missing 'canonical Delivery or Harness'
    Test-Publication 'temporary runtime file' ($single.Replace('/evidence.md', '/runtime/evidence.md')) $base $missing 'canonical Delivery or Harness'

    $published = New-TestRevision $missing
    Test-Publication 'single pending native record' $single $base $published
    Test-Publication 'last layer carries the record' $stack $missing $published
    Set-Content -LiteralPath "$fixture/after-review.txt" -Value 'Substantive edit after verification'
    $unreviewed = New-TestRevision $published
    Test-Publication 'a later product push makes old review stale' $single $base $unreviewed 'differs from the reviewed_head'
    Add-Content -LiteralPath $evidence -Value "`n## Fresh validation snapshot`n- **reviewed_head**: $unreviewed`n- **content_fingerprint**: sha256:$('c' * 64)`n- **requirements_fingerprint**: sha256:$('b' * 64)"
    Test-Publication 'an appended SHA cannot replace the native publication summary' $single $base (New-TestRevision $unreviewed) 'differs from the reviewed_head'
    $fresh = $record.Replace($missing, $unreviewed).Replace(('a' * 64), ('c' * 64)) + "`n`n## Earlier validation`n`n$record"
    Set-Content -LiteralPath $evidence -Value $fresh
    $finalHead = New-TestRevision $unreviewed
    Test-Publication 'publishing a fresh summary preserves the earlier review' $single $base $finalHead
    Remove-Item -LiteralPath "$fixture/after-review.txt"
    Set-Content -LiteralPath $evidence -Value $record
    Test-Publication 'base-only evidence cannot be borrowed' $single $published $missing 'Missing regular evidence'
    Test-Publication 'previously shared evidence must change in this PR' $single $published $published 'add or update'
    Set-Content -LiteralPath $evidence -Value ($record.Replace('**delivery_run**: fixture', '**delivery_run**: other'))
    Test-Publication 'wrong run inside the right path' $single $base (New-TestRevision $published) 'canonical record path'
    Set-Content -LiteralPath $evidence -Value ($record.Replace('**pull_request**: pending', '**pull_request**: #27'))
    Test-Publication 'different PR identity' $single $base (New-TestRevision $published) 'different pull request'
    Set-Content -LiteralPath $evidence -Value ($record.Replace("**reviewed_head**: $missing", '**reviewed_head**: abcd123'))
    Test-Publication 'native SHA is incomplete' $single $base (New-TestRevision $published) 'full 40-character SHA'
    Set-Content -LiteralPath $evidence -Value ($record.Replace('## 限制与未验证项', '## Summary'))
    Test-Publication 'native limitations are required' $single $base (New-TestRevision $published) 'missing limitations'
    Set-Content -LiteralPath "$fixture/after-review.txt" -Value 'Substantive edit after verification'
    $tree = & git -C $fixture rev-parse "$finalHead^{tree}"
    $merged = & git -C $fixture commit-tree $tree -p $base -m squash
    & git -C $fixture update-ref HEAD $merged
    $local = Join-Path (Split-Path -Parent $evidence) 'runtime'
    @{
        schema_version = 1; delivery_run = 'fixture'; lane = 'lightweight'
        provider = 'github'; repository = 'example/repo'; number = 27; state = 'MERGED'
        url = 'https://github.com/example/repo/pull/27'
        head_revision = $finalHead; base_revision = $base; merged_revision = $merged
        merged_at = '2026-11-23T17:46:03Z'; observed_at = '2026-11-25T10:07:40Z'
    } | ConvertTo-Json | Set-Content -LiteralPath "$local/observed-pr.json"
    $archive = Join-Path $local 'published.diff'
    & git -C $fixture diff --no-ext-diff --no-renames --binary --full-index "--output=$archive" $base $finalHead --
    $digest = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
    Set-Content -LiteralPath $evidence -Value @"
$fresh

## Publication binding

- **published_head**: $finalHead
- **reviewed_diff_archive**: runtime/published.diff
- **reviewed_diff_archive_sha256**: $digest
- **reviewed_diff_archive_base**: $base
- **reviewed_diff_archive_head**: $finalHead
- **reviewed_diff_archive_reviewed_head**: $unreviewed
"@
    $close = (& $python -B $runtime close-record --root $fixture --run fixture --outcome merged --pr 27 --verified) -join "`n" | ConvertFrom-Json
    if ($close.status -ne 'delivered' -or $close.reviewed_head -cne $unreviewed -or
        $close.published_head_proof -ne 'published-evidence-archive' -or $close.merge_proof -ne 'evidence-archive') {
        throw 'Native Close did not verify the fixture publication and squash using its exact archived diff.'
    }
    $closed = New-TestRevision $merged
    Test-Publication 'Close-only follow-up uses the original record' $single $merged $closed
    Test-Publication 'historical Close cannot cover product changes' $single $base $closed 'changing that evidence file alone'
    $closeText = Get-Content -LiteralPath $evidence -Raw
    $wrongLane = [regex]::new('lane\*\*: lightweight').Replace($closeText, 'lane**: feature', 1)
    Set-Content -LiteralPath $evidence -Value $wrongLane
    Test-Publication 'integration Close cannot become Feature acceptance' $single $merged (New-TestRevision $closed) 'historical delivery lane'
    $abandoned = $closeText.Replace('status**: delivered', 'status**: abandoned').Replace('outcome**: merged', 'outcome**: closed')
    $abandoned = $abandoned.Replace("merged_revision**: $merged", 'merged_revision**: null').Replace("effective_head**: $merged", 'effective_head**: null').Replace('merged_at**: 2026-11-23T17:46:03Z', 'merged_at**: null')
    Set-Content -LiteralPath $evidence -Value $abandoned
    Test-Publication 'closed unmerged result keeps null merge fields' $single $merged (New-TestRevision $closed)
    $superseded = $abandoned.Replace('status**: abandoned', 'status**: superseded').Replace('outcome**: closed', "outcome**: superseded`n- **reason**: replaced`n- **superseded_by**: #43")
    Set-Content -LiteralPath $evidence -Value $superseded
    Test-Publication 'superseded result with replacement and reason' $single $merged (New-TestRevision $closed)
    Set-Content -LiteralPath $evidence -Value ($closeText.Replace("merged_revision**: $merged", 'merged_revision**: pending'))
    Test-Publication 'merged Close requires a merge SHA' $single $merged (New-TestRevision $closed) 'full merged_revision'
    Set-Content -LiteralPath $evidence -Value ($closeText.Replace('2026-11-25T10:07:40Z', '2026-11-23T17:45:41Z'))
    Test-Publication 'observation cannot predate the merge' $single $merged (New-TestRevision $closed) 'at or after merged_at'
    Set-Content -LiteralPath $evidence -Value ($closeText.Replace('CI pending at review time.', 'Claim changed in hindsight.'))
    Test-Publication 'published review history is immutable through Close' $single $merged (New-TestRevision $closed) 'preserve the previously published'
    Remove-Item -LiteralPath "$fixture/after-review.txt"
    $incomplete = $closeText -replace '(?m)^- \*\*reviewed_head\*\*: [a-f0-9]{40}\r?$', ''
    Set-Content -LiteralPath $evidence -Value ($incomplete.Replace('## Current delivery outcome', "## Current delivery outcome`n- **reviewed_head**: $unreviewed"))
    Test-Publication 'Close metadata cannot supply missing historical review on recovery' $single $missing (New-TestRevision $missing) 'missing field: reviewed_head'
    Remove-Item -LiteralPath $evidence
    Test-Publication 'deleted evidence' $single $published (New-TestRevision $published) 'Missing regular evidence'
    $link = 'README.md' | & git -C $fixture hash-object -w --stdin
    & git -C $fixture update-index --add --cacheinfo "120000,$link,$path"
    $linkTree = & git -C $fixture write-tree
    $linkHead = & git -C $fixture commit-tree $linkTree -p $base -m symlink
    Test-Publication 'a symbolic link cannot stand in for a record' $single $base $linkHead 'Missing regular evidence'

    $harnessPath = 'harness/evidence/governance.md'
    $harnessBody = $single.Replace($path, $harnessPath)
    $null = [IO.Directory]::CreateDirectory("$fixture/harness/evidence")
    $harness = @"
- feature_id: fixture
- phase_id: governance
- base_revision: $base
- head_revision: working-tree
- working_directory: fixture
- recorded_at: 2026-11-25
- result: pass
- limitations: Local fixture only.
"@
    Set-Content -LiteralPath "$fixture/$harnessPath" -Value $harness
    Test-Publication 'Harness evidence needs its build log in the head' $harnessBody $base (New-TestRevision $base) 'reference the Harness evidence'
    Set-Content -LiteralPath "$fixture/harness/build-log.md" -Value $harnessPath
    Test-Publication 'a single Harness governance PR' $harnessBody $base (New-TestRevision $base)
    $null = [IO.Directory]::CreateDirectory("$fixture/packages/core")
    Set-Content -LiteralPath "$fixture/packages/core/pyproject.toml" -Value '[project]'
    Test-Publication 'Harness governance cannot replace package Delivery evidence' $harnessBody $base (New-TestRevision $base) 'require the Delivery run evidence'
    Remove-Item -LiteralPath "$fixture/packages/core/pyproject.toml"
    Set-Content -LiteralPath "$fixture/$harnessPath" -Value ($harness.Replace('result: pass', 'result: blocked'))
    Test-Publication 'blocked Harness evidence' $harnessBody $base (New-TestRevision $base) 'passing result'
    Test-Publication 'guide is not Harness evidence' ($harnessBody.Replace('governance.md', 'README.en.md')) $base $missing 'canonical Delivery or Harness'
    Write-Host "PR evidence regression passed: $count scenarios."
} finally {
    if ([IO.Path]::GetDirectoryName($fixture) -eq [IO.Path]::GetTempPath().TrimEnd([IO.Path]::DirectorySeparatorChar)) {
        Remove-Item -LiteralPath $fixture -Recurse -Force
    }
}
exit 0
