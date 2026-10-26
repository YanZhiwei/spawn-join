#Requires -Version 7.0
<##
.SYNOPSIS
Run read-only quality checks using each Distribution's locked environment.
##>
[CmdletBinding()]
param(
    [ValidateSet('spawn-join-core', 'spawn-join-llm-provider',
        'spawn-join-llm-provider-langchain', 'spawn-join-observability')]
    [string]$Package,

    [ValidateSet('all', 'format', 'lint', 'type', 'test', 'build', 'docs')]
    [string]$Check = 'all'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
$root = Split-Path -Parent $PSScriptRoot
$config = Join-Path $root 'pyproject.toml'
$packages = [ordered]@{
    'spawn-join-core' = @{
        Path = 'packages/core/spawn-join-core'
        Import = 'spawn_join_core'
        Build = @('spawn-join-core')
    }
    'spawn-join-llm-provider' = @{
        Path = 'packages/core/llm-provider'
        Import = 'spawn_join_llm_provider'
        Build = @('spawn-join-core', 'spawn-join-llm-provider')
    }
    'spawn-join-llm-provider-langchain' = @{
        Path = 'packages/infra/llm-provider-langchain'
        Import = 'spawn_join_llm_provider_langchain'
        Build = @('spawn-join-core', 'spawn-join-llm-provider',
            'spawn-join-llm-provider-langchain')
    }
    'spawn-join-observability' = @{
        Path = 'packages/infra/spawn-join-observability'
        Import = 'spawn_join_observability'
        Build = @('spawn-join-core', 'spawn-join-observability')
    }
}

function Invoke-Checked {
    param([string]$Command, [string[]]$Arguments)
    Write-Host "> $Command $($Arguments -join ' ')"
    & $Command @Arguments
    $code = $LASTEXITCODE
    Write-Host "exit_code=$code"
    if ($code -ne 0) {
        throw "Command failed (exit $code): $Command $($Arguments -join ' ')"
    }
}

function Get-VenvPython {
    param([string]$Directory)
    $relative = if ($IsWindows) { 'Scripts/python.exe' } else { 'bin/python' }
    return Join-Path $Directory $relative
}

function Test-Documentation {
    $files = @('README.md', 'AGENTS.md', '.specify/memory/constitution.md')
    foreach ($directory in @('docs', 'harness', 'specs')) {
        if (Test-Path -LiteralPath $directory -PathType Container) {
            $files += @(Get-ChildItem -LiteralPath $directory -Recurse -File -Filter '*.md' |
                ForEach-Object { $_.FullName })
        }
    }
    $linkCount = 0
    foreach ($file in $files) {
        $resolved = (Resolve-Path -LiteralPath $file).Path
        $text = Get-Content -LiteralPath $resolved -Raw
        if ($text -match '(?m)[\t ]+\r?$') {
            throw "Trailing whitespace: $file"
        }
        foreach ($match in [regex]::Matches($text, '\[[^\]]+\]\(([^)]+)\)')) {
            $target = ($match.Groups[1].Value -split '#', 2)[0]
            if ([string]::IsNullOrWhiteSpace($target) -or
                $target -match '^(https?://|mailto:)') { continue }
            $linkCount++
            $destination = Join-Path (Split-Path -Parent $resolved) $target
            if (-not (Test-Path -LiteralPath $destination)) {
                throw "Missing Markdown target: $file -> $target"
            }
        }
    }
    Invoke-Checked 'git' @('diff', '--check')
    Write-Host "Documentation: $($files.Count) files, $linkCount local targets checked."
}

function Copy-BuildSource {
    param([string]$Source, [string]$Destination)
    New-Item -ItemType Directory -Path $Destination | Out-Null
    foreach ($entry in Get-ChildItem -LiteralPath $Source -Force) {
        if ($entry.Name -in @('.venv', 'build', 'dist', '__pycache__',
                '.pytest_cache', '.ruff_cache', '.mypy_cache') -or
            $entry.Name -like '*.egg-info') { continue }
        $target = Join-Path $Destination $entry.Name
        if ($entry.PSIsContainer) {
            Copy-BuildSource $entry.FullName $target
        } else {
            Copy-Item -LiteralPath $entry.FullName -Destination $target
        }
    }
}

function Test-DistributionBuild {
    param([string]$Name, [string]$Python)
    $parent = if ($env:SPAWN_JOIN_TEMP_DIR) {
        (Resolve-Path -LiteralPath $env:SPAWN_JOIN_TEMP_DIR).Path
    } else { [IO.Path]::GetTempPath() }
    $temporary = Join-Path $parent ('spawn-join-quality-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $temporary | Out-Null
    try {
        $wheels = @()
        foreach ($buildName in $packages[$Name].Build) {
            $staging = Join-Path $temporary "staging/$buildName"
            $artifacts = Join-Path $temporary "artifacts/$buildName"
            Copy-BuildSource (Join-Path $root $packages[$buildName].Path) $staging
            Invoke-Checked 'uv' @('build', '--no-sources', '--python', $Python,
                $staging, '--out-dir', $artifacts)
            $builtWheels = @(Get-ChildItem -LiteralPath $artifacts -Filter '*.whl')
            $sdists = @(Get-ChildItem -LiteralPath $artifacts -Filter '*.tar.gz')
            if ($builtWheels.Count -ne 1 -or $sdists.Count -ne 1) {
                throw "Expected one wheel and one sdist for $buildName"
            }
            $wheels += $builtWheels[0].FullName
        }

        $requirements = Join-Path $temporary 'runtime-requirements.txt'
        $export = @('export', '--locked', '--directory', $packages[$Name].Path,
            '--no-dev', '--no-emit-project', '--format', 'requirements-txt',
            '--output-file', $requirements)
        foreach ($localName in $packages.Keys) {
            $export += @('--no-emit-package', $localName)
        }
        Invoke-Checked 'uv' $export
        $venv = Join-Path $temporary 'installed'
        Invoke-Checked 'uv' @('venv', '--python', $Python, $venv)
        $installedPython = Get-VenvPython $venv
        Invoke-Checked 'uv' (@('pip', 'install', '--python', $installedPython,
                '--no-deps', '-r', $requirements) + $wheels)
        Invoke-Checked 'uv' @('pip', 'check', '--python', $installedPython)
        $importName = $packages[$Name].Import
        Invoke-Checked $installedPython @('-I', '-c',
            "import importlib; importlib.import_module('$importName')")
    } finally {
        # This exact unique directory is created and owned by this invocation only.
        Remove-Item -LiteralPath $temporary -Recurse -Force
    }
}

Push-Location $root
try {
    if ($Check -in @('all', 'docs')) { Test-Documentation }
    if ($Check -ne 'docs') {
        Get-Command uv -ErrorAction Stop | Out-Null
        if ($Check -in @('all', 'type')) {
            Get-Command node -ErrorAction Stop | Out-Null
            $nodeVersion = & node --version
            if ($LASTEXITCODE -ne 0 -or $nodeVersion -notmatch '^v(\d+)\.' -or
                [int]$Matches[1] -lt 22) { throw 'Node 22+ is required for Pyright.' }
        }
        $names = if ($Package) { @($Package) } else { @($packages.Keys) }
        foreach ($name in $names) {
            $directory = Join-Path $root $packages[$name].Path
            $source = Join-Path $directory 'src'
            $tests = Join-Path $directory 'tests'
            Write-Host "Checking $name ($Check)"
            Invoke-Checked 'uv' @('lock', '--check', '--directory', $directory)
            Invoke-Checked 'uv' @('sync', '--locked', '--directory', $directory)
            $run = @('run', '--locked', '--no-sync', '--directory', $directory)
            if ($Check -in @('all', 'format')) {
                Invoke-Checked 'uv' ($run + @('black', '--check', '--config',
                        $config, $source, $tests))
                Invoke-Checked 'uv' ($run + @('isort', '--check-only',
                        '--settings-path', $config, $source, $tests))
            }
            if ($Check -in @('all', 'lint')) {
                Invoke-Checked 'uv' ($run + @('ruff', 'check', '--config',
                        $config, $source, $tests))
            }
            $python = Get-VenvPython (Join-Path $directory '.venv')
            if ($Check -in @('all', 'type')) {
                Invoke-Checked 'uv' ($run + @('pyright', '--project', $config,
                        '--pythonpath', $python, $source, $tests))
            }
            if ($Check -in @('all', 'test')) {
                Invoke-Checked 'uv' ($run + @('pytest', '-c', $config, $tests, '-q'))
            }
            if ($Check -in @('all', 'build')) {
                Test-DistributionBuild $name $python
            }
        }
    }
    Write-Host 'Quality checks passed for the requested scope.'
} catch {
    Write-Error -Message $_ -ErrorAction Continue
    exit 1
} finally {
    Pop-Location
}
