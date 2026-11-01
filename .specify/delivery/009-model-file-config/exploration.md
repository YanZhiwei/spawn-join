# Exploration and scope packet: 009-model-file-config

## Request and investigation

- Request and desired outcome: 在 `spawn-join-llm-provider` 与 LangChain 适配实现中增加
  `model.yaml`：`.env`/进程环境只保存 API key，YAML 保存协议、endpoint、模型标识、
  超时/重试和协议选项，并支持对外展示的模型名字。
- Delivery run / canonical packet path: `.specify/delivery/009-model-file-config/`
- Feature location: `specs/009-model-file-config/`（本文件落盘时已确定）
- Investigation: **new capability**（仓库内无任何 YAML / dotenv / model 文件机制）
- Provisional / recommended lane: **Feature** —— 新增公共 API、跨两个 Distribution 的
  配置边界、新增第三方依赖和安全边界。
- Baseline HEAD: `392aa909bcfe57f47d84d3d5e782ffd5fed4ae1f`；`git status --short` 为空。
- Governing instructions / ADRs:
  - ADR-0006（Accepted）：协议包保持框架无关；`ChatModelConfig` / `create_chat_model`
    在适配包；密钥只在工厂调用时传入并包成 `SecretStr`。
  - ADR-0001 / ADR-0002：交付工件与长期设计分离；`specs/` 本地忽略。
  - ADR-0007：默认 Slice 交付。
  - Constitution v1.0.0、`AGENTS.md`、`docs/architecture/package-boundaries.md`。
- Tools / fallback / freshness: `.codegraph/` 只有 `.gitignore`，没有可用索引；使用
  `rg` + 逐文件阅读作为回退。本地 Git 历史、PyPI 元数据和公开文档可访问。

## Findings

- Facts:
  - `packages/core/llm-provider` 仅依赖 `spawn-join-core`，导出 21 个名字，无文件/环境
    读取能力（`pyproject.toml`、`src/spawn_join_llm_provider/__init__.py`）。
  - `packages/infra/llm-provider-langchain` 只导出 `ChatModelConfig` 与
    `create_chat_model`；密钥由调用方传入（`src/.../config.py`、`factory.py`、
    `tests/test_public_api.py`）。
  - 仓库无 YAML/dotenv/model 文件实现；README 示例手工使用 `os.environ`。
  - 历史交付：`008-langchain-first-llm-runtime` 已 delivered；`006` superseded。
- Hypotheses:
  - 应用层愿意用显式路径换取可预测性（待用户确认；已确认）。
  - `display_name` 对 UI/CLI 有真实价值（用户提出并确认）。
- Recommendations:
  - 加载器归 LangChain 适配包；core 不新增依赖，避免复制 `ChatModelConfig`。
  - 新增 PyYAML 与 python-dotenv，仅进适配包。
  - 纯配置与 `.env` 解析在加载期完成；密钥引用在创建期解析。
- Unknowns: 无阻塞项；CodeGraph 不可用只影响导航效率。

## Current directory tree

```text
packages/core/llm-provider/
├── pyproject.toml                     # 仅依赖 spawn-join-core；无 YAML
├── README.md                          # 现有公共 API 与设计边界
├── src/spawn_join_llm_provider/
│   ├── __init__.py                    # 精确导出 21 个名字
│   ├── endpoints.py                   # EndpointConfig
│   ├── channels.py                    # ChannelConfig / ModelInfo
│   ├── options.py                     # 三种协议选项与校验
│   └── errors.py                      # ConfigurationError 等
└── tests/                             # test_channels / test_options / test_public_api 等

packages/infra/llm-provider-langchain/
├── pyproject.toml                     # 无 PyYAML / python-dotenv
├── README.md                          # 手工 os.environ 示例
├── src/spawn_join_llm_provider_langchain/
│   ├── __init__.py                    # 仅 2 个公共名字
│   ├── config.py                      # ChatModelConfig + validate_*
│   └── factory.py                     # create_chat_model
└── tests/                             # test_factory / test_validation / test_public_api

specs/009-model-file-config/           # 本地 Feature 工件（忽略）
```

## Current flow

```text
调用方代码
  → ChatModelConfig(protocol, endpoint, model, timeout, max_retries)
  → create_chat_model(config, api_key=os.environ[...], options=...)
      → validate_request → SecretStr → ChatOpenAI / ChatAnthropic
```

所有配置目前只能写在代码里；跨环境切换需要改代码或另写一层自定义解析。

## Project history and external references

| Source / repository | Issue / PR / commit / version | Read paths and evidence | Relevance / adopted idea | Rejected parts / constraints / scope impact |
| --- | --- | --- | --- | --- |
| 当前仓库 | `468ee7f`（PR #18）、`e05587d`（PR #24） | ADR-0006、两个包源码与测试、README | 继承“协议包框架无关、适配包做工厂”的边界 | 不重定义消息/Provider；不在协议包读文件 |
| LiteLLM | `BerriAI/litellm@2c733c0`，`litellm/proxy/example_config_yaml/simple_config.yaml`；docs 2026-11-01 | `model_list` + `litellm_params`；`os.environ/VAR` 文档与 issue #8919 | 具名模型列表、endpoint/model 分离 | 拒绝 env 插值小语言、代理路由语义 |
| aider | `Aider-AI/aider@308b154`，`aider/resources/model-settings.yml`；docs 2026-11-01 | `.env` 放 key、YAML 放模型元数据；多位置搜索 | key 与模型信息分离 | 拒绝隐式多路径合并与 last-wins |
| PyPI metadata | PyYAML 6.0.3（MIT，≥3.8）；python-dotenv 1.2.4（BSD-3-Clause，≥3.10） | `https://pypi.org/pypi/<name>/json` | 依赖可行性与许可证 | 版本锁进适配包 |

- Search coverage: 两个包全部源码/测试、README、ADR、Git 历史、PyPI、LiteLLM/aider 文档。
- External research: performed（比例匹配新能力）。
- Evidence gaps: 参考实现未逐版本运行；不影响范围决策，已接受。

## Options and candidate change tree

| 方案 | 结论 |
| --- | --- |
| 加载器放 core 协议包 | 拒绝：需要把 `ChatModelConfig` 下移或复制一份，破坏 ADR-0006 的边界 |
| 新建独立配置包 | 拒绝：当前只有一个消费者，制造无复用 Distribution |
| 加载器放适配包（采用） | 与 `ChatModelConfig` 同址，复用现有校验和工厂 |

```text
packages/infra/llm-provider-langchain/
├── pyproject.toml                     [预计修改] + PyYAML, python-dotenv
├── README.md                          [预计修改] model.yaml / .env 章节
├── src/spawn_join_llm_provider_langchain/
│   ├── __init__.py                    [预计修改] 导出 5 个名字
│   ├── model_file.py                  [预计新增] YAML → ModelCatalog
│   ├── config.py                      [复用] ChatModelConfig
│   └── factory.py                     [复用] create_chat_model
└── tests/
    ├── test_model_file.py             [预计新增] 主测试
    ├── fixtures/model.yaml            [预计新增] 正常夹具
    ├── fixtures/model-invalid-*.yaml  [预计新增] 失败夹具
    └── test_public_api.py             [预计修改] 精确导出

packages/core/llm-provider/README.md   [预计修改] 仅交叉引用
docs/decisions/llm-provider/0008-*.md  [预计新增] ADR
docs/decisions/README.md               [预计修改] 索引
docs/architecture/package-boundaries.md [预计修改] 明确加载归适配包
.gitignore                             [预计修改] 忽略 /.env
```

## Scope, risks, and verification

- Included: 单文件 `model.yaml`（schema v1）、显式 `.env`、进程环境优先、严格校验、
  模型清单与展示名、复用现有工厂、README/ADR/边界文档。
- Excluded: channel 配置、多文件合并/自动搜索、热重载、变量插值、密钥管理服务、
  真实 Provider 请求、路由/池。
- Interfaces / security: 新增 5 个公共名字；密钥仅以变量名入库；错误与 repr 不含密钥；
  不修改 `os.environ`；`safe_load` + 重复键拒绝。
- Verification: 适配包 Quality 命令、隔离构建、离线 pytest、docs/governance 检查。
- Decision blockers: 无。

## Checkpoint record

- EXPLORATION_VERDICT: ready
- Evidence location: `.specify/delivery/009-model-file-config/exploration.md`
- SCOPE_APPROVAL: **approved**

### Recorded decisions

- 2026-11-01：用户选择 **内置 `.env` 加载**、**只覆盖 chat model**。
- 2026-11-01：用户选择 **新增 `ModelSummary`** 暴露展示名。
- 2026-11-01：用户接受默认项：`env_file` 默认 `None`（显式传入）、重复键严格报错、
  `load_model_catalog` / `ModelCatalog` / `catalog.create_chat_model()` 命名。
- 2026-11-01：用户以“按默认”批准范围，随后以“spec”批准 Spec 澄清结果。
