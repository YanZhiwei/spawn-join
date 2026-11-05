# spawn-join-core

[简体中文](#中文) | [English](#english)

## 中文

SpawnJoin 生态共享的稳定契约与基础原语。

### 当前状态

`0.1.0` 骨架，要求 Python `>=3.11`。`config`、`exceptions`、`protocols` 和 `types`
目前只有模块契约，尚无实现或公开导出；包根只提供 `__version__`。`0.x` 期间接口仍可能
按文档化变更调整。

### 使用与验证

本包属于 SpawnJoin monorepo，尚未发布到 PyPI。使用该 Distribution 自己的环境：

```powershell
uv sync --locked --directory packages/core/spawn-join-core
```

当前可用的最短导入：

```python
import spawn_join_core

print(spawn_join_core.__version__)
```

不存在可调用的公共 API、CLI 或配置项；阅读本 README 后不应推断出尚未实现的运行时能力。

### 边界

- 不依赖其他 SpawnJoin 包。
- 不引入第三方运行时依赖。
- 不存放单领域辅助函数、Provider 适配或副作用。
- 只有出现至少两个组件的稳定复用时，才向 Core 添加能力。

### 目录、开发与质量

- `src/spawn_join_core/`：运行时源码；当前模块只有契约说明。
- `tests/`：导入、身份和零运行时依赖边界测试。
- 独立 `pyproject.toml`、`uv.lock` 与 `.venv/`；不要创建根级 uv workspace。

```powershell
uv lock --check --directory packages/core/spawn-join-core
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-core
```

质量命令执行 Black、isort、Ruff、Pyright strict、pytest、wheel/sdist、隔离安装、
`pip check` 和隔离导入检查。

### 维护、版本与许可证

公共能力必须先通过 Feature 交付路由说明复用理由、依赖方向和验证方式；新增或删除模块时
同步测试、包边界和仓库文档。本包使用独立版本号，尚未发布；发布需要单独授权。许可证见
[LICENSE](LICENSE)。

## English

Stable contracts and foundational primitives shared across the SpawnJoin ecosystem.

### Status and compatibility

`0.1.0` scaffold, requiring Python `>=3.11`. `config`, `exceptions`, `protocols`, and
`types` currently contain module contracts only, with no implementation or public
exports; the package root exposes only `__version__`. Interfaces may still change in
documented ways during `0.x`.

### Installation and shortest use

This package belongs to the SpawnJoin monorepo and is not published to PyPI. Use the
Distribution's own environment:

```powershell
uv sync --locked --directory packages/core/spawn-join-core
```

The shortest currently valid import:

```python
import spawn_join_core

print(spawn_join_core.__version__)
```

There is no callable public API, CLI, or configuration surface; do not infer runtime
capabilities that are not implemented.

### Boundaries and non-goals

- Must not depend on another SpawnJoin package.
- Must not introduce third-party runtime dependencies.
- Must not host single-domain helpers, Provider adapters, or side effects.
- Add capabilities to Core only after at least two components have a stable reuse need.

### Layout, development, and quality

- `src/spawn_join_core/`: runtime source; currently contract documentation only.
- `tests/`: import, identity, and zero-runtime-dependency boundary tests.
- Independent `pyproject.toml`, `uv.lock`, and `.venv/`; never create a root uv workspace.

```powershell
uv lock --check --directory packages/core/spawn-join-core
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-core
```

The quality command runs Black, isort, Ruff, Pyright strict, pytest, wheel/sdist, isolated
installation, `pip check`, and an isolated import check.

### Maintenance, versioning, and license

Public capabilities must first pass the Feature delivery route with a documented reuse
rationale, dependency direction, and verification method; synchronize tests, package
boundaries, and repository docs when adding or removing modules. This package uses an
independent version and is not published; publication requires separate authorization.
See [LICENSE](LICENSE).
