# Phase 01 — Python Quality Gates

**Feature**: `specs/002-python-quality-gates/spec.md`（本地交付工件，不保证随仓库分发）

**Status**: Implemented and locally verified; remote CI / Ruleset not executed

## Approval and source

用户在确认 Black/isort 方案和保留现有修改的人工 SDD 路线后说“好 帮我增加处理”。
来源为 Feature 的 Spec/Plan/Tasks 和 Constitution v1.0.0；本文件不是第二份任务队列。

## Scope / non-goals

范围：共享工具配置、各包 dev 依赖和测试、PowerShell 检查入口、GitHub Actions、文档及证据。
非目标：运行时 API/依赖、Ralph、Delivery 初始化、分支/提交/推送、远端设置、发布与覆盖率门槛。

## Dependencies, paths and blueprint

- 输入：可选固定 Package 与 Check；输出：可见的命令/退出码和 0/非零终态。
- `scripts/quality.ps1` 只拥有检查编排和临时文件，不承担领域逻辑；异常不吞掉。
- `pyproject.toml` 只拥有共享工具策略；包 pyproject/uv.lock 继续拥有独立环境和依赖。
- 正常、错误、零测试、文档链接、构建依赖和隔离安装场景必须验证。
- 依赖 Git、uv、pwsh、Node 和 Python；缺失时报错，不静默跳过。
- 基线不干净已获用户明确批准人工推进；不把本次工作当作 Ralph gate pass。

## Red / green / verification

先记录现有 lock/sync/build 基线，再建立包契约测试和故障 fixture；实现后运行全部门禁、
runner 回归、CodeGraph sync/affected、静态 CI/权限审查、文档和 diff 检查。

本地原始入口见 `specs/002-python-quality-gates/quickstart.md`（干净检出不保证存在）；
共享运行说明见 [质量门说明](../../docs/development/quality-gates.md)。
实际命令和结果保存在 `harness/evidence/phase-01-python-quality-gates.md`，不是在此预写 PASS。

## Security, recovery and stop condition

不使用私有凭据，不写外部系统；CI 只读仓库内容。只清理自建唯一临时目录。
不得删除用户既有修改；失败时保留错误记录并停止完成声明。
完成条件是本机适用检查通过、审查问题关闭、远端/跨平台未执行项被明确标注；不提交、不推送。
