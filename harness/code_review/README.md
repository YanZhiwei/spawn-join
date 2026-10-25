# Harness Code Review Records

`harness/code_review/` 保存需要跨阶段保留的详细评审发现。普通聊天评论不能替代这里的
阻塞项、修复状态和复核结果。

推荐文件名：

```text
review-<phase-id>-<short-slug>.md
```

## Required Finding Fields

每个评审发现至少包含：

- 唯一 Finding ID；
- 严重级别：Blocker、Major、Minor 或 Note；
- 关联的 Spec、Plan、Task、阶段和变更路径；
- 观察到的问题和可复现证据；
- 影响：正确性、标准、架构、安全、可靠性或证据完整性；
- 建议修复和明确非目标；
- 状态：Open、In Progress、Resolved、Accepted Risk 或 Rejected；
- 修复后的复核命令、revision 和结果；
- 剩余风险和下一步。

## Review Rules

- 评审必须针对真实 base/head 和 outgoing diff；
- 测试通过不能替代 DRY、模块拥有者、目录归属、公共 API 和依赖方向审查；
- Blocker 未关闭时不能声明阶段完成；
- 需要代码或配置修复的发现必须回写 `tasks.md` 或重新打开已有任务；
- 新提交或变更范围产生后，旧评审必须重新确认，而不是直接沿用。

评审记录拥有“发现和签核状态”，不拥有测试结果、完整命令日志或 Feature 的执行队列。
