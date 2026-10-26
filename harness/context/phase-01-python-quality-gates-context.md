# Phase 01 Context — Python Quality Gates

**Feature**: `002-python-quality-gates` | **Date**: 2026-10-26

- 用户明确选择 Black/isort；Ruff 仅 lint，不启用 formatter/I，避免两套格式化规则竞争。
- 用户批准保留既有修改的人工 Spec/Plan/Tasks 实施，不启用 Ralph、不提交/推送。
- 根 TOML 仅 tool 表；重复的包级 dev group 是独立 Distribution 边界，不提升到共享环境。
- 本机全局 `python` 指向不可用的 Windows alias；所有检查使用 uv 管理的包级解释器，
  不修复用户全局 Python 设置。本机默认解释器是 Python 3.13.5；额外在临时工作树副本中
  使用 Python 3.11.13 完整检查四包，未切换真实包已有环境。uv 0.7.13 和 CI 固定的
  uv 0.13.5 均已本机验证，后者通过临时工具环境运行，不升级用户全局 uv。
- Black 首次实际拒绝 Core `__init__.py` 的多余末尾空行；只删除该空行，API/版本不变。
- 构建采用临时 staging；本地上游用 wheel 安装，第三方运行时依赖从目标包锁导出。
- 源码骨架目前只支持包身份、导入和依赖方向断言；不借此声称业务覆盖率或 100% 测试覆盖。
- 原有 setuptools 包级 README 警告保留，不夹带元数据修复。uv 跨盘 hardlink 回退 copy
  是本机性能警告，不等于检查失败。
- CI 配置及其静态检查不等于 GitHub 实际执行。远端 Ruleset 和 Delivery/hook 仍需后续授权。

本地原始研究：`specs/002-python-quality-gates/research.md`（Git 忽略，不保证随仓库分发）。
共享记录：
[Evidence](../evidence/phase-01-python-quality-gates.md)、
[Review](../code_review/review-phase-01-python-quality-gates.md)。
