# Exploration and scope packet

## Request and investigation

- Request and desired outcome: 采用 LangChain-first 的 LLM runtime；删除自定义消息、内容块、工具、
  请求/响应和 `LLMProvider` 抽象；只保留 LangChain 不提供的 channel 契约、协议选项和少量错误。
- Delivery run / canonical packet path: `.specify/delivery/008-langchain-first-llm-runtime/exploration.md`
- Feature location / Bug slug: `specs/008-langchain-first-llm-runtime/`（本地，Git 忽略）
- Investigation: new capability；同时是 PR #16 的替代设计，不是在现有实现上做小重构。
- Provisional lane / recommended lane: Feature。涉及公共 API、包职责、依赖边界和长期 ADR。
- Baseline HEAD / relevant working-tree changes: `353af49cf9db6014b7af0437a3f9dc0dd651437c`
  （`origin/main`），工作区干净；PR #16 的实现不在 `main`。
- Governing instructions / ADRs: `AGENTS.md`、Constitution、`docs/architecture/package-boundaries.md`、
  ADR-0001–0004。ADR-0005 只存在于未合并 PR #16 的分支，不在 `main`；其“公共消息 + LLMProvider
  + 协议原生选项”方案不进入本基线，新 ADR-0006 记录替代设计。
- Tools / fallback / freshness limitations: 当前分支基于 `main`；PR #16 仅作为设计参考，不读取为
  已合并代码。未执行真实模型或渠道请求。

## Findings

- Facts: `main` 上两个目标包只有命名空间骨架；PR #16 中的消息层、`LLMProvider` 和适配层实现
  尚未合并。当前没有外部应用依赖这些公共类型。
- Facts: PR #16 的协议包有 54 个公共导出；适配层源码实际导入 41 个，13 个仅在 core 测试中使用：
  channel 类型、`AnthropicThinking`、`ContentBlock`、`JsonScalar`、`ProtocolOptions`、
  channel 错误。
- Facts: `Channel` 设计没有实现或外部消费者；它是最“未来”的部分，但也是 LangChain 不提供的
  连接/目录能力。
- Facts: LangChain 已提供 `BaseMessage`、`AIMessage`、`AIMessageChunk`、`ToolMessage`、
  `tool_calls`、`usage_metadata` 和工具调用流式块。若全仓库基于 LangChain，自定义这些类型是重复。
- Hypotheses: 采用 LangChain 消息后，删除消息映射可显著减少适配层代码和公共 API；剩余价值集中在
  channel、协议选项、配置校验和错误/日志边界。
- Recommendations: 从 `main` 重新实现精简版；不合并 PR #16；保留 channel 契约；暂不做 pool。
- Unknowns: channel 是否需要本 Feature 同时实现 HTTP；`llm-provider` 是否应改名；工厂是否只返回
  `BaseChatModel`，还是保留极薄的调用辅助。

## Current directory tree

```text
spawn-join/
├── packages/core/llm-provider/
│   ├── pyproject.toml
│   ├── README.md
│   ├── src/spawn_join_llm_provider/
│   │   ├── __init__.py
│   │   └── abstractions/__init__.py
│   └── tests/test_package.py
├── packages/infra/llm-provider-langchain/
│   ├── pyproject.toml
│   ├── README.md
│   ├── src/spawn_join_llm_provider_langchain/
│   │   ├── __init__.py
│   │   └── providers/{azure_openai,deepseek}/__init__.py
│   └── tests/test_package.py
├── docs/architecture/package-boundaries.md
├── docs/decisions/ (ADR-0001–0004；ADR-0005 只在未合并 PR #16)
└── .specify/extensions/delivery/delivery-config.yml
```

PR #16 中的开启分支 `ralph/007-llm-protocol-abstraction` 不在当前基线；本 Feature 不基于它。

## Current flow

当前没有运行时 LLM 调用流。两个包只提供命名空间；`Channel`、协议选项、Provider 或适配实现都
不存在于 `main`。PR #16 的旧设计是：公共消息/选项 → `LLMProvider` → LangChain Provider。
新设计改为：LangChain `BaseMessage` → 配置好的 `BaseChatModel`；`Channel` 独立于推理。

## Project history and external references

| Source / repository | Issue / PR / commit / version | Read paths and evidence | Relevance / adopted idea | Rejected parts / constraints / scope impact |
| --- | --- | --- | --- | --- |
| 本项目 | PR #16 / `3b7b850` | 旧实现、ADR-0005、测试、公共导出统计 | 作为旧设计验证；保留 channel/协议选项 | 不合并旧消息层和 `LLMProvider` |
| LangChain | `langchain-core 1.7.0`、`langchain-openai 1.7.3`、`langchain-anthropic 1.7.7` | `BaseChatModel`、`AIMessage`、`ToolMessage`、content blocks、usage metadata | 使用 LangChain 原生消息和模型接口 | 不把 LangChain 类型放进 channel 契约 |
| ADR-0005 | Proposed | 协议原生选项、渠道/Provider 分离、推理 opaque state | 保留协议原生选项和 channel 分离 | 其公共消息与 `LLMProvider` 部分被新 ADR 替代 |

- Search coverage: 当前仓库路径、PR #16 实现、ADR-0005、包边界、LangChain 固定版本源码。
- External research: performed（LangChain 消息/模型接口）。
- Evidence gaps: 未执行真实 Provider；channel HTTP 方案未定。

## Options and candidate change tree

比较选项：

1. **LangChain-first + channel 契约（推荐）**：应用使用 LangChain 消息；适配层只做配置、选项映射、
   校验和错误/日志；`llm-provider` 只保留 channel、协议选项、少量错误。
2. **协议包直接依赖 `langchain-core`**：代码更少，但协议包不再框架无关，需改包边界和 ADR；不推荐。
3. **保留 PR #16 的自定义消息/Provider**：公共面过大，与“全仓库 LangChain”重复；不推荐。

候选树（预计新增/修改）：

```text
spawn-join/
├── packages/core/llm-provider/
│   ├── src/spawn_join_llm_provider/
│   │   ├── __init__.py                 [modify] 仅导出 channel/options/errors
│   │   ├── options.py                  [new] ProtocolKind + 三种协议选项
│   │   ├── channels.py                 [new] Channel/ChannelConfig/PingResult/ModelPage
│   │   └── errors.py                   [new] 少量配置/渠道错误
│   ├── tests/test_options.py            [new]
│   ├── tests/test_channels.py           [new]
│   ├── tests/test_package.py            [modify]
│   └── README.md                        [modify] 重新定义为 channel/options 包
├── packages/infra/llm-provider-langchain/
│   ├── src/spawn_join_llm_provider_langchain/
│   │   ├── __init__.py                 [modify] 只导出 ChatModelConfig/create_chat_model
│   │   ├── config.py                   [new] ChatModelConfig + 调用前校验
│   │   └── factory.py                  [new] 三协议工厂与显式参数映射
│   ├── tests/test_factory.py            [new]
│   ├── tests/test_validation.py         [new]
│   ├── tests/test_public_api.py         [new]
│   └── README.md                        [modify] LangChain-first 使用示例
├── docs/architecture/package-boundaries.md [modify] 更新协议包职责
├── docs/decisions/llm-provider/0006-*.md   [new] 替代 ADR-0005 的 LangChain-first 决策
└── AGENTS.md                              [modify] 如包职责变化需要同步
```

明确不做：`ChannelPool`、模型路由、健康选路、HTTP 连接池、真实渠道实现（除非另开范围）。

## Scope, risks, and verification

- Included scope: 从 `main` 实现 LangChain-first runtime；删除重复消息层和 `LLMProvider` 设计；
  保留 `ProtocolKind`、三种协议选项、channel 契约、少量错误；工厂返回 `BaseChatModel`；
  选项映射/校验；离线测试；ADR/包边界/README。
- Excluded scope: `ChannelPool`、真实渠道 HTTP、每个 Provider 的独立 SDK、跨协议统一推理/上下文、
  自动重试/降级、持久化/密钥管理。
- Interfaces, compatibility, migrations, security: 两个包仍是 `0.1.0`；无外部调用方迁移；LangChain
  类型只出现在适配层；channel 配置只存 `credential_ref`。
- Verification: 两个包质量命令、docs/governance/static、`git diff --check`；测试使用 fake/构造模型，
  不请求网络。
- Decision blockers / questions: 无。三个决策已在 2026-10-31 由用户确认：
  1. 保留 `spawn-join-llm-provider` 名称，不重命名；
  2. Channel 只交付契约和 fake 测试，不实现 HTTP；
  3. 工厂直接返回 `BaseChatModel`，不保留额外调用包装。

## Checkpoint record

- EXPLORATION_VERDICT: ready
- Evidence location: `.specify/delivery/008-langchain-first-llm-runtime/exploration.md`
- SCOPE_APPROVAL: approved（用户 2026-10-31 确认）
- SPEC_APPROVAL: approved（用户 2026-10-31 确认）
- PLAN_GATE: approved（用户 2026-10-31 确认，含 `ChannelConfig.name` 修正）
- SLICE_PLAN: S0–S3 stacked（用户要求默认开启 `pr_slicing: "auto"`）
- SLICE_GATE: approved（用户 2026-10-31 接受 S0–S3 与 S0/S1/S2 行数例外）
