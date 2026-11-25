# Shared by the docs and governance gates. Feature selection is always explicit.
function Resolve-LocalFeatureDirectory {
    param([string]$Root, [string]$FeatureDir)
    if (-not $FeatureDir) { return }
    $path = [IO.Path]::GetFullPath($FeatureDir, $Root)
    $relative = [IO.Path]::GetRelativePath($Root, $path).Replace('\', '/').TrimEnd('/')
    if ($relative -cnotmatch '^specs/[^/]+$' -or
        -not (Test-Path -LiteralPath $path -PathType Container)) {
        throw "Feature directory must be an existing specs/<feature-id> directory: $FeatureDir"
    }
    return $path
}

function Get-MarkdownPage {
    param([string]$File, $Pipeline, $Cache)
    if ($Cache.ContainsKey($File)) { return $Cache[$File] }
    $text = [IO.File]::ReadAllText($File)
    $document = [Markdig.Markdown]::Parse($text, $Pipeline)
    $anchors = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    $links = [Collections.Generic.List[object]]::new()
    foreach ($node in [Markdig.Syntax.MarkdownObjectExtensions]::Descendants($document)) {
        if ($node -is [Markdig.Syntax.HeadingBlock]) {
            $id = [Markdig.Renderers.Html.HtmlAttributesExtensions]::GetAttributes($node).Id
            [void]$anchors.Add($id)
        } elseif ($node -is [Markdig.Syntax.Inlines.LinkInline]) {
            $links.Add($node)
        } elseif ($node -is [Markdig.Syntax.Inlines.HtmlInline] -or $node -is [Markdig.Syntax.HtmlBlock]) {
            $html = if ($node -is [Markdig.Syntax.HtmlBlock]) { $node.Lines.ToString() } else { $node.Tag }
            $html = [regex]::Replace($html, '(?s)<!--.*?(?:-->|\z)', '')
            foreach ($tag in [regex]::Matches($html, '(?i)<a\s+[^>]*>')) {
                $attribute = '(?i)\s(?:id|name)\s*=\s*(?:"(?<id>[^"]+)"|''(?<id>[^'']+)''|(?<id>[^\s>]+))'
                foreach ($match in [regex]::Matches($tag.Value, $attribute)) {
                    [void]$anchors.Add([Net.WebUtility]::HtmlDecode($match.Groups['id'].Value))
                }
            }
        }
    }
    $page = [pscustomobject]@{
        Links = $links
        Anchors = $anchors
        TrailingWhitespace = $text -match '(?m)[\t ]+\r?$'
    }
    $Cache[$File] = $page
    return $page
}

function Get-MarkdownIssues {
    param([string]$Root, [string]$FeaturePath, [switch]$CheckWhitespace)
    # Markdig ships with PowerShell 7. Parse Markdown once per target, including reference
    # links and table cells, without treating fenced or inline code as live links.
    Add-Type -AssemblyName Markdig.Signed
    $builder = [Markdig.MarkdownPipelineBuilder]::new()
    $builder.PreciseSourceLocation = $true
    $null = [Markdig.MarkdownExtensions]::UseAutoIdentifiers($builder, [Markdig.Extensions.AutoIdentifiers.AutoIdentifierOptions]::GitHub)
    $null = [Markdig.MarkdownExtensions]::UsePipeTables($builder, $null)
    $null = [Markdig.MarkdownExtensions]::UseYamlFrontMatter($builder)
    $pipeline = $builder.Build()
    $cache = [Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)

    $listed = & git -C $Root ls-files -z --cached --others --exclude-standard -- ':(icase)*.md'
    if ($LASTEXITCODE -ne 0) { throw 'Unable to list repository Markdown files.' }
    $shared = @(($listed -join "`n") -split "`0" | Where-Object {
        $_ -and $_ -notmatch '^(?:specs/|\.agents/skills/|\.opencode/commands/|\.specify/extensions/)' -and
        (Test-Path -LiteralPath (Join-Path $Root $_) -PathType Leaf)
    })
    $local = @()
    if ($FeaturePath) {
        $local = @(Get-ChildItem -LiteralPath $FeaturePath -Recurse -File -Filter '*.md' |
            ForEach-Object { [IO.Path]::GetRelativePath($Root, $_.FullName).Replace('\', '/') })
        if (-not $local.Count) { throw "Feature directory contains no Markdown files: $FeaturePath" }
    }

    $sharedTargets = [Collections.Generic.Dictionary[string,string]]::new([StringComparer]::Ordinal)
    $linkCount = 0
    foreach ($relative in ($shared + $local)) {
        $file = Join-Path $Root $relative
        $page = Get-MarkdownPage $file $pipeline $cache
        # Keep the existing whitespace policy on its owning paths. Historical Delivery
        # records can use Markdown hard line breaks and still have all their links checked.
        if ($CheckWhitespace -and $page.TrailingWhitespace -and
            $relative -match '^(?:README\.md$|AGENTS\.md$|\.specify/memory/constitution\.md$|docs/|harness/|specs/)') {
            "${relative}: trailing whitespace"
        }
        foreach ($link in $page.Links) {
            $url = $link.Url
            if (-not $url -or $url -match '^(?:[a-z][a-z0-9+.-]*:|//)') { continue }
            $parts = $url -split '#', 2
            $path = [Uri]::UnescapeDataString(($parts[0] -split '\?', 2)[0])
            $target = if (-not $path) { $file } elseif ($path.StartsWith('/')) {
                [IO.Path]::GetFullPath($path.TrimStart('/'), $Root)
            } else {
                [IO.Path]::GetFullPath($path, [IO.Path]::GetDirectoryName($file))
            }
            $linkCount++
            $source = "${relative}:$($link.Line + 1)"
            if (-not (Test-Path -LiteralPath $target)) {
                "${source}: missing link target: $url"
                continue
            }
            $destination = [IO.Path]::GetRelativePath($Root, $target).Replace('\', '/').TrimEnd('/')
            if (-not $relative.StartsWith('specs/') -and $destination -notin @('.', '..') -and
                -not $destination.StartsWith('../') -and -not [IO.Path]::IsPathRooted($destination)) {
                $sharedTargets[$destination] = $source
            }
            if ($parts.Count -eq 2 -and $parts[1] -and [IO.Path]::GetExtension($target) -eq '.md' -and
                [IO.File]::Exists($target)) {
                $targetPage = Get-MarkdownPage $target $pipeline $cache
                if (-not $targetPage.Anchors.Contains([Uri]::UnescapeDataString($parts[1]))) {
                    "${source}: missing Markdown anchor: $url"
                }
            }
        }
    }
    # Ask Git once, including for directory links. An explicit Feature never makes an
    # ignored destination shareable from a project document.
    if ($sharedTargets.Count) {
        $paths = ($sharedTargets.Keys -join "`0") + "`0"
        $ignored = $paths | & git -C $Root check-ignore -z --no-index --stdin
        if ($LASTEXITCODE -notin @(0, 1)) { throw 'Unable to check ignored Markdown targets.' }
        foreach ($path in (($ignored -join "`n") -split "`0")) {
            if ($sharedTargets.ContainsKey($path)) { "$($sharedTargets[$path]): links to local-only path: $path" }
        }
    }
    Write-Host "Markdown: $($shared.Count) shared files, $($local.Count) local Feature files, $linkCount local links checked."
}
