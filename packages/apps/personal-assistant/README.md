# spawn-join-personal-assistant

[简体中文](README.md) | [English](README.en.md)

`spawn-join-personal-assistant` 是 SpawnJoin 的个人助理宿主应用：组合
`spawn-join-agent-deepagents` 与 `spawn-join-llm-provider-langchain`，把"接活 → 受控执行 →
审批 → 汇报 → 重启恢复"收敛成一个可测试的本地产品。它拥有工作项存储、调度循环、
HITL 审批持久化和 CLI 入口；**记忆能力不在 v1 范围内**（接缝已留位，见 ADR-0015）。

> 状态说明：本包处于按切片交付的开发过程中。当前已提供：配置边界（`AppConfig`）、
> 稳定错误分类与**工作项存储**（sqlite3 状态机、幂等键、恢复扫描）；调度、审批与
> CLI 在后续切片落地。本文只描述已实现的能力。

**目录**

- [状态与兼容性](#状态与兼容性)
- [提供的能力](#提供的能力)
- [安装](#安装)
- [配置](#配置)
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

- `AppConfig`：宿主配置边界对象，急切校验数据目录、工作区根、模型目录文件与
  调度上限/deadline；凭据一律不进入配置（走环境变量，ADR-0008）。
- 稳定错误分类：`HostError` 及其 `HostConfigError` / `HostStoreError` /
  `HostSchedulingError` / `HostApprovalError` / `WorkTransitionError` 子类，
  用于区分宿主侧失败类别。
- `WorkStore`：sqlite3 单写者持久化——`accept` 录入（幂等键唯一，重放拒绝）、
  `mark` 状态机迁移（`queued/running/waiting_approval/completed/failed/cancelled`，
  非法迁移抛 `WorkTransitionError` 且零副作用）、`pending_recovery` 重启恢复扫描、
  按状态计数；`WorkItem`/`WorkStatus` 为公共数据类型。

后续切片（见任务队列）：asyncio due 调度、受限工作区装配
（`FilesystemBackend` + 权限门禁 + strict msgpack checkpointer）、
HITL 审批持久化与 `accept/due/run/report/approve` CLI。

## 安装

从仓库根目录使用该 Distribution 自己的环境：

```powershell
uv lock --check --directory packages/apps/personal-assistant
uv sync --locked --directory packages/apps/personal-assistant
```

## 配置

`AppConfig` 字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `data_dir` | `pathlib.Path` | 宿主持久化目录（SQLite 数据库所在） |
| `workspace_root` | `pathlib.Path` | agent 文件副作用的唯一合法根目录 |
| `model_catalog_path` | `pathlib.Path` | 模型目录文件；经 `ModelCatalog` 消费，必须已存在 |
| `max_concurrency` | `int = 2` | 同时运行的工作项上限（至少 1） |
| `work_deadline_seconds` | `float \| None = None` | 单个工作项运行的总期限；`None` 关闭 |

非法输入（非 `Path`、目录文件缺失、并发上限 < 1、deadline <= 0）在构造时抛出
`HostConfigError`，不会进入后续阶段。

## 错误与失败行为

- 所有宿主侧失败都以 `HostError` 子类表达，错误信息稳定可断言。
- 本包不吞掉、不改写模型或框架包的异常语义；跨包错误保持原有类型与原因链。

## 兼容性与限制

- Python `>=3.11`；DeepAgents 锁定由装配包持有（`>=0.7.32,<0.8`）。
- 记忆（langmem、`BaseStore`、embeddings、记忆文件）不在 v1 范围；
  `SupervisorSpec.store`/`memory` 透传接缝保留，见 ADR-0015。
- 不实现多租户、IM 通道、Web UI、MCP Server、容器/远程沙箱与 Postgres 部署；
  生产迁移路径只作为接缝文档（ADR-0015）。

## 开发与验证

```powershell
uv lock --check --directory packages/apps/personal-assistant
uv sync --locked --directory packages/apps/personal-assistant
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-personal-assistant
```

- 布局：`src/spawn_join_personal_assistant/` 是运行时源码，`tests/` 是离线测试。
- 离线测试不读取真实密钥、不连接外部服务。

## 相关文档

- [ADR-0015：个人助理宿主边界与持久化基线](../../../docs/decisions/agent/0015-personal-assistant-host-boundary.md)
- [包边界](../../../docs/architecture/package-boundaries.md)
- [仓库地图](../../../docs/architecture/repository-map.md)
- [质量门说明](../../../docs/development/quality-gates.md)

## 许可证

本包为专有软件，保留所有权利。详见 [LICENSE](LICENSE)。
