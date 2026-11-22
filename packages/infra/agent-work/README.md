# spawn-join-agent-work

[简体中文](README.md) | [English](README.en.md)

可复用的桌面长任务运行时：SQLite 持久化、租约/fencing、重试/退避、ZeroMQ 唤醒与常驻 runner。
桌面默认不要求任何外部服务；存储与通知通过端口替换，为后续 Postgres/MQ 服务端档位保留接缝。

> 状态：Phase 1，版本 `0.1.0`，要求 Python `>=3.11`；尚未发布到 PyPI。包边界决策见
> [ADR-0018](../../../docs/decisions/engineering/0018-agent-work-package-boundary.md)。

## 适用与不适用

适用：

- 桌面应用需要“提交后可恢复、崩溃后不丢”的后台任务；
- 宿主希望自己装配 SQLite + 本地唤醒，而不是引入 Temporal/Celery；
- 需要可替换的存储/通知接口，为服务端档位预留路径。

不适用：

- 需要 exactly-once 副作用（本包只承诺 at-least-once）；
- 多机分布式调度、多租户/认证/配额/计费；
- 需要内置 Web UI、MCP Server 或远程沙箱。

## 安装

尚未发布。仓库内开发：

```powershell
uv lock --check --directory packages/infra/agent-work
uv sync --locked --directory packages/infra/agent-work
```

宿主可通过本地路径依赖开发：

```toml
dependencies = ["spawn-join-agent-work>=0.1.0,<0.2.0"]
[tool.uv.sources]
spawn-join-agent-work = { path = "../../infra/agent-work", editable = true }
```

运行时依赖只有 `pyzmq>=27.3.0,<28`（BSD-3-Clause；随包 libzmq 为 MPL-2.0）。SQLite 使用 stdlib。

## 最短示例

```python
import asyncio
from pathlib import Path

from spawn_join_agent_work import (
    SqliteWorkStore, WorkOutcome, WorkResult, WorkRunner, WorkSpec,
)


async def main() -> None:
    store = SqliteWorkStore(Path("work.db"))
    await store.enqueue(
        WorkSpec(kind="report", payload=b"hello", idempotency_key="demo-1")
    )

    async def executor(item):
        return WorkResult(outcome=WorkOutcome.SUCCESS, summary="done")

    runner = WorkRunner(store, executor, owner="desktop-1")
    processed = await runner.run_once()
    print(processed)  # 1


asyncio.run(main())
```

常驻模式：

```python
runner = WorkRunner(store, executor, owner="desktop-1")
stop = asyncio.Event()
task = asyncio.create_task(runner.serve(stop))
# ...
await runner.astop()   # 停止领取、释放在飞租约、关闭 notifier，≤10s
```

`WorkRunner.serve()` 是单次生命周期：`astop()` 后该 runner 不再启动新循环；再次常驻请新建 runner。

## 公开 API

| 类别 | 名称 | 说明 |
|---|---|---|
| 模型 | `WorkSpec` | 入队定义：`kind`、`payload: bytes`、`idempotency_key`、queue/namespace/priority、available_at、deadline、max_attempts |
| 模型 | `WorkItem` | 持久化任务：状态、attempts、lease、last_error、result、时间戳 |
| 模型 | `WorkState` / `WorkOutcome` | `queued/running/waiting/completed/failed/dead/cancelled`；执行结果 `success/retry/fail/defer` |
| 模型 | `WorkLease` / `WorkResult` / `WorkEvent` | 所有权窗口 / 执行结果 / 唤醒事件（事件不携带业务 payload） |
| 策略 | `RetryPolicy` / `LeasePolicy` / `ConcurrencyPolicy` | 指数退避、租约与心跳、并发/claim 批量/poll |
| 端口 | `WorkStore` / `Notifier` / `Clock` / `WorkExecutor` | 存储、唤醒、时钟、执行器 |
| 适配器 | `SqliteWorkStore` / `InMemoryWorkStore` / `ZmqNotifier` | 桌面默认、契约测试第二实现、PUB/SUB 唤醒 |
| 运行时 | `WorkRunner` | `run_once()` 单批；`serve()/astop()` 常驻与优雅关闭 |
| 错误 | `WorkError` 及子类 | 配置、未找到、冲突、租约丢失、存储、通知 |

`WorkStore` 方法：`enqueue`、`claim`、`heartbeat`、`complete`、`fail`、`defer`、`resume`、
`cancel`、`get`、`prune`。公共签名不暴露 SQL、连接或路径类型。

## 语义与不变量

- Store 是真相；唤醒只是 best-effort，丢失时由轮询兜底；
- `claim` 在 SQLite 中通过 `BEGIN IMMEDIATE` 原子领取；同一任务同一时刻只有一个有效租约；
- 所有执行写回（heartbeat/complete/fail/defer）必须携带匹配的 lease token；过期执行者的写回被拒绝
  （fencing）。`resume`/`cancel` 是宿主控制面操作，不需要 token；
- 重试按 `RetryPolicy` 退避；实际停止点为 `min(WorkSpec.max_attempts, RetryPolicy.max_attempts)`：
  spec 耗尽进入 `dead`，policy 提前停止进入 `failed`；不可重试失败进入 `failed`；
- `waiting` 不会被自动领取，宿主必须调用 `resume`；
- 不承诺 exactly-once；执行器应使用 `idempotency_key` 或外部幂等键；
- 关闭停止 claim、取消并等待在途任务、重新排队已释放任务，幂等。

## 配置与默认值

- `SqliteWorkStore(path)`：WAL、`busy_timeout=5000ms`、`schema_version=1`，首启创建当前 schema；
  **不提供旧 `work.db` 迁移**（产品未上线）。
- `LeasePolicy(seconds=60, heartbeat_seconds=20)`；心跳只延长，不缩短。
- `RetryPolicy(max_attempts=3, base_seconds=1, multiplier=2, jitter=0)`。
- `ConcurrencyPolicy(max_concurrency=2, claim_batch=1, poll_interval_seconds=1)`。
- `ZmqNotifier(endpoint="tcp://127.0.0.1:5559")`，payload 只有 `work_id`/`queue`，`LINGER=0`。
  Windows 上 `zmq.asyncio` 需要 selector event loop；默认 Proactor 宿主应设置
  `WindowsSelectorEventLoopPolicy` 或使用 `asyncio.Runner(loop_factory=asyncio.SelectorEventLoop)`。
  `tcp://…:0` 先 publish 绑定后再用 `notifier.endpoint` 供对端订阅。

## 错误与限制

- `WorkConflictError`：重复幂等键；`LeaseLostError`：写回不再拥有租约；
- `StoreError`/`NotifierError` 保留底层原因；
- SQLite 为单写者；不支持多机共享；服务端档位不得使用 SQLite；
- Phase 1 不实现 Postgres/MQ、Temporal、多租户、认证、配额；
- 关闭时若执行器吞掉取消，runner 只能记录日志并停止抢占，其租约由进程退出/过期处理。

## 与相邻包的关系

- `spawn-join-agent-deepagents` 负责 Agent 装配，不实现数据库/后台调度；
- `spawn-join-personal-assistant` 组合本包与 agent 包；HITL 审批仍在宿主兼容层；
- 依赖方向：宿主 → `agent-work`；本包不依赖 LangChain、模型包或 Agent 包。

## 开发与测试

```powershell
uv lock --check --directory packages/infra/agent-work
uv sync --locked --directory packages/infra/agent-work
uv run --directory packages/infra/agent-work pytest -q
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-agent-work
```

契约测试对 SQLite 与 InMemory 参数化；ZMQ 测试使用临时/`inproc` 端点。

## 目录布局

```text
src/spawn_join_agent_work/
  models.py policies.py protocols.py runner.py errors.py
  stores/   sqlite.py memory.py
  notify/   zmq.py
tests/      test_contract_store.py test_runner.py test_lease_and_fencing.py
            test_retry.py test_shutdown.py test_zmq_integration.py ...
```

存储、通知、执行器都与公共模型/端口分离；`stores/` 与 `notify/` 是适配器，不作为新的公共契约。

## 版本与发布

当前版本 `0.1.0`，未发布到 PyPI。发布时以包级 `uv.lock`、质量门和 PR CI 9×3 组合为前置证据；
变更说明记录在仓库发布记录，不在 README 复制历史。Phase 1 的公共 API 可能随反馈调整。

## 所有权、版本与许可证

维护者：SpawnJoin 仓库维护者。当前尚未发布；版本与兼容性以仓库发布记录为准，Phase 1
接口可能随反馈调整。许可证：见 [LICENSE](LICENSE)（LicenseRef-Proprietary）。问题与贡献遵循
仓库根 `AGENTS.md`。
