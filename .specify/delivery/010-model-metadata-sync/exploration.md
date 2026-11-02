# Exploration and scope packet: 010-model-metadata-sync

## Request and investigation

- Request and desired outcome: 为模型目录补齐价格、能力、模态和上下文等元数据，参考
  models.dev 设计可扩展的同步机制；当前阶段只提供手动同步，不启用定时任务，不自动把
  上游模型注册进应用目录。
- Delivery run / canonical packet path: `.specify/delivery/010-model-metadata-sync/`
- Feature location: `specs/010-model-metadata-sync/`（由 `speckit.specify` 创建）
- Investigation: **new capability**（仓库内没有价格、capability、modality、快照或同步实现）
- Provisional / recommended lane: **Feature** —— 新增持久数据格式、公共 API、可能新增
  Distribution、外部数据源和长期架构决策。
- Baseline HEAD: `f717f71b5360b1c4e8b421301359787b0e41db9e`；开始时 `git status --short`
  为空。
- Governing instructions / ADRs:
  - ADR-0006（Accepted）：协议包保持框架无关；应用直接使用 LangChain 类型；不定义运行时
    `ModelCapabilities` 协商抽象。
  - ADR-0008（Accepted）：`model.yaml` schema v1 严格校验；显式路径；排除远程配置中心、
    热重载和多文件合并。
  - ADR-0001 / ADR-0002：Spec 是本地临时工件，长期设计提炼到 `docs/decisions/`。
  - ADR-0007：默认 Slice 交付。
  - Constitution v1.0.0、`AGENTS.md`、`docs/architecture/package-boundaries.md`。
- Tools / fallback / freshness: 本 worktree 的 `.codegraph/` 未初始化（`codegraph status`
  返回 Not initialized）；使用源码、测试、Git 历史和公开文档作为回退。网络可用。

## Findings

- Facts:
  - `model.yaml` schema v1 只包含 `protocol`、`endpoint`、`model`、`api_key_env`、
    `display_name`、`timeout_seconds`、`max_retries` 和协议 `options`
    （`packages/infra/llm-provider-langchain/src/.../model_file/_schema.py`）。
  - `ModelSummary` 只有 `name`、`model`、`display_name`
    （`.../model_file/_catalog.py`）。
  - `ModelInfo` 只有 `id` 和 `display_name`；没有价格、模态、上下文或能力
    （`packages/core/llm-provider/src/.../channels.py`）。
  - `ChatModelConfig` 不依赖 `ChannelConfig`；渠道名是独立概念（ADR-0006 不变量 2/3）。
  - 仓库没有 AppData、platformdirs 或用户数据目录约定；`model.yaml` 默认当前工作目录，
    `.env` 默认当前工作目录，显式路径优先（ADR-0008）。
  - `platformdirs` 只作为开发依赖的传递依赖出现在锁文件中，项目本身未使用。
  - 仓库当前只有 `.github/workflows/quality.yml`，没有 scheduled workflow。
  - 现有测试覆盖 v1 解析、重复键、递归别名、密钥优先级和工厂构造；没有元数据或同步测试。
- Hypotheses:
  - 应用/CLI/UI 需要价格和能力信息来展示或选型，但仓库内暂时没有第二个消费者；因此运行时
    读取必须可选，不能改变现有行为。
  - models.dev 的 provider/lab 分层适合我们的多渠道场景，但需要显式 `metadata_ref` 映射，
    不能依赖名称猜测。
- Recommendations:
  - 元数据类型放在 `spawn-join-llm-provider`，保持纯类型、无 I/O。
  - 同步工具作为新的 infra Distribution，拥有源注册、抓取、合并、校验、差异、写入和报告。
  - 快照使用确定性的 JSON，与 `model.yaml` 分离；同步不修改 `model.yaml`。
  - 运行时通过显式 `metadata_file` 可选读取快照，不联网、不隐式搜索。
  - 当前只做手动同步；定时、自动 PR、后台刷新明确排除。
- Unknowns:
  - 渠道覆盖最终按 `model.yaml` 条目名还是独立渠道名索引；Plan 固定，不改变 Spec 语义。
  - 价格字段按模态分组的具体形状；Plan 固定。
  - 新包最终名称；当前倾向 `spawn-join-llm-model-sync`。
  - models.dev 的具体端点、字段映射和单位换算需在 Plan/实现阶段用 fixture 验证。

## Current directory tree

```text
packages/core/llm-provider/
├── src/spawn_join_llm_provider/
│   ├── __init__.py                 # 21 个公共导出
│   ├── channels.py                 # ChannelConfig / ModelInfo / ModelPage
│   ├── endpoints.py                # EndpointConfig
│   ├── options.py                  # 三种协议选项
│   └── errors.py
└── tests/

packages/infra/llm-provider-langchain/
├── src/spawn_join_llm_provider_langchain/
│   ├── model_file/
│   │   ├── _schema.py              # schema v1；严格拒绝未知字段
│   │   ├── _catalog.py             # ModelCatalog / ModelSummary
│   │   ├── _env.py                 # .env / 进程环境
│   │   └── _yaml.py
│   ├── config.py                   # ChatModelConfig
│   └── factory.py                  # create_chat_model
└── tests/

docs/decisions/llm-provider/
├── 0006-langchain-first-llm-runtime.md
└── 0008-model-file-and-env-boundary.md
```

## Current flow

```text
model.yaml
  └── parse_catalog
        ├── protocol / endpoint / model / api_key_env
        ├── display_name / timeout / retries
        └── options
              └── ModelCatalog.create_chat_model(name)
                    └── 进程环境 > .env 快照
                          └── ChatOpenAI / ChatAnthropic
```

所有配置目前只能写在代码或 v1 文件中；没有价格、能力、模态、上下文或 embedding 元数据。

## Project history and external references

| Source / repository | Issue / PR / commit / version | Read paths and evidence | Relevance / adopted idea | Rejected parts / constraints / scope impact |
| --- | --- | --- | --- | --- |
| 当前仓库 | `1958071`（PR #27）、ADR-0008 | `model_file/_schema.py`、`_catalog.py`、`tests/test_model_file.py` | 复用严格解析、显式路径、`.env` 边界和 `ModelCatalog` | 不把元数据塞进 v1；不破坏现有密钥语义 |
| 当前仓库 | ADR-0006、`468ee7f`（PR #18） | 协议包公共面、`ChatModelConfig` / `ChannelConfig` | 保持 `ModelConfig` 不依赖 `ChannelConfig` | 不恢复运行时 `ModelCapabilities` 协商抽象 |
| models.dev | `anomalyco/models.dev`，MIT；README v2 schema；`sync.md` | provider/lab 分层、`base_model` 继承、runner + provider 模块、dry-run/删除保护 | 共享模型事实 + 渠道覆盖；adapter 只抓取/转换 | 不引入其 AI SDK/前端；不直接采用 TOML 作为运行时格式 |
| LiteLLM | `BerriAI/litellm` 的 `model_prices_and_context_window.json` | `mode`、`output_vector_size`、多计价单位、`supports_*` | 未来 adapter 的字段参考；embedding/image 计价单位 | 字段扁平且命名不统一；不作为唯一权威 |
| OpenRouter | `https://openrouter.ai/api/v1/models` | 每 token 字符串价格、`supported_parameters` | 未来 adapter 候选 | 路由价不等于 lab 价；本次不实现 |

- Search coverage: 两个 LLM 包的源码/测试/README、ADR-0006/0008、v1 契约、Git 历史、
  models.dev README 与 `sync.md`、LiteLLM 价格 JSON。
- External research: performed（新能力，按比例检索公开实现）。
- Evidence gaps: models.dev 的实际响应尚未用 fixture 跑通；不影响范围决策，但必须在
  Plan/实现阶段验证字段和单位。

## Options and candidate change tree

| 方案 | 结论 |
| --- | --- |
| 只扩展 `model.yaml` 手工填写元数据 | 拒绝：价格/能力变化快，生成内容与手写配置混合，diff 噪音大 |
| 元数据类型 + 生成快照 + 可插拔同步 runner（采用） | 满足当前需求，后续新增源只加 adapter；运行时保持离线 |
| 在 LangChain 适配包内直接同步并联网 | 拒绝：元数据不是 LangChain 专属；网络副作用进入运行时包 |
| 立即做多源注册中心 + CI 定时 + UI | 拒绝：当前没有第二个运行时消费者；违反 YAGNI |

```text
packages/core/llm-provider/
├── src/spawn_join_llm_provider/
│   ├── metadata.py                  [预计新增] 纯元数据类型与校验
│   └── __init__.py                  [预计修改] 导出
└── tests/test_metadata.py           [预计新增]

packages/infra/llm-provider-langchain/
├── src/.../model_file/
│   ├── _schema.py                   [预计修改] schema v2 + metadata_ref + inline metadata
│   ├── _catalog.py                  [预计修改] metadata_file + ModelSummary.metadata
│   └── _metadata.py                 [预计新增] 快照读取与合并
├── tests/test_model_metadata.py     [预计新增]
└── README.md                        [预计修改]

packages/infra/llm-model-sync/       [预计新增 Distribution]
├── pyproject.toml / README.md
├── src/spawn_join_llm_model_sync/
│   ├── MetadataSource / SourceRegistry
│   ├── runner / snapshot / cache / CLI
│   └── sources/models_dev.py
└── tests/ + fixtures/

docs/decisions/llm-provider/0009-model-metadata-and-sync.md   [预计新增]
docs/architecture/package-boundaries.md                        [预计修改]
docs/architecture/repository-map.md                            [预计修改]
.specify/extensions/quality/quality-config.yml                 [预计修改] 新包 profile
.gitignore                                                      [预计修改] 如使用项目内缓存
```

## Scope, risks, and verification

- Included:
  - 纯元数据类型与校验。
  - `model.yaml` v2（读取 v1 兼容）与 `metadata_ref` / 人工覆盖。
  - 确定性 JSON 快照、来源 provenance、共享模型事实 + 渠道覆盖。
  - 手动同步 CLI：预览、应用、检查、指定源/输出/缓存。
  - 源注册表与 `MetadataSource` 契约；models.dev 首个 adapter。
  - 空响应/异常缩水/删除阈值保护、原子写、失败保留旧快照。
  - 运行时可选读取快照；不传时行为不变。
  - ADR、README、包边界、质量 profile 和测试。
- Excluded:
  - 定时任务、cron、自动 PR、后台刷新。
  - OpenRouter / LiteLLM 等第二个源。
  - 数据库、远程配置中心、热重载。
  - 模型路由、池、健康选路。
  - embedding/image/audio 的运行时工厂（本次只做元数据）。
  - UI、名称模糊匹配、自动注册上游模型。
- Interfaces / compatibility / security:
  - `ModelSummary` 追加可选 `metadata`；不传 `metadata_file` 时行为不变。
  - 快照只含非敏感元数据；源认证只引用环境变量名。
  - 同步不修改 `model.yaml`；不自动新增模型。
  - 新增包需要独立 `pyproject.toml`、`uv.lock`、`.venv`、构建和 quality profile。
- Verification:
  - 元数据解析/合并/优先级/单位/未知字段测试。
  - models.dev fixture 契约测试；live 网络测试不进入默认门禁。
  - v1 向后兼容测试。
  - 新包 `uv lock --check`、`uv sync --locked`、`scripts/quality.ps1 -Package ...`、
    隔离构建/安装。
  - 全仓库 `scripts/quality.ps1`、docs/governance、`git diff --check`。
- Decision blockers / questions:
  - 无阻塞项。
  - Plan 阶段固定：渠道覆盖键、价格字段形状、包最终名称、models.dev 端点/单位映射。

## Checkpoint record

- EXPLORATION_VERDICT: ready
- Evidence location: `.specify/delivery/010-model-metadata-sync/exploration.md`
- SCOPE_APPROVAL: **approved**
- User decision and date:
  - 2026-11-02：用户确认当前阶段只做手动同步，不启用定时任务。
  - 2026-11-02：用户确认采用“共享模型事实 + 渠道覆盖”的同一套快照结构。
  - 2026-11-02：用户确认权威快照放 `%APPDATA%\SpawnJoin\`，缓存/状态/报告放
    `%LOCALAPPDATA%\SpawnJoin\cache\`；库只接受显式路径。
  - 2026-11-02：用户确认提供源注册能力，但不自动注册/导入模型。
  - 2026-11-02：用户选择快照只包含被 `metadata_ref` 引用的模型及其渠道覆盖；未引用的上游模型忽略并在报告中列出。
  - 2026-11-02：用户以“按照建议”批准推荐范围。
  - 2026-11-02：用户批准更新后的 10 个切片和 S1/S5/S7 预算例外；明确要求不创建本地 git commit，代码留在工作树供晚间 code review。本次不执行 Ralph 的 per-task commit gate，也不声明 `ALL_TASKS_DONE`。
- Accepted non-critical limitations:
  - models.dev 实际响应尚未跑通；Plan/实现阶段用 fixture 验证。
  - 新包会增加独立锁文件、构建和 quality profile 维护成本。
  - 当前没有第二个运行时消费者；因此运行时读取保持可选，不默认启用。
