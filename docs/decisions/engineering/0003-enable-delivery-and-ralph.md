# ADR-0003: 启用 Spec Kit Delivery 与 Ralph 协议

- Status: Accepted
- Date: 2026-10-27
- Domain: engineering
- Classification: 约束全仓库的交付路由、证据和 Ralph 执行边界，不属于单一领域包。
- Decision owner: 仓库维护者
- Accepted by / date: 用户于 2026-10-27 明确要求启用 Delivery/Ralph
- Depends on: [ADR-0001](0001-delivery-and-durable-design.md)、[ADR-0002](0002-untrack-historical-feature-artifacts.md)
- Related: [Constitution](../../../.specify/memory/constitution.md)、[AGENTS](../../../AGENTS.md)
- Supersedes: 无
- Superseded by: 无

## Context and drivers

项目已安装 `speckit-delivery` 技能和全局 `speckit.delivery.*` 入口，但项目内没有
`delivery-config.yml`，也没有 Delivery 证据或 Ralph receipt。这个半启用状态让人无法判断
某次交付应当走哪条路线、证据放在哪里、Ralph 是否可以提交或推送。

Constitution 要求 Feature 走 Spec/Plan/Tasks，Bugfix 先有 red evidence，Lightweight
保留窄范围验证；ADR-0002 又规定 Spec 工件只在本地。Delivery 必须在不恢复 Specs 跟踪、
不引入自动远端写入的前提下，把这些规则串成可执行路径。

## Options considered

1. 保持半启用：不改配置，只依赖口头约定。成本最低，但技能入口与项目事实不一致，
   容易把“入口存在”误当成“流程已启用”。
2. 启用项目配置和协议，但保留人工授权边界：路由、证据、receipt 和 gate 明确；
   提交/推送/合并仍需用户逐步授权。采用此方案。
3. 同时启用 hooks、自动提交、自动 push/merge：自动化程度最高，但越过当前权限边界，
   而且质量门和证据门尚未覆盖所有远端场景，风险不可接受。

## Decision

- 项目配置固定在
  [`delivery-config.yml`](../../../.specify/extensions/delivery/delivery-config.yml)，
  记录 artifact policy、context/ADR 路径、验证入口、文档同步、Ralph 上限和集成能力。
- Artifact policy 为 `ephemeral`：`specs/` 继续本地化；Delivery 证据与 ADR 必须自包含，
  不依赖被忽略的 Spec 才能理解。
- Ralph 分支前缀为 `ralph/`；一次只执行一个依赖已满足的任务；默认不并行 Worker；
  每个通过 gate 的任务写 `.specify/delivery/<feature-id>/receipts/<task-id>.md`。
- `RALPH_TASK_GATE: PASS` 必须同时具备有效证据、允许路径、当前 `HEAD` 和
  `QUALITY_VERDICT: pass`、`STANDARDS_VERDICT: pass`。
- Ralph 可以在任务 gate 通过后创建该任务的提交；**不自动 push、不自动 merge、
  不发布、不修改远端设置**，这些动作仍需用户明确授权。
- `.specify/extensions.yml` 和可执行 hook 仍不安装；Delivery 是手动路由 + 协议，
  不是后台自动化。
- 长期证据放在 `.specify/delivery/`、`harness/evidence/` 和 `docs/decisions/`；
  handoff 不引用被忽略的 Spec/Plan/Tasks。

## Consequences and migration

收益是路线、证据路径和执行边界明确，Feature/Bugfix/Lightweight 可以按同一套入口推进；
Ralph 的任务 gate 不再依赖口头判断。成本是配置需要随工具、命令和目录变化同步，
`delivery-config.yml` 的 schema 由本项目维护，不是上游强制格式。

重新评估触发条件：启用 Spec Kit hook、引入并行 Worker、增加发布流水线，或需要外部
协作者直接审阅 Spec 工件时。

## Verification and implementation status

- `scripts/check-governance.ps1` 校验配置存在、关键设置安全（`ephemeral`、`ralph/`、
  不并行、不自动 push/merge、task gate）和引用路径存在；
- Feature 005 的 Spec/Plan/Tasks、Harness evidence 和 review 记录在
  `harness/evidence/phase-01-delivery-enablement.md`；
- 本次不运行完整 Ralph 循环；首次实际交付仍需用户授权。

## Revision history

- 2026-10-27：用户要求启用；采纳“启用配置与协议、保留人工远端授权”的方案。
