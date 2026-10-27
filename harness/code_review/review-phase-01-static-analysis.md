# Review — Phase 01 Static Analysis

**Feature**: `004-static-analysis` | **Date**: 2026-10-27

**Base/head**: `2a895da` → `ba8993d`（实现提交）。

## Findings

| ID | Severity | Scope / observation | Status / remediation / verification |
|---|---|---|---|
| SA-001 | Minor | actionlint 参数写成 `-color=never`，实际是 `-no-color` | Resolved：改为 `-no-color`，current repo 通过 |
| SA-002 | Minor | 静态 fixture 没有 Git 仓库，actionlint 找不到项目 | Resolved：fixture 增加 `git init`，3 场景通过 |
| SA-003 | Minor | `Assert-GovernanceResult` 不是 approved verb | Resolved：改名为 `Test-GovernanceResult`，11 场景无回归 |
| SA-004 | Note | PSScriptAnalyzer 未在本地永久安装 | Accepted：本地用临时模块路径；CI 固定版本安装 |
| SA-005 | Note | 静态分析不等于运行时验证 | Accepted：只作为机械门禁，行为仍由测试/评审覆盖 |

## Standards review result

**STANDARDS_VERDICT: pass** for the declared local implementation.

- 单一职责：`check-static.ps1` 拥有工具编排，规则集独立，`test-static.ps1` 拥有夹具。
- 依赖方向：只使用 uvx/actionlint-py 与 PSScriptAnalyzer；不新增 Python 包或运行时依赖。
- DRY：工具版本、规则集和入口各一处；文档引用实现。
- 失败语义：工具缺失或 finding 非零退出；`test-static.ps1` 显式 `exit 0` 避免 CI 复用旧退出码。
- 测试：3 个静态场景；治理 11 场景与门禁 9 场景无回归。
- 副作用：只读；fixture 在 finally 删除；不修改源文件。
- 范围：不扫描第三方技能脚本，不改业务代码或公共 API。

## Verdicts

- `QUALITY_VERDICT: pass`（本地；远端 CI not-run）
- `STANDARDS_VERDICT: pass`

See [evidence](../evidence/phase-01-static-analysis.md) for commands and results.
