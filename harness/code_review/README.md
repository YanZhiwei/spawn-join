# Harness Code Review Records

[简体中文](README.md) | [English](README.en.md)

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

## Consumer verification

按实际变更选择真实消费者的验证，不增加统一的新门禁或无关测试矩阵：

| 变更面 | 应核对的实际边界 | 不能据此推断 |
|---|---|---|
| 包/构建/公共导出 | 复用 [质量入口](../../docs/development/quality-gates.md#artifact-isolation) 的隔离 wheel 安装/导入，契约变化时验证受影响调用方 | 源码环境测试绿不等于分发包可用 |
| CLI、配置、SDK/适配边界 | 从受影响的真实入口执行针对性用例；单测保持离线，真实外部服务另记权限/环境和结果 | mock 或辅助函数通过不等于实际协议/资源生命周期正确 |
| 生成命令、Workflow、角色交接 | 分开记录安装一致性、fixture/结构测试与真实宿主交接；真实交接未执行时明确记缺口 | 安装或 fixture 通过不等于模型行为评估或完整 SD/Ralph 通过 |

复用当前有效的检查证据；只有命名的风险/缺口才补针对性验证。不可用环境记为未执行或
blocked，不为了“全绿”补造成功。前置需求/设计审查仍走既有 Clarify/Analyze/Gate；不得把
Agent 的补充解释当作用户批准，或拿前置审查替代独立代码 Review。

## Closure and reusable learning

在既有 Docs Sync/收口中，从当前已复核 findings 和材料性 context 筛选可复用经验，通常
0–3 条即可；没有适用经验可明确说明，不为配额写新规则或新增文档。

- 每条经验说明触发条件、已验证结论、适用包/版本、来源 evidence 或 Finding ID、限制及
  何时需复核。未证实假设留在调查 owner，不把一次环境相关性升级为全局约束。
- API 用法归目标包文档，组合机制归现有架构/开发说明；稳定的跨实现长期取舍才走 ADR。
  与现有知识合并，不新建 Learning/KnowledgeBase 数据库，不复制完整日志。
- 文档更新在当前批准范围内随变更完成；若需要扩大范围或改变设计，回原 owner 和既有
  队列/审批流程，不借经验提炼顺手修改代码、删除保护或增设强制机制。
- 接口、依赖、平台或来源实现变化时复核对应经验；过期内容修正或标注，不改写历史 evidence。
  在原收口记录引用更新路径和原因，经验条目不拥有任务关闭或评审豁免权。

许可证见 [LICENSE](../../LICENSE)。
