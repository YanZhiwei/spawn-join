# Harness Verification Evidence

[简体中文](#中文) | [English](#english)

## 中文

`harness/evidence/` 保存与真实变更范围绑定的验证记录。它记录实际发生的检查，不保存
只写在计划里的预期结果。

推荐文件名：

```text
<phase-id>-<check-slug>.md
```

### Required Evidence Fields

`scripts/check-governance.ps1` 机器校验以下字段，缺失即失败：

```text
feature_id:
phase_id:
base_revision:
head_revision:
working_directory:
recorded_at:
result:
```

`result` 必须以下列词开头：`pass`、`fail`、`blocked`、`skipped` 或 `not-run`。
`recorded_at` 以 `YYYY-MM-DD` 开头。每条 Evidence 还必须包含 `limitations` 字段或
标题（如 `## Limitations`），并且文件名必须出现在 `harness/build-log.md` 中。

按适用范围补充 `task_id`、`changed_paths`、`command`、`environment`、`exit_code`、
`blockers` 等字段。多条命令的 evidence 用表格记录各自退出码，不强制单一 `exit_code`。

### Freshness Rules

- `head_revision` 或 `changed_paths` 变化后，原 Evidence 标记为 stale；
- 旧 Evidence 必须重新执行或明确重新确认，才能支持新的收口结论；
- 机器检查只在落后期间存在 `packages/`、`scripts/`、`.github/` 等非文档路径变更时告警；
  纯文档或证据追加不触发 freshness warning；
- 如果环境、权限、依赖或外部服务不可用，记录原因和替代证据，不得静默跳过；
- Evidence 不拥有计划范围、任务状态或评审发现。

### Sensitive Data

不要记录密钥、令牌、私有 URL、完整用户数据或不必要的命令环境变量。只保留复现检查
所需的最小安全上下文。

许可证见 [LICENSE](../../LICENSE)。

## English

`harness/evidence/` stores verification records bound to real change scope. It records checks that
actually ran, never expected results that exist only in a plan.

Recommended filenames:

```text
<phase-id>-<check-slug>.md
```

### Required evidence fields

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

### Freshness rules

- after `head_revision` or `changed_paths` changes, mark the original Evidence stale;
- old Evidence must be rerun or explicitly reconfirmed before supporting a new closure conclusion;
- the machine check warns only when non-documentation paths such as `packages/`, `scripts/`, or `.github/` changed during the lag; pure documentation or evidence appends do not trigger a freshness warning;
- when environment, permissions, dependencies, or external services are unavailable, record the reason and alternative evidence; never silently skip;
- Evidence does not own planned scope, task state, or review findings.

### Sensitive data

Never record secrets, tokens, private URLs, full user data, or unnecessary command environment
variables. Keep only the minimum safe context needed to reproduce the check.

See the repository [LICENSE](../../LICENSE).
