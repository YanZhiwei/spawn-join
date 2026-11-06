# Harness Verification Evidence

[English](README.md) | [简体中文](README.zh-CN.md)

`harness/evidence/` stores verification records bound to real change scope. It records checks that
actually ran, never expected results that exist only in a plan.

Recommended filenames:

```text
<phase-id>-<check-slug>.md
```

## Required evidence fields

`scripts/check-governance.ps1` machine-validates the following fields; a missing field fails:

```text
feature_id:
phase_id:
base_revision:
head_revision:
working_directory:
recorded_at:
result:
```

`result` must begin with one of `pass`, `fail`, `blocked`, `skipped`, or `not-run`. `recorded_at` must
begin with `YYYY-MM-DD`. Every Evidence record must also contain a `limitations` field or heading
(for example `## Limitations`), and its filename must appear in `harness/build-log.md`.

Add `task_id`, `changed_paths`, `command`, `environment`, `exit_code`, `blockers`, and similar fields
as applicable. When evidence covers multiple commands, record each exit code in a table rather than
forcing a single `exit_code`.

## Freshness rules

- after `head_revision` or `changed_paths` changes, mark the original Evidence stale;
- old Evidence must be rerun or explicitly reconfirmed before supporting a new closure conclusion;
- the machine check warns only when non-documentation paths such as `packages/`, `scripts/`, or `.github/` changed during the lag; pure documentation or evidence appends do not trigger a freshness warning;
- when environment, permissions, dependencies, or external services are unavailable, record the reason and alternative evidence; never silently skip;
- Evidence does not own planned scope, task state, or review findings.

## Sensitive data

Never record secrets, tokens, private URLs, full user data, or unnecessary command environment
variables. Keep only the minimum safe context needed to reproduce the check.

See the repository [LICENSE](../../LICENSE).
