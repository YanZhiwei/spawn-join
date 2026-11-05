# spawn-join-llm-model-sync

[简体中文](#中文) | [English](#english)

## 中文

SpawnJoin 的手动模型元数据同步工具。

它从显式选择的数据源抓取模型目录，只翻译 `model.yaml` 已引用的模型，校验后写出确定性的
`model-metadata.json` 快照。它不会修改 `model.yaml`，不会自动注册模型，也不会定时运行。

### 状态

本包属于 SpawnJoin monorepo，不发布到 PyPI。它是维护工具，不是 LangChain 适配包的
运行时依赖。长期边界见
[ADR-0009](../../../docs/decisions/llm-provider/0009-model-metadata-and-sync.md)。

### 使用者：安装与日常操作

```powershell
uv sync --locked --directory packages/infra/llm-model-sync
```

在 `model.yaml` 中显式声明共享模型和源坐标：

```yaml
schema_version: 2
default: fast
models:
  fast:
    protocol: chat_completions
    endpoint: https://api.openai.com/v1
    model: gpt-5
    api_key_env: OPENAI_API_KEY
    metadata_ref: openai/gpt-5
    metadata_source:
      models.dev:
        provider: openai
        model: gpt-5
```

在包含 `model.yaml` 的目录执行（把 `<repo>` 替换为仓库路径；`--project` 不会改变当前目录）：

```powershell
uv run --project <repo>/packages/infra/llm-model-sync spawn-join-model-sync sources
uv run --project <repo>/packages/infra/llm-model-sync spawn-join-model-sync sync --source models.dev --model-file model.yaml
uv run --project <repo>/packages/infra/llm-model-sync spawn-join-model-sync sync --source models.dev --model-file model.yaml --apply
uv run --project <repo>/packages/infra/llm-model-sync spawn-join-model-sync sync --source models.dev --model-file model.yaml --check
uv run --project <repo>/packages/infra/llm-model-sync spawn-join-model-sync sync --source models.dev --model-file model.yaml --output model-metadata.json
uv run --project <repo>/packages/infra/llm-model-sync spawn-join-model-sync sync --source models.dev --model-file model.yaml --cache-dir <path> --timeout 60
```

- 不带 `--apply` / `--check` 时只计算差异，不写快照；有差异时返回 `2`。
- `--apply` 原子替换快照；内容不变时不重写。
- `--check` 发现漂移返回 `2`，不写快照。
- `--apply` 和 `--check` 互斥。

退出码：

| 退出码 | 含义 |
|---|---|
| `0` | 成功；无漂移或应用成功 |
| `1` | 参数、配置或凭据 URL 非法 |
| `2` | 检测到漂移（dry-run 或 `--check`），或快照不存在 |
| `3` | 网络、上游结构、空/缩水响应、快照校验失败 |

运行时读取必须显式传快照路径；库不会搜索用户目录或发起网络请求：

```python
from spawn_join_llm_provider_langchain import ModelCatalog

catalog = ModelCatalog.from_file(
    "model.yaml",
    metadata_file="model-metadata.json",
)
for summary in catalog.models:
    print(summary.name, summary.metadata_ref, summary.metadata)
```

#### 失败保护与回滚

- 空响应、低于安全下限、全部被引用模型缺失、异常渠道缩水会阻断写入，旧快照保持不变。
- 单个模型或渠道缺失时保留旧条目并给出警告。
- 快照已替换后缓存/报告/状态写入失败，命令返回成功并显示 `post-commit` 警告。
- 回滚只需恢复上一份 `model-metadata.json`；不需要重新抓取上游。
- `model.yaml` 永远不会被同步命令修改。

#### 存储

- 快照默认位于 `model.yaml` 同目录，可用 `--output` 覆盖。
- 原始响应、状态和报告位于平台用户缓存目录，可用 `--cache-dir` 覆盖。
- 运行时库不读取这些目录；应用显式传入 `metadata_file`。

### 维护者：架构与扩展

#### 包边界

- `spawn-join-llm-provider`：框架无关的元数据类型、快照解析和共享严格字段读取。
- `spawn-join-llm-provider-langchain`：完整 `model.yaml` 解析和运行时目录读取；仅作为
  本包的测试/dev 依赖，不是 CLI 运行时依赖。
- `spawn-join-llm-model-sync`：网络抓取、源注册、原始 DTO、元数据投影、快照生成、缓存
  和 CLI。

运行时依赖方向为 `llm-provider` → `llm-model-sync`；完整模型文件解析器仍属于
`llm-provider-langchain`，但同步工具只读取元数据投影，不导入 LangChain。运行时包不得
反向依赖同步工具。

#### models.dev 数据流

```text
catalog.json
  -> ModelsDevCatalog / ModelsDevProvider / ModelsDevModel       原始 DTO
  -> 只解析请求的 refs / hosts
  -> ModelMetadata / ModelHostMetadata / ModelPricing 等统一类型
  -> 严格校验并写出 model-metadata.json
```

- 未知上游字段被忽略，避免新增字段破坏同步。
- 分层价格同时支持旧 `min_input_tokens` 和当前 `tier: {type: context, size: ...}` 形状。
- 官方 models.dev、镜像和同结构源可复用同一 adapter；不同结构必须新增独立 adapter。
- 源标识和 URL 通过 `SourceInfo`、`SourceConfig.url` / `SyncContext.url` 提供；adapter
  不保存第二份 URL，保证抓取地址与快照 provenance 一致。

#### 添加同步源

实现 `MetadataSource`，只负责 `fetch` 和 `translate`：

```python
from spawn_join_llm_model_sync import MetadataSource, SourceInfo, SourceRegistry

class MySource:
    info = SourceInfo(
        id="my-source",
        display_name="My Source",
        homepage="https://example.com",
        license="MIT",
        default_url="https://example.com/catalog.json",
    )

    def fetch(self, context):
        ...

    def translate(self, payload, request):
        ...

registry = SourceRegistry.with_builtins()
registry.register(MySource())
```

转换结果必须是统一类型，不是裸字典：

- `SourceCatalog.models: Mapping[str, ModelMetadata]`
- `SourceCatalog.hosts: Mapping[provider, Mapping[model, ModelHostMetadata]]`
- `SourceCatalog.unreferenced_models` 记录被忽略的上游模型标识。

新增源应提供 fixture-based 翻译测试、空/畸形载荷测试、失败隔离测试，并更新源描述和
文档；通用 runner、快照 schema 和运行时读取不应因为新增源而改变。

#### 质量与维护

```powershell
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-model-sync
pwsh -NoProfile -File scripts/quality.ps1
pwsh -NoProfile -File scripts/test-quality.ps1
```

- 每个 Distribution 使用独立 `.venv` 和 `uv.lock`；不要创建根级 uv 环境。
- 修改共享解析规则时优先复用 `spawn_join_llm_provider.parsing.FieldReader`，不要在多个
  adapter 中复制字段读取代码。
- 缓存和报告不提交；只提交经过审查的 `model-metadata.json`。
- ADR 状态由独立评审和 `speckit.decision.finalize` 收口，工具存在不等于评审完成。

许可证见 [LICENSE](LICENSE)。

## English

The manual model metadata synchronization tool for SpawnJoin.

It fetches a model catalog from an explicitly selected source, translates only the models referenced
by `model.yaml`, validates the result, and writes a deterministic `model-metadata.json` snapshot. It
never modifies `model.yaml`, never registers models automatically, and never runs on a schedule.

### Status

This package belongs to the SpawnJoin monorepo and is not published to PyPI. It is a maintenance
tool, not a runtime dependency of the LangChain adapter package. See
[ADR-0009](../../../docs/decisions/llm-provider/0009-model-metadata-and-sync.md) for the long-term
boundary.

### Users: installation and daily operations

```powershell
uv sync --locked --directory packages/infra/llm-model-sync
```

Declare shared models and source coordinates explicitly in `model.yaml`:

```yaml
schema_version: 2
default: fast
models:
  fast:
    protocol: chat_completions
    endpoint: https://api.openai.com/v1
    model: gpt-5
    api_key_env: OPENAI_API_KEY
    metadata_ref: openai/gpt-5
    metadata_source:
      models.dev:
        provider: openai
        model: gpt-5
```

Run from the directory containing `model.yaml` (replace `<repo>` with the repository path;
`--project` does not change the current directory):

```powershell
uv run --project <repo>/packages/infra/llm-model-sync spawn-join-model-sync sources
uv run --project <repo>/packages/infra/llm-model-sync spawn-join-model-sync sync --source models.dev --model-file model.yaml
uv run --project <repo>/packages/infra/llm-model-sync spawn-join-model-sync sync --source models.dev --model-file model.yaml --apply
uv run --project <repo>/packages/infra/llm-model-sync spawn-join-model-sync sync --source models.dev --model-file model.yaml --check
uv run --project <repo>/packages/infra/llm-model-sync spawn-join-model-sync sync --source models.dev --model-file model.yaml --output model-metadata.json
uv run --project <repo>/packages/infra/llm-model-sync spawn-join-model-sync sync --source models.dev --model-file model.yaml --cache-dir <path> --timeout 60
```

- Without `--apply` / `--check`, it only computes the difference and writes no snapshot; differences
  return `2`.
- `--apply` atomically replaces the snapshot; unchanged content is not rewritten.
- `--check` returns `2` on drift and writes no snapshot.
- `--apply` and `--check` are mutually exclusive.

Exit codes:

| Exit code | Meaning |
|---|---|
| `0` | success; no drift or applied successfully |
| `1` | invalid argument, configuration, or credential URL |
| `2` | drift detected (dry-run or `--check`), or snapshot missing |
| `3` | network, upstream structure, empty/shrunken response, or snapshot validation failure |

Runtime reads must pass the snapshot path explicitly; the library searches no user directory and
performs no network request:

```python
from spawn_join_llm_provider_langchain import ModelCatalog

catalog = ModelCatalog.from_file(
    "model.yaml",
    metadata_file="model-metadata.json",
)
for summary in catalog.models:
    print(summary.name, summary.metadata_ref, summary.metadata)
```

#### Failure protection and rollback

- Empty responses, values below safety floors, all referenced models missing, or abnormal channel
  shrinkage block the write and leave the old snapshot unchanged.
- A single missing model or channel preserves the old entry and emits a warning.
- If cache/report/state writing fails after the snapshot was replaced, the command returns success
  and displays a `post-commit` warning.
- Rollback only requires restoring the previous `model-metadata.json`; no upstream refetch is
  needed.
- `model.yaml` is never modified by the sync command.

#### Storage

- The snapshot defaults to the directory containing `model.yaml` and can be overridden with
  `--output`.
- Raw responses, state, and reports live in the platform user cache directory and can be overridden
  with `--cache-dir`.
- The runtime library reads none of these directories; applications pass `metadata_file`
  explicitly.

### Maintainers: architecture and extension

#### Package boundaries

- `spawn-join-llm-provider`: framework-independent metadata types, snapshot parsing, and shared
  strict field reading.
- `spawn-join-llm-provider-langchain`: full `model.yaml` parsing and runtime catalog reading; a
  test/dev dependency only, not a CLI runtime dependency.
- `spawn-join-llm-model-sync`: network fetching, source registration, raw DTOs, metadata projection,
  snapshot generation, cache, and CLI.

Runtime dependency direction is `llm-provider` → `llm-model-sync`; the full model-file parser still
belongs to `llm-provider-langchain`, but the sync tool reads only the metadata projection and imports
no LangChain. Runtime packages must not depend on the sync tool.

#### models.dev data flow

```text
catalog.json
  -> ModelsDevCatalog / ModelsDevProvider / ModelsDevModel       raw DTOs
  -> parse only requested refs / hosts
  -> ModelMetadata / ModelHostMetadata / ModelPricing unified types
  -> strict validation and write model-metadata.json
```

- Unknown upstream fields are ignored so new fields do not break synchronization.
- Tiered pricing supports both legacy `min_input_tokens` and the current
  `tier: {type: context, size: ...}` shape.
- Official models.dev, mirrors, and structurally identical sources can reuse the same adapter;
  different structures require a separate adapter.
- Source identity and URL are provided through `SourceInfo`, `SourceConfig.url` /
  `SyncContext.url`; the adapter stores no second URL, keeping the fetch address and snapshot
  provenance consistent.

#### Adding a sync source

Implement `MetadataSource`, responsible only for `fetch` and `translate`:

```python
from spawn_join_llm_model_sync import MetadataSource, SourceInfo, SourceRegistry

class MySource:
    info = SourceInfo(
        id="my-source",
        display_name="My Source",
        homepage="https://example.com",
        license="MIT",
        default_url="https://example.com/catalog.json",
    )

    def fetch(self, context):
        ...

    def translate(self, payload, request):
        ...

registry = SourceRegistry.with_builtins()
registry.register(MySource())
```

Translation results must be unified types, not raw dictionaries:

- `SourceCatalog.models: Mapping[str, ModelMetadata]`
- `SourceCatalog.hosts: Mapping[provider, Mapping[model, ModelHostMetadata]]`
- `SourceCatalog.unreferenced_models` records ignored upstream model identifiers.

A new source should provide fixture-based translation tests, empty/malformed payload tests, and
failure-isolation tests, and update source descriptions and documentation; the generic runner,
snapshot schema, and runtime reading should not change for a new source.

#### Quality and maintenance

```powershell
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-model-sync
pwsh -NoProfile -File scripts/quality.ps1
pwsh -NoProfile -File scripts/test-quality.ps1
```

- Each Distribution uses an independent `.venv` and `uv.lock`; never create a root uv environment.
- When changing shared parsing rules, reuse `spawn_join_llm_provider.parsing.FieldReader` rather than
  duplicating field-reading code across adapters.
- Cache and reports are not committed; only a reviewed `model-metadata.json` is committed.
- ADR status is closed by independent review and `speckit.decision.finalize`; tool presence does not
  prove review completion.

See [LICENSE](LICENSE).
