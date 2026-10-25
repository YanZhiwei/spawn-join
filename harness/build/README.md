# Harness Build Phase Records

`harness/build/` 记录一个已经批准的、边界明确的实施阶段。文件名使用：

```text
phase-<NN>-<phase-slug>.md
```

## Required Sections

每个阶段计划至少包含：

- 阶段编号、标题和状态；
- 来源文档和当前 Feature；
- 目标；
- In-scope 工作；
- Explicit non-goals；
- 依赖和前置条件；
- 预期影响路径或组件；
- 需要用户确认的决策；
- 批准门；
- Red、Green、Refactor 和 Verification 计划（适用时）；
- 精确的验证命令；
- 安全、隐私、可靠性、回滚和恢复考虑（适用时）；
- 可观察验收标准；
- 完成前必须记录的 Evidence；
- Handoff 或 Stop 条件。

## Ownership Rules

- `specs/<feature-id>/plan.md` 拥有整个 Feature 的技术方案；
- `specs/<feature-id>/tasks.md` 拥有唯一执行队列；
- 本目录的文件只拥有一个阶段的批准范围和执行计划；
- 阶段计划不是实现完成证据，也不能把预期命令写成通过结果；
- 阶段未获明确批准前，Agent 必须停止在计划和审查阶段。

如果阶段范围发生变化，先更新 Spec/Plan/Tasks 或重新打开任务，再更新阶段文件；不要在
阶段文件中悄悄扩大范围。
