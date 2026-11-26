Delivery-Evidence: .specify/delivery/adr-lifecycle-closure-20261126/evidence.md

Delivery-Stack: single

## 摘要

- 解决的问题：ADR 索引与实现状态长期不同步；ADR-0016 仍写“尚未实现任何包/迁移”，而 `spawn-join-agent-work` 已交付；ADR-0011/0012/0016 已具备接受证据但一直是 `Proposed`。
- 合并后的行为或契约：ADR-0011、ADR-0012、ADR-0016 转为 `Accepted`；ADR-0009、ADR-0014 经独立六维 Review 后判定 `blocked`，保持 `Proposed` 并记录缺口；决策索引和安装说明同步。
- 本次不包含：不修改任何产品源码、公共 API、依赖、测试或运行时行为；不修复 ADR-0009/0014 Review 发现的缺陷；不发布包。

## 关联问题与变更类型

Part of #<none>；本 PR 不关闭 Issue。

- [ ] 新功能或新组件
- [ ] Bugfix 或契约修正
- [ ] 重构或简化
- [x] 文档或治理
- [ ] 发布准备

## 变更内容

| 位置 | 变更 | 原因 |
| --- | --- | --- |
| `docs/decisions/engineering/0011-common-helper-package.md` | `Proposed` → `Accepted`，记录接受人/日期与依据 | 实现、独立六维 Review、PR #47 CI 已完成 |
| `docs/decisions/agent/0012-deepagents-official-p0.md` | `Proposed` → `Accepted`，记录接受人/日期与依据 | P0 独立六维 Review 已完成，阻塞项已修复 |
| `docs/decisions/engineering/0016-desktop-first-service-ready-packages.md` | `Proposed` → `Accepted`；修正“尚未实现”的过时描述 | `agent-work` 已交付、`personal-assistant` 已迁移；服务端适配器仍未实现 |
| `docs/decisions/llm-provider/0009-model-metadata-and-sync.md` | 保持 `Proposed`；修正实现状态并记录 2026-11-26 Review `blocked` | 实现已交付，但 F1–F5 仍未解决，不能接受 |
| `docs/decisions/agent/0014-deepagents-p1-capabilities.md` | 保持 `Proposed`；记录 Review `blocked` 与 F1–F3 | rubric gate、tool_count、位置参数兼容性仍不满足 ADR |
| `docs/decisions/README.md` | 同步 0011/0012/0016 的索引状态 | 索引是机器检查的权威状态 |
| `docs/development/spec-kit-delivery.md` | 更新 ADR-0016 已接受的说明 | 安装说明不再称其为提案 |
| `.specify/delivery/adr-lifecycle-closure-20261126/reviews/` | 新增 0009/0014 的独立 Review 报告 | 持久化 verdict、findings、命令和限制 |
| `harness/build-log.md` | 登记本次治理变更 | 可追溯的实际执行记录 |

## 验证

| 场景或检查 | 实际结果 | 证据 |
| --- | --- | --- |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0；206 个共享 Markdown、1041 个本地链接 | evidence 的 Verification 表 |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 0 errors、3 条既有历史 warning；9 个 Distribution 覆盖一致 | evidence 的 Verification 表 |
| `git diff --check` | 0 | evidence 的 Verification 表 |
| ADR-0009 独立 Review 目标测试 | 34 + 115 + 58 passed；verdict `blocked` | `reviews/adr-0009-review.md` |
| ADR-0014 独立 Review 目标测试 | 45 + 48 passed；verdict `blocked` | `reviews/adr-0014-review.md` |

- 未执行或未覆盖的验证及原因：未运行包构建、隔离 wheel 安装、远端 CI 或完整质量矩阵；本次不改产品源码。ADR-0009/0014 的 Review 只运行目标测试，未在最终 HEAD 重跑完整包门禁。

## 影响（仅填写适用项）

| 维度 | 影响 | 证据 |
| --- | --- | --- |
| 公共 API、命令、配置 | 无 | 仅 ADR/文档/证据变更 |
| 持久化、迁移或数据兼容 | 无 | 同上 |
| 安全、权限或敏感信息 | 无 | 未新增密钥、URL 或用户数据 |
| 性能、资源或可观测性 | 无 | 同上 |
| 依赖、供应链或发布 | 无 | 未修改 `pyproject.toml`、锁文件或 CI |

## 审查身份

- `base_revision`：`79425090f442506663c0024bde02c62f1f5c7ea6`
- `reviewed_head`：本 PR 的文档提交（以 GitHub head 为准）
- `content_fingerprint`：未计算（Lightweight 文档改动，使用实际 diff 与 docs/governance 证据）
- `requirements_fingerprint`：未计算（无 Feature/Task 工件）
- native Review report / receipt：ADR-0009/0014 的独立 Review 报告位于 `.specify/delivery/adr-lifecycle-closure-20261126/reviews/`；本次 ADR 状态编辑本身未执行独立六维 Review
- 发布后的 `original_pr_head` / `published_head`：待发布或实际值

## 本地 AI Code Review 与修复历程

| 轮次 | 工具 / 方法 | 审查版本或范围 | 主要发现与状态 | 修复 / 复审结论 |
| --- | --- | --- | --- | --- |
| 1 | 独立只读子代理 | ADR-0009 实现与 ADR 文本，HEAD `7942509` | F1 blocker；F2–F5 major/minor | `blocked`，保持 Proposed |
| 2 | 独立只读子代理 | ADR-0014 实现与 ADR 文本，HEAD `7942509` | F1 blocker；F2–F3 major；F4–F8 minor/nit | `blocked`，保持 Proposed |

- 最终 AI 审查结论：ADR-0009/0014 均 `blocked`；ADR-0011/0012/0016 依据历史实现/Review/CI 接受。
- 未解决问题与剩余风险：两份 Review 的 F1–F3 等需要在后续 Bugfix 中修复并复评。
- 本地报告或证据：`.specify/delivery/adr-lifecycle-closure-20261126/reviews/`
- [ ] 未执行本地 AI Code Review（请说明原因）
- [x] 已执行；实现者已处理或明确记录每个问题，最终代码已重新审查（本次仅记录，不宣称修复）

## 评审重点

- 入口或建议阅读顺序：`docs/decisions/README.md` → 3 个 Accepted ADR → 0009/0014 的 Verification 段 → 两份 Review 报告。
- 关键行为、边界或设计取舍：状态变更只代表维护者接受长期决策，不代表实现/发布完成；0009/0014 的 blocker 是代码/契约问题，保持 Proposed 是刻意选择。
- 需要人工或特定环境验证：若要求把 0009/0014 也接受，先完成对应 Bugfix 与复评。

## 条件章节

### 架构、设计或 ADR（仅有相关变化时）

- 当前设计、入口、归属与依赖方向：ADR 根为 `docs/decisions/`；本次不改包边界或依赖。
- 设计变化与原因：只改变 ADR 生命周期状态与事实描述，不改变决策内容。
- ADR / 决策链接：ADR-0011、0012、0016（Accepted）；0009、0014（Proposed，review blocked）。
- 设计图或接口说明：本次不需要。

### 文档、发布或迁移（仅适用时）

- 源文档 / 生成文档：`docs/decisions/*`、`docs/development/spec-kit-delivery.md`。
- 发布说明：无包发布；仅决策记录状态更新。
- 迁移、回滚或恢复步骤：不需要迁移；回滚本 PR 即可恢复原状态。

## 回滚

回滚本 PR 的文档提交即可。不会影响运行时或包产物。

## 提交前确认

- [x] 我理解并能解释本次提交的变更。
- [x] 验证结果来自实际执行；未执行项、环境限制和剩余风险已明确标出。
- [x] 本次实际 diff 与 `reviewed_head` / 审查范围一致。
- [x] 阻断性 Review 问题已解决，或已记录明确的 owner 与处理决定（0009/0014 保持 Proposed，后续 Bugfix）。
- [x] 关联 ADR、文档、迁移和兼容性说明与最终代码一致。
