# Delivery Evidence — Release installation

- **feature_id**: `006-delivery-release-install`
- **phase_id**: `delivery-release-installation`
- **base_revision**: `fdd0c072186ef3cea7f4b3261acd1d82b358ef56`
- **head_revision**: `fdd0c072186ef3cea7f4b3261acd1d82b358ef56` plus uncommitted migration
- **working_directory**: `D:\Repos\Github\spawn-join`
- **recorded_at**: 2026-10-28
- **result**: pass for v0.1.1 Bundle installation and the declared verification environment

The authoritative command, source, preservation and failure record is
[Harness installation evidence](../../../harness/evidence/delivery-release-installation.md).
This is a manual installation/migration record, not a Ralph receipt. The published v0.1.1
Bundle owns 12 components; project configs and core task customizations were preserved.
The Profile commands and final full quality entry point passed. The live OpenCode service
discovers all 31 native project commands. Default-environment readiness is separately recorded in
[Doctor](doctor.md) and remains blocked on local static-tool availability.

## Limitations

Commit-dependent closure, ADR acceptance, real Ralph execution and remote CI are not performed.
Bundle v0.1.1 is installed, but the default local environment still lacks PSScriptAnalyzer 1.25.0,
so Doctor remains blocked for autonomous default-environment execution.
