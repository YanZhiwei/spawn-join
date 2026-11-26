# spawn-join-core

[简体中文](README.md) | [English](README.en.md)

SpawnJoin 生态共享的稳定契约与基础原语。

**目录**

- [当前状态](#当前状态)
- [使用与验证](#使用与验证)
- [错误与限制](#错误与限制)
- [边界](#边界)
- [目录、开发与质量](#目录开发与质量)
- [维护与发布](#维护与发布)
- [许可证](#许可证)

## 当前状态

`0.0.1.dev0` 骨架，要求 Python `>=3.11`。`config`、`exceptions`、`protocols` 和 `types`
目前只有模块契约，尚无实现或公开导出；包根只提供 `__version__`。`0.x` 期间接口仍可能
按文档化变更调整。

## 使用与验证

本包属于 SpawnJoin monorepo，尚未发布到 PyPI。使用该 Distribution 自己的环境：

```powershell
uv sync --locked --directory packages/core/spawn-join-core
```

当前可用的最短导入：

```python
import spawn_join_core

print(spawn_join_core.__version__)
```

也可以不创建脚本，直接从仓库根目录运行：

```powershell
uv run --locked --directory packages/core/spawn-join-core python -c "import spawn_join_core; print(spawn_join_core.__version__)"
```

预期输出为 `0.0.1.dev0`，无需密钥或网络请求。

不存在可调用的公共 API、CLI 或配置项；阅读本 README 后不应推断出尚未实现的运行时能力。

## 错误与限制

- 包根当前只导出 `__version__`；导入不会发起 I/O、网络请求或读取环境变量。
- 没有可调用的公共 API，因此本包当前不定义运行时异常类型，也不承诺业务错误语义。
- `config`、`exceptions`、`protocols` 和 `types` 只有模块契约；直接导入其内部模块不是公开契约。
- `0.x` 期间接口可能按文档化变更调整；不要基于本 README 推断尚未实现的配置或错误处理能力。

## 边界

- 不依赖其他 SpawnJoin 包。
- 不引入第三方运行时依赖。
- 不存放单领域辅助函数、Provider 适配或副作用。
- 只有出现至少两个组件的稳定复用时，才向 Core 添加能力。

## 目录、开发与质量

- `src/spawn_join_core/`：运行时源码；当前模块只有契约说明。
- `tests/`：导入、身份和零运行时依赖边界测试。
- 独立 `pyproject.toml`、`uv.lock` 与 `.venv/`；不要创建根级 uv workspace。

```powershell
uv lock --check --directory packages/core/spawn-join-core
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-core
```

质量命令执行 Black、isort、Ruff、Pyright strict、pytest、wheel/sdist、隔离安装、
`pip check` 和隔离导入检查。

## 维护与发布

本包由 SpawnJoin 仓库维护者拥有，作者为 Yan Zhiwei。公共能力必须先通过 Feature 交付路由
说明复用理由、依赖方向和验证方式；新增或删除模块时同步测试、包边界和仓库文档。变更遵循
[贡献规则](../../../AGENTS.md) 和
[质量前置条件](../../../docs/development/quality-gates.md#prerequisites)。本包使用独立版本号，
当前 `0.0.1.dev0` 尚未发布；发布需要单独授权，当前没有自动发布或包级 changelog。

## 许可证

本包为专有软件，使用和分发须遵守仓库授权条款，详见 [LICENSE](LICENSE)。
