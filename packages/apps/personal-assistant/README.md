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
- [配置](#配置)
- [CLI](#cli)
- [错误与失败行为](#错误与失败行为)
- [兼容性与限制](#兼容性与限制)
- [开发与验证](#开发与验证)
- [相关文档](#相关文档)
- [许可证](#许可证)

## 状态与兼容性

- 版本与稳定性：`0.1.0`，preview；`0.x` 期间公共 API 仍可能按文档化变更调整。
- 运行时：Python `>=3.11`；依赖 `spawn-join-agent-deepagents`、
  `spawn-join-llm-provider-langchain` 与 `langgraph-checkpoint-sqlite>=3.1.3,<4`。
- 发布状态：当前仅支持仓库内本地开发，尚未发布到 PyPI 或私有 Registry。

## 提供的能力

- **配置边界**：`AppConfig` 急切校验数据目录、工作区根、模型目录文件与调度上限/
  deadline；凭据一律不进入配置（走环境变量，ADR-0008）。
- **稳定错误分类**：`HostError` 及其 `HostConfigError` / `HostStoreError` /
  `HostSchedulingError` / `HostApprovalError` / `WorkTransitionError` 子类。
- **工作项存储**（`WorkStore`）：sqlite3 单写者持久化——`accept` 录入（幂等键唯一，
  重放拒绝）、`mark` 状态机迁移（`queued/running/waiting_approval/completed/
  failed/cancelled`，非法迁移抛 `WorkTransitionError` 且零副作用）、
  `pending_recovery` 重启恢复扫描、`list_all` 历史查询；`WorkItem`/`WorkStatus`
  为公共数据类型。
- **宿主装配**（`open_host_session`）：`FilesystemBackend(workspace_root,
  virtual_mode=True)` 路径守卫（拒绝 `..`/`~`/根外绝对路径）、显式
  `FilesystemPermission` 工作区策略、`tools=()` 默认不暴露 shell 执行工具、
  `AsyncSqliteSaver` 持久 thread 状态且反序列化白名单默认严格
  （等价于文档化 `LANGGRAPH_STRICT_MSGPACK` 开关，不修改进程环境）；
  返回 `HostSession`（`aclose` 幂等关闭宿主拥有的连接）。
- **due 调度**（`Scheduler`）：`run_due` 单周期拾取到期排队项，信号量约束并发
  上限，`asyncio.timeout` 实施 deadline（到期落 `failed`，类别 `deadline`，槽位
  释放）；执行器异常转 `failed`（类别=异常类名，存储即记录，不中断兄弟项）；
  父级取消把运行项重排队（`RUNNING → QUEUED`）并传播 `CancelledError`；
  `recover_interrupted` 在重启后把中断项恰好一次重入队。
  `WorkExecutor` 为执行器契约类型（接收 RUNNING 项、自行持久化最终状态）。
- **HITL 审批**（`ApprovalBook`/`ApprovalRecord`）：审批请求持久化（独立 SQLite
  表：动作列表、决定、时间戳；已决记录不可变）。`pause_for_approval` 同时落请求
  并把工作项转为 `waiting_approval`；`apply_decision` 记录用户决定并返回**对齐的**
  原生恢复命令（`resume_batched`，决定数与顺序严格对应 action 数；批准回
  `running`，拒绝落 `failed(rejected)` 且不执行被拒动作）。
- **CLI**（`main`）：`accept/due/run/report/approve` 五个子命令；退出码 0/1
  稳定；`main(bindings=…)` 为模型绑定注入缝（生产走 `ModelCatalog`，离线走
  构造好的 `BaseChatModel`）。

## 安装

从仓库根目录使用该 Distribution 自己的环境：

```powershell
uv lock --check --directory packages/apps/personal-assistant
uv sync --locked --directory packages/apps/personal-assistant
```

## 快速开始

先运行完整离线示例（无需模型文件或密钥）：

```powershell
uv run --locked --directory packages/apps/personal-assistant python examples/offline_run.py
```

示例用 [`fake_model.py`](examples/fake_model.py) 提供确定性响应，输出
accept → run（暂停待审批）→ approve → report 完整闭环。安装后可通过
console 入口 `spawn-join-personal-assistant` 调用 CLI。

## 配置

`AppConfig` 字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `data_dir` | `pathlib.Path` | 宿主持久化目录（工作项/审批 SQLite + threads.db） |
| `workspace_root` | `pathlib.Path` | agent 文件副作用的唯一合法根目录 |
| `model_catalog_path` | `pathlib.Path` | 模型目录文件；经 `ModelCatalog` 消费，必须已存在 |
| `max_concurrency` | `int = 2` | 同时运行的工作项上限（至少 1） |
| `work_deadline_seconds` | `float \| None = None` | 单个工作项运行的总期限；`None` 关闭 |

CLI 默认 root 为 `~/.spawn-join-personal-assistant`（可用 `--root` 覆盖），
模型目录默认 `<root>/model.yaml`（可用 `--model-catalog` 覆盖）。

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

`run` 子命令先恢复中断项再执行一个 due 周期。v1 审批策略：`write_file` 工具
调用需人工批准（`approve --list` 查看 → `approve --record ID` 批准或
`--record ID --reject` 拒绝）。退出码 0 成功、1 宿主错误（stderr 前缀
`personal-assistant:`）或用法错误。

## 错误与失败行为

- 所有宿主侧失败以 `HostError` 子类表达，CLI 转稳定退出码 1。
- 调度执行器异常不中断兄弟项：转 `failed`（类别=异常类名），存储即记录。
- 上游模型/框架异常保持原有类型与原因链；跨包错误经
  `ConfigurationError → HostError` 转换时保留原因链。

## 兼容性与限制

- Python `>=3.11`；DeepAgents 锁定由装配包持有（`>=0.7.32,<0.8`）。
- 记忆（langmem、`BaseStore`、embeddings、记忆文件）不在 v1 范围；
  `SupervisorSpec.store`/`memory` 透传接缝保留，见 ADR-0015。
- 单写者假设：一个数据目录同一时刻只允许一个宿主进程；多进程并发打开同一
  SQLite 属不支持场景。
- 恢复调用方需完整消费 `astream(stream_mode="updates")` 后再以同 thread
  `ainvoke(command)` 续跑（提前 break 会中断底层运行的 checkpoint 落盘）；
  CLI 已内建此模式。
- 不实现多租户、IM 通道、Web UI、MCP Server、容器/远程沙箱与 Postgres 部署；
  生产迁移路径只作为接缝文档（ADR-0015）。

## 开发与验证

```powershell
uv lock --check --directory packages/apps/personal-assistant
uv sync --locked --directory packages/apps/personal-assistant
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-personal-assistant
```

- 布局：`src/spawn_join_personal_assistant/` 是运行时源码，`tests/` 是离线
  测试（60 用例），`examples/` 是可执行示例。
- 离线测试不读取真实密钥、不连接外部服务；e2e 覆盖 accept→run→approve→report
  全链路（含越界写守卫与硬杀恢复）。

## 相关文档

- [ADR-0015：个人助理宿主边界与持久化基线](../../../docs/decisions/agent/0015-personal-assistant-host-boundary.md)
- [包边界](../../../docs/architecture/package-boundaries.md)
- [仓库地图](../../../docs/architecture/repository-map.md)
- [质量门说明](../../../docs/development/quality-gates.md)

## 许可证

本包为专有软件，保留所有权利。详见 [LICENSE](LICENSE)。
