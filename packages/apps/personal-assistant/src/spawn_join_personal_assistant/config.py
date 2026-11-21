"""个人助理宿主的应用配置。

``AppConfig`` 是宿主侧配置的公共边界对象：它在校验阶段就急切校验
路径与调度约束，让后续阶段只接收已收窄的类型化输入。凭据从不属于
配置：模型认证保留在环境中，由 ``spawn-join-llm-provider-langchain``
解析（ADR-0008 环境边界）。

校验辅助函数有意接收 ``object``：它们在边界处收窄无类型的动态输入
（Constitution IV），同时避免类型检查器对静态可证明的 isinstance
调用报错。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .errors import HostConfigError

_MIN_CONCURRENCY = 1


def _require_path(label: str, value: object) -> None:
    """拒绝非 Path 输入，抛出稳定、可断言的错误。"""

    if not isinstance(value, Path):
        raise HostConfigError(f"{label}: must be a pathlib.Path")


def _require_positive_int(label: str, value: object) -> None:
    """拒绝非 int、bool 或低于下限的并发输入。"""

    if not isinstance(value, int) or isinstance(value, bool):
        raise HostConfigError(f"{label}: must be an int")
    if value < _MIN_CONCURRENCY:
        raise HostConfigError(f"{label}: must be at least {_MIN_CONCURRENCY}")


def _require_positive_number_or_none(label: str, value: object) -> None:
    """拒绝非数值（或非正数）的 deadline 输入；None 表示禁用。"""

    if value is None:
        return
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise HostConfigError(f"{label}: must be a number or None")
    if value <= 0:
        raise HostConfigError(f"{label}: must be greater than 0")


@dataclass(frozen=True, slots=True)
class AppConfig:
    """已校验的宿主应用配置。

    字段:
        data_dir: 宿主自有持久化（SQLite 数据库）所在目录。
        workspace_root: 唯一允许 agent 文件副作用的目录树。
        model_catalog_path: 经 ``ModelCatalog`` 消费的模型目录文件路径；
            凭据来自环境。
        max_concurrency: 同时处于 running 的工作项上限。
        work_deadline_seconds: 单个工作项一次运行的可选总 deadline；
            ``None`` 表示禁用 deadline。
    """

    data_dir: Path
    workspace_root: Path
    model_catalog_path: Path
    max_concurrency: int = 2
    work_deadline_seconds: float | None = None

    def __post_init__(self) -> None:
        for label, value in (
            ("data_dir", self.data_dir),
            ("workspace_root", self.workspace_root),
            ("model_catalog_path", self.model_catalog_path),
        ):
            _require_path(label, value)
        if not self.model_catalog_path.is_file():
            raise HostConfigError(
                f"model_catalog_path: file does not exist: "
                f"{self.model_catalog_path}"
            )
        _require_positive_int("max_concurrency", self.max_concurrency)
        _require_positive_number_or_none(
            "work_deadline_seconds", self.work_deadline_seconds
        )
