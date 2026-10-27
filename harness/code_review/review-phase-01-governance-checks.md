# Review — Phase 01 Governance Checks

**Feature**: `003-governance-checks` | **Date**: 2026-10-27

**Base/head**: `c5ad576` + uncommitted worktree.

## Findings

| ID | Severity | Scope / observation | Status / remediation / verification |
|---|---|---|---|
| GC-001 | Minor | 目录链接被 `git check-ignore` 误判为 local-only（`packages/*/`、`.specify/`） | Resolved: 目录只校验存在，文件才检查忽略状态；第三方 `.agents/skills/` 文档排除 |
| GC-002 | Minor | StrictMode 下标量对象没有 `.Count` | Resolved: 对管道结果使用 `@(...)`；重复任务 ID 场景通过 |
| GC-003 | Minor | 浅克隆缺少历史会让 SHA 校验失败 | Resolved: 浅克隆降为 warning；CI governance checkout 使用 `fetch-depth: 0` |
| GC-004 | Note | 旧 evidence 的 head 落后 HEAD | Accepted: 只 warning；清理属于后续优先级 2 |
| GC-005 | Note | 治理检查不判断 evidence 语义 | Accepted: 结构门禁与 Standards Review 分工，不替代人工判断 |

## Standards review result

**STANDARDS_VERDICT: pass** for the declared local implementation.

- 单一职责：`check-governance.ps1` 拥有规则，`quality.ps1` 只调度，`test-governance.ps1`
  拥有失败夹具。
- 依赖方向：只依赖 PowerShell 7 与 Git，无新增包、网络或外部服务。
- DRY：evidence 字段、ADR 状态和结果词表各只定义一次；文档引用实际实现。
- 失败语义：诊断格式 `ERROR: path: message`，退出码 0/1；freshness 只 warning。
- 测试：9 个治理场景覆盖结构、索引、链接、缺失日志和状态矛盾；原 9 个门禁场景无回归。
- 副作用：只读；不写源文件、不 stage、不 commit；临时 fixture 在 finally 删除。
- 范围：未恢复 specs 跟踪，未启用 Delivery/Ralph，未修改 Python 源码或远端设置。

## Verdicts

- `QUALITY_VERDICT: pass`（本地检查与回归；远端 CI not-run）
- `STANDARDS_VERDICT: pass`

See [evidence](../evidence/phase-01-governance-checks.md) for commands and results.
