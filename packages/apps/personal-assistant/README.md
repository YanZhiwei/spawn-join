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
- [调度](#调度)
- [审批](#审批)
  - [ApprovalRecord 字段说明](#approvalrecord-字段说明)
  - [审批流程](#审批流程)
- [装配](#装配)
- [CLI](#cli)
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
- 非法迁移抛 `WorkTransitionError` 且零副作用（`queued → completed` 直接被拒绝）；
- 终态（`completed/failed/cancelled`）拒绝一切后续迁移；
- `running → queued` 恢复边是中断重跑专用：硬杀进程后由
  `Scheduler.recover_interrupted()` 恰好一次重入队。

代码示例：

```python
from spawn_join_personal_assistant import WorkStatus, WorkStore
from pathlib import Path

with WorkStore(Path("data/work.db")) as store:
    item = store.accept("整理发票", idempotency_key="invoices-001")

    running = store.mark(item.id, WorkStatus.RUNNING, increment_attempt=True)
    assert running.attempts == 1

    done = store.mark(
        running.id, WorkStatus.COMPLETED, result_summary="12 张已汇总"
    )
    assert done.result_summary == "12 张已汇总"
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
状态**；调度器通过读取落库结果验证执行器遵守契约。生产中 CLI 的 `_drive_to_outcome`
就是标准实现：完整消费 astream 更新流、检测中断、无中断则以 `aget_state` 取终态
摘要落库。

代码示例：

```python
import asyncio
from pathlib import Path
from spawn_join_personal_assistant import Scheduler, WorkStatus, WorkStore

async def scenario() -> None:
    with WorkStore(Path("data/work.db")) as store:
        async def execute(item) -> None:
            store.mark(item.id, WorkStatus.COMPLETED, result_summary="完成")

        scheduler = Scheduler(store, max_concurrency=2, deadline_seconds=120)
        recovered = await scheduler.recover_interrupted()
        outcomes = await scheduler.run_due(execute)
        print(f"{len(outcomes)} item(s) processed")

asyncio.run(scenario())
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

代码示例（完整可运行版本见 `tests/test_approvals.py`）：

```python
# 在 run_due 的执行器中检测到中断后：
record = pause_for_approval(
    store, book, work_item_id=item.id, thread_id="t-1", interrupt=found
)

# 用户批准后：
command = apply_decision(
    store, book, record_id=record.id, work_item_id=item.id, approve=True
)
await graph.ainvoke(command, {"configurable": {"thread_id": "t-1"}})
```

**两个经实证验证的运行时事实**（本包测试与探针记录）：

1. 恢复前必须**完整消费** `astream(stream_mode="updates")`——提前 break 会
   中断底层运行的 checkpoint，批准后工具不会执行；
2. deepagents `write_file` 工具的参数名是 `file_path`，不是 `path`。

CLI 已内建此模式；直接调用库的用户须遵守第 1 条。

## 装配

`open_host_session(config, models=…)` 装配原生 supervisor：

```python
import asyncio
from pathlib import Path
from spawn_join_personal_assistant import AppConfig, HostSession
from spawn_join_personal_assistant.host import open_host_session

config = AppConfig(
    data_dir=Path("~/.spawn-join-personal-assistant/data").expanduser(),
    workspace_root=Path("~/.spawn-join-personal-assistant/workspace").expanduser(),
    model_catalog_path=Path("model.yaml"),
)

async def main() -> None:
    session = await open_host_session(
        config, models=models, interrupt_on={"write_file": True}
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

- `HostSession.spec/backend/checkpointer/connection` 四个字段全部可断言：
  测试直接验证 `spec.tools == ()`、`backend.cwd == workspace_root`、
  `checkpointer.serde` 与严格序列化器行为等价；
- 装配只读配置并创建图，**不执行图、不打开外部模型连接**（运行时才消费模型）；
- 修改审批门禁工具集：传入不同的 `interrupt_on` Mapping。

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

- 输出走 `sys.stdout.write`（无 `print`、无运行时日志混入）；
- 错误前缀 `personal-assistant:`，stderr；
- v1 审批策略：`write_file` 工具调用需人工批准。

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
