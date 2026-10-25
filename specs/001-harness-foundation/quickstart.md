# Harness Foundation Quickstart

## Prerequisites

- 从仓库根目录执行命令；
- 已完成 Spec Kit 初始化；
- PowerShell 可用；
- 当前工作区中的既有修改不应被本 Feature 自动覆盖。

## Inspect the authoritative entries

```powershell
Get-Content -Raw .specify\memory\constitution.md
Get-Content -Raw AGENTS.md
Get-Content -Raw docs\architecture\repository-map.md
Get-Content -Raw docs\architecture\package-boundaries.md
Get-Content -Raw harness\README.md
```

预期：每个文件只描述自己的职责，并能通过相对链接找到相关权威入口。

## Validate local Markdown links

```powershell
$files = @(
    'README.md',
    'AGENTS.md',
    'docs\architecture\repository-map.md',
    'docs\architecture\package-boundaries.md',
    'harness\README.md',
    'harness\build\README.md',
    'harness\context\README.md',
    'harness\code_review\README.md',
    'harness\evidence\README.md'
)

$failed = $false
foreach ($file in $files) {
    $base = Split-Path -Parent (Resolve-Path $file)
    $text = Get-Content -Raw $file
    $matches = [regex]::Matches($text, '\[[^\]]+\]\(([^)]+)\)')
    foreach ($match in $matches) {
        $target = $match.Groups[1].Value -split '#', 2 | Select-Object -First 1
        if ([string]::IsNullOrWhiteSpace($target) -or $target -match '^(https?://|mailto:)') {
            continue
        }
        if (-not (Test-Path (Join-Path $base $target))) {
            Write-Error "$file -> $target"
            $failed = $true
        }
    }
}
if ($failed) { exit 1 }
```

## Validate whitespace and diff boundaries

```powershell
git diff --check
git status --short --branch
```

本 Feature 的文档验证不要求运行 Python 构建或测试。若后续新增执行脚本、hook、依赖或
CI，则必须在新的 Feature 中补充对应的实际验证命令和权限说明。
