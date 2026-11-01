# ADR-0008: 模型目录文件与凭据边界

- Status: Proposed
- Date: 2026-11-01
- Domain: llm-provider
- Classification: 本决策约束 LLM 模型配置的持久格式、凭据来源、适配包公共契约和依赖边界，属于 `llm-provider` 领域。
- Decision owner: 仓库维护者
- Accepted by / date: 未批准
- Depends on: [ADR-0006](../llm-provider/0006-langchain-first-llm-runtime.md)
- Related: [包边界](../../architecture/package-boundaries.md)；Spec、Plan 与文件契约留在本地被忽略的 Feature 目录，不在此建立链接
- Supersedes: 无；本 ADR 扩展 ADR-0006 的适配包公共面，不替代其 LangChain-first 决策
- Superseded by: 无

## Context and drivers

当前应用只能在代码中构造 `ChatModelConfig` 并手工从环境变量读取 API key
（`packages/infra/llm-provider-langchain/README.md` 的示例）。由此产生三个问题：

1. 切换模型、endpoint、超时或协议选项需要改代码并重新发布；
2. key 的读取方式分散在各个调用点，缺少统一的优先级与错误语义；
3. 面向用户的模型列表没有稳定的展示名，UI/CLI 只能显示内部别名或 Provider 标识。

ADR-0006 已确定：

- `spawn-join-llm-provider` 保持框架无关，不依赖 LangChain、Provider SDK 或 HTTP 客户端；
- `ChatModelConfig` 与 `create_chat_model` 位于适配包；
- API key 只在工厂调用时传入并包装为 `SecretStr`；
- 当前不实现 pool、路由或健康选路。

本决策需要在不破坏上述边界的前提下，引入一个可审查、可测试的文件配置格式。

## Options considered

1. **把加载器放进 `spawn-join-llm-provider`**
   需要把 `ChatModelConfig` 下移或复制到协议包，并让协议包依赖 YAML 解析库；直接违反
   ADR-0006 的框架无关与依赖方向，拒绝。

2. **新建独立配置 Distribution**
   当前只有 LangChain 适配包一个消费者，没有第二个稳定复用需求；会制造额外的版本、
   锁文件和发布边界，违反 YAGNI，拒绝。

3. **加载器留在 LangChain 适配包（采用）**
   与 `ChatModelConfig` 同址，复用现有校验与工厂；第三方依赖只进入 infra 包；协议包
   零改动。代价是适配包公共面从 2 个名字扩展到 5 个。

4. **不增加文件配置，只改进文档**
   不能解决跨环境切换与统一密钥语义；用户已明确要求 `model.yaml`，拒绝。

## Decision

在 `spawn-join-llm-provider-langchain` 中增加 `model_file/` 包（公共入口
`__init__.py`，私有实现 `_yaml.py`、`_schema.py`、`_catalog.py`、`_env.py`），
并采用以下约束：

- **文件格式**：默认当前工作目录的 `model.yaml`（可显式覆盖），`schema_version: 1`；顶层 `models` 映射、
  可选 `default`；每个条目包含 `protocol`、`endpoint`、`model`、`api_key_env`，以及
  可选 `display_name`、`timeout_seconds`、`max_retries`、`options`。
- **凭据引用**：只接受 `api_key_env: ENV_VAR_NAME`。不支持 `${VAR}`、`$VAR` 或
  `os.environ/VAR` 插值；内联 `api_key` 作为未知字段拒绝。
- **优先级**：进程环境高于显式传入的 `.env`；变量存在但为空/空白时视为非法，不回退。
- **副作用**：库不修改 `os.environ`；`.env` 只在调用方显式传入时读取，并在加载时
  只快照被引用的变量。
- **严格性**：未知字段、重复键、类型错误、空模型集合、无效 `default` 全部在构造模型
  前拒绝；错误包含 YAML 路径，不包含密钥值或文件行内容。
- **展示名**：`display_name` 可选，缺省回退为选择名；它不参与查找、默认选择或协议判断。
- **公共 API**：新增 `load_model_catalog`、`ModelCatalog`、`ModelSummary`；
  `catalog.create_chat_model(name=None, *, environ=None)` 在创建瞬间解析密钥并调用现有
  工厂。`ChatModelConfig` 与 `create_chat_model` 的行为保持不变。
- **依赖**：适配包新增 `PyYAML`（MIT）与 `python-dotenv`（BSD-3-Clause）；协议包不新增
  依赖。
- **明确不处理**：channel 配置、多文件合并、自动路径发现、热重载、远程配置中心、
  密钥管理服务、路由/池/健康选路。

## Key design and diagrams

```text
应用
  └── load_model_catalog("model.yaml", env_file=".env")
        ├── YAML compose + 重复键/递归别名检查
        ├── schema 校验 → ChatModelConfig / ProtocolOptions（复用现有类型）
        ├── .env 读取（可选）→ 仅保留 api_key_env 引用
        └── ModelCatalog（不可变）
              ├── models: ModelSummary(name, model, display_name)
              ├── default_name
              └── create_chat_model(name?, environ?)
                    └── 进程环境 > .env 快照
                          └── create_chat_model(config, api_key, options)
                                └── LangChain BaseChatModel（SecretStr）
```

依赖方向保持：

```text
spawn-join-llm-provider
    └── spawn-join-llm-provider-langchain
            ├── PyYAML
            └── python-dotenv
```

关键不变量：

1. 目录对象创建后不可变；重新加载才反映文件修改。
2. 错误消息、清单与 `repr` 不含密钥值。
3. `.env` 不是隐式输入；不传 `env_file` 就不读取。
4. 选择名在单个文件内唯一；展示名允许重复。
5. 文件层不定义第二套协议选项，只映射到现有类型。

## Consequences and migration

收益：

- 模型配置可以随环境替换，不必改代码；
- 密钥与模型元数据分离，降低明文凭据进入版本库的风险；
- UI/CLI 获得稳定的展示名和有序清单；
- 解析、校验和工厂复用现有实现，不引入第二套运行时。

成本与限制：

- 适配包公共面扩大，需要同步 README、契约测试和 ADR；
- 新增两个第三方依赖和锁文件变化；
- 文件格式成为长期契约，后续字段调整需要遵守 `schema_version`；
- 不支持热重载、远程配置或密钥轮换；这些由宿主应用负责；
- 未来出现非 LangChain 运行时或多个配置消费者时，需要重新评估加载器归属。

迁移：当前没有已发布的文件格式或调用方；现有代码内配置继续有效。

## Verification and implementation status

已实现并通过目标包与全仓库本地质量门、quickstart 和最终独立评审；等待用户
Code Review 与 PR CI。本 ADR 仍为 `Proposed`，不代表已合并或已发布。实际命令与
结果由 Delivery evidence 记录。

## Revision history

- 2026-11-01：提出模型文件、`.env` 边界与公共 API 扩展的候选决策。
