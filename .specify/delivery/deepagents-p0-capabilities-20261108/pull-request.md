## 摘要

- 解决的问题：`spawn-join-agent-deepagents` 只覆盖 DeepAgents 0.7.32 的 v1 装配能力，
  async 子代理会以 `AttributeError` 失败，Memory/Skills 只有裸列表透传，Harness/Provider
  profile 完全不感知。
- 合并后的行为或契约：新增 `AsyncSubAgentDefinition`、`MemoryConfiguration`/
  `SkillsConfiguration`、`ProfilesConfiguration` 及对应报告/错误类型；beta 能力显式 opt-in，
  默认关闭，报告不泄露 URL、headers、路径或凭据。
- 本次不包含：Rubric、Backend 工厂、HITL resume helper、Streaming 适配、异步诊断；
  不实现 MCP Server、数据库、沙箱、UI、租户/计费或发布自动化。

## 关联问题与变更类型

Part of #<issue>；本 PR 不关闭 Issue。

- [x] 新功能或新组件
- [ ] Bugfix 或契约修正
- [ ] 重构或简化
- [x] 文档或治理
- [ ] 发布准备

## 变更内容

| 位置 | 变更 | 原因 |
| --- | --- | --- |
| `src/.../subagents.py` | 新增 `AsyncSubAgentDefinition`、`SubAgentKind.ASYNC`、async/fork 双 gate | 对齐官方 `AsyncSubAgent` + `AsyncSubAgentMiddleware` |
| `src/.../context_sources.py` | 新增 Memory/Skills 配置对象与 source 校验 | 让 source 形状错误在装配前可见 |
| `src/.../profiles.py` | 新增 Harness/Provider profile 注册封装 | 统一 beta gate、保留名校验与异常链 |
| `src/.../supervisor.py` | 接线 async、memory/skills、profiles；报告新增 `ContextReport`/`ProfileReport` | 一处装配入口保持向后兼容 |
| `src/.../diagnostics.py` / `errors.py` / `middleware.py` | 新报告分区、两个错误子类、async override 文案 | 可观察、稳定失败 |
| `tests/` | 新增 async/context/profile 测试；扩展公共 API 与上游契约测试 | 覆盖 beta gate、报告脱敏和 0.7.32 契约 |
| `README.md` / `README.en.md` / ADR-0012 | 记录能力、beta 风险、限制和示例 | 使用文档与实现一致 |

## 验证

| 场景或检查 | 实际结果 | 证据 |
| --- | --- | --- |
| `uv lock --check` | 通过 | 本 run `runtime/` 日志 |
| `black --check` / `isort --check-only` / `ruff check` | 通过 | 同上 |
| `pyright` | 0 errors, 0 warnings | 同上 |
| `pytest -q` | 146 passed | 同上 |
| `scripts/quality.ps1 -Package spawn-join-agent-deepagents` | 通过（构建/隔离安装/`pip check`/隔离导入） | 同上 |
| `scripts/quality.ps1 -Check docs` | 通过（68 files / 333 targets） | 同上 |
| `scripts/quality.ps1 -Check governance` | 0 errors；1 个历史 warning | 同上 |
| `git diff --check` | 通过 | 同上 |

- 未执行或未覆盖的验证及原因：真实远程 Agent Protocol 服务、真实 harness profile 行为、
  真实 `fork` 执行未覆盖；async/profile 只验证原生 kwargs、报告和失败语义。

## 影响（仅填写适用项）

| 维度 | 影响 | 证据 |
| --- | --- | --- |
| 公共 API、命令、配置 | 新增 9 个公共类型/错误；旧 `Sequence[str]` 写法保持兼容 | `__init__.py`、`tests/test_public_api.py` |
| 持久化、迁移或数据兼容 | 无；不新增数据库或持久化 | 变更范围 |
| 安全、权限或敏感信息 | 报告不含 URL、headers、webhook、路径或凭据；profile 排除保留名被拒绝 | `tests/test_async_subagents.py`、`tests/test_profiles.py` |
| 性能、资源或可观测性 | 仅新增可选配置与报告字段；资源生命周期仍由宿主拥有 | ADR-0012 |
| 依赖、供应链或发布 | 无新增依赖；仍锁定 `deepagents 0.7.32` | `pyproject.toml`、`uv.lock` |

## 审查身份

- `base_revision`：`7dbc714e8d575ae326da81c92eca7459807a241d`
- `reviewed_head`：`4d27b6c65ddcfea11f749d6c6ae45b9062347027`
- `content_fingerprint`：`2fce5f93d4872262480f7da5b31413e5a59a88d856895faf3bfd8c9af9d9ce39`
- `requirements_fingerprint`：见同 run `runtime/result-review.json`
- native Review report / receipt：`.specify/delivery/deepagents-p0-capabilities-20261108/review.md`
- 发布后的 `original_pr_head` / `published_head`：待发布

## 本地 AI Code Review 与修复历程

| 轮次 | 工具 / 方法 | 审查版本或范围 | 主要发现与状态 | 修复 / 复审结论 |
| --- | --- | --- | --- | --- |
| 1 | 独立只读 reviewer session | `7dbc714` + working tree | 4 个 blocking：memory replaced 误报、profile 可排除包管理 memory、async fork 绕过 gate、spec 错误类型不一致；全部 resolved | 已修复并重新运行质量门与 146 项测试 |

- 最终 AI 审查结论：pass（process/session 级独立；同一模型家族，未跨供应商）
- 未解决问题与剩余风险：远程 async/profile/fork 未做真实集成；已在 Evidence 记录
- 本地报告或证据：`.specify/delivery/deepagents-p0-capabilities-20261108/review.md`
- [ ] 未执行本地 AI Code Review（请说明原因）
- [x] 已执行；实现者已处理或明确记录每个问题，最终代码已重新审查

## 评审重点

- 入口或建议阅读顺序：`supervisor.py` → `subagents.py` / `context_sources.py` / `profiles.py`
  → `diagnostics.py` → tests。
- 关键行为、边界或设计取舍：async/profile 默认关闭；`memory.add_cache_control=False` 时
  包自己创建 `MemoryMiddleware` 并传 `memory=None`，fork 不继承；provider profile 只影响
  上游字符串模型路径。
- 需要人工或特定环境验证：远程 Agent Protocol 部署、真实 harness profile、真实 fork。

## 条件章节

### 架构、设计或 ADR（仅有相关变化时）

- 当前设计、入口、归属与依赖方向：仍由 `spawn-join-agent-deepagents` 拥有装配边界，
  依赖方向不变。
- 设计变化与原因：新增三项官方能力的显式、可选接线。
- ADR / 决策链接：`docs/decisions/agent/0012-deepagents-official-p0.md`（Proposed）。
- 设计图或接口说明：见 ADR 与 README。

## 回滚

回退本提交即可；默认路径未改变，beta 能力默认关闭，无数据迁移。

## 提交前确认

- [x] 我理解并能解释本次提交的变更。
- [x] 验证结果来自实际执行；未执行项、环境限制和剩余风险已明确标出。
- [x] 本次实际 diff 与 `reviewed_head` / 审查范围一致。
- [x] 阻断性 Review 问题已解决，或已记录明确的 owner 与处理决定。
- [x] 关联 ADR、文档、迁移和兼容性说明与最终代码一致。
