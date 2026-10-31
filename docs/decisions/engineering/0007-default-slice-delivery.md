# ADR-0007: 默认启用 Slice 交付

- Status: Accepted
- Date: 2026-10-31
- Domain: engineering
- Classification: 本决策约束全仓库 Feature 的评审与合并边界，属于交付治理。
- Decision owner: 仓库维护者
- Accepted by / date: 用户 2026-10-31 明确要求默认开启并批准 S0–S3 切片计划
- Depends on: [ADR-0003](0003-enable-delivery-and-ralph.md)、[ADR-0004](0004-release-managed-delivery-installation.md)
- Related: [Delivery 配置](../../../.specify/extensions/delivery/delivery-config.yml)、[ADR-0006](../llm-provider/0006-langchain-first-llm-runtime.md)
- Supersedes: 无；本 ADR 只改变 ADR-0004 中“单 PR 运行选择”这一项，不替代其固定 Release 安装决策
- Superseded by: 无

## Context and drivers

Bundle v0.2.2 已提供 `speckit.delivery.slice`、`slices.md`、Slice Gate 和
`pr_slicing`/`merge_policy` 配置。此前项目显式设置 `pr_slicing: "off"`，以单 PR 路径匹配
仓库的线性历史要求。该选择记录在 ADR-0004 和 Delivery 配置中。

当前需求发生变化：

- 维护者要求默认启用 Slice 交付，而不是每个 Feature 都手工决定是否切片。
- 仓库仍要求线性历史；不能使用需要最终 merge-commit rollup 的 integration 交付。
- `stack_provider: manual`、`use_queue: false` 保持不变；本仓库没有原生 Stacked PR 或
  Merge Queue，不能声称具备这些能力。
- `tasks.md` 必须继续是唯一执行队列；`slices.md` 只能划分评审/合并边界，不能增删或重排任务。

## Options considered

1. **保持 `pr_slicing: "off"`**
   单 PR 最简单，但不利于独立评审和合并边界；每次 Feature 都需要重复判断是否切片。

2. **`pr_slicing: "auto"`（采用）**
   默认让 Slice 命令根据任务和依赖派生切片；当所有切片都是 `standalone` 或 `flagged` 时使用 stacked，
   逐个 squash 到 `main`。需要 integration 时仍由命令返回 `needs_decision`，不静默选择
   与线性历史冲突的最终 merge commit。

3. **`pr_slicing: "stacked"`**
   强制 stacked；对必须使用 integration 的变更会制造策略冲突，灵活性低于 `auto`。

4. **`pr_slicing: "integration"`**
   需要 integration 分支和最终 merge-commit rollup，与当前 required linear history 冲突；
   不采用。

## Decision

- 项目配置改为 `pr_slicing: "auto"`。
- 所有切片均为 `standalone` 或 `flagged` 时使用 stacked：每个切片按顺序 squash 到 `main`，
  保持线性历史。
- `integration` 交付仍需单独策略评审；在仓库允许 merge-commit rollup 前不得启用。
- `stack_provider: manual`、`use_queue: false`、`delete_branch: true` 保持不变；不声称具备
  原生 Stacked PR 或 Merge Queue。
- `slices.md` 只记录切片边界；`tasks.md` 仍是唯一执行队列。
- 引入本策略的 Feature 可以先以一个策略切片（S0）落地；S0 是策略生效前的 bootstrap PR，
  之后的切片按 stacked 顺序交付。S0 不授权自动 push、创建 PR 或 merge。

## Key design and diagrams

```text
Feature tasks.md
      │
      ▼
speckit.delivery.slice
      │  pr_slicing=auto
      ▼
S0 policy → S1 contract → S2 consumer → S3 verification
      │          │             │             │
      └── squash ┴── squash ───┴── squash ───┘
                    main (linear)
```

约束：

1. 每个任务必须且只能映射到一个切片。
2. 每个切片的 prefix 必须在目标分支上可构建、可测试；没有证据时不得标记 `standalone`。
3. stacked 切片按顺序合并；若某个中间切片失败，后续切片不得继续合并。
4. `integration`、merge queue 或原生 stack provider 的能力不在本决策中授权。
5. 任何自动 push、PR 创建或 merge 仍需用户单独授权。

## Consequences and migration

收益：

- 默认获得更小的评审单元和更清晰的回滚边界。
- 不再需要每个 Feature 手工决定是否启用切片。
- 线性历史保持不变；每个切片使用 squash。

成本与限制：

- 增加 PR 数量和协调成本；`stack_provider: manual` 意味着分支/PR 需要人工顺序管理。
- 策略变更本身需要先落地（S0），因此第一个 Feature 会有一个 bootstrap 单切片。
- 不是所有变更都适合 stacked；需要 integration 时必须重新评审策略，不能强行套用。

迁移：

- 配置从 `off` 改为 `auto`；AGENTS、Delivery 说明和 ADR-0004 的历史注记同步更新。
- 既有 Feature 若已按单 PR 执行，不追溯拆分；新 Feature 默认按 Slice 计划执行。
- 不修改 Bundle 安装文件、生成命令或上游模板。

## Verification and implementation status

本 ADR 的 Accepted 只表示策略方向已获维护者批准；S0 的实际命令与退出码记录在 Delivery
evidence 中，不把 ADR 状态当作机器验证结果。

S0 必须验证：

- `.specify/extensions/delivery/delivery-config.yml` 可解析，`pr_slicing` 为 `auto`；
- `slices.md` 记录的 S0–S3 计划与 `pr_slicing: "auto"` 配置一致；本机未执行独立的
  slice CLI receipt，不把计划文本当作命令执行证据；
- `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` 通过；
- `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` 通过；
- ADR 索引、AGENTS、Delivery 说明和 ADR-0004 历史注记一致。

实际 stacked PR 的创建、push 和 merge 不在本 ADR 的验证范围；它们需要单独授权。

## Revision history

- 2026-10-31：维护者要求默认启用 Slice 交付，提出 `pr_slicing: "auto"` 候选决策。
- 2026-10-31：维护者批准 S0–S3 切片计划，ADR 由 Proposed 改为 Accepted；固定 Release、
  来源和权限边界不变。
