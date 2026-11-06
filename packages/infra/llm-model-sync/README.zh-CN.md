# spawn-join-llm-model-sync

[English](README.md) | [简体中文](README.zh-CN.md)

SpawnJoin 的手动模型元数据同步工具。

它从显式选择的数据源抓取模型目录，只翻译 `model.yaml` 已引用的模型，校验后写出确定性的
`model-metadata.json` 快照。它不会修改 `model.yaml`，不会自动注册模型，也不会定时运行。

**目录**

- [状态](#状态)
- [安装与日常操作](#使用者安装与日常操作)
  - [失败保护与回滚](#失败保护与回滚)
  - [存储](#存储)
- [架构与扩展](#维护者架构与扩展)
  - [包边界](#包边界)
  - [models.dev 数据流](#modelsdev-数据流)
  - [添加同步源](#添加同步源)
  - [质量与维护](#质量与维护)
- [维护与发布](#维护与发布)

## 状态

版本 `0.1.0`，早期开发，要求 Python `>=3.11`。运行时依赖为
`spawn-join-llm-provider`、`platformdirs` 和 `PyYAML`。

本包属于 SpawnJoin monorepo，不发布到 PyPI。它是维护工具，不是 LangChain 适配包的
运行时依赖。长期边界见
[ADR-0009](../../../docs/decisions/llm-provider/0009-model-metadata-and-sync.md)。

## 使用者：安装与日常操作

```powershell
uv sync --locked --directory packages/infra/llm-model-sync
```

先从仓库根目录验证 CLI（不联网）：

```powershell
uv run --locked --directory packages/infra/llm-model-sync spawn-join-model-sync --help
uv run --locked --directory packages/infra/llm-model-sync spawn-join-model-sync sources
```

两条命令成功退出（`0`）；`sources` 包含内置的 `models.dev`。以下 `sync` 命令才会访问
所选元数据源；内置公开源不需要 `OPENAI_API_KEY`，模型文件中的变量名供推理应用使用。

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

完成 `--apply` 后，将下面代码保存为 `model.yaml` 同目录的 `read_snapshot.py`，在该目录
运行 `uv run --locked --project <repo>/packages/infra/llm-model-sync python read_snapshot.py`。
它使用同步包已有的协议依赖读取快照，无需额外安装 LangChain、配置推理密钥或联网。
预期打印快照中的模型键、显示名与上下文长度（未知长度为 `None`）：

```python
from pathlib import Path

from spawn_join_llm_provider import decode_metadata_document

document = decode_metadata_document(
    Path("model-metadata.json").read_text(encoding="utf-8")
)
for key, metadata in document.models.items():
    print(key, metadata.name, metadata.limits.context)
```

需要与模型调用配置合并时，在[LangChain 适配包环境](../llm-provider-langchain/README.zh-CN.md#模型元数据快照)
使用 `ModelCatalog.from_file(..., metadata_file=...)`；该环境及其凭据配置由应用负责。

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
- `spawn-join-llm-provider-langchain`：完整 `model.yaml` 解析和运行时目录读取；仅作为
  本包的测试/dev 依赖，不是 CLI 运行时依赖。
- `spawn-join-llm-model-sync`：网络抓取、源注册、原始 DTO、元数据投影、快照生成、缓存
  和 CLI。

同步工具依赖 `llm-provider`；完整模型文件解析器仍属于
`llm-provider-langchain`，但同步工具只读取元数据投影，不导入 LangChain。运行时包不得
反向依赖同步工具。

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

实现 `MetadataSource`，只负责 `fetch` 和 `translate`。下面是完整的离线源示例，保存为
仓库根目录的 `source_demo.py`，执行
`uv run --locked --project packages/infra/llm-model-sync python source_demo.py`。
它使用固定字节演示源注册、获取与类型化投影，不联网、不写快照，临时目录自动清理；
真实源应获取并解析自己的载荷，不能直接使用此固定响应。

```python
from pathlib import Path
from tempfile import TemporaryDirectory

from spawn_join_llm_model_sync import (
    SourceCatalog,
    SourceInfo,
    SourceRegistry,
    SourceRequest,
    SyncContext,
    SyncError,
)
from spawn_join_llm_provider import Modality, ModelMetadata, ModelModalities, ModelType


class DemoSource:
    info = SourceInfo(
        id="demo",
        display_name="Offline Demo",
        homepage="https://example.com",
        license="Example data only",
        default_url="https://example.com/catalog.json",
    )

    def fetch(self, context: SyncContext) -> bytes:
        return b"demo/chat"

    def translate(self, payload: bytes, request: SourceRequest) -> SourceCatalog:
        if payload != b"demo/chat" or request.hosts:
            raise SyncError("DemoSource supports only its fixed model payload")
        model = ModelMetadata(
            key="demo/chat",
            name="Demo Chat",
            type=ModelType.CHAT,
            modalities=ModelModalities(input=(Modality.TEXT,), output=(Modality.TEXT,)),
        )
        selected = model.key in request.refs
        return SourceCatalog(
            models={model.key: model} if selected else {},
            hosts={},
            total_models=1,
            total_providers=1,
            unreferenced_models=() if selected else (model.key,),
        )


def main() -> None:
    registry = SourceRegistry.with_builtins()
    registry.register(DemoSource())
    source = registry.get("demo")
    with TemporaryDirectory() as directory:
        payload = source.fetch(SyncContext(cache_dir=Path(directory)))
        catalog = source.translate(payload, SourceRequest(refs=("demo/chat",)))
    print("source registered:", source.info.id)
    for key, model in catalog.models.items():
        print(key, model.name)


if __name__ == "__main__":
    main()
```

预期输出：

```text
source registered: demo
demo/chat Demo Chat
```

注册只影响当前 `SourceRegistry` 实例，不会让另一个 CLI 进程自动发现该源。
需要写入快照时，由宿主把这个 registry 传给其 `sync()` 方法，并提供显式的模型文件、
输出路径、`SourceConfig` 与 `SyncContext`。

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

许可证见 [LICENSE](LICENSE)。

## 维护与发布

源码位于 `src/spawn_join_llm_model_sync/`，适配器位于其 `sources/` 目录，离线测试位于
`tests/`。CLI 名为 `spawn-join-model-sync`，使用 `--help` 或 `sources` 查看命令和注册源。
公共 Python API 见 [`__init__.py`](src/spawn_join_llm_model_sync/__init__.py)。

本包由 SpawnJoin 仓库维护者拥有，作者为 Yan Zhiwei。遵循[贡献规则](../../../AGENTS.md)
和[质量前置条件](../../../docs/development/quality-gates.md#prerequisites)
（PowerShell 7、uv 0.7.13+、Git、Node.js 22+）。报告问题时提供源标识、退出码和脱敏模型文件
示例。本包独立版本化，当前未配置自动发布或包级 changelog；发布需有质量检查、两种语言
README、兼容性说明和单独授权。
