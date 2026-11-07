# spawn-join-common

[简体中文](README.md) | [English](README.en.md)

SpawnJoin 中与领域无关、可独立安装的公共辅助能力包。当前提供严格的标准库字段读取器，以及可选安装的 Pydantic 校验异常转换函数。

## 目录

- [状态与边界](#状态与边界)
- [安装](#安装)
- [快速开始](#快速开始)
- [公共 API](#公共-api)
- [开发与验证](#开发与验证)
- [维护与许可证](#维护与许可证)

## 状态与边界

版本为 `0.1.0`，要求 Python `>=3.11`。基础安装没有运行时依赖，不依赖任何 SpawnJoin 领域包、模型框架或 Provider SDK。

首批能力只有两个明确的公共入口：

- `spawn_join_common.FieldReader`：只使用 Python 标准库，严格读取不可信的标量、列表和映射；错误工厂由调用方提供，默认是 `ValueError`。
- `spawn_join_common.validation.validate_with`：通过可选的 `validation` extra 安全地把 Pydantic `ValidationError` 转换为调用方错误；消息和异常类型都由调用方提供。

时间转换、序列化、网络、文件、缓存、重试和并发能力不属于当前版本，也没有为未来方向创建空 API。新的公共能力应先有至少两个组件的稳定复用需求，再按职责加入对应模块。

## 安装

本包属于 SpawnJoin monorepo，尚未发布到 PyPI。每个 Distribution 都是独立 uv project。

只使用标准库读取器，并且不安装开发组或 Pydantic：

```powershell
uv sync --locked --no-dev --directory packages/core/common
```

需要 Pydantic 转换能力时安装可选依赖（同样不安装开发组）：

```powershell
uv sync --locked --no-dev --extra validation --directory packages/core/common
```

开发和测试环境可以安装包含 Pydantic 测试依赖的 dev group：

```powershell
uv sync --locked --directory packages/core/common
```

基础安装可以在没有 Pydantic 的环境中导入：

```powershell
uv run --locked --no-dev --directory packages/core/common python -c "from spawn_join_common import FieldReader; print(FieldReader().as_int(3, 'count'))"
```

## 快速开始

### 严格读取外部字段

`FieldReader` 不把数字字符串当作数字，也不把布尔值当作整数。`as_number` 接受整数或浮点数并返回 `float`；有限且非负的约束由独立方法检查。映射会复制为新的 `dict`，并保留源迭代顺序。`optional` 只跳过缺失字段，显式 `None` 仍交给调用方 parser，因此每个消费者可以保留自己的 null 策略。

```python
from spawn_join_common import FieldReader

reader = FieldReader()
fields = reader.as_mapping({"name": "demo", "limit": 3}, "config")
reader.require_keys(
    fields,
    required=frozenset({"name"}),
    optional=frozenset({"limit"}),
    path="config",
)

name = reader.as_str(fields["name"], "config.name")
limit = reader.optional(fields, "limit", reader.as_non_negative_int, "config")
print(name, limit)
```

非法值会抛出带路径的 `ValueError`；调用方可以注入自己的 `Callable[[str], Exception]` 错误工厂。

### 转换 Pydantic 校验错误

`validate_with` 只捕获 Pydantic `ValidationError`。调用方负责提供安全消息和错误类型，原始校验异常会保留为 `__cause__`；其他异常原样传播。

```python
from pydantic import TypeAdapter, ValidationError

from spawn_join_common.validation import validate_with

adapter = TypeAdapter(int)

try:
    value = validate_with(
        lambda: adapter.validate_python("not-an-integer"),
        error=ValueError,
        message=lambda exc: "config.limit: invalid integer",
    )
except ValueError as exc:
    assert isinstance(exc.__cause__, ValidationError)
    print(exc)
```

不要在公共函数中直接渲染校验输入；消息格式化策略属于调用方。

## 公共 API

### `spawn_join_common`

- `FieldReader`
- `__version__`（当前为 `"0.1.0"`）

`FieldReader` 提供 `fail`、`as_mapping`、`require_keys`、`as_str`、`as_int`、`as_non_negative_int`、`as_number`、`as_non_negative_number`、`as_bool`、`as_list` 和 `optional`。它是 frozen/slotted dataclass，没有 I/O、日志、全局注册或对输入映射的原地修改。

### `spawn_join_common.validation`

- `validate_with(operation, *, error, message)`

该子包是唯一的可选 Pydantic 入口；导入 `spawn_join_common` 本身不会加载 Pydantic。

## 开发与验证

在仓库根目录执行以下独立包检查：

```powershell
uv lock --check --directory packages/core/common
uv sync --locked --directory packages/core/common
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-common
```

统一入口显式使用仓库工具配置，执行 Black/isort、Ruff、Pyright strict、pytest、构建及基础/可选依赖两种隔离安装验证。

包使用 `src/` layout，源码位于 `src/spawn_join_common/`，测试位于 `tests/`。默认运行时依赖保持为空；Pydantic 只在 `validation` extra 和开发测试环境中声明。

## 维护与许可证

公共能力必须保持领域无关、依赖方向单向，并在新增 API 时同步测试、双语文档和独立安装验证。当前包版本独立管理，发布需要单独授权。

本包为专有软件，使用和分发须遵守仓库授权条款，详见 [LICENSE](LICENSE)。
