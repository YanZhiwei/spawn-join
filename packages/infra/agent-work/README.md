# spawn-join-agent-work

[简体中文](README.md) | [English](README.en.md)

供 SpawnJoin 宿主复用的长任务契约与桌面适配器。
当前能力：模型、策略与适配器端口。提供 SQLite 持久化、原子 claim 与租约 fencing。内存存储作为同一契约的第二实现。

## 状态、适用范围与兼容性

版本 0.1.0，preview，Python >=3.11；尚未发布到 PyPI，使用仓库本地安装。
适合需要组合下列契约和已实现适配器的宿主，桌面默认不要求外部服务。

- 当前提供存储，执行与调度由宿主自行实现。
- 本层不切换宿主 CLI，不提供 Postgres/MQ、多机调度或租户/认证系统。

## 安装与最短示例

从仓库根目录执行：

```powershell
uv lock --check --directory packages/infra/agent-work
uv sync --locked --directory packages/infra/agent-work
```

```python
import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

from spawn_join_agent_work import SqliteWorkStore, WorkSpec


async def main() -> None:
    with TemporaryDirectory() as directory:
        store = SqliteWorkStore(Path(directory) / "work.db")
        item = await store.enqueue(
            WorkSpec(kind="report", payload=b"hello", idempotency_key="demo")
        )
        assert item.spec.kind == "report"


asyncio.run(main())
```

Distribution 声明 pyzmq>=27.3.0,<28；SQLite 使用标准库。
不引入 LangChain、模型适配器或其他 SpawnJoin 包的运行时依赖。

## 公开 API 与默认值

本版本仅导出下表名称：

| 类别 | 导出 |
| --- | --- |
| models | `WorkSpec`, `WorkItem`, `WorkState`, `WorkOutcome`, `WorkLease`, `WorkResult`, `WorkEvent` |
| policies | `RetryPolicy`, `LeasePolicy`, `ConcurrencyPolicy` |
| ports | `Clock`, `Notifier`, `WorkExecutor`, `WorkStore` |
| storage | `SqliteWorkStore`, `InMemoryWorkStore` |
| errors | `WorkError`, `WorkConfigurationError`, `WorkConflictError`, `WorkNotFoundError`, `LeaseLostError`, `StoreError`, `NotifierError` |

WorkSpec 接收 kind、bytes payload 和 idempotency_key。WorkState 表达
queued/running/waiting/completed/failed/dead/cancelled，端口定义适配器边界。

| WorkSpec 字段 | 类型 | 默认值 |
| --- | --- | --- |
| `kind` | `str` | `required` |
| `payload` | `bytes` | `required` |
| `idempotency_key` | `str` | `required` |
| `queue` | `str` | `'default'` |
| `namespace` | `str` | `'default'` |
| `priority` | `int` | `0` |
| `available_at` | `datetime \| None` | `None` |
| `deadline_seconds` | `float \| None` | `None` |
| `max_attempts` | `int` | `3` |

WorkItem 保存 spec、state、attempts、lease、last_error 与 result；
WorkLease 保存 owner/token/until；WorkResult 通过 outcome 与可选 summary/error/wait_until
表达执行结果。WorkEvent 为事件元数据，不包含业务 payload。
WorkStore 定义 enqueue/claim/heartbeat/complete/fail/defer/resume/cancel/get/prune；
Notifier 定义 publish/subscribe/aclose，Clock 提供 now()，WorkExecutor 为异步执行器。

RetryPolicy 默认 max_attempts=3、base_seconds=1、multiplier=2、jitter=0；
LeasePolicy 默认 seconds=60、heartbeat_seconds=20；ConcurrencyPolicy 默认
max_concurrency=2、claim_batch=1、poll_interval_seconds=1。

SQLite 默认 WAL、busy_timeout=5000ms、schema_version=1。Store 是真相；heartbeat/complete/fail/defer 校验租约 token，waiting 需由宿主 resume 后才可领取；控制面 resume/cancel 不需要 token。不提供旧 work.db 迁移。

## 错误与限制

WorkConfigurationError 拒绝非法契约输入；WorkConflictError、WorkNotFoundError、
LeaseLostError 分别表达冲突、未找到和租约丢失，StoreError/NotifierError 区分适配器失败；
它们均继承 WorkError。公共端口不暴露 SQL、连接或文件路径。
SQLite 属于桌面适配器，不适用于服务端档位或多机部署。

## 架构、所有权与相邻包

宿主依赖 agent-work，本包拥有模型、策略、端口与当前已实现的适配器，
业务执行和进程装配由宿主拥有；Store 为真相，通知只提供 best-effort 唤醒。
边界见 [ADR-0018](../../../docs/decisions/engineering/0018-agent-work-package-boundary.md)。
[agent-deepagents](../agent-deepagents/README.md) 拥有 Agent 装配，
[personal-assistant](../../apps/personal-assistant/README.md) 拥有 CLI 与审批。

## 开发与验证

源码位于 src/spawn_join_agent_work/（models.py / policies.py / protocols.py / errors.py / stores/），测试位于 tests/。
每包拥有独立 uv.lock 与 .venv，仓库根目录仅有工具配置。
配置质量门需要 Python >=3.11、uv、PowerShell 7 和 Node 22+。

```powershell
uv run --locked --directory packages/infra/agent-work pytest -q
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-agent-work
```

## 版本、维护与许可证

本包由 SpawnJoin 维护者负责，贡献遵循 [AGENTS.md](../../../AGENTS.md)。
0.x 公共契约仍为 preview；发布前需要包级门禁及单独发布授权，0.1.0 仅为源码版本。
尚未发布，因此无已发布 changelog/tag；版本历史归仓库发布记录所有。
许可证为 LicenseRef-Proprietary，见 [LICENSE](LICENSE)。
