# Delivery Evidence — Release installation

- **feature_id**: `006-delivery-release-install`
- **phase_id**: `delivery-release-installation`
- **base_revision**: `06f6303b597ce01a707164762f55369706b13063`
- **head_revision**: `06f6303b597ce01a707164762f55369706b13063` plus the v0.1.2 Bundle upgrade working tree
- **working_directory**: `D:\Repos\Github\spawn-join`
- **recorded_at**: 2026-10-28
- **result**: pass for v0.1.2 Bundle upgrade; default-environment Doctor remains blocked

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
