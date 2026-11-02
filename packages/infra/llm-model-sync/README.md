# spawn-join-llm-model-sync

SpawnJoin 的手动模型元数据同步工具。

它从显式选择的数据源抓取模型目录，只翻译 `model.yaml` 已引用的模型，校验后写出确定性的
`model-metadata.json` 快照。它不会修改 `model.yaml`，不会自动注册模型，也不会定时运行。

## 状态

本包属于 SpawnJoin monorepo，不发布到 PyPI。它是维护工具，不是 LangChain 适配包的
运行时依赖。长期边界见
[ADR-0009](../../../docs/decisions/llm-provider/0009-model-metadata-and-sync.md)。

## 使用者：安装与日常操作

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

在包目录执行（或激活该包 `.venv` 后直接使用 `model-sync`）：

```powershell
uv run --locked model-sync sources
uv run --locked model-sync sync --source models.dev
uv run --locked model-sync sync --source models.dev --apply
uv run --locked model-sync sync --source models.dev --check
uv run --locked model-sync sync --source models.dev --model-file model.yaml --output model-metadata.json
uv run --locked model-sync sync --source models.dev --cache-dir <path> --timeout 60
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

### 失败保护与回滚

- 空响应、低于安全下限、全部被引用模型缺失、异常渠道缩水会阻断写入，旧快照保持不变。
- 单个模型或渠道缺失时保留旧条目并给出警告。
- 快照已替换后缓存/报告/状态写入失败，命令返回成功并显示 `post-commit` 警告。
- 回滚只需恢复上一份 `model-metadata.json`；不需要重新抓取上游。
- `model.yaml` 永远不会被同步命令修改。

### 存储

- 快照默认位于 `model.yaml` 同目录，可用 `--output` 覆盖。
- 原始响应、状态和报告位于平台用户缓存目录，可用 `--cache-dir` 覆盖。
- 运行时库不读取这些目录；应用显式传入 `metadata_file`。

## 维护者：架构与扩展

### 包边界

- `spawn-join-llm-provider`：框架无关的元数据类型、快照解析和共享严格字段读取。
- `spawn-join-llm-provider-langchain`：`model.yaml` 解析和运行时目录读取。
- `spawn-join-llm-model-sync`：网络抓取、源注册、原始 DTO、快照生成、缓存和 CLI。

依赖方向为 `llm-provider` → `llm-provider-langchain` → `llm-model-sync`，运行时包不得反向
依赖同步工具。

### models.dev 数据流

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

### 添加同步源

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

### 质量与维护

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
