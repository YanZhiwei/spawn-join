# Decision context

**Feature**: `007-llm-protocol-abstraction`

**Baseline**: `9cdb10a334acf9100ae822f7220cb67fa7a25650`

**Mode**: discover (pre-spec)

## Active constraints

- [Constitution](../../../.specify/memory/constitution.md) v1.0.0：公共契约必须精确类型化；
  每次只改一个独立模块；未执行的检查不得写成通过。
- [ADR-0001](../../../docs/decisions/engineering/0001-delivery-and-durable-design.md)：
  Spec/Plan/Tasks 是交付工件，长期设计决策进入 `docs/decisions/`；ADR 必须自包含。
- [ADR-0002](../../../docs/decisions/engineering/0002-untrack-historical-feature-artifacts.md)：
  `specs/` 只在本地，文档和 ADR 不得依赖被忽略的 Spec 才能理解。
- [ADR-0003](../../../docs/decisions/engineering/0003-enable-delivery-and-ralph.md)：
  Feature 走 Spec/Plan/Tasks；Ralph 串行、任务级质量/标准/评审门；不自动远端写入。
- [ADR-0004](../../../docs/decisions/engineering/0004-release-managed-delivery-installation.md)：
  Delivery 组件由固定 Release 管理；安装不等于执行通过。
- [包边界](../../../docs/architecture/package-boundaries.md)：
  `spawn-join-llm-provider` 不依赖 LangChain 或具体 Provider SDK；
  `spawn-join-llm-provider-langchain` 拥有 LangChain 适配和实现，不能把框架类型泄漏回协议包。

## Superseded historical context

无。ADR-0001 至 ADR-0004 均仍有效；ADR-0005 为本次新增 Proposed 决策，不替代既有 ADR。

## Conflicts with proposed work

未发现与现有 ADR、Constitution 或包边界冲突的约束。

需要一个新决策，因为本次会同时确定：

- 公共 LLM 请求/响应契约的边界；
- 三个协议适配器的拥有者；
- 协议原生高级参数与“不支持即失败”的策略；
- 渠道能力与推理 Provider 的分离。

## Open decisions the plan must resolve

1. 具体 LangChain 集成依赖：`langchain-openai`、`langchain-anthropic` 的版本范围，以及是否
   需要显式声明底层 SDK 依赖。
2. 三个协议的精确选项字段和跨字段校验规则；以锁定版本的 LangChain 与上游协议为准。
3. 响应内容块的公共表示，特别是推理块不透明状态的字段和序列化方式。
4. 渠道契约的首版字段；真实 HTTP 实现是否另起 Feature 和独立 Distribution。
5. 模型能力声明的来源：静态表、调用方提供，或从 LangChain model profile 转换。
6. 日志字段和脱敏测试的具体断言。

## Missing evidence

- 未执行真实模型请求或真实渠道探测；默认验证使用 fake/mock。
- 未核对所有模型和协议版本的参数约束；实现前按锁定依赖读取实际接口和测试。
- 渠道 HTTP 实现的依赖、认证和生命周期尚未设计。

## Resolve mode findings (pre-plan)

基准 `9cdb10a` 的两个目标包仍只有命名空间骨架，因此 ADR-0005 不与现有实现冲突。对 Plan
有约束的已确认事实：

- `langchain-core 1.7.0` 已安装；`langchain-openai 1.7.3` 要求
  `langchain-core>=1.7.0`，`langchain-anthropic 1.7.7` 要求 `>=1.6.10`，均支持 Python 3.11。
- `langchain_core.exceptions` 提供 `ModelAuthenticationError`、`ModelRateLimitError`、
  `ModelTimeoutError`、`ContextOverflowError` 等稳定异常，可用于适配层映射，无需直接依赖
  OpenAI/Anthropic SDK 异常。
- `ChatOpenAI` 的 Responses 模式默认 `store=True`；实现必须显式覆盖为 `False`，除非调用方
  显式开启。
- `ChatAnthropic` 默认 `max_retries=2`；实现必须显式设置 `0`，避免隐式重试。
- `ModelProfile` 提供上下文窗口、最大输出、工具、推理档位和 temperature 能力字段，可作为
  能力来源，但缺失字段必须保持未知。
- `providers/azure_openai` 与 `providers/deepseek` 目前只是命名空间；Azure 专用认证与
  deployment 语义与普通 Chat Completions 不同，首个切片只支持 OpenAI-compatible endpoint。

ADR-0005 的决策与 Plan 一致；没有需要新增的冲突项。ADR 仍为 `Proposed`，实现和 reviewed
HEAD 评审完成前不提升为 `Accepted`。
