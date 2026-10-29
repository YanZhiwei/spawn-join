# ADR-0005: 采用协议原生 LLM 契约与独立渠道边界

- Status: Proposed
- Date: 2026-10-29
- Domain: llm-provider
- Classification: 约束 LLM 领域契约、协议适配和渠道边界，属于 LLM 领域的跨模块架构决策。
- Decision owner: 仓库维护者
- Accepted by / date: 未批准
- Depends on: [ADR-0001](../engineering/0001-delivery-and-durable-design.md)
- Related: [包边界](../../architecture/package-boundaries.md)、[Constitution](../../../.specify/memory/constitution.md)、`specs/007-llm-protocol-abstraction/`（仅本地）
- Supersedes: 无
- Superseded by: 无

## Context and drivers

`packages/core/llm-provider` 与 `packages/infra/llm-provider-langchain` 目前只有命名空间骨架，
尚无请求、响应、Provider 或适配实现。项目需要支持三类常见 LLM 调用协议：

- OpenAI Chat Completions；
- OpenAI Responses；
- Anthropic Messages。

这三类协议的请求参数、响应内容块、错误和状态语义并不等价。尤其是“思考”和“上下文”：

- 推理开关、强度档位和 token 预算的名称与约束不同；
- 推理内容可能带签名或不透明状态，多轮工具调用需要原样回传；
- 服务端会话、上下文压缩、截断和提示缓存属于协议特有行为；
- 模型列表通常不能证明模型能力，能力也不应只由模型名称推断。

因此，把所有高级参数归一化为一个跨协议“通用选项”会产生有损映射，并隐藏能力差异。
另一方面，如果三个协议完全独立，业务调用又会在常见路径上重复分支。

现有包边界要求：`spawn-join-llm-provider` 只承载与框架无关的协议和领域抽象，不依赖
LangChain 或具体 Provider SDK；LangChain 适配和具体实现属于
`spawn-join-llm-provider-langchain`。网络、认证和客户端生命周期必须有明确拥有者。

本决策不涉及数据库、密钥存储或真实服务集成；这些在实现阶段另行设计。

## Options considered

1. **统一跨协议请求和推理/上下文语义**：调用方只写一套高级参数，由适配器映射到三个协议。
   优点是切换协议时业务代码变化小；缺点是推理档位、预算、采样约束、服务端会话和上下文
   压缩无法无损等价，容易静默降级或产生错误计费，因此不采用。
2. **三个完全独立的 Provider API**：每个协议拥有独立的请求、响应和调用接口。优点是协议
   差异最清楚；缺点是文本对话、工具调用、流式和错误处理等共同调用面重复，调用方在常见
   路径也要分支，因此不采用。
3. **薄公共调用契约 + 协议原生类型化选项 + 独立渠道能力**：公共层只承诺真正可移植的
   请求字段和响应外壳；高级参数使用协议原生类型；渠道层独立承担连接检查和模型目录。
   该方案保留共同调用面，同时不制造有损语义，采用此方案。

## Decision

- `spawn-join-llm-provider` 拥有与框架无关的公共消息、请求、响应、流式事件、能力声明、
  渠道契约和稳定错误语义；不得依赖 LangChain、HTTP 客户端或具体 Provider SDK。
- 公共请求只包含可移植字段：消息、工具、工具选择、最大输出、`temperature` 和 `top_p`。
  `stop`、推理、上下文管理、服务端会话和缓存等参数放入协议原生选项。
- 三个协议各自拥有类型化选项：
  - Chat Completions 选项；
  - Responses 选项；
  - Anthropic Messages 选项。
- 禁止使用无限制 `**kwargs`、任意字典或字符串化 JSON 作为公共高级参数通道。Provider
  收到不匹配的选项类型时必须拒绝，不猜测转换。
- 不建立统一的 `ReasoningIntent` 或统一上下文策略。协议无法表达或不支持某个参数时，
  返回明确的“不支持”错误；不得静默丢弃、近似映射、自动降级或自动重试。
- 公共响应保留统一外壳，但推理内容块必须携带协议原生不透明状态，以支持多轮回传；
  不得把推理块压成纯文本。推理内容默认不写日志。
- Provider 不得擅自裁剪历史消息以适配上下文窗口；超限返回稳定错误，由应用决定截断、
  摘要或更换模型。
- 服务端会话、`store`、`previous_response_id` 等状态参数必须显式开启，默认关闭；其数据
  留存和安全影响在实现阶段单独评审。
- 协议类型由渠道配置显式选择；不得根据模型名称推断协议，也不得在请求失败后自动切换
  协议。
- 渠道（Channel）与推理 Provider 分离：渠道拥有 `ping()` 和 `list_models()` 等连接/目录
  能力；推理 Provider 只负责请求参数封装、调用和响应转换。具体 HTTP/认证实现不在本决策
  的当前实现范围，后续以独立 Feature 和独立 infra Distribution 评估。
- 首个 Chat Completions 实现支持 OpenAI-compatible endpoint；Azure OpenAI 的 `api-key`
  认证、`api_version`、deployment 和 URL 语义与普通 Chat Completions 不同，作为后续任务
  单独设计，不用 `base_url` 伪装成同一配置。
- 渠道配置只保存凭据引用，不保存明文密钥；日志、异常和配置展示不得包含密钥、提示词、
  回答正文或推理内容。
- `spawn-join-llm-provider-langchain` 拥有三个协议适配器、参数校验、LangChain 类型转换、
  工厂和调用日志；LangChain 类型不得泄漏回协议包。
- 公共 API 通过 `__init__.py` 显式导出；依赖方向保持
  `llm-provider-langchain -> llm-provider -> spawn-join-core`。

## Key design and diagrams

目标边界如下，箭头表示依赖或调用方向，不是数据流图：

```text
业务应用
  └── LLMProvider（公共推理外壳）
        ├── ChatCompletionsProvider  -> LangChain ChatOpenAI(use_responses_api=False)
        ├── ResponsesProvider        -> LangChain ChatOpenAI(use_responses_api=True)
        └── AnthropicMessagesProvider -> LangChain ChatAnthropic

渠道 Channel（独立契约）
  ├── ping()
  └── list_models()
```

关键不变量：

1. 公共调用外壳不包含协议分支；协议差异由类型化选项和适配器承担。
2. 高级参数“不支持即失败”，不进行有损转换。
3. 推理块和工具调用在多轮交互中可原样回传。
4. 渠道检查不会隐式执行生成请求。
5. 任何日志都不包含密钥、提示词、回答正文或推理内容。

## Consequences and migration

收益：调用方在最常见的文本、工具和流式场景只依赖一套外壳；协议差异保持显式；测试可以
使用 fake 模型验证契约，不依赖真实凭据；渠道能力与推理能力不会互相污染。

成本：切换协议时，使用了高级参数的调用方必须调整选项构造；三个适配器需要分别维护参数
校验和映射测试；协议版本变化可能要求更新适配逻辑。

兼容性：当前两个包尚未发布具体契约，因此没有既有调用方需要迁移。新增运行时依赖
（如具体 LangChain 集成包）会在实现计划中单独列出并验证依赖方向。

重新评估触发条件：

- 业务确实需要在运行时跨协议切换，且愿意接受明确的有损映射规则；
- 需要把渠道实现与世界模型目录作为独立 Distribution 发布；
- LangChain 或上游协议发生破坏性变更；
- 需要持久化渠道配置或引入密钥管理服务。

## Verification and implementation status

本 ADR 目前只有决策，没有实现。相关 Spec、Plan、Tasks 仍是本地交付工件，不作为长期
契约来源。

已执行：

```text
pwsh -NoProfile -File scripts/quality.ps1 -Check static
结果：Static analysis: 0 failing check(s); exit_code=0
```

未执行：三个 Provider 的实现、真实服务调用、集成测试、构建、类型检查和完整质量门。
ADR 由 `Proposed` 改为 `Accepted` 前，必须完成 reviewed HEAD 对应的实现、评审和证据。

## Revision history

- 2026-10-29：提出协议原生选项、渠道/Provider 分离与推理块回传的候选决策。
