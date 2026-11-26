# Development package publishing CD

delivery_run: package-publishing-cd-20261127
lane: feature
evidence_path: .specify/delivery/package-publishing-cd-20261127/evidence.md
base_revision: b867b68c8aaa8f93bc02afe838f9ce2a248dd040
reviewed_head: ce5c02f94169e3957dfe80ac55374880cc357f09
original_pr_head: pending
content_fingerprint: ce5c02f94169e3957dfe80ac55374880cc357f09
requirements_fingerprint: b867b68c8aaa8f93bc02afe838f9ce2a248dd040
method_identity: builtin
pull_request: 105
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
