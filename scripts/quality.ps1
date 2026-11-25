#Requires -Version 7.0
<##
.SYNOPSIS
Run read-only quality checks using each Distribution's locked environment.

.PARAMETER FeatureDir
Include one local specs/<feature-id> directory in docs or governance checks.
##>
[CmdletBinding()]
param(
    [ValidateSet('spawn-join-core', 'spawn-join-common', 'spawn-join-llm-provider',
        'spawn-join-llm-provider-langchain', 'spawn-join-llm-channel',
        'spawn-join-llm-model-sync', 'spawn-join-agent-deepagents',
        'spawn-join-personal-assistant', 'spawn-join-agent-work')]
    [string]$Package,

    [ValidateSet('all', 'format', 'lint', 'type', 'test', 'build', 'docs', 'governance', 'static')]
    [string]$Check = 'all',

    [ValidateNotNullOrEmpty()]
    [string]$FeatureDir
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
$root = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'markdown-checks.ps1')
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
    'spawn-join-agent-work' = @{
        Path = 'packages/infra/agent-work'
        Import = 'spawn_join_agent_work'
        Build = @('spawn-join-agent-work')
    }
    'spawn-join-personal-assistant' = @{
        Path = 'packages/apps/personal-assistant'
        Import = 'spawn_join_personal_assistant'
        Build = @('spawn-join-core', 'spawn-join-common', 'spawn-join-llm-provider',
            'spawn-join-llm-provider-langchain', 'spawn-join-agent-deepagents',
            'spawn-join-agent-work', 'spawn-join-personal-assistant')
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
    foreach ($required in @('README.md', 'AGENTS.md', '.specify/memory/constitution.md')) {
        if (-not (Test-Path -LiteralPath (Join-Path $root $required) -PathType Leaf)) {
            throw "Missing required document: $required"
        }
    }
    $featurePath = Resolve-LocalFeatureDirectory $root $FeatureDir
    $issues = @(Get-MarkdownIssues -Root $root -FeaturePath $featurePath -CheckWhitespace)
    foreach ($issue in $issues) { Write-Host "ERROR: $issue" }
    if ($issues.Count) { throw "Documentation checks found $($issues.Count) issue(s)." }
    Invoke-Checked 'git' @('diff', '--check')
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

function Test-AgentInstallVariants {
    param([string]$Directory, [string]$Python, [string]$BasePython, [string[]]$Wheels)
    $baseProbe = @'
import asyncio
import importlib.util
import sys
import spawn_join_agent_deepagents
from spawn_join_agent_deepagents.mcp import McpConfigurationError, McpLoadReport, McpTools, open_mcp_tools
assert McpTools((), {"empty": ()}, McpLoadReport("ready", (), 0)).tools_for("empty") == ()
assert importlib.util.find_spec("fastmcp") is None, "base wheel installed FastMCP"
assert importlib.util.find_spec("mcp") is None, "base wheel installed MCP"
assert not any(
    name == "fastmcp" or name.startswith("fastmcp.")
    or name == "mcp" or name.startswith("mcp.")
    for name in sys.modules
), "root import loaded optional MCP SDKs"
async def missing_extra():
    async with open_mcp_tools("not-read-without-extra.json"):
        raise AssertionError("base wheel opened MCP without its extra")
try:
    asyncio.run(missing_extra())
except McpConfigurationError as exc:
    assert "install spawn-join-agent-deepagents[mcp]" in str(exc)
    assert isinstance(exc.__cause__, ModuleNotFoundError)
else:
    raise AssertionError("base wheel did not report the missing extra")
'@
    Invoke-Checked $BasePython @('-I', '-c', $baseProbe)

    $requirements = Join-Path $Directory 'mcp-requirements.txt'
    $export = @('export', '--locked', '--directory', $packages['spawn-join-agent-deepagents'].Path,
        '--extra', 'mcp', '--no-dev', '--no-emit-project', '--format', 'requirements-txt',
        '--output-file', $requirements)
    foreach ($localName in $packages.Keys) {
        $export += @('--no-emit-package', $localName)
    }
    Invoke-Checked 'uv' $export
    $extraDirectory = Join-Path $Directory 'installed-mcp'
    Invoke-Checked 'uv' @('venv', '--python', $Python, $extraDirectory)
    $extraPython = Get-VenvPython $extraDirectory
    Invoke-Checked 'uv' (@('pip', 'install', '--python', $extraPython,
            '--no-deps', '-r', $requirements) + $Wheels)
    Invoke-Checked 'uv' @('pip', 'check', '--python', $extraPython)
    $extraProbe = @'
import asyncio
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from fastmcp import Client
from fastmcp.client.group import ClientGroup
from fastmcp.mcp_config import MCPConfig
from langchain.mcp import MCPAdapter
from spawn_join_common import FieldReader
from spawn_join_agent_deepagents.mcp import McpLoadReport, McpTools, open_mcp_tools
assert McpTools((), {"empty": ()}, McpLoadReport("ready", (), 0)).tools_for("empty") == ()
assert MCPConfig.from_dict({"mcpServers": {}}).mcpServers == {}
assert FieldReader().as_int(3, "count") == 3
assert all(callable(item) for item in (Client, ClientGroup, MCPAdapter))

def process_alive(pid):
    if sys.platform == "win32":
        output = subprocess.check_output(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"])
        return f'"{pid}"'.encode() in output
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True

async def read_port(path):
    async with asyncio.timeout(30):
        while True:
            try:
                value = await asyncio.to_thread(path.read_text, encoding="utf-8")
            except FileNotFoundError:
                value = ""
            if value.endswith("\n"):
                return int(value)
            await asyncio.sleep(0.02)

async def call_installed_tools():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        server = root / "server.py"
        server.write_text(
            "import asyncio, os, socket, sys\n"
            "from pathlib import Path\n"
            "from fastmcp import FastMCP\n"
            "name, root = sys.argv[1], Path(sys.argv[2])\n"
            "(root / (name + '.pid')).write_text(str(os.getpid()), encoding='utf-8')\n"
            "server = FastMCP(name)\n"
            "@server.tool()\n"
            "def echo(value: str) -> str: return name + ':' + value\n"
            "if name == 'remote':\n"
            "    with socket.socket() as listener:\n"
            "        listener.bind(('127.0.0.1', 0))\n"
            "        listener.listen()\n"
            "        port = listener.getsockname()[1]\n"
            "        (root / 'port').write_text(str(port) + '\\n', encoding='utf-8')\n"
            "        asyncio.run(server.run_http_async(host='127.0.0.1', port=port, sockets=[listener], show_banner=False))\n"
            "else:\n"
            "    server.run(transport='stdio', show_banner=False)\n",
            encoding="utf-8",
        )
        remote = await asyncio.create_subprocess_exec(sys.executable, str(server), "remote", str(root))
        try:
            url = f"http://127.0.0.1:{await read_port(root / 'port')}/mcp"
            path = root / "mcp.json"
            path.write_text(json.dumps({"mcpServers": {
                "wheel": {"command": sys.executable, "args": [str(server), "wheel", str(root)]},
                "remote": {"url": url},
                "unavailable": {"command": sys.executable, "args": ["-c", "raise SystemExit(1)"]}
            }, "spawnJoin": {"optionalServers": ["unavailable"]}}), encoding="utf-8")
            async with Client(url) as host:
                async with open_mcp_tools(path) as tools:
                    assert tools.report.status == "degraded" and tools.report.tool_count == 2
                    assert [row.status for row in tools.report.servers] == ["loaded", "loaded", "failed"]
                    assert tuple(tools.failures) == ("unavailable",)
                    response = await tools.tools_for("supervisor")[0].ainvoke({"value": "call"})
                    assert "wheel:call" in str(response), "mcp-wheel-call-probe"
                    response = await tools.tools_for("supervisor")[1].ainvoke({"value": "http"})
                    assert "remote:http" in str(response), "mcp-wheel-http-probe"
                    pid = int(await asyncio.to_thread((root / "wheel.pid").read_text))
                async with asyncio.timeout(30):
                    while await asyncio.to_thread(process_alive, pid):
                        await asyncio.sleep(0.05)
                assert remote.returncode is None, "helper stopped the host HTTP process"
                assert "remote:after" in str(await host.call_tool("echo", {"value": "after"}))
        finally:
            if remote.returncode is None:
                remote.terminate()
            await remote.wait()

asyncio.run(call_installed_tools())
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
        if ($Name -eq 'spawn-join-agent-deepagents') {
            Test-AgentInstallVariants -Directory $temporary -Python $Python `
                -BasePython $installedPython -Wheels $wheels
        }
    } finally {
        # This exact unique directory is created and owned by this invocation only.
        Remove-Item -LiteralPath $temporary -Recurse -Force
    }
}

Push-Location $root
try {
    if ($FeatureDir -and $Check -notin @('all', 'docs', 'governance')) {
        throw '-FeatureDir applies to docs, governance or all.'
    }
    # Governance and static analysis are repository-level; package-scoped runs skip them.
    $runGovernance = $Check -eq 'governance' -or ($Check -eq 'all' -and -not $Package)
    $runStatic = $Check -eq 'static' -or ($Check -eq 'all' -and -not $Package)
    if ($runGovernance) {
        $arguments = @('-NoProfile', '-File',
            (Join-Path $root 'scripts/check-governance.ps1'), '-Root', $root)
        if ($FeatureDir) { $arguments += @('-FeatureDir', $FeatureDir) }
        Invoke-Checked 'pwsh' $arguments
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
            $sync = @('sync', '--locked', '--directory', $directory)
            if ($name -eq 'spawn-join-agent-deepagents') { $sync += @('--extra', 'mcp') }
            Invoke-Checked 'uv' $sync
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
