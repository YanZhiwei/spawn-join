# Decision context: 009-model-file-config

Mode: **resolve**（Plan 前；核对 ADR 声明与当前代码）
Baseline HEAD: `392aa909bcfe57f47d84d3d5e782ffd5fed4ae1f`
Date: 2026-11-01

## Active constraints

| 来源 | 约束 | 与本次工作的关系 |
| --- | --- | --- |
| ADR-0006 | `spawn-join-llm-provider` 不依赖 LangChain/SDK/HTTP；适配包拥有 `ChatModelConfig` 与 `create_chat_model`；密钥只在工厂调用时进入并包 `SecretStr` | 决定加载器放适配包；决定密钥在创建瞬间解析 |
| ADR-0001 | 交付工件与长期设计分离 | spec/plan/tasks 留在 `specs/`；决策写 ADR |
| ADR-0002 | 历史 Feature 工件不跟踪；长期契约必须在可跟踪位置 | `specs/` 忽略；README/ADR 承担长期文档 |
| ADR-0007 | 默认 Slice 交付 | tasks 之后需要 slice 计划与门禁 |
| Constitution v1.0.0 | 外部输入边界校验；密钥不入源码/日志；依赖方向单向；证据绑定真实 diff | 严格 schema、错误脱敏、只改适配包 |
| `package-boundaries.md` | 协议包框架无关；第三方依赖优先放领域/infra 包 | PyYAML/python-dotenv 只进适配包 |
| `AGENTS.md` | 新依赖需许可证/维护性理由；不为低概率风险增加机制 | 两个成熟依赖，理由已记录；不做插值/热重载 |

## Verified claims against current code

| ADR 声明 | 核对结果 | 证据 |
| --- | --- | --- |
| 协议包无 LangChain / Provider SDK | 成立 | `packages/core/llm-provider/pyproject.toml` 仅 `spawn-join-core` |
| 适配包只导出两个公共名字 | 成立（本次将扩展） | `src/spawn_join_llm_provider_langchain/__init__.py`、`tests/test_public_api.py` |
| 密钥只在工厂调用时传入并包 `SecretStr` | 成立 | `factory.py` 的 `SecretStr(api_key)`；`config.py` 的 `ChatModelConfig` 无 key 字段 |
| 构造前校验协议/端点/选项 | 成立 | `config.py::validate_request`、`endpoints.py`、`options.py` |
| 无 pool / 路由 / 真实 channel HTTP | 成立 | 全包检索无相关符号；README 明确声明 |

## Conflicts / open decisions

1. **适配包公共面扩展**：ADR-0006 写“只保留 `ChatModelConfig` 与 `create_chat_model`”。
   本次新增 `load_model_catalog`、`ModelCatalog`、`ModelSummary`，属于**扩展**而非替代。
   → 需要 ADR-0008，并在其中说明 ADR-0006 仍然有效。
2. **新增第三方依赖**：PyYAML + python-dotenv 进入适配包。ADR-0006 未禁止适配包依赖，
   但需要记录选择理由与替代方案。
3. **术语重叠**：core 已有 `ModelInfo(id, display_name)`（渠道目录条目）。本次的
   `ModelSummary(name, model, display_name)` 是本地配置视图，不复用、不修改 `ModelInfo`。
   → 在 README/ADR 中明确两者语义，避免后续误用。
4. **`.env` 读取归属**：内置解析意味着库会读文件。已决定：仅显式参数触发、不写
   `os.environ`、进程环境优先、加载时快照。

## Superseded / historical

- 无 ADR 被替代。
- `008-langchain-first-llm-runtime` 的探索/证据保留为历史上下文；本次不重新讨论
  LangChain-first 本身。

## Missing evidence

- CodeGraph 索引不可用（只有 `.gitignore`），导航使用文本检索；不影响架构判断。
- 未运行参考实现（LiteLLM/aider）；只读取文档与固定提交路径，限制已记录。

## Resolution

- 无未解决的架构冲突；ADR-0008 以 `Proposed` 记录上述扩展，待最终评审后提升为 Accepted。
- Plan 可以按“适配包拥有文件加载 + 两个新依赖 + 五个公共名字”推进。
