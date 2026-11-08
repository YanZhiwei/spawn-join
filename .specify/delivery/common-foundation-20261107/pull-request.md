## 摘要

- 解决的问题：公共严格读取与校验机制位于 LLM 协议包，其他领域复用时会引入领域依赖；适配包与同步工具还各自封装了 Pydantic 异常转换。
- 合并后的行为或契约：新增独立 `spawn-join-common`（默认零依赖，`validation` extra 提供 Pydantic 异常转换），协议/适配/Sync 共享同一实现；旧 `spawn_join_llm_provider.parsing.FieldReader` 保持导入路径、默认 `ConfigurationError` 和 frozen/slotted 行为。
- 本次不包含：时间转换、序列化、YAML 思考默认值、schema/错误策略统一、发布或真实 Provider 验证。

## 关联问题与变更类型

无关联 Issue；不虚构 `Closes`。下层 PR #45 已 squash 合入 main（`6906acc`），本 PR 现直接面向 main。

- [x] 新功能或新组件
- [ ] Bugfix 或契约修正
- [x] 重构或简化
- [x] 文档或治理
- [ ] 发布准备

## 变更内容

| 位置 | 变更 | 原因 |
| --- | --- | --- |
| `packages/core/common/` | 新 Distribution：`FieldReader`、可选 `validation.validate_with`、独立锁/README/测试 | 建立用户要求的跨领域公共辅助归属 |
| `packages/core/llm-provider/` | `FieldReader` 改为薄兼容子类；metadata 的 mapping 与顶层 ValidationError 转换委托 Common | 保留原公开行为并消除重复机制 |
| `packages/infra/llm-provider-langchain/` | 仅把意外 ValidationError 转换委托 Common；FileInput/null/首错顺序不变 | 行为保持迁移 |
| `packages/infra/llm-model-sync/` | 直接使用 Common reader，继续注入 ConfigurationError/SourcePayloadError | 复用严格读取，保留元数据投影与外部源 null 策略 |
| `packages/infra/agent-deepagents/uv.lock` | 仅传递锁更新 | 构建图完整，无直接依赖或业务改动 |
| `scripts/quality.ps1`、CI、Quality Profile | 第六包、两种隔离安装、消费者构建图 | 新包与消费者真实接入现有门禁 |
| ADR-0011、包边界、根/包 README | 记录 Common 职责、依赖方向和验证入口 | 长期契约与使用文档 |

## 验证

| 场景或检查 | 实际结果 | 证据 |
| --- | --- | --- |
| 六个包 `quality.ps1` | 全部 exit 0；格式、lint、Pyright strict、测试、构建、隔离安装 | `T002-quality-<distribution>.log` |
| 公共包基础/可选安装 | 基础环境无 Pydantic/领域包且含 `py.typed`；extra 环境实际执行校验与错误转换 | `merged-T001-common-quality.log` |
| 协议 / 适配 / Sync 测试 | 161 / 240 / 58 passed | `T002-quality-protocol-retry.log` 等 |
| 1,536 项解析差分 | 0 差异（值、错误文本/类型、直接 cause 类型） | `T002-differential.log`；冻结参考 SHA256 `8fa9427a…` 未改写 |
| 8 项 metadata 精确对照 | 0 差异 | `T002-metadata-compare.log` |
| docs / governance / static | 通过；隔离工作区治理 0 error（1 条历史 warning） | `T002-docs-retry.log` 等 |
| 门禁回归 | 15 / 26 / 3 场景通过 | `T002-quality/governance/static-regression.log` |
| 独立六维 Review | T001 与 T002 均 pass；最终集成审查 pass | run-local Review 报告 |
| GitHub CI（PR #47, head 4454f22） | 18 个包任务 + governance + `Quality Gate` 全部 success；mergeStateStatus CLEAN | `gh pr checks 47` |

- 未执行或未覆盖的验证及原因：真实 Provider 调用、macOS 与其他 Python 版本未执行；本机为 Windows / Python 3.13.5。CodeGraph 在隔离 worktree 未初始化，使用 AST 导入扫描替代并记录限制。

## 影响（仅填写适用项）

| 维度 | 影响 | 证据 |
| --- | --- | --- |
| 公共 API、命令、配置 | 新增 Common 公共 API；旧协议 reader 导入与默认行为保持；无配置/命令变化 | 包测试、公开导出测试、兼容性测试 |
| 持久化、迁移或数据兼容 | 无持久化或数据迁移；YAML/schema 格式不变 | 原文件与差分 |
| 安全、权限或敏感信息 | 无新增权限；适配包安全错误文本与原因链保持；Common 不渲染 Pydantic 输入 | 错误/cause 回归 |
| 性能、资源或可观测性 | 无新网络、缓存、重试、并发或生命周期；读取与转换步骤等价 | 模块边界核对 |
| 依赖、供应链或发布 | 新增 Common 内部 Distribution；协议/适配声明 common[validation]，Sync 声明 common；锁仅新增条目，无第三方升级 | 四个锁 diff、隔离安装 |

## 审查身份

- `base_revision`：`5021b18880aa470b328ac671ba8eaaabe972f0a0`（main，合入 #45 前）；当前 main 为 `6906acc`
- `reviewed_head`：`4454f2205904e04f1ab44d149743f6cd05fb4806`（最终集成审查内容）；`ea2c9e76195520183a9b8c05c381a64e3314f9ff`（仅合并新 main，产品内容逐字节相同）
- `content_fingerprint`：T001 `654ba25d1d15329926cfdb797d3ae5f8ca2e56b747c082c8bf1e3870131bfc49`；T002 `5d8225bc9ba9037724d51b33111d5659729dc122e1cef85237e78a16d85654aa`；最终集成 `47912a9bb4762d008cfc37bc16ff95fdf3c2e707780ab6b2a219e82ac36ad13d`（产品代码/测试/配置/锁指纹 `cb5cb89122bed7162a8b5d03e8ca5d9533b10a3c26e79cd8f800d5f56ad02318`，与 19930b2 相同）
- `requirements_fingerprint`：T001 `75260905843cd273032a7397fc3b86e5580af8ffe76c516b0037401697453d96`；T002 `7b8165b1b2996c61bd87be49db3a6b19572c2ce6ebc08b5e17981c0f5f091bce`；最终集成 `054795a27a64a764f6d65280dc842d96c80cb7b50c742fe82b616a42fe464d39`
- native Review report / receipt：standalone 例外，无 SD native receipt；fresh-context Review 报告保存在本地 `.specify/delivery/common-foundation-20261107/runtime/`
- 发布后的 `original_pr_head` / `published_head`：待发布

## 本地 AI Code Review 与修复历程

| 轮次 | 工具 / 方法 | 审查版本或范围 | 主要发现与状态 | 修复 / 复审结论 |
| --- | --- | --- | --- | --- |
| 1 | fresh-context 独立 Review | T001 | 5 项：边界文档、隔离断言、py.typed、CodeGraph、README | 全部修复/记录；复审 pass |
| 2 | fresh-context 独立 Review | T001 + main 合并 | 合并未破坏 T001 | pass |
| 3 | fresh-context 独立 Review | T002 | 6 项：Sync 文档、边界表、兼容测试、精确消息、AST 相对导入、命名 | 全部修复；复审 pass |
| 4 | fresh-context 最终集成 Review | T001+T002 @ 19930b2/4454f22 | 1 项非阻塞：ADR-0011 实现状态段过期（F-001） | F-001 已在 4454f22 修正并独立复核；最终 verdict pass |

- 最终 AI 审查结论：最终集成 fresh-context 六维 Review pass（content `47912a9b…`，产品代码指纹 `cb5cb891…`，requirements `054795a2…`）；F-001 已 resolved。
- 未解决问题与剩余风险：Feature 依赖未合并的 #45；ADR-0011 仍为 Proposed（等待决策 owner 接受）；真实 Provider 未验证
- 本地报告或证据：`.specify/delivery/common-foundation-20261107/runtime/`
- [ ] 未执行本地 AI Code Review
- [x] 已执行；实现者已处理或明确记录每个问题，最终代码已重新审查

## 评审重点

- 入口或建议阅读顺序：`packages/core/common/` → `packages/core/llm-provider/src/spawn_join_llm_provider/parsing.py` → `metadata/parsing.py` → adapter `_validation.py` → Sync `_model_file.py` → 锁/构建图。
- 关键行为、边界或设计取舍：Common 默认零依赖；错误类型由调用方拥有；adapter 的 null/首错顺序与元数据 formatter 不下沉；Sync 不引入 LangChain。
- 需要人工或特定环境验证：GitHub CI 六个包矩阵；Linux/Python 3.11/3.14；真实 Provider 调用不在本 PR。

## 条件章节

### 架构、设计或 ADR（仅有相关变化时）

- 当前设计、入口、归属与依赖方向：Core 保留稳定契约；Common 拥有领域无关辅助实现，默认零依赖，`validation` extra 提供 Pydantic 能力；协议/适配/Sync 指向 Common，Core/Common 不反向依赖领域包。
- 设计变化与原因：从 LLM 协议包下沉已有复用机制，建立用户要求的统一公共辅助归属。
- ADR / 决策链接：[ADR-0011](../../../docs/decisions/engineering/0011-common-helper-package.md)（Proposed）
- 设计图或接口说明：`docs/architecture/package-boundaries.md`

### Slice / Stack（仅切片交付）

- Slice 与目标：本 PR 为 Feature 层，包含 T001 公共包与 T002 消费者迁移。
- Base 分支、依赖及合并顺序：下层 #45 已 squash 合入 main `6906acc`；本 PR 直接以 `main` 为 base。原基于 #45 的 #47 因基分支删除被关闭，本 PR 取代其发布。
- 本层不包含：时间/序列化辅助、思考默认值、schema 统一。
- 本层回滚：先回滚消费者迁移，再移除 Common 包与门禁接入；无数据迁移。

### 文档、发布或迁移（仅适用时）

- 源文档 / 生成文档：`README.md` / `README.en.md`、`AGENTS.md`、`docs/architecture/`、`docs/development/`、包级双语 README。
- 发布说明：新增未发布 Distribution；无 registry 或自动发布变更。
- 迁移、回滚或恢复步骤：旧协议导入保持；回滚按“本层回滚”。

## 回滚

按提交逆序恢复：先撤销 T002 消费者迁移与锁/构建图，再撤销 T001 公共包、CI/Profile/文档与 ADR 提案。无需数据迁移；回滚会恢复协议包内嵌读取实现，其他行为不变。

## 提交前确认

- [x] 我理解并能解释本次提交的变更。
- [x] 验证结果来自实际执行；未执行项、环境限制和剩余风险已明确标出。
- [x] 本次实际 diff 与 `reviewed_head` / 审查范围一致。
- [x] 阻断性 Review 问题已解决，或已记录明确的 owner 与处理决定。
- [x] 关联 ADR、文档、迁移和兼容性说明与最终代码一致。
