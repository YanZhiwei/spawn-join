# Read the actual quality runner's registrations without running its tests or builds.
function Get-QualityRunnerPackages {
    param([string]$Runner)
    $command = Get-Command -Name $Runner -CommandType ExternalScript -ErrorAction Stop
    $parameter = $command.Parameters['Package']
    if ($null -eq $parameter) { throw 'scripts/quality.ps1: missing -Package parameter.' }
    $validateSet = @($parameter.Attributes | Where-Object { $_ -is [ValidateSet] })
    if ($validateSet.Count -ne 1) { throw 'scripts/quality.ps1: expected a -Package ValidateSet.' }

    $assignment = @($command.ScriptBlock.Ast.EndBlock.Statements | Where-Object {
        $_ -is [System.Management.Automation.Language.AssignmentStatementAst] -and
        $_.Left -is [System.Management.Automation.Language.VariableExpressionAst] -and
        $_.Left.VariablePath.UserPath -eq 'packages'
    })
    if ($assignment.Count -ne 1) { throw 'scripts/quality.ps1: expected one $packages assignment.' }
    $table = $assignment[0].Right.Expression
    if ($table -is [System.Management.Automation.Language.ConvertExpressionAst] -and
        $table.Type.TypeName.FullName -eq 'ordered') { $table = $table.Child }
    if ($table -isnot [System.Management.Automation.Language.HashtableAst]) {
        throw 'scripts/quality.ps1: expected a literal $packages table.'
    }
    return [ordered]@{
        'scripts/quality.ps1 -Package ValidateSet' = $validateSet[0].ValidValues
        'scripts/quality.ps1 $packages' = @($table.KeyValuePairs | ForEach-Object { $_.Item1.SafeGetValue() })
    }
}

function Get-PackageCoverageIssues {
    param([string]$Root)
    # Parse the same TOML and YAML fields their consumers read. uv keeps this tool
    # separate from the root and from every Distribution's environment.
    $readConfig = @'
# /// script
# requires-python = ">=3.11"
# dependencies = ["PyYAML==6.0.3"]
# ///
import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import yaml

root = Path(sys.argv[1])
source = 'packages/*/*/pyproject.toml'
try:
    paths = subprocess.check_output([
        'git', '-C', str(root), 'ls-files', '-z', '--cached', '--others',
        '--exclude-standard', '--', ':(glob)' + source,
    ])
    manifests = []
    for entry in sorted(filter(None, paths.split(b'\0'))):
        source = os.fsdecode(entry)
        manifest = root / source
        if manifest.is_file():  # A tracked manifest can have an unstaged deletion.
            name = tomllib.loads(manifest.read_text(encoding='utf-8-sig'))['project']['name']
            if not isinstance(name, str) or not name.strip():
                raise ValueError('expected a nonempty [project].name')
            manifests.append(name)

    source = '.github/workflows/quality.yml'
    workflow = yaml.safe_load((root / source).read_text(encoding='utf-8-sig'))
    matrix = workflow['jobs']['packages']['strategy']['matrix']['package']
    if not isinstance(matrix, list) or not all(isinstance(name, str) and name for name in matrix):
        raise ValueError('jobs.packages.strategy.matrix.package must list distribution names')

    source = '.specify/extensions/quality/quality-config.yml'
    config = yaml.safe_load((root / source).read_text(encoding='utf-8-sig'))
    if not isinstance(config['profiles'], list):
        raise ValueError('profiles must be a list')
    profiles = []
    for profile in config['profiles']:
        name = profile['id']
        if not isinstance(name, str) or not name.strip():
            raise ValueError('expected a nonempty profile id')
        quality = profile.get('commands', {}).get('quality', '')
        # A retired package can still have a package-specific command. Shared
        # profiles can mention retired paths without owning a Distribution.
        package_command = isinstance(quality, str) and re.search(r'(?:^|\s)-Package\b', quality, re.I)
        if name in manifests or package_command:
            profiles.append(name)
except (OSError, ValueError, KeyError, TypeError, AttributeError, yaml.YAMLError) as exc:
    sys.exit(f'{source}: {exc}')

print(json.dumps(dict(manifests=manifests, matrix=matrix, profiles=profiles)))
'@
    $output = $readConfig | & uv run --quiet --script - $Root
    if ($LASTEXITCODE -ne 0) { throw "Could not read package coverage inputs (uv exit $LASTEXITCODE)." }
    $config = $output | ConvertFrom-Json -AsHashtable
    $lists = Get-QualityRunnerPackages (Join-Path $Root 'scripts/quality.ps1')
    $lists['.github/workflows/quality.yml jobs.packages.strategy.matrix.package'] = $config.matrix
    $lists['.specify/extensions/quality/quality-config.yml profiles'] = $config.profiles
    $manifestSource = 'packages/*/*/pyproject.toml [project].name'
    $lists[$manifestSource] = $config.manifests
    $declared = @($config.manifests | Sort-Object -Unique -CaseSensitive)
    if (-not $declared.Count) { "${manifestSource}: no distribution manifests found" }

    foreach ($source in $lists.Keys) {
        $names = $lists[$source]
        foreach ($name in $declared) {
            if ($name -cnotin $names) { "${source}: missing package: $name" }
        }
        foreach ($group in ($names | Group-Object -CaseSensitive)) {
            if ($group.Count -gt 1) { "${source}: duplicate package: $($group.Name)" }
            if ($group.Name -cnotin $declared) { "${source}: extra package: $($group.Name)" }
        }
    }
    Write-Host "Package coverage: $($declared.Count) distributions compared with CI, Quality Profiles and both local runner lists."
}
