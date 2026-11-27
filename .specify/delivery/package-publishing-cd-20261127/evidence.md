# Development package publishing CD

delivery_run: package-publishing-cd-20261127
lane: feature
evidence_path: .specify/delivery/package-publishing-cd-20261127/evidence.md
base_revision: b867b68c8aaa8f93bc02afe838f9ce2a248dd040
reviewed_head: 3ae3a6ba29a5a6aa79c583dd9affde037546ae45
original_pr_head: pending
content_fingerprint: 3ae3a6ba29a5a6aa79c583dd9affde037546ae45
requirements_fingerprint: b867b68c8aaa8f93bc02afe838f9ce2a248dd040
method_identity: builtin
pull_request: 108
exploration_path: .specify/delivery/package-publishing-cd-20261127/exploration.md

## Scope

Add a manually authorized GitHub Packages publishing workflow for the nine
existing distributions, with PEP 440 development versions `0.0.1.dev0`,
dependency-order publication, locked verification, and operator documentation.

## Verification

| Check | Result |
| --- | --- |
| All nine `uv lock --check` commands | pass |
| Core isolated wheel build, install, `uv pip check`, and import | pass |
| Documentation quality check | pass |
| Static workflow/PowerShell check | pass |
| Governance check | pass locally; three historical evidence freshness warnings |
| PR CI | pending after correction commit; previous run exposed stale version assertions and missing shared evidence |

## Publication status

No package has been published. Publication remains a separate manual
workflow-dispatch operation after this PR is merged and GitHub Packages access
has been verified.

## Limitations

The real GitHub Packages upload and registry visibility have not been exercised.
The first PR CI run failed before the version-assertion correction and before
this shared evidence file was added; a fresh CI run is required. Historical
governance warnings are unrelated to this run.

## Follow-up: GitHub Packages uploader

The initial publish run `45861856373` built and verified all nine
distributions, then received HTTP 404 responses from `uv publish`. No package
upload succeeded. The workflow was changed to use Twine's legacy upload
protocol with the GitHub Actions actor and `GITHUB_TOKEN`; this correction is
covered by PR `106` and this refreshed evidence snapshot.

The follow-up run `45866262742` reached Twine but no files were uploaded:
GitHub Packages rejected the unsupported `--skip-existing` option before any
upload. PR `107` removes that option.
## Follow-up: registry pivot

GitHub Packages has no Python registry: the PyPI registry request was closed as
"no longer planned" (github/roadmap#94) and the supported registries are npm,
RubyGems, Maven, Gradle, Docker and NuGet only. Every upload to
`https://pypi.pkg.github.com/YanZhiwei/` returned HTTP 404 with no asset
created, including after `write:packages` was granted and the personal
account's package inheritance toggle was enabled.

PR `108` therefore publishes the distributions as GitHub Release assets and
exposes them through a static PEP 503 index deployed to the `gh-pages` branch.
