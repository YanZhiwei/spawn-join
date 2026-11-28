# 代码上下文

- 运行：`deepagents-planning-middleware-20261128`
- 基线：`87e809f2b8d405c19d9bced4bfda89d018fa430e`
- 范围：仅 `spawn-join-agent-deepagents` 的 planning seam。

## 入口与所有权

| 路径/符号 | 职责 | 变更影响 |
| --- | --- | --- |
| `supervisor.py::SupervisorSpec` | 校验后的装配输入 | 新增可选 `planning` 字段 |
| `supervisor.py::build_supervisor` | 模型解析、中间件装配、调用 `create_deep_agent` | 新增 planning 中间件与冲突校验 |
| `supervisor.py::_supervisor_middleware` | supervisor 中间件顺序 | 在宿主 supervisor 中间件之后、summarization 之前插入 planning |
| `supervisor.py::_declarative_middleware` | worker 中间件装配 | 不变；planning 仅 supervisor |
| `middleware/scopes.py::MiddlewareScopeReport` | 生效中间件名称 | 不改 schema；planning 名称出现在 `supervisor_names` |
| `__init__.py` | 公共导出 | 新增 `PlanningConfiguration` |
| `planning.py`（新增） | 配置与校验 | 新公共类型 |

## 依赖的上游契约

- `langchain.agents.middleware.TodoListMiddleware`（`langchain 1.4.8`）
  - `.name == "TodoListMiddleware"`
  - 可选 `system_prompt`、`tool_description`
  - 提供 `write_todos`
- `deepagents 0.7.32` 的 `create_deep_agent` 按 `.name` 合并用户中间件，默认不添加
  `TodoListMiddleware`。

## 现有验证面

- `tests/test_supervisor.py`：fake sequence model、装配报告、图行为。
- `tests/test_middleware.py`：作用域、保留名、重复拒绝。
- `tests/test_public_api.py`：包导出面。
- `scripts/quality.ps1 -Package spawn-join-agent-deepagents`：格式、lint、Pyright
  strict、pytest、构建、隔离安装。
