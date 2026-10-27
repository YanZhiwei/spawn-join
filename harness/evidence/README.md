# Harness Verification Evidence

`harness/evidence/` 保存与真实变更范围绑定的验证记录。它记录实际发生的检查，不保存
只写在计划里的预期结果。

推荐文件名：

```text
<phase-id>-<check-slug>.md
```

## Required Evidence Fields

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

## Freshness Rules

- `head_revision` 或 `changed_paths` 变化后，原 Evidence 标记为 stale；
- 旧 Evidence 必须重新执行或明确重新确认，才能支持新的收口结论；
- 如果环境、权限、依赖或外部服务不可用，记录原因和替代证据，不得静默跳过；
- Evidence 不拥有计划范围、任务状态或评审发现。

## Sensitive Data

不要记录密钥、令牌、私有 URL、完整用户数据或不必要的命令环境变量。只保留复现检查
所需的最小安全上下文。
