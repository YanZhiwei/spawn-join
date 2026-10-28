#Requires -Version 7.0
<##
.SYNOPSIS
Validate tracked governance records without modifying the repository.

.DESCRIPTION
Checks evidence metadata, build-log linkage, ADR index consistency, local Spec/Tasks
state, and tracked Markdown links that point at Git-ignored paths. Freshness issues
are warnings because whether an old record still applies needs human judgement.

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

$script:errorCount = 0
$script:warningCount = 0
$script:isShallow = $false
$script:headCommit = ''
$resultWords = @('pass', 'fail', 'blocked', 'skipped', 'not-run')
$adrStatusWords = @('Proposed', 'Accepted', 'Rejected', 'Deprecated', 'Superseded')

function Add-CheckError {
    param([string]$Path, [string]$Message)
    Write-Host "ERROR: ${Path}: $Message"
    $script:errorCount++
}

function Add-CheckWarning {
    param([string]$Path, [string]$Message)
    Write-Host "WARN: ${Path}: $Message"
    $script:warningCount++
}

function Get-RelativePath {
    param([string]$Base, [string]$Path)
    return [IO.Path]::GetRelativePath($Base, $Path).Replace('\', '/')
}

function Read-Text {
    param([string]$Path)
    $text = Get-Content -LiteralPath $Path -Raw -ErrorAction Stop
    if ($null -eq $text) { return '' }
    return $text
}

function Get-EvidenceFields {
    param([string]$Text)
    $fields = @{}
    $patterns = @(
        '^\s*(?:-\s*)?\*\*([A-Za-z_]+)\*\*\s*:\s*(.*?)\s*$',
        '^\s*(?:-\s*)?([A-Za-z_]+)\s*:\s*(.*?)\s*$'
    )
    foreach ($line in ($Text -split "\r?\n")) {
        foreach ($pattern in $patterns) {
            if ($line -match $pattern) {
                $key = $Matches[1].ToLowerInvariant()
                $value = $Matches[2].Trim().Trim('`').Trim()
                if (-not $fields.ContainsKey($key) -and $value) {
                    $fields[$key] = $value
                }
                break
            }
        }
    }
    return $fields
}

function Test-Revision {
    param([string]$Path, [string]$Field, [string]$Value)
    $text = $Value.Trim()
    if ($text -match '^(?i)working-tree\b') { return }

    if ($text -match '([0-9a-f]{40})') {
        $revision = $Matches[1]
        & git -C $rootPath cat-file -e "$revision^{commit}" 2>$null
        if ($LASTEXITCODE -ne 0) {
            if ($script:isShallow) {
                Add-CheckWarning $Path "$Field is not in this shallow clone: $revision"
            } else {
                Add-CheckError $Path "$Field is not a commit in this repository: $revision"
            }
        }
        return
    }

    if ($text -match '(?i)(?<![0-9a-f])[0-9a-f]{7,39}(?![0-9a-f])') {
        Add-CheckError $Path "$Field must use a full 40-character SHA or working-tree; got: $text"
        return
    }
    Add-CheckError $Path "$Field must be a full 40-character SHA or working-tree; got: $text"
}

function Test-Evidence {
    $evidenceDir = Join-Path $rootPath 'harness/evidence'
    if (-not (Test-Path -LiteralPath $evidenceDir -PathType Container)) { return }

    $buildLogPath = Join-Path $rootPath 'harness/build-log.md'
    $buildLog = if (Test-Path -LiteralPath $buildLogPath) {
        Read-Text $buildLogPath
    } else { '' }
    if (-not $buildLog) {
        Add-CheckError 'harness/build-log.md' 'missing or empty evidence build log'
    }

    $required = @('feature_id', 'phase_id', 'base_revision', 'head_revision',
        'working_directory', 'recorded_at', 'result')
    $files = @(Get-ChildItem -LiteralPath $evidenceDir -File -Filter '*.md' |
            Where-Object { $_.Name -ne 'README.md' })

    foreach ($file in $files) {
        $relative = Get-RelativePath $rootPath $file.FullName
        $text = Read-Text $file.FullName
        $fields = Get-EvidenceFields $text

        foreach ($field in $required) {
            if (-not $fields.ContainsKey($field) -or -not $fields[$field]) {
                Add-CheckError $relative "missing field: $field"
            }
        }

        if ($fields.ContainsKey('result')) {
            $word = ($fields['result'] -split '\s+', 2)[0].ToLowerInvariant()
            if ($word -notin $resultWords) {
                Add-CheckError $relative "invalid result: $($fields['result'])"
            }
        }

        if ($fields.ContainsKey('recorded_at') -and
            $fields['recorded_at'] -notmatch '^\d{4}-\d{2}-\d{2}') {
            Add-CheckError $relative "recorded_at must start with YYYY-MM-DD"
        }

        if ($text -notmatch '(?im)^#{2,4}\s+.*limitation' -and
            -not $fields.ContainsKey('limitations')) {
            Add-CheckError $relative 'missing limitations field or section'
        }

        if ($buildLog -and $buildLog -notmatch [regex]::Escape($file.Name)) {
            Add-CheckError $relative "not referenced from harness/build-log.md"
        }

        foreach ($field in @('base_revision', 'head_revision')) {
            if ($fields.ContainsKey($field)) {
                Test-Revision $relative $field $fields[$field]
            }
        }

        if ($fields.ContainsKey('head_revision') -and
            $fields['head_revision'] -match '([0-9a-f]{40})' -and $script:headCommit) {
            $head = $Matches[1]
            & git -C $rootPath merge-base --is-ancestor $head HEAD 2>$null
            if ($LASTEXITCODE -eq 0) {
                $behind = (& git -C $rootPath rev-list --count "$head..HEAD").Trim()
                $changed = @(& git -C $rootPath diff --name-only "$head..HEAD")
                $material = @($changed | Where-Object {
                        $_ -and
                        $_ -notmatch '^(docs/|harness/|specs/)' -and
                        $_ -notmatch '^(README|AGENTS)\.md$' -and
                        $_ -notmatch '\.(md|svg|png|gif)$'
                    })
                if ([int]$behind -gt 0 -and $material.Count -gt 0) {
                    Add-CheckWarning $relative ("head_revision is $behind commit(s) behind HEAD; " +
                        "material paths changed since then (for example $($material[0]))")
                }
            } elseif ($head -ne $script:headCommit) {
                if ($script:isShallow) {
                    Add-CheckWarning $relative 'cannot verify freshness in this shallow clone'
                } else {
                    Add-CheckWarning $relative 'head_revision is not an ancestor of HEAD'
                }
            }
        }
    }
}

function Test-DeliveryEvidence {
    $deliveryDir = Join-Path $rootPath '.specify/delivery'
    if (-not (Test-Path -LiteralPath $deliveryDir -PathType Container)) { return }

    $required = @('feature_id', 'phase_id', 'base_revision', 'head_revision',
        'working_directory', 'recorded_at', 'result')
    $files = @(Get-ChildItem -LiteralPath $deliveryDir -Recurse -File -Filter 'evidence.md')

    foreach ($file in $files) {
        $relative = Get-RelativePath $rootPath $file.FullName
        $text = Read-Text $file.FullName
        $fields = Get-EvidenceFields $text

        foreach ($field in $required) {
            if (-not $fields.ContainsKey($field) -or -not $fields[$field]) {
                Add-CheckError $relative "missing field: $field"
            }
        }

        if ($fields.ContainsKey('result')) {
            $word = ($fields['result'] -split '\s+', 2)[0].ToLowerInvariant()
            if ($word -notin $resultWords) {
                Add-CheckError $relative "invalid result: $($fields['result'])"
            }
        }

        if ($fields.ContainsKey('recorded_at') -and
            $fields['recorded_at'] -notmatch '^\d{4}-\d{2}-\d{2}') {
            Add-CheckError $relative 'recorded_at must start with YYYY-MM-DD'
        }

        if ($text -notmatch '(?im)^#{2,4}\s+.*limitation' -and
            -not $fields.ContainsKey('limitations')) {
            Add-CheckError $relative 'missing limitations field or section'
        }

        foreach ($field in @('base_revision', 'head_revision')) {
            if ($fields.ContainsKey($field)) {
                Test-Revision $relative $field $fields[$field]
            }
        }
    }
}

function Test-Delivery {
    $configPath = Join-Path $rootPath '.specify/extensions/delivery/delivery-config.yml'
    if (-not (Test-Path -LiteralPath $configPath)) { return }

    $relative = Get-RelativePath $rootPath $configPath
    $text = Read-Text $configPath
    $requiredSettings = [ordered]@{
        'version=1'                         = '(?m)^version:\s*1\s*$'
        'artifact_policy=ephemeral'         = '(?m)^artifact_policy:\s*ephemeral\s*$'
        'adr_directories includes docs/decisions' = '(?m)^adr_directories:\s*.*docs/decisions'
        'artifacts.policy=ephemeral'        = '(?m)^\s*policy:\s*ephemeral\s*$'
        'ralph.branch_prefix=ralph/'        = '(?m)^\s*branch_prefix:\s*ralph/\s*$'
        'ralph.parallel_workers=false'      = '(?m)^\s*parallel_workers:\s*false\s*$'
        'ralph.auto_push=false'             = '(?m)^\s*auto_push:\s*false\s*$'
        'ralph.auto_merge=false'            = '(?m)^\s*auto_merge:\s*false\s*$'
        'ralph.evidence_root=.specify/delivery/' = '(?m)^\s*evidence_root:\s*\.specify/delivery/\s*$'
        'ralph.task_gate=RALPH_TASK_GATE: PASS'  = '(?m)^\s*task_gate:\s*(?:"RALPH_TASK_GATE:\s*PASS"|''RALPH_TASK_GATE:\s*PASS'')\s*$'
    }
    foreach ($name in $requiredSettings.Keys) {
        if ($text -notmatch $requiredSettings[$name]) {
            Add-CheckError $relative "missing or invalid setting: $name"
        }
    }

    $requiredPaths = @(
        '.specify/memory/constitution.md'
        'AGENTS.md'
        'docs/architecture'
        'docs/decisions'
        'scripts/quality.ps1'
        'scripts/test-quality.ps1'
        'scripts/test-governance.ps1'
        'scripts/test-static.ps1'
    )
    foreach ($path in $requiredPaths) {
        if (-not (Test-Path -LiteralPath (Join-Path $rootPath $path))) {
            Add-CheckError $relative "referenced path is missing: $path"
        }
    }

}

function Test-ExtensionSettings {
    $extensionsPath = Join-Path $rootPath '.specify/extensions.yml'
    if (-not (Test-Path -LiteralPath $extensionsPath)) { return }
    $extensionsText = Read-Text $extensionsPath
    if ($extensionsText -match '(?m)^\s*auto_execute_hooks:\s*true\s*$') {
        Add-CheckError (Get-RelativePath $rootPath $extensionsPath) `
            'auto_execute_hooks must be false; Delivery requires explicit hook authorization'
    }
}

function Test-Decisions {
    $decisionsDir = Join-Path $rootPath 'docs/decisions'
    if (-not (Test-Path -LiteralPath $decisionsDir -PathType Container)) { return }

    $indexPath = Join-Path $decisionsDir 'README.md'
    if (-not (Test-Path -LiteralPath $indexPath)) {
        Add-CheckError 'docs/decisions/README.md' 'missing decision index'
        return
    }

    $indexText = Read-Text $indexPath
    $index = @{}
    $rowPattern = '^\|\s*ADR-(\d{4})\s*\|[^|\r\n]*\|\s*\[[^\]\r\n]+\]\(([^)\r\n]+)\)\s*\|\s*([A-Za-z]+)\s*\|'
    foreach ($line in ($indexText -split "\r?\n")) {
        if ($line -match $rowPattern) {
            $number = $Matches[1]
            if ($index.ContainsKey($number)) {
                Add-CheckError 'docs/decisions/README.md' "duplicate index entry: ADR-$number"
                continue
            }
            $index[$number] = @{ Target = $Matches[2].Trim(); Status = $Matches[3] }
        }
    }

    $seen = @{}
    $adrFiles = @(Get-ChildItem -LiteralPath $decisionsDir -Recurse -File -Filter '*.md' |
            Where-Object { $_.Name -match '^\d{4}-' })

    foreach ($file in $adrFiles) {
        $number = $file.Name.Substring(0, 4)
        $relative = Get-RelativePath $rootPath $file.FullName
        if ($seen.ContainsKey($number)) {
            Add-CheckError $relative "duplicate ADR number: $number"
        }
        $seen[$number] = $true

        $text = Read-Text $file.FullName
        if ($text -notmatch '(?m)^-\s*Status:\s*([A-Za-z]+)') {
            Add-CheckError $relative 'missing Status field'
            continue
        }
        $fileStatus = $Matches[1]
        if ($fileStatus -notin $adrStatusWords) {
            Add-CheckError $relative "invalid ADR status: $fileStatus"
        }

        if (-not $index.ContainsKey($number)) {
            Add-CheckError 'docs/decisions/README.md' "ADR-$number file exists but is not indexed"
            continue
        }
        $entry = $index[$number]
        $target = [IO.Path]::GetFullPath((Join-Path $decisionsDir $entry.Target))
        if ($target -ne $file.FullName) {
            Add-CheckError 'docs/decisions/README.md' "ADR-$number index target does not match its file"
        }
        if ($entry.Status -ne $fileStatus) {
            Add-CheckError 'docs/decisions/README.md' "ADR-$number status differs from its file"
        }

        if ($text -match '(?m)^-\s*Superseded by:\s*(.+)$') {
            $superseded = $Matches[1].Trim()
            if ($superseded -and $superseded -notin @('无', 'None', 'none') -and
                $superseded -match '\(([^)]+)\)') {
                $linkTarget = [IO.Path]::GetFullPath((Join-Path $file.DirectoryName $Matches[1]))
                if (-not (Test-Path -LiteralPath $linkTarget)) {
                    Add-CheckError $relative "Superseded by target does not exist: $superseded"
                }
            }
        }
    }

    foreach ($number in $index.Keys) {
        $target = [IO.Path]::GetFullPath((Join-Path $decisionsDir $index[$number].Target))
        if (-not (Test-Path -LiteralPath $target)) {
            Add-CheckError 'docs/decisions/README.md' "ADR-$number index target is missing"
        }
    }
}

function Test-Specs {
    $specsDir = Join-Path $rootPath 'specs'
    if (-not (Test-Path -LiteralPath $specsDir -PathType Container)) { return }

    foreach ($directory in @(Get-ChildItem -LiteralPath $specsDir -Directory)) {
        $specPath = Join-Path $directory.FullName 'spec.md'
        if (-not (Test-Path -LiteralPath $specPath)) { continue }
        $relativeSpec = Get-RelativePath $rootPath $specPath
        $specText = Read-Text $specPath
        if ($specText -notmatch '(?m)^\*\*Status\*\*:\s*(.+)$') {
            Add-CheckWarning $relativeSpec 'missing Status field'
            continue
        }
        $status = $Matches[1].Trim()

        $tasksPath = Join-Path $directory.FullName 'tasks.md'
        if (-not (Test-Path -LiteralPath $tasksPath)) { continue }
        $relativeTasks = Get-RelativePath $rootPath $tasksPath
        $tasksText = Read-Text $tasksPath

        if ($status -match '^Implemented' -and $tasksText -match '(?m)^-\s*\[\s\]\s') {
            Add-CheckError $relativeSpec 'Status is Implemented but tasks.md has unchecked items'
        }

        $ids = @([regex]::Matches($tasksText, '(?m)^-\s*\[[ xX]\]\s*T(\d{3})\b') |
                ForEach-Object { [int]$_.Groups[1].Value })
        if ($ids.Count -eq 0) { continue }
        if (@($ids | Sort-Object -Unique).Count -ne $ids.Count) {
            Add-CheckError $relativeTasks 'duplicate task IDs'
        }
        $expected = 1..$ids.Count
        if (@(Compare-Object $expected $ids).Count -gt 0) {
            Add-CheckError $relativeTasks 'task IDs must start at T001 and be sequential'
        }
    }
}

function Test-TrackedLinks {
    $tracked = @(& git -C $rootPath ls-files)
    if ($LASTEXITCODE -ne 0) {
        Add-CheckError 'git' 'unable to list tracked files'
        return
    }

    foreach ($relativeFile in $tracked) {
        if ($relativeFile -notmatch '\.md$') { continue }
        # Vendor prompts/docs retain upstream links; project policy/evidence stays checked.
        if ($relativeFile -like '.agents/skills/*' -or
            $relativeFile -like '.opencode/commands/*' -or
            $relativeFile -like '.specify/extensions/*') { continue }
        $fullPath = Join-Path $rootPath $relativeFile
        if (-not (Test-Path -LiteralPath $fullPath)) { continue }
        $text = Read-Text $fullPath

        foreach ($match in [regex]::Matches($text, '\[[^\]]+\]\(([^)]+)\)')) {
            $target = ($match.Groups[1].Value -split '#', 2)[0].Trim()
            if (-not $target -or $target -match '^(https?://|mailto:)') { continue }

            $resolved = [IO.Path]::GetFullPath((Join-Path (Split-Path -Parent $fullPath) $target))
            if (-not (Test-Path -LiteralPath $resolved)) {
                Add-CheckError $relativeFile "missing link target: $target"
                continue
            }
            # Directory links are validated for existence above; Git tracks files, not directories.
            if (Test-Path -LiteralPath $resolved -PathType Container) { continue }

            $resolvedRelative = Get-RelativePath $rootPath $resolved
            if ($resolvedRelative.StartsWith('..')) { continue }

            & git -C $rootPath check-ignore -q --no-index -- $resolvedRelative 2>$null
            if ($LASTEXITCODE -eq 0) {
                Add-CheckError $relativeFile "links to local-only path: $resolvedRelative"
            }
        }
    }
}

Push-Location $rootPath
try {
    & git -C $rootPath rev-parse --is-inside-work-tree *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "Not a Git repository: $rootPath"
    }
    $script:isShallow = ((& git -C $rootPath rev-parse --is-shallow-repository).Trim() -eq 'true')
    & git -C $rootPath rev-parse --verify HEAD *> $null
    if ($LASTEXITCODE -eq 0) {
        $script:headCommit = (& git -C $rootPath rev-parse HEAD).Trim()
    }

    Test-Evidence
    Test-DeliveryEvidence
    Test-Delivery
    Test-ExtensionSettings
    Test-Decisions
    Test-Specs
    Test-TrackedLinks
} catch {
    Add-CheckError 'governance' $_.Exception.Message
} finally {
    Pop-Location
}

Write-Host "Governance checks: $($script:errorCount) error(s), $($script:warningCount) warning(s)."
if ($script:errorCount -gt 0) { exit 1 }
exit 0
