#Requires -Version 7.0
<#
.SYNOPSIS
Check the shared evidence named by a GitHub pull_request event against its actual head.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$EventPath,
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
. (Join-Path $PSScriptRoot 'evidence-records.ps1')

function Get-PublicationFields {
    param([string]$Body)
    Add-Type -AssemblyName Markdig.Signed
    $fields = @{}
    foreach ($block in [Markdig.Markdown]::Parse($Body)) {
        # Only literal declarations in top-level paragraphs count. Quoted examples,
        # HTML comments, and fenced code are common in handoffs.
        if ($block -isnot [Markdig.Syntax.ParagraphBlock]) { continue }
        $paragraph = $Body.Substring($block.Span.Start, $block.Span.Length)
        foreach ($line in ($paragraph -split '\r?\n')) {
            if ($line -cmatch '^Delivery-(Evidence|Stack):[ \t]*(.*)$') {
                $key = $Matches[1]
                if ($fields.ContainsKey($key)) { throw "Duplicate Delivery-$key declaration." }
                $fields[$key] = $Matches[2].Trim()
            }
        }
    }
    foreach ($key in @('Evidence', 'Stack')) {
        if (-not $fields[$key]) { throw "Missing Delivery-$key declaration in the PR body." }
    }
    return $fields
}

function Get-TreeBlob {
    param([string]$Revision, [string]$Path)
    $entry = & git -C $Root ls-tree --full-tree $Revision -- $Path
    if ($LASTEXITCODE -ne 0) { throw "Cannot read Git tree $Revision." }
    if (-not $entry) { return '' }
    if ($entry -cnotmatch '^100(?:644|755) blob ([0-9a-f]{40})\t') {
        throw "Missing regular evidence file at $Revision / $Path."
    }
    return $Matches[1]
}

$event = Get-Content -LiteralPath $EventPath -Raw -Encoding utf8 | ConvertFrom-Json -AsHashtable
$pr = $event['pull_request']
if (-not $pr) { throw 'Expected a pull_request event.' }
$head = $pr.head.sha
$base = $pr.base.sha
$branch = $pr.head.ref
if ($head -notmatch '^[0-9a-f]{40}$' -or $base -notmatch '^[0-9a-f]{40}$' -or -not $branch) {
    throw 'The event must identify the full PR base SHA, head SHA and source branch.'
}
$publication = Get-PublicationFields ([string]$pr.body)
$path = $publication.Evidence
$nativePath = $path -cmatch '^\.specify/delivery/([a-zA-Z0-9][a-zA-Z0-9._-]{0,79})/evidence\.md$'
if ($nativePath) {
    $run = $Matches[1]
    if ($run.Contains('..') -or $run.EndsWith('.') -or $run -match '^(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)') {
        throw 'Invalid Delivery run in the evidence path.'
    }
} elseif ($path -cnotmatch '^harness/evidence/[a-zA-Z0-9][a-zA-Z0-9._-]*\.md$' -or
    $path -match '/README(?:\.en)?\.md$' -or $path.Contains('..')) {
    throw 'Expected a canonical Delivery or Harness evidence path.'
}

$mergeBase = & git -C $Root merge-base $base $head
if ($LASTEXITCODE -ne 0 -or -not $mergeBase) { throw 'Cannot resolve the PR merge base. Fetch both event revisions.' }
if ($publication.Stack -ceq 'stacked') {
    if (-not $nativePath) { throw 'A Delivery stack must name its canonical run evidence.' }
    $mapPath = ".specify/delivery/$run/publication-branches.txt"
    $map = Get-TreeBlob $head $mapPath
    if (-not $map) { throw "Missing approved publication branches in the PR head at $mapPath." }
    $priorMap = Get-TreeBlob $mergeBase $mapPath
    if ($priorMap -and $priorMap -cne $map) { throw 'This layer must use the previously published branch order.' }
    $layers = @(& git -C $Root cat-file blob $map)
    if ($LASTEXITCODE -ne 0) { throw "Cannot read $mapPath." }
    $seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach ($layer in $layers) {
        & git check-ref-format "refs/heads/$layer"
        if ($LASTEXITCODE -ne 0 -or $layer.StartsWith('-') -or -not $seen.Add($layer)) {
            throw 'The publication map must list valid, distinct source branch names in publication order.'
        }
    }
    if ($layers.Count -lt 2 -or -not $seen.Contains($branch)) {
        throw 'The publication map must include the actual PR source branch and at least two layers.'
    }
    if ($layers[-1] -cne $branch) {
        Write-Host "Intermediate PR ($branch). The final PR ($($layers[-1])) must publish $path."
        return
    }
} elseif ($publication.Stack -cne 'single') {
    throw 'Delivery-Stack must be single or stacked.'
}

$blob = Get-TreeBlob $head $path
if (-not $blob) { throw "Missing regular evidence file in PR head $head at $path." }
$previous = Get-TreeBlob $mergeBase $path
if ($previous -ceq $blob) { throw "The PR must add or update its own evidence: $path." }
$record = (& git -C $Root cat-file blob $blob) -join "`n"
if ($LASTEXITCODE -ne 0 -or -not $record) { throw "Cannot read evidence blob $blob." }
$parts = Split-DeliveryEvidence $record
$snapshot = $parts.History
$fields = Get-EvidenceFields $snapshot
$closed = $nativePath -and $null -ne $parts.Outcome
if ($closed) {
    # A follow-up may publish the original run's Close result, including a historical
    # recovery. That result cannot serve as the acceptance record for other changes.
    $changes = @(& git -C $Root diff --name-only --no-renames $mergeBase $head)
    if ($LASTEXITCODE -ne 0 -or $changes.Count -ne 1 -or $changes[0] -cne $path) {
        throw 'A closed run can only be cited by a follow-up changing that evidence file alone.'
    }
    $outcome = $parts.Outcome
    $statusByOutcome = @{ merged = 'delivered'; closed = 'abandoned'; superseded = 'superseded' }
    if ($outcome['delivery_run'] -cne $run -or ($fields['delivery_run'] -and $fields['delivery_run'] -cne $run) -or -not $outcome['outcome'] -or
        -not $statusByOutcome.ContainsKey($outcome['outcome']) -or $statusByOutcome[$outcome['outcome']] -ne $outcome['status']) {
        throw 'The Close outcome must identify this run and its matching terminal status.'
    }
    if ($outcome['lane'] -notin @('feature', 'bugfix', 'lightweight') -or
        ($fields['lane'] -in @('feature', 'bugfix', 'lightweight') -and $outcome['lane'] -ne $fields['lane'])) {
        throw 'The Close lane must match the historical delivery lane.'
    }
    if ($fields['reviewed_head'] -and $outcome['reviewed_head'] -ne $fields['reviewed_head']) {
        throw 'The Close reviewed_head must match the historical review.'
    }
    if ($outcome['outcome'] -eq 'merged') {
        if ("$($outcome['merged_revision'])" -notmatch '^[a-f0-9]{40}$') { throw 'Merged Close requires a full merged_revision.' }
        if ($outcome['effective_head'] -ne $outcome['merged_revision']) { throw 'Merged Close must use the merged_revision as effective_head.' }
        $mergedAt = [datetimeoffset]::MinValue
        $observedAt = [datetimeoffset]::MinValue
        if (-not [datetimeoffset]::TryParse($outcome['merged_at'], [ref]$mergedAt) -or
            -not [datetimeoffset]::TryParse($outcome['observed_at'], [ref]$observedAt) -or $observedAt -lt $mergedAt) {
            throw 'Merged Close requires an observation at or after merged_at.'
        }
    } elseif ($outcome['outcome'] -eq 'superseded' -and (-not $outcome['superseded_by'] -or -not $outcome['reason'])) {
        throw 'Superseded Close requires a replacement and a reason.'
    } elseif ($outcome['outcome'] -eq 'closed' -and (-not $outcome['pull_request'] -or
        $outcome['merged_revision'] -ne 'null' -or $outcome['effective_head'] -ne 'null' -or $outcome['merged_at'] -ne 'null')) {
        throw 'Abandoned Close requires the original PR reference and null merge fields.'
    }
    if ($previous) {
        $oldRecord = (& git -C $Root show "${mergeBase}:$path") -join "`n"
        if ($LASTEXITCODE -ne 0) { throw 'Could not read the previous evidence.' }
        $oldHistory = (Split-DeliveryEvidence $oldRecord).History
        if (-not $snapshot.Contains($oldHistory, [StringComparison]::Ordinal)) {
            throw 'Close must preserve the previously published validation history.'
        }
    }
}
$native = $nativePath -and (-not $closed -or (Test-NativeEvidenceFormat $fields))
$issues = @(Get-EvidenceRecordIssues $path $snapshot $fields -Native:$native)
if ($issues.Count) { throw "$path — $($issues -join ', ')" }
if ($nativePath -and -not $closed) {
    $reference = $fields['pull_request']
    $repo = $event.repository.full_name
    $number = [string]$pr.number
    if ($reference -notin @('pending', 'none', 'not-created', 'not-published', 'not-yet-published',
            $number, "#$number", "$repo#$number", "https://github.com/$repo/pull/$number")) {
        throw 'The evidence names a different pull request.'
    }
    # Evidence is written after Review. An evidence-only publication can have a new
    # commit SHA; every other file, including the approved stack map, must still match.
    $reviewed = $fields['reviewed_head']
    & git -C $Root cat-file -e "$reviewed^{commit}" 2>$null
    if ($LASTEXITCODE -ne 0) { throw 'The reviewed_head in the publication summary must be available to PR CI for comparison.' }
    & git -C $Root diff --quiet --no-ext-diff --no-textconv --ignore-submodules=none $reviewed $head -- . ":(top,exclude,literal)$path"
    if ($LASTEXITCODE -ne 0) { throw 'The PR tree differs from the reviewed_head outside its evidence file. Refresh Review and Evidence.' }
} elseif (-not $nativePath) {
    if (($fields['result'] -split '\s+', 2)[0] -ne 'pass') { throw 'Final Harness evidence must record a passing result.' }
    & git -C $Root diff --quiet $mergeBase $head -- packages/
    if ($LASTEXITCODE -ne 0) { throw 'Changes to distributions under packages/ require the Delivery run evidence.' }
    $log = (& git -C $Root show "${head}:harness/build-log.md" 2>$null) -join "`n"
    if ($LASTEXITCODE -ne 0 -or -not $log.Contains([IO.Path]::GetFileName($path))) {
        throw 'The PR head must reference the Harness evidence from harness/build-log.md.'
    }
}
Write-Host "Verified shared evidence in PR head $head at $path."
