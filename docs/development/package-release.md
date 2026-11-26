# Python Package Release

The repository contains nine independent Python distributions. The root
`pyproject.toml` is tool-only and is not published.

## Versioning

Development releases use PEP 440 versions such as:

```text
0.1.0.dev0
0.1.0.dev1
```

Do not reuse an uploaded version. Increment the `.devN` suffix for each
publication. Distribution names remain stable; do not add `-dev` to the
package name.

## Manual release

The workflow is `.github/workflows/publish-package.yml`. Run it from the
Actions page after the corresponding PR has merged and choose one package or
`all`.

`all` publishes in dependency order:

1. `spawn-join-core`
2. `spawn-join-common`
3. `spawn-join-llm-provider`
4. `spawn-join-llm-provider-langchain`
5. `spawn-join-llm-channel`
6. `spawn-join-llm-model-sync`
7. `spawn-join-agent-deepagents`
8. `spawn-join-agent-work`
9. `spawn-join-personal-assistant`

Each package is locked, synced, checked by the existing quality entry point,
built in isolation, and then uploaded with Twine's legacy Python upload
protocol to the repository's GitHub Packages Python registry. The workflow
requires `packages: write` and uses the short-lived `GITHUB_TOKEN`; no token is
stored in the repository.

Before the first release, the repository owner must verify that GitHub Packages
is enabled and that the target package visibility and consumer access policy
are correct. A failed upload may leave earlier packages published, so rerun
only the failed or remaining package after checking the registry.

## Local verification

From the repository root:

```powershell
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-core
pwsh -NoProfile -File scripts/quality.ps1 -Check docs
pwsh -NoProfile -File scripts/quality.ps1 -Check governance
```
