# ADR-0002: 取消跟踪历史 Feature 工件

- Status: Accepted
- Date: 2026-10-27
- Domain: engineering
- Classification: 约束全仓库的交付工件分发策略，不属于单一领域包。
- Decision owner: 仓库维护者
- Accepted by / date: 用户于 2026-10-27 明确要求取消跟踪 `specs/001-harness-foundation/` 并保留本地文件
- Depends on: [ADR-0001](0001-delivery-and-durable-design.md)
- Related: [仓库地图](../../architecture/repository-map.md)、[Harness](../../../harness/README.md)
- Supersedes: 部分取代 [ADR-0001](0001-delivery-and-durable-design.md) 中“不取消已跟踪文件跟踪”的条款；分层记录决策继续有效
- Superseded by: 无

## Context and drivers

`/specs/` 已加入 Git 忽略，但 `specs/001-harness-foundation/` 在忽略规则生效前已被跟踪，
而 `specs/002-python-quality-gates/` 从未跟踪。混合状态导致干净检出只包含 001、不包含 002，
文档导航也仍把 001 当作现行入口。维护者确认 001 是 SDD 初始化阶段的一次性产物，不是现行
治理依据或长期契约来源。

## Options considered

1. 保持现状，继续跟踪 001：无须迁移，但继续制造“部分 Feature 随仓库分发”的不一致，
   后续每个 Feature 都需要单独判断是否跟踪。
2. 取消跟踪 001，保留本地文件：分发状态统一为“specs 全部只在本地”，历史内容不丢失，
   代价是干净检出无法直接审计这些工件。
3. 删除 001：最彻底，但会丢失历史上下文，且用户只要求忽略，不要求销毁。

选择方案 2。

## Decision

- 使用 `git rm --cached -r specs/001-harness-foundation` 取消跟踪，**不删除本地文件**。
- 所有 `specs/<feature-id>/` 工件默认只在本地，不随仓库分发。
- 现行文档不得链接只在本地存在的 spec 文件，否则干净检出的文档检查会失败；需要共享的
  长期理由写入 ADR 或 `docs/architecture/`，验证结果写入 `harness/evidence/`。
- `harness/build-log.md` 中涉及 001 的历史条目是追加式记录，保留原文，不改写归因。
- 未来若需要外部协作者审查 Feature 工件，需另行决策是否恢复跟踪或发布副本，不能默认
  依赖本机文件。

## Key design and diagrams

这是交付工件分发策略，不新增运行时模块、公共 API 或依赖。文档职责分层维持 ADR-0001 的
结论：Spec/Plan/Tasks 面向交付，ADR 面向长期决策，Harness 面向执行证据。

## Consequences and migration

- 干净检出不再包含任何 `specs/` 文件；`scripts/quality.ps1 -Check docs` 只检查实际存在的
  目录，不会因 001 缺失而失败。
- 本机文件与 Git 历史仍保留 001 的原内容（提交历史可追溯）；本地删除后才不可恢复。
- 迁移动作是一次性索引变更，不需要修改 `.gitignore` 规则或取消 002 的忽略。
- 重新评估触发条件：需要外部审计 Feature 交付过程、或出现合规要求必须随仓库保存
  Spec/Plan/Tasks 时。

## Verification and implementation status

- 索引变更：`git rm --cached -r specs/001-harness-foundation`；本地文件保留。
- `git ls-files specs` 结果为空，`git check-ignore` 命中 `/specs/`。
- 干净检出模拟运行 `scripts/quality.ps1 -Check docs`，确认没有指向本地工件的断链。
- 实际命令、退出码和限制见
  [Harness evidence](../../../harness/evidence/untrack-historical-specs.md)。

## Revision history

- 2026-10-27：用户要求忽略 001；采纳取消跟踪并保留本地文件。
