# Harness Verification Evidence

`harness/evidence/` 保存与真实变更范围绑定的验证记录。它记录实际发生的检查，不保存
只写在计划里的预期结果。

推荐文件名：

```text
<phase-id>-<check-slug>.md
```

## Required Evidence Fields

每条 Evidence 至少包含：

```text
feature_id:
phase_id:
task_id:
base_revision:
head_revision:
changed_paths:
working_directory:
command:
environment:
exit_code:
result:
limitations:
blockers:
recorded_at:
```

`result` 只能使用与实际执行相符的状态，例如 `pass`、`fail`、`blocked`、`skipped` 或
`not-run`。未执行的命令不得写成 `pass`。

## Freshness Rules

- `head_revision` 或 `changed_paths` 变化后，原 Evidence 标记为 stale；
- 旧 Evidence 必须重新执行或明确重新确认，才能支持新的收口结论；
- 如果环境、权限、依赖或外部服务不可用，记录原因和替代证据，不得静默跳过；
- Evidence 不拥有计划范围、任务状态或评审发现。

## Sensitive Data

不要记录密钥、令牌、私有 URL、完整用户数据或不必要的命令环境变量。只保留复现检查
所需的最小安全上下文。
