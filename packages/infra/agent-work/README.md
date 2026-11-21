# spawn-join-agent-work

[简体中文](README.md) | [English](README.en.md)

> 状态：Phase 1 骨架（T001）。完整 API、示例、安装与限制在后续任务补齐。

可复用的长任务生命周期运行时：桌面默认 SQLite + ZeroMQ 唤醒；公共契约可通过端口替换为
服务端存储与消息队列。当前尚未发布；决策背景见 ADR-0017（Proposed）。

## 当前范围

- 本包尚未接入任何宿主；
- 存储/队列/runner 在后续任务实现；
- 默认桌面档不要求外部服务；
- 服务端档（Postgres/MQ）不在 Phase 1。

## 依赖说明

- `pyzmq>=27.3.0,<28` 是桌面默认唤醒依赖；pyzmq 为 BSD-3-Clause，随包 libzmq 为 MPL-2.0，
  引入前已记录供应链与平台 wheel 评估。完整说明由 T016 补齐。

## 验证

```powershell
uv lock --check --directory packages/infra/agent-work
uv sync --locked --directory packages/infra/agent-work
uv run --directory packages/infra/agent-work pytest -q
```
