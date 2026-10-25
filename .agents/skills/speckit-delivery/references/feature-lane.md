# Feature 路线

1. 在编写规格之前，先执行决策上下文发现（decision context discovery）。
2. 对有实际意义的变更运行 `speckit.specify`，然后运行 `speckit.clarify`。
3. 在运行 `speckit.plan` 之前，先解析并确认约束当前设计的 ADR。
4. Plan 建立实现基线后，创建或更新状态为 Proposed 的 ADR。
5. 运行 `speckit.tasks` 和 `speckit.analyze`，并解决阻塞性的工件问题。
6. 针对依赖已满足的任务运行 Ralph。
7. 运行 `speckit.converge`；如果它追加了任务，则重新运行 analyze 和 Ralph，并按照项目配置限制循环次数。
8. 针对实际 diff 执行简化检查。接受的局部简化候选必须进入 tasks；行为或架构变化应返回 clarify/plan/ADR 流程。
9. 在项目配置要求时同步文档，然后审查 Standards、Spec、架构、正确性、安全性、测试和简洁性。
10. 将阻塞性审查发现转化为任务，然后重复 analyze → Ralph → converge → review。
11. 以当前仓库 HEAD 为基准 finalize ADR，收集 evidence，并生成 PR handoff。
