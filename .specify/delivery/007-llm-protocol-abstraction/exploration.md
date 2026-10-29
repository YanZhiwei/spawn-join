# Exploration and scope packet

## Request and investigation

- Request and desired outcome: 为 `spawn-join-llm-provider` 定义与框架无关的 LLM 请求/响应契约，
  在 `spawn-join-llm-provider-langchain` 中基于 LangChain 实现 Chat Completions、
  Responses 和 Anthropic Messages 三个协议适配器；渠道的 `ping()` 和模型列表能力与推理
  Provider 分离。
- Delivery run / canonical packet path: `.specify/delivery/007-llm-protocol-abstraction/exploration.md`
- Feature location / Bug slug: `specs/007-llm-protocol-abstraction/`（本地，Git 忽略）
- Investigation: new capability
- Provisional lane / recommended lane: Feature；涉及跨包公共契约、协议适配、安全与长期
  架构决策，不能按 Lightweight 处理。
- Baseline HEAD / relevant working-tree changes: `9cdb10a334acf9100ae822f7220cb67fa7a25650`；
  开始时工作区干净，无 changed paths。
- Governing instructions / ADRs: `AGENTS.md`、`.specify/memory/constitution.md`、
  `docs/architecture/package-boundaries.md`、ADR-0001 至 ADR-0004；本 Feature 新增
  Proposed [ADR-0005](../../../docs/decisions/llm-provider/0005-protocol-native-llm-contracts.md)。
- Tools / fallback / freshness limitations: CodeGraph 索引最新；GitHub Issues/PRs 已检索，
  当前无对应 LLM 契约讨论；LangChain 上游代码按固定 revision 读取；未执行真实模型请求。

## Findings

- Facts: 两个目标包目前只有命名空间骨架；现有测试只验证导入、Distribution 身份和依赖
  边界。`spawn-join-llm-provider` 只依赖 `spawn-join-core`，适配包只依赖协议包和
  `langchain-core`。
- Facts: 现有包边界禁止协议包依赖 LangChain 或具体 Provider SDK；适配层不得把框架类型
  泄漏回协议包。
- Facts: Chat Completions、Responses 和 Anthropic Messages 在推理参数、内容块、结束原因、
  服务端会话和上下文管理上不等价；LangChain 的 OpenAI 集成可以在同一类中切换 API 模式，
  因此协议必须在配置中显式选择。
- Hypotheses: 统一高级参数会产生有损映射；通过协议原生类型化选项和明确的“不支持”错误，
  可以在保持共同调用外壳的同时避免静默降级。
- Recommendations: 采用薄公共调用契约 + 三个协议原生选项 + 独立渠道契约；首个实现切片为
  Chat Completions，随后 Responses、Anthropic Messages。
- Unknowns: 具体 LangChain 集成包版本、各协议参数的精确校验规则、渠道 HTTP 实现是否
  需要独立 Distribution；这些在 Plan 和后续 Feature 中解决。

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
│   │   └── providers/
│   │       ├── __init__.py
│   │       ├── azure_openai/__init__.py
│   │       └── deepseek/__init__.py
│   └── tests/test_package.py
├── docs/architecture/package-boundaries.md
├── docs/decisions/README.md
└── .specify/memory/constitution.md
```

## Current flow

当前没有运行时调用流。导入路径只提供命名空间；没有消息、请求、响应、Provider、渠道或
错误映射实现。现有测试仅验证模块可导入、Distribution 身份和依赖集合。

## Project history and external references

| Source / repository | Issue / PR / commit / version | Read paths and evidence | Relevance / adopted idea | Rejected parts / constraints / scope impact |
| --- | --- | --- | --- | --- |
| 本项目 | `9cdb10a`；Issues/PRs #1–#15 | 源码骨架、测试、包边界、ADR-0001–0004 | 依赖方向和本地 Specs 规则 | 无既有 LLM 契约可复用 |
| LangChain | `350568952c4b65d1310081d45a2536b6449712f0` | `langchain_core` 的 `BaseChatModel`、内容块、OpenAI/Anthropic 集成与测试 | 统一调用接口、内容块和模型 profile 的参考 | 不把 LangChain 类型作为公共契约 |
| LangChain | commit `17d3d892cd1f05273c23b36bd8f3a13ee4220939` | Responses API 路由修复及测试 | 协议模式影响实际请求行为，必须显式配置 | 不按模型名自动推断协议 |
| langchain-google | `b49d2b7122d889fe5e1c406102c737bba61eac17` | Gemini `generateContent` 集成 | 三种 API 家族不是完整集合 | 不作为首版协议范围 |

- Search coverage: 本仓库路径、符号、Git 历史和全部 Issues/PRs；LangChain 上游实现、测试和
  相关修复提交。
- External research: performed（只读 GitHub 与官方文档）。
- Evidence gaps: 未执行上游测试或真实服务请求；具体参数约束按实现时锁定的依赖版本核对。

## Options and candidate change tree

```text
spawn-join/
├── packages/core/llm-provider/
│   ├── src/spawn_join_llm_provider/
│   │   ├── __init__.py                 [modify] 显式公共导出
│   │   ├── models.py                   [new] 消息、内容块、usage
│   │   ├── requests.py                 [new] 公共请求与协议选项
│   │   ├── capabilities.py             [new] 模型能力声明
│   │   ├── channels.py                 [new] 渠道契约与结果类型
│   │   ├── errors.py                   [new] 稳定错误语义
│   │   └── abstractions/provider.py    [new] 公共 Provider 契约
│   ├── tests/test_contracts.py         [new] 契约与边界测试
│   └── README.md                       [modify] 公共 API 与边界
├── packages/infra/llm-provider-langchain/
│   ├── src/spawn_join_llm_provider_langchain/
│   │   ├── config.py                   [new] 三个协议配置
│   │   ├── factory.py                  [new] 按协议创建 Provider
│   │   ├── validation.py               [new] 参数与跨字段校验
│   │   ├── mapping.py                  [new] 公共转换
│   │   └── protocols/
│   │       ├── chat_completions.py     [new] 首个纵向切片
│   │       ├── responses.py            [new] 第二切片
│   │       └── anthropic_messages.py   [new] 第三切片
│   ├── tests/test_protocols.py         [new] fake model 契约测试
│   └── README.md                       [modify] 使用与验证说明
├── docs/architecture/package-boundaries.md [modify] 补充协议/渠道边界
└── docs/decisions/llm-provider/0005-*.md   [new] 本决策
```

其他候选：

1. 统一 `ReasoningIntent`/上下文策略：被排除，存在有损映射。
2. 三套完全独立 Provider API：被排除，公共调用面重复。
3. 渠道 HTTP 实现立即放入适配包：暂缓；渠道与 LangChain 无关，后续以独立 Feature 和独立
   infra Distribution 评估。

## Scope, risks, and verification

- Included scope: 公共消息/请求/响应/流式事件/错误/能力/渠道契约；三个协议类型化选项；
  Chat Completions、Responses、Anthropic Messages 三个 Provider；LangChain 适配和 fake
  model 测试；README 与包边界文档同步。
- Excluded scope: 真实渠道 HTTP 实现；统一推理意图；多模态/音频/视频；内置搜索、computer
  use、批处理；自动重试/降级/协议切换；自动历史裁剪；提示缓存和上下文压缩实现；数据库
  持久化；真实凭据集成测试。
- Interfaces, compatibility, migrations, security: 新公共 API，无既有调用方迁移；协议包
  不新增第三方运行时依赖；适配包新增 LangChain 集成依赖需在 Plan 中确认；密钥只以引用
  形式进入渠道配置；日志不记录内容。
- Verification: 两个包各自的 `pwsh -NoProfile -File scripts/quality.ps1 -Package ...`；
  fake model 的普通/流式/工具/推理/错误契约测试；`git diff --check`；文档与治理检查。
- Defect handoff: 不适用，本次不是 Bugfix。
- Decision blockers / questions: 具体依赖版本和参数约束在 Plan 解决；渠道实现是否独立
  Distribution 留待后续 Feature。

## Checkpoint record

- EXPLORATION_VERDICT: ready
- Evidence location: `.specify/delivery/007-llm-protocol-abstraction/exploration.md`
- SCOPE_APPROVAL: approved

Approval record:

- 2026-10-29：用户确认“Chat Completions → Responses → Anthropic”实现顺序，并授权安装
  `PSScriptAnalyzer 1.25.0`。本次批准范围为本包中的 ADR 与 Spec 固化，不授权源码实现、
  提交、推送或合并。
- Accepted limitations: 未执行真实服务请求；具体 LangChain 集成包版本和协议参数约束在
  Plan 阶段核对。
