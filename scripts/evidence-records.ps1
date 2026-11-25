# The native Close block can describe a different base and head from the original review.
function Split-DeliveryEvidence {
    param([string]$Text)
    $text = $Text.Replace("`r`n", "`n")
    $begin = '<!-- DELIVERY_CURRENT_OUTCOME_BEGIN -->'
    if (-not $text.StartsWith($begin, [StringComparison]::Ordinal)) { return @{ History = $text; Outcome = $null } }
    $block = [regex]::Match($text, '(?ms)\A<!-- DELIVERY_CURRENT_OUTCOME_BEGIN -->\n## Current delivery outcome\n.*?^<!-- DELIVERY_CURRENT_OUTCOME_END -->$')
    if (-not $block.Success) { throw 'Expected a complete Delivery Close outcome block at the start of the record.' }
    $history = $text.Remove($block.Index, $block.Length).TrimStart("`n")
    if ($history -match '(?m)^<!-- DELIVERY_CURRENT_OUTCOME_BEGIN -->\n## Current delivery outcome$') {
        throw 'Evidence contains more than one current Delivery outcome.'
    }
    $heading = "## Historical validation snapshots`n`n"
    $notice = '<!-- Existing validation, review, CI, and limitation content below is retained verbatim as historical evidence. -->'
    $prefix = "$heading$notice`n`n"
    if ($history.StartsWith($prefix, [StringComparison]::Ordinal)) { $history = $history.Substring($prefix.Length) }
    return @{ History = $history; Outcome = (Get-EvidenceFields $block.Value) }
}

function Get-EvidenceFields {
    param([string]$Text)
    $fields = @{}
    $pattern = '^\s*(?:[-*]\s*)?(?:\*\*)?(?<key>[A-Za-z][A-Za-z0-9_]*)(?:\*\*)?\s*:\s*(?<value>.*?)\s*$'
    foreach ($line in ($Text -split "\r?\n")) {
        if ($line -match $pattern) {
            $key = $Matches['key']
            $value = $Matches['value'].Trim().Trim('`').Trim()
            if (-not $fields.ContainsKey($key)) { $fields[$key] = $value }
        }
    }
    return $fields
}

function Test-NativeEvidenceFormat {
    param([hashtable]$Fields)
    # Early mixed records have a feature_id; some bind only a native reviewed_head.
    return ($Fields['delivery_run'] -or $Fields['evidence_path']) -and
        -not ($Fields['feature_id'] -and $Fields['head_revision'])
}

function Get-EvidenceRecordIssues {
    param([string]$Path, [string]$Snapshot, [hashtable]$Fields, [switch]$Native)
    if ($Native) {
        $required = @('delivery_run', 'lane', 'evidence_path', 'base_revision', 'reviewed_head',
            'original_pr_head', 'content_fingerprint', 'requirements_fingerprint', 'method_identity', 'pull_request')
        if ($Fields['lane'] -in @('feature', 'bugfix')) { $required += 'exploration_path' }
        if ($Fields['lane'] -eq 'bugfix') { $required += @('bug_slug', 'assessment_path', 'assessment_hash') }
    } else {
        $required = @('feature_id', 'phase_id', 'base_revision', 'head_revision',
            'working_directory', 'recorded_at', 'result')
    }
    foreach ($field in $required) {
        if (-not $Fields[$field]) { "missing field: $field" }
    }
    if ($Snapshot -notmatch '(?im)^#{2,4}[ \t]+[^\r\n]*(?:limitation|限制|未验证)' -and -not $Fields['limitations']) {
        'missing limitations field or section'
    }
    if (-not $Native) {
        if ($Fields['result'] -and ($Fields['result'] -split '\s+', 2)[0] -notin @('pass', 'fail', 'blocked', 'skipped', 'not-run')) {
            "invalid result: $($Fields['result'])"
        }
        if ($Fields['recorded_at'] -and $Fields['recorded_at'] -notmatch '^\d{4}-\d{2}-\d{2}') {
            'recorded_at must start with YYYY-MM-DD'
        }
        return
    }
    if ($Fields['evidence_path'] -cne $Path -or ".specify/delivery/$($Fields['delivery_run'])/evidence.md" -cne $Path) {
        'delivery_run and evidence_path must match the canonical record path'
    }
    if ($Fields['lane'] -notin @('feature', 'bugfix', 'lightweight')) { 'invalid Delivery lane' }
    # Squash merges can make the reviewed commit unreachable in a fresh clone.
    foreach ($name in @('base_revision', 'reviewed_head')) {
        if ($Fields[$name] -and $Fields[$name] -notmatch '^[0-9a-f]{40}$') { "$name must be a full 40-character SHA" }
    }
    if ($Fields['original_pr_head'] -and $Fields['original_pr_head'] -notmatch '^(?:pending|not-yet-published|[0-9a-f]{40})$') {
        'original_pr_head must be pending, not-yet-published or a full SHA'
    }
    foreach ($name in @('content_fingerprint', 'requirements_fingerprint')) {
        if ($Fields[$name] -and $Fields[$name] -notmatch '(?i)(?<![0-9a-f])[0-9a-f]{40,128}(?![0-9a-f])') {
            "$name must identify a digest"
        }
    }
}
