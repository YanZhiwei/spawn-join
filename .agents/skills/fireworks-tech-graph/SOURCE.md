# Vendored source

- Upstream: <https://github.com/yizhiyanhua-ai/fireworks-tech-graph>
- Commit: `1ca1ff9cfcb67893a43d32b9ef3a1b782c44a46f`
- Upstream directory: `skills/fireworks-tech-graph/`
- Package version: `1.2.0`
- License: MIT; original notice retained in `LICENSE`.
- Imported: 2026-10-26, 139 upstream files, 8,882,626 bytes.
- Local changes: this `SOURCE.md` only. The upstream distribution is byte-identical,
  including references, helper scripts, schemas, fixtures, tests and sample assets.

This is a project-local Agent Skill, not a SpawnJoin Python Distribution or a
runtime dependency. Its upstream Python/JavaScript/shell helpers are isolated
third-party development tooling; do not import them from `packages/`, reformat
them with package quality tools, or install renderer dependencies into package
environments. Retaining upstream examples and tests keeps the distribution intact.

For the project ADR/output policy and Windows commands, see
[technical diagrams](../../../docs/development/technical-diagrams.md).
The upstream README is upstream documentation, not proof that this machine has
all renderers installed. Its update, install and publication commands are not
authorization to modify global skills, install dependencies or publish artifacts.

Updates must pin a new full upstream commit, preserve the license, compare the
distribution, run targeted checks and update this record. Do not automatically
follow `main`. The local source manifest used for import verification was stored
in the approved temporary workspace; the pinned commit is the durable source of
truth for reproducing the imported files.
