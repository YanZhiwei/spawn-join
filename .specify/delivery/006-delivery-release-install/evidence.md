# Delivery Evidence — Release installation

- **feature_id**: `006-delivery-release-install`
- **phase_id**: `delivery-release-installation`
- **base_revision**: `0f67f44eb5fb7bd76f85ac9ce2b701dd15e3cbf1`
- **head_revision**: `00d9c402bb2325c3b8f007ece5564312397ac77e` (PR #12 merge commit)
- **working_directory**: `D:\Repos\Github\spawn-join`
- **recorded_at**: 2026-10-29
- **result**: pass for v0.1.2 Bundle installation re-anchored at 00d9c40; main Quality 14/14 passed; default-environment Doctor remains blocked
- **status**: superseded
- **superseded_by**: `harness/evidence/delivery-release-installation.md`
- **reason**: the run only mirrors the durable installation record; v0.3.0 keeps operational one-off records in the project evidence root
- **outcome_recorded_at**: 2026-11-01

The authoritative command, source, preservation and failure record is
[Harness installation evidence](../../../harness/evidence/delivery-release-installation.md).
This is a manual upgrade record, not a Ralph receipt. The published v0.1.2 Bundle owns
13 components (10 extensions and 3 workflows); project configs and core task customizations
were preserved. The live OpenCode service discovers all 33 native project commands.
Default-environment readiness is separately recorded in [Doctor](doctor.md) and remains
blocked on local static-tool availability.

## Limitations

Commit-dependent closure, ADR acceptance, real Ralph execution and remote CI are not performed.
Bundle v0.1.2 is installed, but the default local environment still lacks PSScriptAnalyzer 1.25.0,
so Doctor remains blocked for autonomous default-environment execution.
