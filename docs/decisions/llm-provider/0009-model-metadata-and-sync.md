# ADR-0009: 模型元数据与手动同步边界

- Status: Proposed
- Date: 2026-11-02
- Domain: llm-provider
- Classification: 本决策约束 LLM 模型元数据的长期格式、同步工具归属、渠道覆盖结构和运行时读取边界，属于 `llm-provider` 领域。
- Decision owner: 仓库维护者
- Accepted by / date: 未批准
- Depends on: [ADR-0006](0006-langchain-first-llm-runtime.md)、[ADR-0008](0008-model-file-and-env-boundary.md)
- Related: [包边界](../../architecture/package-boundaries.md)、[ADR-0007](../engineering/0007-default-slice-delivery.md)
- Supersedes: 无；本 ADR 扩展 ADR-0008 的模型文件边界，不替代其显式路径与凭据决策
- Superseded by: 无

## Context and drivers

当前 `model.yaml` schema v1 只描述创建 chat model 所需的最小信息：协议、endpoint、
模型标识、密钥变量、超时/重试和协议选项。它不包含价格、输入/输出模态、上下文限制、
reasoning 控制、工具/结构化输出、embedding 或生命周期状态。应用、CLI 或 UI 若要展示
或比较模型，只能自行维护第二套数据。

同时存在以下约束：

- ADR-0006 规定协议包保持框架无关，应用直接使用 LangChain 类型，并明确不定义运行时的
  `ModelCapabilities` 协商抽象；`ChatModelConfig` 不依赖 `ChannelConfig`。
- ADR-0008 规定 `model.yaml` 严格校验、显式路径、密钥只通过环境变量引用，并明确排除
  远程配置中心、热重载和多文件合并。
- 仓库要求每个 Distribution 独立构建、测试和版本化；网络、文件等副作用必须有明确
  拥有者。
- 用户当前只需要手动刷新，不需要定时任务、自动 PR 或后台刷新。
- models.dev 提供公开的 `catalog.json`，当前约 6.4 MB、235 个 provider，分为
  provider 覆盖和 provider-agnostic 模型；provider 模型通过 `canonical_model_id` 指向
  共享模型。它是合适的首个同步源，但不应成为运行时硬依赖。

本决策需要在不破坏上述边界的前提下，回答四个问题：

1. 元数据放在哪里、由谁拥有；
2. 如何表达同一模型在多个渠道下的不同价格；
3. 外部数据如何进入系统，未来如何增加来源；
4. 运行时如何消费，同时保持离线、可选和向后兼容。

## Options considered

1. **只扩展 `model.yaml`，手工填写全部元数据**
   单文件直观，但价格和能力变化频繁，生成数据与手写配置混合，diff 噪音大，且容易
   把上游事实写错。拒绝。

2. **运行时直接同步或远程配置**
   应用启动时联网获取 models.dev 数据，或从远程配置中心读取。会引入离线失败、启动
   延迟、供应链和隐私问题，违反 ADR-0008 的显式路径与无热重载边界。拒绝。

3. **离线快照 + 手动 CLI + 源注册表（采用）**
   元数据以确定性 JSON 快照提交；CLI 在维护者手动执行时抓取、合并、校验和写入；
   运行时只读显式快照。新增源只增加 adapter。满足当前需求，并保留扩展缝。

4. **立即实现多源注册中心、定时 CI、自动 PR 和 UI**
   当前没有第二个运行时消费者，也没有定时需求；会显著扩大范围并引入 CI 权限和
   自动合并风险。拒绝，留待真实需求出现。

## Decision

采用方案 3，并明确以下边界。

### 元数据契约

- 纯元数据类型、快照文档解析和覆盖合并放在 `spawn-join-llm-provider`：
  `ModelMetadata`、`ModelMetadataDocument`、`ModelMetadataOverride`、`ModelPricing`、
  `ModelPriceRate`、`ModelPriceTier`、`ModelType`、`Modality`、`ModelStatus` 等。
- 边界字段校验使用 Pydantic dataclass；公共对象仍是 dataclass，保留 frozen、slots、
  kw_only 和 `dataclasses.replace` 语义。Pydantic 只作为通用校验依赖，不引入 LangChain
  或 Provider SDK。
- 这些类型只描述事实，不参与协议选择、路由、降级或能力协商。它们不是 ADR-0006 禁止的
  运行时 `ModelCapabilities` 抽象。
- 价格使用带 `modality`、`direction`、`unit`、`amount` 的费率列表；金额必须是有限
  非负数，单位必须显式；支持可选的长上下文阶梯。

### 持久格式

- `model.yaml` 升级到 schema v2，新增可选字段：
  - `metadata_ref: <lab>/<model>`：显式关联共享模型事实；
  - `metadata_source: {<source-id>: {provider, model}}`：显式关联源内渠道坐标；
  - `metadata`：人工覆盖，字段为 `ModelMetadataOverride`。
- v1 继续可读；v1 出现 v2 字段视为未知字段。
- `metadata_source` 存在时必须同时存在 `metadata_ref`；不做名称模糊匹配。
- 同步永不修改 `model.yaml`，也不自动把上游模型加入应用目录。

### 快照

- 生成并提交 `model-metadata.json`，独立 `schema_version`，当前为 1。
- 结构：
  - `sources`：来源 URL、原始内容 SHA-256、抓取时间、许可证；
  - `models`：只包含被 `model.yaml` 引用的共享模型事实；
  - `channels`：按 `model.yaml` 条目名索引，包含 `base_model`、源坐标和价格/限制/
    能力/模态/状态覆盖。
- 渠道覆盖只允许 `pricing`、`limits`、`capabilities`、`modalities`、`status`；
  名称、描述、类型、日期等共享事实不得在渠道层覆盖。
- 输出确定性：键排序、费率排序、阶梯排序；时间戳只放在 `sources`。
- 上游内容、修订、URL 和许可证不变时复用上次 `fetched_at`，避免重跑产生假漂移。
- 写入原子化；替换失败保留旧快照。快照已替换后缓存/报告/状态写入失败返回成功并
  附加可见警告，避免“命令失败但数据已改变”的矛盾结果。
- 多源快照按源保留仍被引用的渠道和来源；当前同步源更新其共享事实和声明渠道，并在
  同一条目被多个源映射时优先。

### 同步工具与源注册

- 新增 infra Distribution `spawn-join-llm-model-sync`，拥有网络、缓存、报告、原子写和
  CLI 副作用。
- 它依赖 `spawn-join-llm-provider` 获取元数据类型，并依赖 `PyYAML`/`platformdirs` 完成
  文件与缓存边界；运行时**不依赖** `spawn-join-llm-provider-langchain`。
- 完整 `model.yaml` 解析仍由 `spawn-join-llm-provider-langchain` 维护；同步工具只读取
  元数据投影（`metadata_ref`、`metadata_source`、`metadata`），避免把 LangChain 带入
  CLI 安装。LangChain 适配包仅作为测试/dev 依赖用于一致性验证。
- 首个源为 models.dev，抓取 `https://models.dev/catalog.json`，无需认证。
- 源通过实例化 `SourceRegistry` 显式注册；重复 ID 默认失败；不做 entry-point 自动
  发现或运行时动态加载。
- `MetadataSource` 只负责抓取和翻译；runner 负责合并、校验、diff、写入和报告。
- 源 URL 只接受 HTTP(S)，拒绝 userinfo 和凭据类查询参数；快照来源和错误信息不得
  暴露凭据。
- 新增源只增加 adapter、fixture 和注册项，不修改 runner、快照 schema 或运行时读取。

### 运行时

- `ModelCatalog.from_file` / `load_model_catalog` 增加可选 `metadata_file=None`。
- 提供快照时，按“共享事实 → 渠道覆盖 → 人工覆盖”合并；不匹配的 `base_model` 报错；
  缺失的共享事实显式返回无元数据，不编造默认值。
- `ModelSummary` 追加 `metadata_ref` 和 `metadata`，默认 `None`；不传快照时行为与当前
  版本一致。
- 运行时加载不发起网络请求、不自动刷新、不隐式搜索 AppData；所有路径由调用方显式提供。

### 存储与操作

- 桌面 App：`model.yaml` 和 `model-metadata.json` 放 `%APPDATA%\SpawnJoin\`；
  缓存、状态和报告放 `%LOCALAPPDATA%\SpawnJoin\cache\`。
- 服务/CLI：使用显式项目配置目录；库不硬编码 AppData。
- 当前只提供手动 CLI：`sync`、`--apply`、`--check`、`--source`、`--output`、
  `--cache-dir`。默认只计算 diff，不写文件。
- 不实现定时任务、自动 PR、后台刷新或自动模型注册。以后接入调度时复用同一命令。

### 明确不处理

- 模型路由、池、健康选路或基于元数据的自动选型；
- embedding/image/audio 的运行时创建工厂；
- 数据库、远程配置中心、热重载；
- 第二个同步源的具体实现；
- UI 展示。

## Key design and diagrams

```text
model.yaml (v2, 手写)
  ├── 现有推理字段
  ├── metadata_ref ──────────────┐
  ├── metadata_source ────────┐  │
  └── metadata (人工覆盖)     │  │
                              │  │
model-metadata.json (生成)    │  │
  ├── sources                 │  │
  ├── models.<lab>/<model> <──┼──┘  共享事实
  └── channels.<entry>       │      渠道覆盖
        ├── base_model <─────┘
        ├── source
        └── pricing / limits / capabilities / modalities / status

运行时：
ModelCatalog.from_file(metadata_file=...)
  └── shared → channel → inline override
        └── ModelSummary.metadata

同步：
model-sync sync --source models.dev
  ├── 读取 model.yaml 引用（复用适配包）
  ├── source.fetch → raw bytes
  ├── source.translate → SourceCatalog（只翻译请求的 refs/hosts）
  ├── runner: merge → validate → diff
  └── --apply: 原子写 model-metadata.json
```

依赖方向：

```text
spawn-join-core
    └── spawn-join-llm-provider              # 元数据类型 + Pydantic 边界校验
            ├── pydantic                     # 通用字段校验
            ├── spawn-join-llm-provider-langchain
            │       └── spawn-join-llm-model-sync   # dev/test only
            └── spawn-join-llm-model-sync           # runtime: provider + PyYAML + platformdirs
```

实际 CLI 运行时只依赖 `spawn-join-llm-provider` 与通用工具；LangChain 适配包仅用于测试
一致性，不进入运行时依赖图。

关键不变量：

1. `model.yaml` 是应用模型集合的唯一手写来源；同步不修改它。
2. 快照只包含被引用模型；完整上游目录只在本机缓存。
3. 同一模型共享事实只有一份；渠道只写差异。
4. 运行时默认离线；不传快照时行为不变。
5. 所有价格带单位；所有未知字段在写入前拒绝。
6. 源注册是显式、可测试的实例行为，不是全局魔法。
7. 重跑相同上游内容不产生字节漂移；异常渠道缩水不覆盖旧快照。
8. 同步一个源不会删除其他源仍被引用的渠道和来源。

## Consequences and migration

收益：

- 应用、CLI 和 UI 可以从同一份可审查快照读取价格、能力、模态和限制；
- 多渠道路由可以表达不同价格，而不复制共享事实；
- 新增源只需 adapter，不触碰运行时和已有快照结构；
- 运行时保持离线和向后兼容；
- 同步失败不会破坏最后一份可用数据。

成本与限制：

- 新增一个 Distribution，带来独立 `pyproject.toml`、`uv.lock`、`.venv`、构建、
  README、quality profile 和维护责任；
- 同步 CLI 不依赖 LangChain 适配包，运行时只需 `spawn-join-llm-provider`、PyYAML 和
  `platformdirs`；完整模型文件解析与运行时时序仍由适配包负责；
- 快照需要手动刷新和评审，存在过期风险；
- `model.yaml` v2 和快照 v1 都是长期格式，后续字段调整需要版本策略；
- 当前只有一个源，源注册表的多数扩展路径尚未被第二个真实源验证。

迁移：

- 现有 v1 `model.yaml` 不需要修改；不传 `metadata_file` 的调用方行为不变；
- 需要元数据的调用方在条目中增加 `metadata_ref`，并可选择 `metadata_source` 和
  `metadata`；
- 需要渠道价格的调用方增加 `metadata_source`，然后运行手动同步；
- 没有已发布的快照格式或外部消费者需要迁移。

重新评估触发条件：

- 出现非 LangChain 运行时或第二个元数据消费者；
- 需要第二个以上同步源，或源需要独立版本/认证/限流；
- 需要定时同步、自动 PR 或后台刷新；
- 快照 schema 需要破坏性变更；
- 需要 embedding/image/audio 的运行时创建能力。

## Verification and implementation status

本 ADR 当前为 Proposed，仅表示设计候选，不代表实现已完成。计划中的验证包括：

- `spawn-join-llm-provider`：元数据解析、校验、覆盖合并和确定性测试；
- `spawn-join-llm-provider-langchain`：v1 兼容、v2 解析、快照读取、多渠道和公共 API；
- `spawn-join-llm-model-sync`：源契约、models.dev fixture、runner、CLI 和失败保护；
- 新包独立锁文件、构建、隔离安装和 quality profile；
- 全仓库质量门、docs/governance 和 `git diff --check`。

实际命令、退出码和残余风险由 Delivery evidence 记录；在获得 reviewed HEAD 之前不得
将本 ADR 改为 Accepted，也不得用本 ADR 替代测试或运行证据。

## Revision history

- 2026-11-02：提出模型元数据、手动同步、源注册和运行时可选读取的候选决策。
- 2026-11-03：元数据边界增加 Pydantic dataclass 校验，保持 dataclass 公共语义；拆分
  `metadata/` 包并共享 JSON codec。
