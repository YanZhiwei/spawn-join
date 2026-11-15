#Requires -Version 7.0
<##
.SYNOPSIS
Run read-only quality checks using each Distribution's locked environment.
##>
[CmdletBinding()]
param(
    [ValidateSet('spawn-join-core', 'spawn-join-common', 'spawn-join-llm-provider',
        'spawn-join-llm-provider-langchain', 'spawn-join-llm-channel',
        'spawn-join-llm-model-sync', 'spawn-join-agent-deepagents')]
    [string]$Package,

    [ValidateSet('all', 'format', 'lint', 'type', 'test', 'build', 'docs', 'governance', 'static')]
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
    'spawn-join-common' = @{
        Path = 'packages/core/common'
        Import = 'spawn_join_common'
        Build = @('spawn-join-common')
    }
    'spawn-join-llm-provider' = @{
        Path = 'packages/core/llm-provider'
        Import = 'spawn_join_llm_provider'
        Build = @('spawn-join-core', 'spawn-join-common', 'spawn-join-llm-provider')
    }
    'spawn-join-llm-provider-langchain' = @{
        Path = 'packages/infra/llm-provider-langchain'
        Import = 'spawn_join_llm_provider_langchain'
        Build = @('spawn-join-core', 'spawn-join-common', 'spawn-join-llm-provider',
            'spawn-join-llm-provider-langchain')
    }
    'spawn-join-llm-channel' = @{
        Path = 'packages/infra/llm-channel'
        Import = 'spawn_join_llm_channel'
        Build = @('spawn-join-core', 'spawn-join-common', 'spawn-join-llm-provider',
            'spawn-join-llm-channel')
    }
    'spawn-join-llm-model-sync' = @{
        Path = 'packages/infra/llm-model-sync'
        Import = 'spawn_join_llm_model_sync'
        Build = @('spawn-join-core', 'spawn-join-common', 'spawn-join-llm-provider',
            'spawn-join-llm-model-sync')
    }
    'spawn-join-agent-deepagents' = @{
        Path = 'packages/infra/agent-deepagents'
        Import = 'spawn_join_agent_deepagents'
        Build = @('spawn-join-core', 'spawn-join-common', 'spawn-join-llm-provider',
            'spawn-join-llm-provider-langchain', 'spawn-join-agent-deepagents')
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

function Test-CommonInstallVariants {
    param([string]$Directory, [string]$Python, [string]$BasePython, [string]$Wheel)
    $baseProbe = @'
import importlib.util
from importlib import metadata
from importlib.resources import files
from spawn_join_common import FieldReader
assert importlib.util.find_spec("pydantic") is None, "common base installed Pydantic"
assert not any(
    item.metadata["Name"].startswith("spawn-join-")
    and item.metadata["Name"] != "spawn-join-common"
    for item in metadata.distributions()
), "common base installed a domain package"
assert (files("spawn_join_common") / "py.typed").is_file(), "base wheel lacks py.typed"
assert FieldReader().as_int(3, "count") == 3
try:
    FieldReader().as_int(True, "count")
except ValueError as exc:
    assert str(exc) == "count: must be an integer"
else:
    raise AssertionError("common base accepted bool as int")
'@
    Invoke-Checked $BasePython @('-I', '-c', $baseProbe)

    $requirements = Join-Path $Directory 'validation-requirements.txt'
    Invoke-Checked 'uv' @('export', '--locked', '--directory', $packages['spawn-join-common'].Path,
        '--extra', 'validation', '--no-dev', '--no-emit-project', '--no-emit-package',
        'spawn-join-common', '--format', 'requirements-txt', '--output-file', $requirements)
    $extraDirectory = Join-Path $Directory 'installed-validation'
    Invoke-Checked 'uv' @('venv', '--python', $Python, $extraDirectory)
    $extraPython = Get-VenvPython $extraDirectory
    Invoke-Checked 'uv' @('pip', 'install', '--python', $extraPython,
        '--no-deps', '-r', $requirements, "$Wheel[validation]")
    Invoke-Checked 'uv' @('pip', 'check', '--python', $extraPython)
    $extraProbe = @'
from importlib import metadata
from pydantic import TypeAdapter, ValidationError
from spawn_join_common.validation import validate_with
assert not any(
    item.metadata["Name"].startswith("spawn-join-")
    and item.metadata["Name"] != "spawn-join-common"
    for item in metadata.distributions()
), "validation extra installed a domain package"
assert validate_with(
    lambda: 3, error=RuntimeError, message=lambda exc: "unexpected"
) == 3, "validation-extra-success-probe"
def invalid_input():
    return TypeAdapter(int).validate_python("invalid-install-probe")
try:
    validate_with(
        invalid_input, error=RuntimeError, message=lambda exc: "count: invalid"
    )
except RuntimeError as exc:
    assert str(exc) == "count: invalid"
    assert isinstance(exc.__cause__, ValidationError)
else:
    raise AssertionError("validation extra did not convert the original error")
'@
    Invoke-Checked $extraPython @('-I', '-c', $extraProbe)
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
        if ($Name -eq 'spawn-join-common') {
            Test-CommonInstallVariants -Directory $temporary -Python $Python `
                -BasePython $installedPython -Wheel $wheels[0]
        }
    } finally {
        # This exact unique directory is created and owned by this invocation only.
        Remove-Item -LiteralPath $temporary -Recurse -Force
    }
}

Push-Location $root
try {
    # Governance and static analysis are repository-level; package-scoped runs skip them.
    $runGovernance = $Check -eq 'governance' -or ($Check -eq 'all' -and -not $Package)
    $runStatic = $Check -eq 'static' -or ($Check -eq 'all' -and -not $Package)
    if ($runGovernance) {
        Invoke-Checked 'pwsh' @('-NoProfile', '-File',
            (Join-Path $root 'scripts/check-governance.ps1'), '-Root', $root)
    }
    if ($runStatic) {
        Invoke-Checked 'pwsh' @('-NoProfile', '-File',
            (Join-Path $root 'scripts/check-static.ps1'), '-Root', $root)
    }
    if ($Check -in @('all', 'docs')) { Test-Documentation }
    if ($Check -notin @('docs', 'governance', 'static')) {
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
