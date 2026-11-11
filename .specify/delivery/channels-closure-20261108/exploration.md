# Exploration and scope packet — channels-closure-20261108

## Request and investigation

- Request: 按建议实施 channels，形成闭环：把已有的 `Channel` 契约落成真实
  Provider transport，并让 `ChannelConfig -> ping/list_models -> ModelInfo ->
  ChatModelConfig -> create_chat_model` 成为可用链路。
- Delivery run / canonical packet path:
  `channels-closure-20261108` / `.specify/delivery/channels-closure-20261108/exploration.md`
- FEATURE_DIR: `specs/015-llm-channel-closure`
- Feature location: `specs/015-llm-channel-closure`（Core Specify 创建；Spec artifacts 按项目策略本地保留）
- Investigation: 新能力（existing contract, missing implementation）。
- Provisional lane / recommended lane: **Feature**。新增 Distribution、公共 API、
  网络/凭据边界、CI/质量 Profile 和 ADR，不属于 Lightweight 或 Bugfix。
- Baseline HEAD: `9f8cb1c`（detached HEAD）；工作区只有此前 Delivery run 的
  untracked 运行记录，本次分析未修改产品源码。
- Baseline verification:
  - `uv run --locked --project packages/core/llm-provider pytest packages/core/llm-provider/tests -q` → **185 passed**
  - `uv run --locked --project packages/infra/llm-provider-langchain pytest packages/infra/llm-provider-langchain/tests -q` → **301 passed**
- Governing instructions / ADRs: `AGENTS.md` 0–8、Constitution、
  `docs/architecture/package-boundaries.md`、`docs/development/quality-gates.md`、
  ADR-0006、ADR-0008、ADR-0009、ADR-0010、ADR-0011。
- Tools / fallback / freshness: CodeGraph 当前索引可用；PowerShell 读取源码、
  锁文件、测试和 CI 配置；SDK API 通过已安装的 `openai==3.42.0` /
  `anthropic==2.3.0` 实际 introspection 核对。

## Concepts, boundaries, and research questions

| Term | Meaning in this request / authoritative source | Ambiguity or excluded meaning |
| --- | --- | --- |
| Channel | `spawn-join-llm-provider/channels.py` 的连接级契约：`config`、`ping`、`list_models` | 不是 `BaseChatModel`，不生成 completion；不是路由/池/健康选路 |
| ChannelConfig | 协议包中的命名连接配置：`protocol`、`endpoint`、`timeout_seconds`、`name`、`credential_ref` | `credential_ref` 是 opaque 引用，不是明文密钥 |
| Transport | 具体 Provider SDK 的 `ping`/`list_models` 实现 | 不是 LangChain 模型工厂；不依赖 `BaseChatModel` |
| Bridge | `ChannelConfig` -> `ChatModelConfig`、`ModelInfo` -> `ModelSummary` 的纯转换 | 不做自动选型、自动路由或能力协商 |
| Discovery | `list_models()` 返回的 `ModelInfo` 分页 | 不自动写入 `model.yaml`；写入仍由调用方/产品决定 |
| Credential resolution | 默认把 `credential_ref` 解释为环境变量名 | 不是密钥管理服务、热轮换或多凭据池 |

- Domain boundary:
  - `spawn-join-llm-provider` 继续只拥有框架无关契约、选项、元数据和稳定错误。
  - 新 channel transport 拥有 Provider SDK、网络、分页、认证和错误映射。
  - `spawn-join-llm-provider-langchain` 只增加无网络桥接和目录检视。
  - `spawn-join-agent-deepagents` 保持只消费 `BaseChatModel`，不读取凭据。

| Question / decision affected | Evidence and source identity | Conclusion / conflicting evidence | Remaining gap, impact, and next owner |
| --- | --- | --- | --- |
| `Channel` 是否已有真实实现？ | `channels.py` 只有 `Protocol`/dataclass；全仓库仅 `tests/test_channels.py` 的 `FakeChannel` | 没有生产实现；契约被 ADR-0006 显式延后 | 需要新 Feature/ADR；不是小修补 |
| 是否应放进 LangChain 适配包？ | `ADR-0006` 要求协议包框架无关；适配包职责是模型工厂；`ping` 明确“不生成 completion”，LangChain 无标准 list/ping API | 不建议。Channel 用户不应被迫安装 LangChain；适配包不应变成网络/健康客户端 | 推荐独立 `spawn-join-llm-channel` |
| SDK 是否支持 `ping`/`list_models`？ | 已安装 `openai==3.42.0`：`AsyncOpenAI.models.list()` 返回 `AsyncPaginator`；`anthropic==2.3.0`：`AsyncAnthropic.models.list(after_id, limit)` 支持分页 | 两者都可用 `/models` 做轻量认证探测；OpenAI 当前模型列表无分页参数，Anthropic 有 `after_id`/`limit` | 需要统一 `ModelPage` 语义；OpenAI 的 `next_cursor` 为 `None` |
| `ChannelStatus` 是否足够表达“无 models 端点”？ | `channels.py` 只有 `OK`、`AUTHENTICATION_FAILED`、`UNREACHABLE`、`TIMEOUT`、`INVALID_RESPONSE` | 不足。OpenAI-compatible 网关可能不实现 `/models` | 建议新增 `UNSUPPORTED`，并在 ADR 中说明兼容性 |
| `list_models` 认证失败用什么错误？ | `errors.py` 只有 `ChannelError`、`ChannelUnavailableError`、`UnsupportedChannelOperationError`、`ChannelResponseError` | 没有认证子类，消费者无法稳定区分 401/403 | 建议新增 `ChannelAuthenticationError(ChannelError)` |
| `credential_ref` 如何解析？ | `ChannelConfig.credential_ref` 只要求非空；`model.yaml` 用 `api_key_env`，两者独立 | 不能假设同一个名称空间 | 默认 resolver 把 `credential_ref` 当环境变量名；显式 `api_key`/client 注入优先 |
| 是否需要新的 `channels.yaml`？ | ADR-0008 明确排除 channel 配置；当前没有产品文件格式需求 | 本 Feature 不做文件格式；CLI 用 flags，库用 `ChannelConfig` | 若产品需要渠道管理 UI，另开 Feature |
| 是否能做真实 Provider 验证？ | 当前环境无凭据/测试 endpoint | 不能声称已执行 live 验证 | 增加 opt-in live tests；默认跳过并报告未执行 |

## Findings

- Facts:
  - `Channel` 契约完整但无实现；`ChannelConfig`/`PingResult`/`ModelInfo`/`ModelPage` 已由测试固定。
  - `llm-provider-langchain` 只有模型工厂和 `model.yaml`；没有任何 `Channel` 引用。
  - `ChatModelConfig` 与 `ChannelConfig` 是两套独立类型；`ModelInfo` 与 `ModelSummary` 没有转换。
  - `ModelSummary` 目前只有名称、模型、展示名和元数据，缺少 protocol/endpoint/timeout/options，无法直接支撑渠道 UI/CLI。
  - `scripts/quality.ps1`、CI matrix、quality profile 都按六个 Distribution 枚举；新增包必须同步。
- Hypotheses:
  - 真实 channel transport 能显著缩短“添加渠道 -> 测试 -> 拉模型 -> 用模型”的产品流程；但当前没有 UI 消费者，需以用户本次明确请求作为需求证据。
  - 把 transport 放独立包可以避免 LangChain 成为 channel 使用者的硬依赖。
- Recommendations:
  - 新增 `spawn-join-llm-channel` infra Distribution，实现 OpenAI-compatible 与 Anthropic 两个 transport。
  - 协议包只补 `UNSUPPORTED` 与 `ChannelAuthenticationError` 两个契约缺口。
  - 适配包增加无网络桥接和目录检视，不包装 `BaseChatModel`。
  - 增加最小 CLI `ping`/`list-models`，不做 `channels.yaml`。
- Unknowns:
  - 企业网关是否普遍实现 `/models`；不支持时返回 `UNSUPPORTED` 是否足够。
  - 真实 Provider 的 401/403/429/5xx 具体异常类型是否与 SDK 版本一致；用 opt-in live tests 验证。

## Current directory tree

```text
spawn-join/
├── packages/core/llm-provider/
│   ├── src/spawn_join_llm_provider/
│   │   ├── channels.py                 # Channel/ChannelConfig/ModelInfo/ModelPage/PingResult；无实现
│   │   ├── errors.py                   # 稳定协议/渠道错误；无认证子类
│   │   └── __init__.py                 # 公共导出
│   └── tests/test_channels.py          # 仅 FakeChannel 契约测试
├── packages/infra/llm-provider-langchain/
│   ├── src/spawn_join_llm_provider_langchain/
│   │   ├── config.py                   # ChatModelConfig；与 ChannelConfig 无转换
│   │   ├── factory.py                  # create_chat_model；返回原生 BaseChatModel
│   │   └── model_file/_catalog.py      # ModelCatalog/ModelSummary；无 get/protocol/options
│   ├── tests/                          # 301 个离线测试；无 channel 测试
│   └── pyproject.toml                  # 无 channel SDK 依赖
├── scripts/quality.ps1                 # 六个包的 ValidateSet/映射
├── .github/workflows/quality.yml       # 六个包的 CI matrix
├── .specify/extensions/quality/quality-config.yml # 六个包 Profile
├── docs/architecture/package-boundaries.md        # 六包边界与依赖图
├── docs/architecture/repository-map.md            # 六包目录地图
├── AGENTS.md                            # 六包基线
└── docs/decisions/llm-provider/
    ├── 0006-langchain-first-llm-runtime.md        # 明确延后真实 channel
    ├── 0008-model-file-and-env-boundary.md        # 明确排除 channel 配置
    └── 0009-model-metadata-and-sync.md            # 元数据只读
```

## Current flow

```text
model.yaml / ChatModelConfig
  -> ModelCatalog / create_chat_model
  -> ChatOpenAI / ChatAnthropic（原生 BaseChatModel）
  -> 应用直接调用 LangChain
```

断点：

```text
ChannelConfig -> ??? -> ping/list_models
ModelInfo     -> ??? -> ModelSummary / ChatModelConfig
```

## Project history and external references

| Source / repository | Issue / PR / commit / version | Read paths and evidence | Relevance / adopted idea | Rejected parts / constraints |
|---|---|---|---|---|
| 当前仓库 | HEAD `9f8cb1c` | `channels.py`、`errors.py`、`test_channels.py`、adapter `_catalog.py`/`config.py`/`factory.py` | 保留现有契约和类型；只补缺口 | 不在协议包引入 Provider SDK |
| ADR-0006 | Accepted | `docs/decisions/llm-provider/0006-langchain-first-llm-runtime.md` | 保持 LangChain-first、原生 `BaseChatModel`、协议包框架无关 | 不把 channel transport 塞进适配包；不做 pool/路由/健康 |
| ADR-0008 | Accepted | `docs/decisions/llm-provider/0008-model-file-and-env-boundary.md` | `model.yaml`/`.env` 归适配包 | 本 Feature 不新增 `channels.yaml` |
| ADR-0009 | Proposed | `docs/decisions/llm-provider/0009-model-metadata-and-sync.md` | 元数据只描述事实 | 不用元数据自动选型/路由 |
| OpenAI Python SDK | `3.42.0`（仓库 lock） | `AsyncOpenAI.models.list()` introspection；`AsyncPage.data`、`AsyncPaginator` | 用 `/models` 做 ping/list；client 可注入 | OpenAI 模型列表当前无 `limit`/`after` 参数；`next_cursor=None` |
| Anthropic Python SDK | `2.3.0`（仓库 lock） | `AsyncAnthropic.models.list(after_id, limit)`；`AsyncPage.has_more/last_id` | 支持 cursor 分页；`ModelInfo` 有 `display_name`/`lifecycle` | 需要统一到 `ModelPage`；只映射 id/display_name |
| Python packaging / uv | 仓库现有六包 | `scripts/quality.ps1`、CI matrix、quality profile | 新包按现有 Distribution 方式独立锁/构建/测试 | 不创建根级 uv workspace |

- Search coverage: `Channel`/`ChannelConfig`/`ping`/`list_models` 全仓库检索；
  adapter 公共 API/测试；quality/CI/ADR/边界文档。
- External research: 使用已安装 SDK 的实际签名和 lock 版本，不另抓未固定上游文档。
- Evidence gaps: 无真实 Provider 凭据；live 行为未验证。非决策关键，需在实施后以 opt-in
  live tests 或用户环境补证。

## Options and candidate change tree

### Options

1. **把 channel transport 放进 `spawn-join-llm-provider-langchain`**  
   复用现有 SDK 依赖和配置，但会让只想 ping/list 的用户被迫安装 LangChain，并把
   “模型工厂”扩成“网络/健康/目录客户端”。与 ADR-0006 的框架无关 channel 契约冲突。拒绝。

2. **把 channel transport 放进 `spawn-join-llm-provider`**  
   类型同址，但会给框架无关的核心包引入 `openai`/`anthropic` SDK 和网络副作用，违反
   依赖方向。拒绝。

3. **新增 `spawn-join-llm-channel` infra Distribution（推荐）**  
   独立拥有 Provider SDK、认证、分页、错误映射和 CLI；协议包保持纯契约；适配包只做
   无网络桥接。代价是新增一个 Distribution 的锁文件、README、质量 Profile 和 CI 矩阵。

4. **只保留契约，不实现 transport**  
   维持现状，但不能形成用户要求的闭环。拒绝。

### Candidate change tree

```text
spawn-join/
├── packages/core/llm-provider/
│   ├── src/spawn_join_llm_provider/channels.py          [预计修改] 增加 ChannelStatus.UNSUPPORTED
│   ├── src/spawn_join_llm_provider/errors.py            [预计修改] 增加 ChannelAuthenticationError
│   ├── src/spawn_join_llm_provider/__init__.py          [预计修改] 导出新枚举成员/错误
│   └── tests/test_channels.py, test_public_api.py       [预计修改] 覆盖新契约
├── packages/infra/llm-channel/                          [预计新增] 新 Distribution
│   ├── pyproject.toml / uv.lock / LICENSE               [预计新增] 独立 uv project 与许可证
│   ├── README.md / README.en.md                         [预计新增] 双语包文档
│   ├── src/spawn_join_llm_channel/
│   │   ├── __init__.py                                  [预计新增] 显式公共导出
│   │   ├── _openai.py                                   [预计新增] OpenAI-compatible ping/list_models
│   │   ├── _anthropic.py                                [预计新增] Anthropic ping/list_models
│   │   ├── _credentials.py                              [预计新增] credential_ref -> env 解析
│   │   ├── _errors.py                                   [预计新增] SDK 异常 -> 稳定 Channel 错误/状态
│   │   ├── factory.py                                   [预计新增] create_channel 按协议分派
│   │   ├── cli.py                                       [预计新增] ping/list-models 最小 CLI
│   │   └── py.typed                                     [预计新增] 类型标记
│   └── tests/                                           [预计新增] fake client、错误映射、CLI、live skip
├── packages/infra/llm-provider-langchain/
│   ├── src/spawn_join_llm_provider_langchain/config.py  [预计修改] ChatModelConfig.from_channel
│   ├── src/spawn_join_llm_provider_langchain/model_file/_catalog.py
│   │                                                    [预计修改] ModelSummary 增字段、from_model_info、get/names/contains
│   └── tests/                                           [预计修改] 桥接与目录检视回归
├── scripts/quality.ps1                                  [预计修改] 新包 ValidateSet/映射/Build
├── .github/workflows/quality.yml                        [预计修改] 新包 CI matrix
├── .specify/extensions/quality/quality-config.yml       [预计修改] 新包 Profile
├── AGENTS.md / README.md / README.en.md                  [预计修改] 七包基线与包选择表
├── docs/architecture/package-boundaries.md              [预计修改] 新包职责与依赖方向
├── docs/architecture/repository-map.md                  [预计修改] 目录地图
└── docs/decisions/llm-provider/0013-channel-runtime-and-credentials.md
                                                         [预计新增] Proposed ADR，扩展 ADR-0006 的延后 channel 条款
```

## Scope, risks, and verification

- Included scope:
  - `OpenAIChannel`（`chat_completions` + `responses` 共用 OpenAI-compatible transport）
    和 `AnthropicChannel` 的 `ping`/`list_models`。
  - 认证、超时、连接、限流、5xx、404/不支持的稳定映射。
  - `create_channel` 按 `ProtocolKind` 分派；显式 `api_key`/client 注入；默认
    `credential_ref` 作为环境变量名解析。
  - 最小 CLI `spawn-join-channels ping|list-models`，无 `channels.yaml`。
  - 协议包 `UNSUPPORTED` / `ChannelAuthenticationError`。
  - 适配包 `ChatModelConfig.from_channel`、`ModelSummary.from_model_info`、
    `ModelSummary` 增 protocol/endpoint/timeout/max_retries/options、
    `ModelCatalog.get/names/__len__/__contains__`。
  - 新包 README/许可证/锁文件/质量 Profile/CI；ADR-0013。
- Excluded scope:
  - `channels.yaml`、渠道注册表、多文件合并、热重载、远程配置、密钥管理服务。
  - pool、路由、健康选路、failover、限流、并发控制。
  - 新 Provider（Azure OpenAI、Bedrock、Vertex 等）和 embedding/rerank/image/audio。
  - Agent purpose binding/产品装配改动。
  - 目录 CLI `validate/list/show`（可后续独立 Feature）。
  - 默认质量门中的真实 Provider 请求；live tests 仅 opt-in。
- Interfaces / compatibility / security:
  - 新包公共 API 预计为 `OpenAIChannel`、`AnthropicChannel`、`create_channel`。
  - 协议包增加枚举成员和异常子类属于向后兼容的公共 API 扩展，但需更新 public API 测试。
  - 密钥只在构造/调用时传入 SDK；不进入 `ChannelConfig`、`repr`、日志或错误文本。
  - `credential_ref` 默认按环境变量名解析；显式 `api_key`/client 优先。
  - 客户端生命周期：具体类提供 `aclose()`；CLI 确保关闭。
- Verification:
  - 新包：`uv lock --check`、`uv sync --locked`、`pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-channel`。
  - 协议/适配包：各自 quality 命令 + 针对性 pytest。
  - Fake SDK client 单测覆盖成功、401/403、429、超时、连接失败、5xx、404、畸形响应、
    `limit`/cursor、`UNSUPPORTED`。
  - live tests 通过环境变量启用；无凭据时 skip 并明确报告未执行。
  - 全仓库 `pwsh -NoProfile -File scripts/quality.ps1`、docs/governance、`git diff --check`。
- Decision blockers / questions:
  - 是否批准新增 `spawn-join-llm-channel` Distribution（而不是放进适配包）。
  - 是否批准协议包新增 `ChannelStatus.UNSUPPORTED` 与 `ChannelAuthenticationError`。
  - 是否接受本环境无法执行 live Provider 验证，作为非关键限制。
  - 是否批准最小 CLI；若不批准，可从 scope 移除而不影响库级闭环。

## Checkpoint record

- EXPLORATION_VERDICT: ready
- Evidence location: `.specify/delivery/channels-closure-20261108/exploration.md`
- SCOPE_APPROVAL: approved — 用户 2026-11-08 在会话中明确选择“批准，按推荐范围继续”：新增 `spawn-join-llm-channel`（OpenAI-compatible + Anthropic 的 `ping`/`list_models`）、协议补 `UNSUPPORTED`/`ChannelAuthenticationError`、adapter 增加 `from_channel`/目录检视，并同步 ADR/质量/CI/文档；接受 live Provider 验证当前不可执行这一非关键限制。
- Design reduction: 用户 2026-11-08 在设计门选择“批准，但去掉 CLI”。CLI 从本 Feature 移除，库 API 闭环不变；不视为 scope expansion。
- Accepted limitations: live Provider 验证在当前环境不可执行；需在实施后以 opt-in 测试或用户环境补证。

## Phase handoff

- Receiving owner: Core Specify（scope 批准后）。
- Approved input identity: 本 packet + baseline `9f8cb1c` + 上述 ADR/约束。
- Permitted operations: 只读设计/规划；不实现、不提交、不推送。
- Required reading: `AGENTS.md` 0–8、Constitution、`package-boundaries.md`、
  ADR-0006/0008/0009、`channels.py`、`errors.py`、adapter `_catalog.py`/`config.py`。
- Known gaps: live Provider 行为未验证；`credential_ref` 的产品语义需在 ADR/Plan 固定。
- Expected return: Spec/Plan/Tasks 的 scope 边界、接口、测试/验证路径；任何 material
  expansion 回到 scope approval。
