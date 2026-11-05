# SpawnJoin Harness

[简体中文](#中文) | [English](#english)

## 中文

Harness 是 SpawnJoin 的阶段执行和证据记录层。它把“批准的阶段计划”“材料性上下文”、
“评审发现”和“实际验证结果”分开保存，帮助维护者区分计划、观察和结论。

### Scope

Harness 是文档约定和可追踪的记录层，不自动创建分支、提交、推送、部署或写外部系统。
Python Quality Gates 已增加独立验证脚本和 CI 配置；它们显式执行机械检查，不是 Harness
或 Spec Kit 自动 hook。只有实际运行的检查才能提供通过证据。

### Source-of-Truth Boundaries

| Artifact | Owns | Must not replace |
|---|---|---|
| `.specify/memory/constitution.md` | 项目级不可妥协原则 | Harness 阶段状态和命令结果 |
| `AGENTS.md` | Agent 工作约定、稳定边界和导航入口 | Feature 计划和实际证据 |
| `specs/<feature-id>/spec.md` | 用户场景、需求、范围和成功标准 | 实际实现结果 |
| `specs/<feature-id>/plan.md` | Feature 技术布局、设计决策和验证方案 | 阶段执行日志 |
| `specs/<feature-id>/tasks.md` | Feature 的唯一执行队列 | Harness 证据或评审签字 |
| `docs/decisions/` | 按领域分类的长期决策理由、关键设计和必要图表 | Spec/Plan/Tasks、正式契约或实际验证证据 |
| `harness/build/` | 一个阶段的批准范围和实施计划 | Feature 的整体 Plan/Tasks |
| `harness/context/` | 阶段中的材料性发现、决策和未决事项 | 逐步进度日志和完整命令输出 |
| `harness/code_review/` | 详细评审发现、修复状态和复核结果 | 自动化测试结果本身 |
| `harness/evidence/` | 绑定真实 revision 和 changed paths 的验证记录 | 预先计划的命令 |
| `harness/build-log.md` | 实际发生的进度和观察到的结果 | 未执行检查的通过结论 |

### Lifecycle

```text
Spec / Plan / Tasks
        │
        ▼
approved phase plan
        │
        ├── phase context
        ├── implementation
        ├── review findings
        └── observed evidence
                │
                ▼
          build log / handoff
```

`tasks.md` 仍然是唯一执行队列。Harness 文件不能通过复制任务清单来创建第二个任务系统。

### Directory Guide

- [`build/`](build/README.md)：阶段计划和人工审批边界；每个阶段独立记录。
- [`context/`](context/README.md)：只记录会影响未来决策、范围、接口、验证或风险的材料性上下文。
- [`code_review/`](code_review/README.md)：记录详细评审发现、严重级别、修复和复核状态。
- [`evidence/`](evidence/README.md)：记录实际命令、工作目录、退出码、结果、revision 和限制。
- [`build-log.md`](build-log.md)：追加式记录实际进度；不把计划内容伪装成已经发生的事实。

### Related Project Documents

- [Constitution](../.specify/memory/constitution.md)
- [Agent rules](../AGENTS.md)
- [Repository map](../docs/architecture/repository-map.md)
- [Package boundaries](../docs/architecture/package-boundaries.md)
- [Architecture decisions](../docs/decisions/README.md)
- [Project technical diagrams](../docs/development/technical-diagrams.md)
- [Python quality gates](../docs/development/quality-gates.md)
- 本地历史 Feature：`specs/001-harness-foundation/`（ADR-0002 已取消跟踪，仅保留本机，干净检出不保证存在）
- 本地质量门任务：`specs/002-python-quality-gates/tasks.md`（Git 忽略，干净检出不保证存在）

### Current Limitations

- 当前有 Black/isort/Ruff/Pyright/pytest 和 CI 配置；远端 CI 已运行，Ruleset 已配置
  required `Quality Gate`，并用临时失败 PR 验证为 `BLOCKED`。
- `.specify/extensions.yml` 已登记 Bundle v0.4.2 组件，但自动 Hook 关闭且无已注册 Hook；
  [Delivery 安装](../docs/development/spec-kit-delivery.md)不代表 Ralph 或完整交付循环已执行。
- `scripts/check-governance.ps1` 校验 Harness/Delivery evidence 元数据、截断 revision、
  build-log 引用、ADR 索引、Spec/Tasks 一致性、Delivery 安全设置和自动 hook 开关；freshness
  在非文档路径变化时告警，语义判断仍需人工评审。
- 如果 `HEAD` 或 outgoing paths 变化，旧 evidence 必须重新确认，不能直接沿用。

许可证见 [LICENSE](../LICENSE)。

## English

Harness is SpawnJoin's phase execution and evidence-record layer. It keeps "approved phase plans",
"material context", "review findings", and "actual verification results" separate so maintainers can
distinguish plans, observations, and conclusions.

### Scope

Harness is a documentation convention and traceable record layer; it does not automatically create
branches, commits, pushes, deployments, or external writes. Python Quality Gates add independent
verification scripts and CI configuration; they explicitly run mechanical checks and are not
automatic Harness or Spec Kit hooks. Only checks that actually ran can provide passing evidence.

### Source-of-truth boundaries

| Artifact | Owns | Must not replace |
|---|---|---|
| `.specify/memory/constitution.md` | non-negotiable project principles | Harness phase state and command results |
| `AGENTS.md` | Agent working conventions, stable boundaries, and navigation | Feature plans and actual evidence |
| `specs/<feature-id>/spec.md` | user scenarios, requirements, scope, and success criteria | actual implementation results |
| `specs/<feature-id>/plan.md` | Feature technical layout, design decisions, and verification approach | phase execution logs |
| `specs/<feature-id>/tasks.md` | the Feature's sole execution queue | Harness evidence or review sign-off |
| `docs/decisions/` | domain-classified long-term decision rationale, key design, and necessary diagrams | Spec/Plan/Tasks, formal contracts, or actual verification evidence |
| `harness/build/` | approved scope and implementation plan for one phase | the Feature's overall Plan/Tasks |
| `harness/context/` | material findings, decisions, and open items within a phase | step-by-step progress logs or full command output |
| `harness/code_review/` | detailed review findings, fix status, and re-review results | automated test results themselves |
| `harness/evidence/` | verification records bound to real revision and changed paths | pre-planned commands |
| `harness/build-log.md` | progress that actually occurred and observed results | pass conclusions for checks not executed |

### Lifecycle

```text
Spec / Plan / Tasks
        │
        ▼
approved phase plan
        │
        ├── phase context
        ├── implementation
        ├── review findings
        └── observed evidence
                │
                ▼
          build log / handoff
```

`tasks.md` remains the sole execution queue. Harness files must not create a second task system by
copying a task list.

### Directory guide

- [`build/`](build/README.md): phase plans and human approval boundaries; one record per phase.
- [`context/`](context/README.md): only material context affecting future decisions, scope, interfaces, verification, or risk.
- [`code_review/`](code_review/README.md): detailed review findings, severity, fixes, and re-review status.
- [`evidence/`](evidence/README.md): actual commands, working directory, exit codes, results, revision, and limitations.
- [`build-log.md`](build-log.md): append-only actual progress; never disguise plans as facts that already happened.

### Related project documents

- [Constitution](../.specify/memory/constitution.md)
- [Agent rules](../AGENTS.md)
- [Repository map](../docs/architecture/repository-map.md)
- [Package boundaries](../docs/architecture/package-boundaries.md)
- [Architecture decisions](../docs/decisions/README.md)
- [Project technical diagrams](../docs/development/technical-diagrams.md)
- [Python quality gates](../docs/development/quality-gates.md)
- Local historical Feature: `specs/001-harness-foundation/` (untracked by ADR-0002, local only; a clean checkout is not guaranteed to contain it)
- Local quality-gate tasks: `specs/002-python-quality-gates/tasks.md` (Git-ignored; a clean checkout is not guaranteed to contain it)

### Current limitations

- Black/isort/Ruff/Pyright/pytest and CI configuration exist; remote CI has run, the Ruleset
  configures a required `Quality Gate`, and a temporary failing PR was verified as `BLOCKED`.
- `.specify/extensions.yml` registers Bundle v0.4.2 components, but automatic hooks are disabled and
  no hook is registered; [Delivery installation](../docs/development/spec-kit-delivery.md) does not
  mean Ralph or the full delivery loop has executed.
- `scripts/check-governance.ps1` validates Harness/Delivery evidence metadata, truncated revisions,
  build-log references, the ADR index, Spec/Tasks consistency, Delivery safety settings, and the
  automatic-hook switch; freshness warns when non-documentation paths change, and semantic judgment
  still requires human review.
- If `HEAD` or outgoing paths change, old evidence must be reconfirmed and must not be reused directly.

See the repository [LICENSE](../LICENSE).
