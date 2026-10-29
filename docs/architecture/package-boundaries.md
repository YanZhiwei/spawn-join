# SpawnJoin Package Boundaries

> 本文件维护包的职责、依赖方向和公共边界。
> 每个 Distribution 的名称、版本、依赖和构建配置以对应的 `pyproject.toml` 为最终来源。

## Package Map

| Distribution | Import package | 路径 | 分组 | 允许承担的职责 |
|---|---|---|---|---|
| `spawn-join-core` | `spawn_join_core` | [`packages/core/spawn-join-core`](../../packages/core/spawn-join-core/) | `core` | 跨领域稳定的配置机制、异常、类型和基础协议 |
| `spawn-join-llm-provider` | `spawn_join_llm_provider` | [`packages/core/llm-provider`](../../packages/core/llm-provider/) | `core` | 与框架无关的 LLM 协议和领域抽象 |
| `spawn-join-llm-provider-langchain` | `spawn_join_llm_provider_langchain` | [`packages/infra/llm-provider-langchain`](../../packages/infra/llm-provider-langchain/) | `infra` | LangChain 适配层及 Provider 实现 |
| `spawn-join-observability` | `spawn_join_observability` | [`packages/infra/spawn-join-observability`](../../packages/infra/spawn-join-observability/) | `infra` | 日志、追踪、指标等可观测性能力 |

当前只有最小源码骨架。新增模块前，先确认它属于哪个 Distribution、由哪个包拥有，
以及是否真的需要形成跨组件复用。

## Dependency Direction

```text
业务应用
    ├── spawn-join-llm-provider-langchain
    │       ├── spawn-join-llm-provider
    │       └── langchain-core
    └── spawn-join-observability
            └── spawn-join-core

spawn-join-llm-provider ──> spawn-join-core
spawn-join-llm-provider-langchain ──> spawn-join-llm-provider
```

必须保持以下方向：

1. `spawn-join-core` 不得依赖其他 SpawnJoin 领域包，也不应因一个小工具引入第三方依赖。
2. `spawn-join-llm-provider` 可以依赖 `spawn-join-core`，但不得依赖 LangChain 或具体
   Provider SDK。
3. `spawn-join-llm-provider-langchain` 负责框架适配和 Provider 实现，不能把框架类型
   泄漏回协议包。
4. `spawn-join-observability` 可以依赖 Core，但不能反向成为 Core 的依赖。
5. 业务应用可以组合多个领域包，但包之间的相互依赖必须有明确的领域理由。

## Independent uv Projects

每个 Distribution 都是独立的 uv project，不使用仓库根目录共享环境或根级 uv workspace：

| Distribution | 开发环境 | 锁文件 | 本地开发依赖 |
|---|---|---|---|
| `spawn-join-core` | `packages/core/spawn-join-core/.venv/` | `packages/core/spawn-join-core/uv.lock` | 无 SpawnJoin 包依赖 |
| `spawn-join-llm-provider` | `packages/core/llm-provider/.venv/` | `packages/core/llm-provider/uv.lock` | `spawn-join-core` 的相对路径源 |
| `spawn-join-llm-provider-langchain` | `packages/infra/llm-provider-langchain/.venv/` | `packages/infra/llm-provider-langchain/uv.lock` | `spawn-join-llm-provider` 的相对路径源 |
| `spawn-join-observability` | `packages/infra/spawn-join-observability/.venv/` | `packages/infra/spawn-join-observability/uv.lock` | `spawn-join-core` 的相对路径源 |

包间的发布依赖仍然写在 `[project].dependencies` 中；仅开发期的本地路径解析写在对应
`pyproject.toml` 的 `[tool.uv.sources]` 中。这样既保留 Distribution 的发布元数据，
又允许每个包在自己的环境中以 editable 方式开发。

四个包的 `uv.lock` 应提交到 Git；各包的 `.venv/`、`build/`、`dist/` 和 `*.egg-info/`
属于本机或构建产物，不应提交。

共享质量策略放在根 tool-only `pyproject.toml`，不创建根级 Python project 或共享环境。
Black/isort/Ruff/Pyright/pytest 只加入每包 dev group，不进入发布运行时依赖。
检查命令和隔离 wheel 安装说明见 [质量门说明](../development/quality-gates.md)。

## Source Layout and Public Surface

- 每个 Distribution 必须使用 `src/` layout，并拥有独立的 `pyproject.toml`。
- 测试以 Distribution 为边界放在对应包的 `tests/` 目录。
- 公共 API 通过包的 `__init__.py` 显式导出；内部模块、测试辅助函数和临时兼容层不得
  因为可导入就自动成为公共契约。
- 与框架无关的领域抽象留在领域包；LangChain、Provider SDK、Redis、数据库等外部
  适配和副作用留在对应的 infra 或适配器包。
- 网络、文件、数据库、缓存、线程和任务等副作用必须有明确拥有者；Core 和协议层应
  保持尽可能纯粹、可替换和可测试。

## Extension and Extraction Rules

- 只有至少两个组件存在稳定、真实的复用需求时，才考虑把能力提升到 Core。
- 如果能力依赖第三方库，优先放入相应领域或 infra 包，而不是 Core。
- 不要预先创建没有明确拥有者的 `utils.py`、`helpers.py`、`constants.py` 或万能基类。
- `spawn-join-llm-provider-langchain` 内部的 Azure OpenAI、DeepSeek 等实现暂时共享一个
  适配包。只有当某个 Provider 需要独立版本、依赖、测试或维护周期时，才考虑拆分为
  独立 Distribution。

## LLM Provider Protocol Surface

- `spawn-join-llm-provider` 拥有框架无关的消息、请求、响应、流式事件、三种协议的原生选项、
  模型能力、渠道契约和稳定错误；不依赖 LangChain、Provider SDK 或 HTTP 客户端。
- `spawn-join-llm-provider-langchain` 拥有三个协议 Provider、LangChain 参数/响应映射、工厂、
  凭据引用解析和调用日志；不把 LangChain 类型泄漏回协议包。
- 协议由配置类型显式选择，不根据模型名称推断，也不在失败后自动切换。
- 渠道真实 `ping()`/`list_models()` HTTP 实现尚未加入；渠道契约与推理 Provider 保持分离。
- Azure OpenAI 专用认证、`api_version` 和 deployment 语义尚未实现；首个切片只覆盖
  OpenAI-compatible endpoint。

## Change Review

当新增、移动或拆分包时，Plan 或 Review 必须说明：

1. 新边界解决的真实复用或维护问题；
2. 新增依赖的方向和理由；
3. 公共 API、版本和安装方式是否改变；
4. 需要新增或迁移的测试、构建和文档；
5. 是否需要同步更新 [`repository-map.md`](repository-map.md)、README 和 AGENTS。
