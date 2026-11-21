# spawn-join-personal-assistant

[简体中文](README.md) | [English](README.en.md)

`spawn-join-personal-assistant` 是 SpawnJoin 的个人助理宿主应用：组合
`spawn-join-agent-deepagents` 与 `spawn-join-llm-provider-langchain`，把"接活 →
受控执行 → 审批 → 汇报 → 重启恢复"收敛成一个可测试的本地产品。它拥有工作项存储、
调度循环、HITL 审批持久化和 CLI 入口；**记忆能力不在 v1 范围内**（接缝已留位，见
[ADR-0015](../../../docs/decisions/agent/0015-personal-assistant-host-boundary.md)）。

**目录**

- [状态与兼容性](#状态与兼容性)
- [提供的能力](#提供的能力)
- [安装](#安装)
- [快速开始](#快速开始)
  - [1. 离线运行完整示例](#1-离线运行完整示例)
  - [2. 连接自己的模型服务](#2-连接自己的模型服务)
- [工作项](#工作项)
  - [WorkItem 字段说明](#workitem-字段说明)
  - [状态机](#状态机)
  - [完整示例：录入→执行→完成](#完整示例录入执行完成)
  - [幂等键重放](#幂等键重放)
  - [非法迁移拒绝](#非法迁移拒绝)
  - [重启后数据保留](#重启后数据保留)
- [调度](#调度)
  - [示例 1：基本调度周期](#示例-1基本调度周期)
  - [示例 2：deadline 到期](#示例-2deadline-到期)
  - [示例 3：执行器异常不中断兄弟项](#示例-3执行器异常不中断兄弟项)
  - [示例 4：硬杀恢复](#示例-4硬杀恢复)
  - [示例 5：父级取消传播](#示例-5父级取消传播)
- [审批](#审批)
  - [ApprovalRecord 字段说明](#approvalrecord-字段说明)
  - [审批流程](#审批流程)
  - [完整示例：批准路径（文件写入）](#完整示例批准路径文件写入)
  - [完整示例：拒绝路径（不执行动作）](#完整示例拒绝路径不执行动作)
  - [完整示例：已决记录不可变](#完整示例已决记录不可变)
  - [完整示例：重启后 pending 对齐](#完整示例重启后-pending-对齐)
- [装配](#装配)
  - [完整示例：装配与资源关闭](#完整示例装配与资源关闭)
  - [完整示例：自定义审批门禁](#完整示例自定义审批门禁)
  - [HostSession 字段断言](#hostsession-字段断言)
- [CLI](#cli)
  - [CLI 完整流程演示](#cli-完整流程演示)
- [公共 API](#公共-api)
- [错误与失败行为](#错误与失败行为)
- [兼容性与限制](#兼容性与限制)
- [开发与验证](#开发与验证)
- [发布与版本](#发布与版本)
- [维护与贡献](#维护与贡献)
- [相关文档](#相关文档)
- [许可证](#许可证)

## 状态与兼容性

- 版本与稳定性：`0.1.0`，preview；`0.x` 期间公共 API 仍可能按文档化变更调整。
- 运行时：Python `>=3.11`；DeepAgents `0.7.x`；LangChain/LangGraph 1.x。
- 发布状态：当前仅支持仓库内本地开发，尚未发布到 PyPI 或私有 Registry。

## 提供的能力

- 六状态工作项状态机（`queued/running/waiting_approval/completed/failed/cancelled`）
  与幂等键唯一约束：重放同一键不会创建第二个工作项或副作用；
- asyncio due 调度循环：并发上限、deadline（到期落 `failed`，类别 `deadline`）、
  取消传播（重排队 + 重抛）、重启后中断项恰好一次重入队；
- 受限工作区装配：`FilesystemBackend` 路径守卫（拒绝 `..`/`~`/根外绝对路径）+
  显式 `FilesystemPermission` 策略 + 默认不暴露 shell 执行工具；
- strict msgpack `AsyncSqliteSaver`：thread 状态跨进程恢复，反序列化白名单默认
  启用（等价于 `LANGGRAPH_STRICT_MSGPACK` 开关，但不修改进程环境）；
- HITL 审批持久化：动作列表/决定/时间戳落独立 SQLite 表，已决不可变，
  恢复命令与动作数结构性对齐；
- 五子命令 CLI（`accept/due/run/report/approve`）：稳定退出码 0/1，
  凭据仅走 `LLM_API_KEY` 环境变量；
- 60 个离线测试（含 e2e）+ 可运行示例 + 独立 wheel/sdist、`py.typed`、质量 profile。

## 安装

从仓库根目录使用该 Distribution 自己的环境：

```powershell
uv lock --check --directory packages/apps/personal-assistant
uv sync --locked --directory packages/apps/personal-assistant
```

运行时依赖：

- `spawn-join-agent-deepagents>=0.1.0,<0.2.0`
- `spawn-join-llm-provider-langchain>=0.1.0,<0.2.0`
- `langgraph-checkpoint-sqlite>=3.1.3,<4`

本包不重复解析 `model.yaml`、`.env` 或 Provider SDK；配置模型由
[`spawn-join-llm-provider-langchain`](../../infra/llm-provider-langchain/README.md)
创建，agent 装配由
[`spawn-join-agent-deepagents`](../../infra/agent-deepagents/README.md)
拥有。

## 快速开始

### 1. 离线运行完整示例

从仓库根目录执行，无需模型文件或密钥：

```powershell
uv run --locked --directory packages/apps/personal-assistant python examples/offline_run.py
```

完整源码：[offline_run.py](examples/offline_run.py)。它使用同目录的
[`fake_model.py`](examples/fake_model.py) 提供确定性响应：先让模型请求写一条笔记
（触发审批暂停），然后批准、恢复、汇报。实际输出：

```text
accepted <id> key=notes-1
waiting_approval <id>: needs human decision
run: 1 item(s) processed
approved <id>: completed
completed <id>: 笔记已写入工作区。
report: 1 item(s)
notes.txt exists: True
```

### 2. 连接自己的模型服务

准备 `model.yaml`（两个用途共享 `LLM_API_KEY` 凭据）：

```yaml
schema_version: 1
default: supervisor
models:
  supervisor:
    protocol: chat_completions
    endpoint: https://api.example.com/v1
    model: your-supervisor-model
    api_key_env: LLM_API_KEY
  worker:
    protocol: chat_completions
    endpoint: https://api.example.com/v1
    model: your-worker-model
    api_key_env: LLM_API_KEY
```

模型需要支持工具调用。然后在进程环境中设置 `LLM_API_KEY`，用 CLI 驱动完整闭环：

```powershell
$env:LLM_API_KEY = "<your-key>"
spawn-join-personal-assistant --root <data-dir> --model-catalog <path-to-model.yaml> accept "帮我整理这周的发票" --key invoices-week-47
spawn-join-personal-assistant --root <data-dir> --model-catalog <path-to-model.yaml> run --supervisor-model supervisor --worker-model worker
spawn-join-personal-assistant --root <data-dir> report
spawn-join-personal-assistant --root <data-dir> approve --list
spawn-join-personal-assistant --root <data-dir> approve --record <record-id>
```

## 工作项

### WorkItem 字段说明

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `str` | 存储分配的唯一标识（UUID hex） |
| `idempotency_key` | `str` | 调用方提供，全表唯一；重放同键直接拒绝 |
| `goal` | `str` | 非空自然语言目标 |
| `status` | `WorkStatus` | 当前生命周期状态 |
| `created_at` / `updated_at` | `str` | ISO-8601 UTC 时间戳 |
| `due_at` | `str \| None` | 可选的到期时间；到期后 `run_due` 才会拾取 |
| `deadline_seconds` | `float \| None` | 单次运行的总时间预算 |
| `attempts` | `int` | 已开始的运行次数；每次 `queued → running` 递增 |
| `result_summary` | `str \| None` | 完成时的最终回复摘要（截断 200 字符） |
| `failure_category` | `str \| None` | 稳定失败类别（如 `deadline`、异常类名、`rejected`） |
| `thread_id` | `str \| None` | 关联的 checkpointer thread |

### 状态机

```text
queued ──→ running ──→ completed
   │           │  ↖       │
   │           ↓  │       ↓
   ↓       waiting_approval → failed
cancel ←──┘  │       │
             ↓       ↓
          cancel ←──┘
```

- `transition_allowed(current, target)` 是唯一迁移判定源；
- 非法迁移抛 `WorkTransitionError` 且零副作用；
- 终态（`completed/failed/cancelled`）拒绝一切后续迁移；
- `running → queued` 恢复边是中断重跑专用。

### 完整示例：录入→执行→完成

```python
from pathlib import Path

from spawn_join_personal_assistant import (
    HostStoreError,
    WorkStatus,
    WorkStore,
)

with WorkStore(Path("data/work.db")) as store:
    # 录入（幂等键调用方提供）
    item = store.accept(
        "整理这周的发票并汇总成表",
        idempotency_key="invoices-week-47",
        due_at="2026-11-24T09:00:00+00:00",
        deadline_seconds=120.0,
    )
    print(f"录入: {item.id} status={item.status}")

    # 开始执行（attempts 递增）
    running = store.mark(item.id, WorkStatus.RUNNING, increment_attempt=True)
    print(f"运行: attempts={running.attempts}")

    # 需要审批 → 暂停
    waiting = store.mark(item.id, WorkStatus.WAITING_APPROVAL, thread_id="t-47")
    print(f"暂停: status={waiting.status} thread={waiting.thread_id}")

    # 批准后恢复
    resumed = store.mark(waiting.id, WorkStatus.RUNNING)
    print(f"恢复: status={resumed.status} attempts={resumed.attempts}")

    # 完成（持久化结果摘要）
    done = store.mark(
        resumed.id, WorkStatus.COMPLETED, result_summary="12 张发票已汇总"
    )
    print(f"完成: {done.result_summary}")
```

输出：

```text
录入: 3a8f… status=WorkStatus.QUEUED
运行: attempts=1
暂停: status=WorkStatus.WAITING_APPROVAL thread=t-47
恢复: status=WorkStatus.RUNNING attempts=1
完成: 12 张发票已汇总
```

### 幂等键重放

```python
from pathlib import Path

from spawn_join_personal_assistant import HostStoreError, WorkStore

with WorkStore(Path("data/work.db")) as store:
    first = store.accept("任务A", idempotency_key="key-1")

    # 重放同键 → 稳定错误，不创建第二项
    try:
        store.accept("任务B", idempotency_key="key-1")
    except HostStoreError as exc:
        print(f"重放被拒: {exc}")  # idempotency_key: already exists: key-1

    # 原项不受影响
    assert store.get(first.id) == first
    assert store.count_by_status(WorkStatus.QUEUED) == 1
```

### 非法迁移拒绝

```python
from pathlib import Path

import pytest

from spawn_join_personal_assistant import WorkStatus, WorkStore, WorkTransitionError

with WorkStore(Path("data/work.db")) as store:
    item = store.accept("任务A", idempotency_key="key-1")

    # queued → completed 是非法的（必须经过 running）
    with pytest.raises(WorkTransitionError, match="illegal transition"):
        store.mark(item.id, WorkStatus.COMPLETED)

    # 原项保持不变（零副作用）
    assert store.get(item.id) == item

    # 终态拒绝一切迁移
    running = store.mark(item.id, WorkStatus.RUNNING)
    failed = store.mark(running.id, WorkStatus.FAILED, failure_category="timeout")
    for target in WorkStatus:
        if target is not failed.status:
            with pytest.raises(WorkTransitionError):
                store.mark(failed.id, target)
```

### 重启后数据保留

```python
from pathlib import Path

from spawn_join_personal_assistant import WorkStatus, WorkStore

db_path = Path("data/work.db")

# 第一个"进程"写入
with WorkStore(db_path) as store:
    store.accept("任务A", idempotency_key="key-a")
    store.accept("任务B", idempotency_key="key-b")
    store.accept("任务C", idempotency_key="key-c")

# 模拟硬杀：任务B 留在 RUNNING
with WorkStore(db_path) as store:
    item_b = store.get_by_idempotency_key("key-b")
    store.mark(item_b.id, WorkStatus.RUNNING)

# 第二个"进程"重启 → 数据完好、schema 幂等
with WorkStore(db_path) as store:
    unfinished = store.pending_recovery()
    # 2 个 queued + 1 个 running = 3 个未完成
    assert len(unfinished) == 3

    # 全历史可查
    all_items = store.list_all()
    assert len(all_items) == 3
```

## 调度

`Scheduler` 在一个 `run_due` 周期内拾取全部到期排队项，信号量约束并发，
`asyncio.timeout` 实施 deadline：

| 转移 | 行为 |
| --- | --- |
| 到期拾取 | `due_at is None or due_at <= now` 的 `queued` 项 |
| 并发上限 | `asyncio.Semaphore(max_concurrency)`，超额项排队等待 |
| deadline 到期 | 落 `failed`，类别 `deadline`，槽位立即释放 |
| 执行器异常 | 落 `failed`，类别=异常类名，**不中断兄弟项**（存储即记录） |
| 执行器未持久化 | 落 `failed`，类别 `executor_incomplete`（契约兜底） |
| 父级取消 | 运行项重排队（`running → queued`）+ 传播 `CancelledError` |
| 重启恢复 | `recover_interrupted()` 把 `running` 项恰好一次重入队 |

执行器契约（`WorkExecutor`）：接收 RUNNING 项的 async 可调用，**自行持久化最终
状态**；调度器通过读取落库结果验证执行器遵守契约。

### 示例 1：基本调度周期

```python
import asyncio
from pathlib import Path

from spawn_join_personal_assistant import Scheduler, WorkStatus, WorkStore

async def main() -> None:
    with WorkStore(Path("data/work.db")) as store:
        for i in range(4):
            store.accept(f"任务{i}", idempotency_key=f"key-{i}")

        async def execute(item) -> None:
            # 模拟执行 → 标记完成
            store.mark(item.id, WorkStatus.COMPLETED, result_summary=f"完成 {item.goal}")

        scheduler = Scheduler(store, max_concurrency=2)
        outcomes = await scheduler.run_due(execute)
        print(f"{len(outcomes)} item(s) completed")

asyncio.run(main())
# 输出: 4 item(s) completed
```

### 示例 2：deadline 到期

```python
import asyncio
from pathlib import Path

from spawn_join_personal_assistant import Scheduler, WorkStatus, WorkStore

async def main() -> None:
    with WorkStore(Path("data/work.db")) as store:
        store.accept("慢任务", idempotency_key="slow")
        store.accept("快任务", idempotency_key="fast")

        async def execute(item) -> None:
            if item.idempotency_key == "slow":
                await asyncio.sleep(10)  # 超过 deadline
            store.mark(item.id, WorkStatus.COMPLETED)

        scheduler = Scheduler(store, max_concurrency=1, deadline_seconds=0.1)
        outcomes = await scheduler.run_due(execute)

        for o in outcomes:
            if o.status is WorkStatus.FAILED:
                print(f"{o.idempotency_key}: failed({o.failure_category})")
            else:
                print(f"{o.idempotency_key}: {o.status.value}")

asyncio.run(main())
# 输出:
# slow: failed(deadline)
# fast: completed
```

### 示例 3：执行器异常不中断兄弟项

```python
import asyncio
from pathlib import Path

from spawn_join_personal_assistant import Scheduler, WorkStatus, WorkStore

async def main() -> None:
    with WorkStore(Path("data/work.db")) as store:
        store.accept("会崩的任务", idempotency_key="bad")
        store.accept("正常任务", idempotency_key="good")

        async def execute(item) -> None:
            if item.idempotency_key == "bad":
                raise ValueError("something broke")
            store.mark(item.id, WorkStatus.COMPLETED, result_summary="正常完成")

        scheduler = Scheduler(store, max_concurrency=2)
        outcomes = await scheduler.run_due(execute)

        # bad → failed(ValueError)，good → completed，兄弟项不受影响
        by_key = {o.idempotency_key: o for o in outcomes}
        assert by_key["bad"].status is WorkStatus.FAILED
        assert by_key["bad"].failure_category == "ValueError"
        assert by_key["good"].status is WorkStatus.COMPLETED

asyncio.run(main())
```

### 示例 4：硬杀恢复

```python
import asyncio
from pathlib import Path

from spawn_join_personal_assistant import Scheduler, WorkStatus, WorkStore

async def main() -> None:
    db = Path("data/work.db")

    # 第一个"进程"：任务开始后硬杀（留 RUNNING）
    with WorkStore(db) as store:
        item = store.accept("长任务", idempotency_key="long")
        store.mark(item.id, WorkStatus.RUNNING, increment_attempt=True)
        # ...进程被 kill，没有任何后续 mark

    # 第二个"进程"：重启后恢复 + 重跑
    with WorkStore(db) as store:
        scheduler = Scheduler(store, max_concurrency=1)

        # 恰好一次重入队
        requeued = await scheduler.recover_interrupted()
        print(f"requeued: {len(requeued)} item(s)")
        assert requeued[0].attempts == 1  # 之前的尝试保留

        # 二次调用返回空（幂等）
        assert await scheduler.recover_interrupted() == []

        # 重跑
        async def execute(item) -> None:
            store.mark(item.id, WorkStatus.COMPLETED, result_summary="重跑完成")

        outcomes = await scheduler.run_due(execute)
        final = store.get_by_idempotency_key("long")
        assert final.status is WorkStatus.COMPLETED
        assert final.attempts == 2  # 1 次中断 + 1 次重跑

asyncio.run(main())
# 输出: requeued: 1 item(s)
```

### 示例 5：父级取消传播

```python
import asyncio
from pathlib import Path

from spawn_join_personal_assistant import Scheduler, WorkStatus, WorkStore

async def main() -> None:
    with WorkStore(Path("data/work.db")) as store:
        item = store.accept("阻塞任务", idempotency_key="blocked")
        started = asyncio.Event()

        async def execute(item) -> None:
            started.set()
            await asyncio.Event().wait()  # 永远阻塞

        scheduler = Scheduler(store, max_concurrency=1)
        task = asyncio.create_task(scheduler.run_due(execute))
        await started.wait()

        # 外部取消 → 运行项被重排队
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            print("CancelledError 已传播")

        # 工作项回到 QUEUED，attempts 保留
        recovered = store.get(item.id)
        print(f"status={recovered.status} attempts={recovered.attempts}")
        assert recovered.status is WorkStatus.QUEUED

asyncio.run(main())
# 输出:
# CancelledError 已传播
# status=WorkStatus.QUEUED attempts=1
```

## 审批

### ApprovalRecord 字段说明

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `str` | Book 分配的唯一标识（UUID hex） |
| `work_item_id` | `str` | 关联的工作项 |
| `thread_id` | `str` | 关联的 checkpointer thread |
| `interrupt_id` | `str \| None` | 原生中断标识（可能为空） |
| `actions` | `tuple[dict, ...]` | 请求的动作列表，按序；决定数必须与之对齐 |
| `decision` | `str` | `pending` / `approved` / `rejected` |
| `created_at` / `decided_at` | `str` | ISO-8601 UTC 时间戳 |

### 审批流程

1. `pause_for_approval(store, book, …)`：从原生中断提取动作列表落库 +
   工作项转 `waiting_approval`（`thread_id` 关联）；
2. `apply_decision(…, approve=True)`：记录决定 + 工作项回 `running` +
   返回对齐的 `resume_batched` 命令（批准后执行被批准动作）；
3. `apply_decision(…, approve=False, message="…")`：记录决定 + 工作项落
   `failed(rejected)` + 返回对齐的拒绝命令（**被拒动作不执行**）；
4. 已决记录不可变：二次决定抛 `HostApprovalError`。

### 完整示例：批准路径（文件写入）

```python
import asyncio
from pathlib import Path
from typing import Any, cast

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import Command
from spawn_join_agent_deepagents import pending_interrupts

from spawn_join_personal_assistant import (
    ApprovalBook,
    AppConfig,
    WorkStatus,
    WorkStore,
)
from spawn_join_personal_assistant.approvals import (
    apply_decision,
    interrupt_actions,
    pause_for_approval,
)
from spawn_join_personal_assistant.host import open_host_session

# 构造一个先请求写文件、然后回复"完成"的离线 fake 模型（见 tests/conftest.py）
model = FakeChatModel(
    responses=[
        AIMessage(content="", tool_calls=[{
            "name": "write_file",
            "args": {"file_path": "/notes.txt", "content": "note"},
            "id": "call-1", "type": "tool_call",
        }]),
        AIMessage(content="笔记已写入"),
    ]
)

config = AppConfig(
    data_dir=Path("data"),
    workspace_root=Path("workspace"),
    model_catalog_path=Path("model.yaml"),
)

async def main() -> None:
    with WorkStore(Path("data/work.db")) as store, \
         ApprovalBook(Path("data/approvals.db")) as book:
        item = store.accept("写一条笔记", idempotency_key="notes-1")
        store.mark(item.id, WorkStatus.RUNNING)

        session = await open_host_session(
            config, models=make_models(model),
            interrupt_on={"write_file": True},
        )
        try:
            thread_id = "thread-notes"
            graph_config: dict[str, Any] = {
                "configurable": {"thread_id": thread_id}
            }

            # 1. 完整消费 astream 更新流（不可提前 break！）
            interrupt_found = None
            async for update in session.assembly.graph.astream(
                {"messages": [HumanMessage(content="写一条笔记")]},
                graph_config, stream_mode="updates", version="v1",
            ):
                found = pending_interrupts(update)
                if found:
                    interrupt_found = found[0]

            # 2. 检测到中断 → 暂停
            assert interrupt_found is not None
            actions = interrupt_actions(interrupt_found)
            print(f"待审批动作: {actions[0]['name']}")

            record = pause_for_approval(
                store, book,
                work_item_id=item.id, thread_id=thread_id,
                interrupt=interrupt_found,
            )
            print(f"工作项状态: {store.get(item.id).status}")
            # 输出: waiting_approval

            # 3. 用户批准 → 生成对齐恢复命令
            command = apply_decision(
                store, book,
                record_id=record.id, work_item_id=item.id, approve=True,
            )
            assert isinstance(command, Command)
            resumed = cast(Any, command).resume
            print(f"恢复命令决定数: {len(resumed['decisions'])}")
            # 输出: 1（与 actions 数量对齐）

            # 4. 执行恢复 → 批准的写入真实执行
            await session.assembly.graph.ainvoke(command, graph_config)

            # 文件写入工作区
            assert (Path("workspace") / "notes.txt").is_file()
            print(f"文件内容: {(Path('workspace') / 'notes.txt').read_text()}")
            # 输出: note

            # 标记完成
            store.mark(item.id, WorkStatus.COMPLETED, result_summary="笔记已写入")
        finally:
            await session.aclose()

asyncio.run(main())
```

### 完整示例：拒绝路径（不执行动作）

```python
# ... 接上文同一设置 ...

# 用户拒绝 → 落 failed(rejected)，被拒动作不执行
command = apply_decision(
    store, book,
    record_id=record.id, work_item_id=item.id,
    approve=False, message="不允许写入",
)

# 工作项已落 failed
item_after = store.get(item.id)
print(f"status={item_after.status} category={item_after.failure_category}")
# 输出: status=WorkStatus.FAILED category=rejected

# 被拒动作不执行：文件从未创建
assert not (Path("workspace") / "notes.txt").exists()
```

### 完整示例：已决记录不可变

```python
from spawn_join_personal_assistant import ApprovalBook, HostApprovalError
from spawn_join_personal_assistant.approvals import apply_decision

# ... 先批准 record ...
apply_decision(store, book, record_id=record.id,
               work_item_id=item.id, approve=True)

# 尝试再次决定 → 稳定错误
try:
    apply_decision(store, book, record_id=record.id,
                   work_item_id=item.id, approve=False)
except HostApprovalError as exc:
    print(f"不可变: {exc}")
    # 输出: approval record <id>: already approved
```

### 完整示例：重启后 pending 对齐

```python
from pathlib import Path
from spawn_join_personal_assistant import ApprovalBook, WorkStatus, WorkStore
from spawn_join_personal_assistant.approvals import pause_for_approval

db = Path("data")

# 第一个"进程"：暂停审批后硬杀
with WorkStore(db / "work.db") as store, \
     ApprovalBook(db / "approvals.db") as book:
    item = store.accept("任务A", idempotency_key="key-1")
    store.mark(item.id, WorkStatus.RUNNING)
    record = pause_for_approval(
        store, book,
        work_item_id=item.id, thread_id="t-1",
        interrupt=some_interrupt,
    )

# 第二个"进程"：重启后 pending 审批与 waiting_approval 完全对齐
with WorkStore(db / "work.db") as store, \
     ApprovalBook(db / "approvals.db") as book:
    pending = book.pending()
    assert [r.id for r in pending] == [record.id]
    assert len(pending[0].actions) == 1

    unfinished = store.pending_recovery()
    assert unfinished[0].status is WorkStatus.WAITING_APPROVAL
    assert unfinished[0].thread_id == "t-1"
    print("重启后审批与工作项状态完全对齐")
```

**两个经实证验证的运行时事实**（本包测试与探针记录）：

1. 恢复前必须**完整消费** `astream(stream_mode="updates")`——提前 break 会
   中断底层运行的 checkpoint，批准后工具不会执行；
2. deepagents `write_file` 工具的参数名是 `file_path`，不是 `path`。

CLI 已内建此模式；直接调用库的用户须遵守第 1 条。

## 装配

### 完整示例：装配与资源关闭

```python
import asyncio
from pathlib import Path

from langchain_core.messages import HumanMessage

from spawn_join_personal_assistant import AppConfig
from spawn_join_personal_assistant.host import open_host_session

config = AppConfig(
    data_dir=Path("data"),
    workspace_root=Path("workspace"),
    model_catalog_path=Path("model.yaml"),
    max_concurrency=2,
    work_deadline_seconds=None,
)

async def main() -> None:
    session = await open_host_session(
        config, models=models,
        interrupt_on={"write_file": True},
    )
    try:
        result = await session.assembly.graph.ainvoke(
            {"messages": [HumanMessage(content="你好")]},
            {"configurable": {"thread_id": "greeting"}},
        )
        print(result["messages"][-1].content)
    finally:
        await session.aclose()  # 幂等关闭宿主拥有的连接

asyncio.run(main())
```

### 完整示例：自定义审批门禁

```python
# 什么工具需要人工批准？传入不同的 interrupt_on Mapping 即可。

# 只门禁写操作（默认策略）
session = await open_host_session(
    config, models=models,
    interrupt_on={"write_file": True},
)

# 门禁全部文件操作（读和写都要审批）
session = await open_host_session(
    config, models=models,
    interrupt_on={"read_file": True, "write_file": True,
                  "edit_file": True, "delete": True},
)

# 不门禁任何工具（全部自动执行）
session = await open_host_session(
    config, models=models,
    interrupt_on=None,
)
```

### HostSession 字段断言

```python
from spawn_join_personal_assistant.host import (
    open_host_session, workspace_permissions, strict_msgpack_serializer,
)

session = await open_host_session(config, models=models)

# 装配参数全部可断言
assert session.backend.cwd == config.workspace_root  # 工作区根目录
assert session.spec.tools == ()                        # 默认无 shell 工具
assert tuple(session.spec.permissions) == workspace_permissions()
assert session.spec.checkpointer is session.checkpointer

# 序列化器与严格版行为等价
serde = session.checkpointer.serde
assert serde.pickle_fallback is False
sample = {"kind": "host", "count": 2}
strict = strict_msgpack_serializer()
assert serde.dumps_typed(sample) == strict.dumps_typed(sample)

# 装配报告确认受限工作区
report = session.assembly.report
assert report.resources.backend_kind == "filesystem"
assert report.resources.permissions.allow == 1
```

## CLI

```text
spawn-join-personal-assistant [--root DIR] [--model-catalog PATH]
    accept GOAL [--key KEY] [--due ISO]
    due
    run [--max-concurrency N] [--deadline SECONDS]
        [--supervisor-model NAME] [--worker-model NAME]
    report [--status STATUS]
    approve --list | approve --record ID [--reject] [--message MSG]
```

| 子命令 | 行为 | 退出码 |
| --- | --- | --- |
| `accept` | 录入 + 幂等键唯一 | 0 成功 / 1 键重复或空 goal |
| `due` | 列出未完成项（含 due 状态） | 0 |
| `run` | 先恢复中断项，再执行一个 due 周期 | 0 / 1 目录缺 catalog |
| `report` | 列出全部历史（可按状态过滤） | 0 |
| `approve --list` | 列出待审批记录 | 0 |
| `approve --record ID` | 批准并恢复执行 | 0 / 1 未知或已决记录 |
| `approve --record ID --reject` | 拒绝（动作不执行） | 0 |

### CLI 完整流程演示

```powershell
# 1. 录入两条任务
PS> spawn-join-personal-assistant --root . accept "整理发票" --key inv-1
accepted 3a8f… key=inv-1
PS> spawn-join-personal-assistant --root . accept "写周报" --key wk-1
accepted 9c2d… key=wk-1

# 2. 查看未完成
PS> spawn-join-personal-assistant --root . due
[queued] 3a8f… due=- 整理发票
[queued] 9c2d… due=- 写周报
due: 2 unfinished item(s)

# 3. 执行一个周期（触发审批暂停）
PS> spawn-join-personal-assistant --root . run
waiting_approval 3a8f…: needs human decision
completed 9c2d…: 周报已生成
run: 2 item(s) processed

# 4. 查看待审批
PS> spawn-join-personal-assistant --root . approve --list
record abc123 work=3a8f… thread=work-3a8f… actions=write_file
approve: 1 pending record(s)

# 5. 批准 → 文件真实写入
PS> spawn-join-personal-assistant --root . approve --record abc123
approved 3a8f…: completed

# 6. 查看最终状态
PS> spawn-join-personal-assistant --root . report
completed 9c2d…: 周报已生成
completed 3a8f…: 发票已整理
report: 2 item(s)

# 7. 错误路径：重复幂等键
PS> spawn-join-personal-assistant --root . accept "重复任务" --key inv-1
personal-assistant: idempotency_key: already exists: inv-1
# 退出码 1
```

## 公共 API

公共导出由 `spawn_join_personal_assistant.__all__` 定义，主要包括：

- `main`、`AppConfig`；
- `ApprovalBook`、`ApprovalRecord`、`apply_decision`、`interrupt_actions`、
  `pause_for_approval`、`resume_approved`、`resume_rejected`；
- `HostSession`、`open_host_session`；
- `Scheduler`、`WorkExecutor`；
- `WorkItem`、`WorkStatus`、`WorkStore`；
- 稳定错误类型（`HostError` 基类及 `HostConfigError` / `HostStoreError` /
  `HostSchedulingError` / `HostApprovalError` / `WorkTransitionError`）。

内部模块（`work/`、`scheduler`、`approvals`、`host`、`cli`）不会因为可导入
就自动成为公共契约。

## 错误与失败行为

- 所有宿主侧失败以 `HostError` 子类表达；CLI 转稳定退出码 1。
- 调度执行器异常**不中断兄弟项**：转 `failed`（类别=异常类名），存储即记录。
- `WorkTransitionError`（`HostStoreError` 子类）：非法状态迁移，零副作用。
- 已决审批记录不可变：二次决定抛 `HostApprovalError`。
- 上游模型/框架异常保持原有类型与原因链；跨包错误经
  `ConfigurationError → HostError` 转换时保留原因链。
- 上游 `LLMCallError` 归一化由装配包中间件处理（默认开启），本包不吞掉。

## 兼容性与限制

- Python `>=3.11`；DeepAgents 锁定由装配包持有（`>=0.7.32,<0.8`）。
- **记忆（langmem、`BaseStore`、embeddings、记忆文件）不在 v1 范围**；
  `SupervisorSpec.store`/`memory` 透传接缝保留，后续讨论（ADR-0015）。
- 单写者假设：一个数据目录同一时刻只允许一个宿主进程；多进程并发打开同一
  SQLite 属不支持场景。
- 恢复调用方需完整消费 astream 后再以同 thread `ainvoke(command)` 续跑
  （CLI 已内建此模式；提前 break 会中断底层运行的 checkpoint 落盘）。
- 不实现多租户/授权/计费、IM 通道、Web UI、MCP Server、容器/远程沙箱与
  Postgres 部署；生产迁移路径只作为接缝文档（ADR-0015）。

## 开发与验证

```powershell
uv lock --check --directory packages/apps/personal-assistant
uv sync --locked --directory packages/apps/personal-assistant
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-personal-assistant
```

- 布局：`src/spawn_join_personal_assistant/` 是运行时源码，`tests/` 是离线
  测试（60 用例），`examples/` 是可执行示例；包内自带 `uv.lock`、`py.typed`
  和 `LICENSE`。
- 必需工具：uv `>=0.7.13`、PowerShell 7、Git、Node.js 22+（Pyright 包装器）。
- 包级质量门执行 Black/isort、Ruff、Pyright strict、pytest、wheel/sdist、
  隔离安装、`pip check` 和隔离导入。离线测试不读取真实密钥、不连接外部服务。
- e2e 覆盖：accept→run→approve→report 全链路（含越界写守卫与硬杀恢复，
  断言以受控文件写入计副作用）。

## 发布与版本

本包使用独立版本号和独立 wheel/sdist，不随其他 Distribution 隐式发布。当前版本
`0.1.0`，尚未发布；发布必须经过仓库质量门、独立评审和单独的发布授权。公共 API 的
破坏性变更应更新版本、文档和兼容性说明，并重新运行包级与仓库级门禁。

## 维护与贡献

本包由 SpawnJoin 仓库维护者拥有；变更遵循 `AGENTS.md`、
[包边界](../../../docs/architecture/package-boundaries.md) 和
[ADR-0015](../../../docs/decisions/agent/0015-personal-assistant-host-boundary.md)。
新能力或公共契约变更走 Feature 交付路由；缺陷走 Bugfix；纯文档或机械改动走
Lightweight。提交前必须提供与当前 diff 绑定的质量、标准和评审证据。

## 相关文档

- [ADR-0015：个人助理宿主边界与持久化基线](../../../docs/decisions/agent/0015-personal-assistant-host-boundary.md)
- [ADR-0010：DeepAgents 产品边界](../../../docs/decisions/agent/0010-deepagents-product-boundary.md)（装配包契约）
- [包边界](../../../docs/architecture/package-boundaries.md)
- [仓库地图](../../../docs/architecture/repository-map.md)
- [质量门说明](../../../docs/development/quality-gates.md)

## 许可证

本包为专有软件，保留所有权利。详见 [LICENSE](LICENSE)。
