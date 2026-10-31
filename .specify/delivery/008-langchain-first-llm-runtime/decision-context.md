# Decision context

**Feature**: `008-langchain-first-llm-runtime`（本地 `specs/008-langchain-first-llm-runtime/`）

**Baseline**: `353af49cf9db6014b7af0437a3f9dc0dd651437c` (`origin/main`)

**Mode**: resolve (pre-plan)

## Active constraints

- Constitution v1.0.0：公共契约精确类型化；包边界和依赖方向必须显式；未执行检查不得写成通过。
- ADR-0001：长期设计进入 `docs/decisions/`；ADR 必须自包含。
- ADR-0002：`specs/` 本地忽略；文档/ADR 不依赖本地 Spec。
- ADR-0003/0004：Feature 走 Spec/Plan/Tasks；Delivery 由固定 Release 管理；不自动远端写入。
- [包边界](../../../docs/architecture/package-boundaries.md)：`spawn-join-llm-provider` 不依赖
  LangChain 或具体 Provider SDK；`spawn-join-llm-provider-langchain` 拥有 LangChain 适配。

## Superseded historical context

- 旧候选 ADR-0005（公共消息/响应、`LLMProvider`、协议原生选项）只存在于未合并 PR #16 的
  分支 `ralph/007-llm-protocol-abstraction`，不存在于 `main`。它不能作为 `main` 的有效
  ADR 或链接目标；本 Feature 不修改不存在的文件。
- 新 ADR-0006 已在 `docs/decisions/llm-provider/0006-langchain-first-llm-runtime.md`
  记录 LangChain-first 决策，并明确旧候选不作为基线；它在最终评审 `d6cdc37` 后由
  `Proposed` 改为 `Accepted`。由于旧文件不在 `main`，没有可标记的 `Superseded by` 链接。
- PR #16 保持 open；关闭或标记 superseded 需要用户单独授权。

## Conflicts with proposed work

- 包边界文档仍把 `llm-provider` 描述为“与框架无关的 LLM 协议和领域抽象”，并把
  `llm-provider-langchain` 描述为“LangChain 适配层及 Provider 实现”。Plan 需要把前者改为
  channel/options/errors，把后者改为模型工厂、选项映射和校验。
- AGENTS 中适配层职责的“Provider 实现”措辞需要同步为 LangChain 模型工厂/协议适配。
- 依赖方向本身不冲突：新设计仍让 `llm-provider` 不依赖 LangChain；LangChain 类型只在
  适配层和应用层。

## Resolved decisions

| Decision | Resolution | Evidence |
|---|---|---|
| 包名 | 保留 `spawn-join-llm-provider`；重命名另立 Feature | 用户确认；Plan Scope Deltas |
| Channel 实现 | 只交付契约和 fake 测试；真实 HTTP 另立 Feature/包 | 用户确认；Spec FR-011 |
| 工厂边界 | 直接返回 `BaseChatModel`；不做 Provider 包装或调用辅助 | 用户确认；Plan Public interfaces |
| 交付策略 | `pr_slicing: "auto"`；本 Feature 使用 S0–S3 stacked slices，S0 先落地策略 | ADR-0007、tasks/slices |
| 渠道标识 | `ChannelConfig` 增加必填非敏感 `name`；唯一性由调用方/未来注册表负责 | Spec FR-009、data-model、contracts |
| 选项导出 | 导出三种具体选项、`ProtocolOptions` 联合和 `AnthropicThinking`；不导出字典映射函数 | Plan、contracts |
| `ModelCapabilities` | 不交付；当前无消费者，避免提前固化 | Plan Scope Deltas |
| Channel 能力矩阵 | 不交付；用 `PingResult`、异常和 `ModelPage` 表达当前状态 | data-model、contracts |
| PR #16 | 保持 open，不作为基线；关闭需授权 | Spec FR-018、research Decision 8 |
| ADR | 新增 ADR-0006；最终评审 `d6cdc37` 后 Accepted；不修改不存在的 ADR-0005 | ADR 文件、索引 |
| Slice 策略 | 默认 `auto`；S0 → S1 → S2 → S3，stacked + 逐片 squash | ADR-0007、delivery-config、slices |

## Open decisions after planning

无阻塞性开放决策。实现阶段只允许在不扩大公共契约的前提下调整私有函数、测试文件名和
文档措辞；任何公共 API、依赖方向、pool/HTTP 范围变化都需要重新打开 plan gate。

## Missing evidence

- 未执行真实 LangChain Provider 请求；新设计主要依赖离线构造和 fake 测试。
- 真实 channel HTTP 认证/目录行为尚未验证。
- 没有外部应用消费者，公共 API 精简仍以旧适配层使用情况和当前需求为依据。
- ADR-0006 已在最终评审 `d6cdc37` 后由维护者确认并改为 Accepted。
