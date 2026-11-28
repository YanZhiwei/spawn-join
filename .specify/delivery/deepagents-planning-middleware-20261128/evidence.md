# Delivery evidence: deepagents-planning-middleware-20261128

- delivery_run: deepagents-planning-middleware-20261128
- lane: feature
- status: active
- evidence_path: .specify/delivery/deepagents-planning-middleware-20261128/evidence.md
- reviewed_head: 9067086b2788a03c544601e43cd758fd4c76c713
- content_fingerprint: sha256:b149cbd597ca9c7f8b75a3da52d75b230b957a612d9ed1731c01feb2f037c03c
- requirements_fingerprint: sha256:ec1d60e3d3eef0368e4a9d788488f7c7863596d5310b82901264cdc88bdb33d6
- pr_body_path: .specify/delivery/deepagents-planning-middleware-20261128/pull-request.md
- pull_request: https://github.com/YanZhiwei/spawn-join/pull/110
- base_revision: 87e809f2b8d405c19d9bced4bfda89d018fa430e
- target_branch: main

## Summary

新增 `spawn-join-agent-deepagents` 的 opt-in supervisor planning seam：

- `PlanningConfiguration` 与 `SupervisorSpec.planning`
- 原生 `TodoListMiddleware` / `write_todos` 接线
- 冲突检测覆盖精确实例、子类、改名实例和同名 middleware
- 默认关闭，未配置时行为不变
- 中英文 README 与 Proposed ADR-0019

## Commits

- `85a611fa` docs(agent): propose planning middleware seam (ADR-0019)
- `eec63828` feat(agent): add opt-in planning configuration (T001)
- `3532edf4` feat(agent): wire opt-in supervisor planning (T002)
- `0abd7884` docs(agent): document planning middleware and fork semantics (T003)
- `9067086b` fix(agent): reject todo middleware subclasses in planning (T004)

## Verification

- `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-agent-deepagents`
  在 HEAD 上 exit 0：format、lint、Pyright strict、336 tests、构建、隔离安装。
- `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` exit 0。
- `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` exit 0
  （3 条既有 harness 证据时效 warning，与本次改动无关）。
- `readme_structure.py --base 85a611f --docs-root docs ...`：`README_STRUCTURE: pass`。
- 独立 Review：T001/T002/T003/T004 与 outgoing-diff 六维 pass，独立性 independent。
- 证据文件：
  - `runtime/quality-outgoing.log`
  - `runtime/docs-outgoing.log`
  - `runtime/readme-outgoing.log`
  - `runtime/review-report-outgoing.md`

## Limitations / accepted follow-up

- README 公共 API 摘要列表尚未列出 `PlanningConfiguration`。
- 中文 middleware 顺序段未同步英文的 supervisor planning 插入说明。
- fork 文档未点明 fork 得到空 todo 列表。
- 缺少同一 `PlanningConfiguration` 多次构建独立实例的显式测试；
  `test_upstream_contract.py` 未钉扎 `TodoListMiddleware` 签名。
- `specs/.../data-model.md` 冲突规则措辞未同步实现；ADR Revision history 未追加
  F1 规则收紧记录。
- 缺少“非 `TodoListMiddleware` 实例但 `.name` 相同”的测试。
- 真实模型的 `write_todos` 行为不在自动化范围；fork 继承属上游 beta 语义。
