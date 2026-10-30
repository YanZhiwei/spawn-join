# ADR-0004: 以固定 Release 管理 Delivery 安装

- Status: Accepted
- Date: 2026-10-28
- Domain: engineering
- Classification: 约束仓库交付工具的来源、宿主入口和升级方式，属于工程治理。
- Decision owner: 仓库维护者
- Accepted by / date: 用户在 2026-10-28 合并 PR #8，接受 Bundle v0.1.1 接入与治理方案
- Depends on: [ADR-0001](0001-delivery-and-durable-design.md)、[ADR-0002](0002-untrack-historical-feature-artifacts.md)、[ADR-0003](0003-enable-delivery-and-ralph.md)
- Related: [安装说明](../../development/spec-kit-delivery.md)
- Supersedes: 无；拟更新 ADR-0003 的手动接入实现，不改变其权限和证据边界
- Superseded by: 无

## Context and drivers

基准 `fdd0c072186ef3cea7f4b3261acd1d82b358ef56` 有项目级拷贝门面和自定义配置，
但没有登记 Delivery 扩展，Workflow 只有基础 speckit；用户级旧技能不能证明项目安装状态。
维护者要求采用已发布产物，避免入口、源码副本与实际命令版本漂移。

## Options considered

1. 保留拷贝或从相邻仓库 `--dev` 安装：依赖本机状态，不符合固定 Release 的要求。
2. 使用 v0.1.0 Bundle：预期最简，但隔离验证中 CLI 1.2.3 拒绝 Workflow Catalog 与
   YAML 的 requirements 不一致；官方示例 CLI 0.16.4 也因 Workflow 来源解析失败而中止。
3. 先用原生组件安装命令完成 bootstrap：八个 v0.1.0 扩展 ZIP 与三个 v0.1.0 Tag
   Workflow，由 CLI 校验、登记和渲染。该路径用于 v0.1.0，不登记虚假的 Bundle 回执。
4. v0.1.1 发布后迁移到 Bundle：修复 Catalog requirements，使用 Bundle 管理 12 个组件，
   同时以 `--keep-config` 保留项目配置和核心任务定制。最终采用此方案。

## Decision

- 保留 Specify CLI 1.2.3，使用 v0.2.2 发布 Catalog；Bug 使用该 CLI 随附的 1.0.1。
- 当前交付组件由 v0.2.2 Bundle 管理；逐组件 v0.1.0 仅保留为历史 bootstrap 记录。
- OpenCode 作为当前默认集成，保留已安装 Codex 与项目任务模板/技能定制。
- 删除本项目手工拷贝的 sd、speckit-delivery 门面；不删除用户级共享文件或 Fireworks。
- 配置由项目拥有，组件与原生命令由安装器/Bundle 管理；升级须重查来源、差异和定制保留情况。
- Specs 继续本地化，ADR 根保持不变；串行 Ralph、证据要求和禁止自动远端写入不变。
- 安装扩展不授权执行 Hook、Ralph、提交、推送、合并或发布。Hook 自动执行保持关闭。

## Key design and diagrams

公开 Release/Tag -> CLI 校验和登记 -> 项目原生命令 -> 项目 Quality Profile ->
既有质量脚本 -> Harness evidence。此迁移不增加业务依赖、公共 API 或领域源码。
原生完整命令是权威入口；不再维护另一份生命周期 Prompt。

## Consequences and migration

安装可追溯且不依赖相邻源码，但需要跟踪 Bundle/组件版本与项目配置差异。v0.1.0 的
分发问题已由 v0.1.1 修复；v0.1.2 增加 Diagram 扩展和代码上下文步骤，不改变授权、
证据或禁止自动远端写入的边界。v0.1.3 增加范围取证、有界修复复审及快照绑定的独立 Review，
仍不授权自动执行。v0.2.0/0.2.1/0.2.2 增加 Slice 边界、合并策略、Handoff 正文落盘和
中文兜底 PR 模板，但 Publish/Merge 仍需单独授权；项目选择单 PR 路径时不启用
Stacked/Integration。不得用修改发布文件或降级全局 CLI 掩盖未来漂移。升级 Release 或
改变宿主时重新执行隔离验证。用户级旧入口保留供其他项目使用，本项目使用 Bundle 管理的
项目级命令。

## Verification and implementation status

隔离项目已验证 v0.1.1 发布 Catalog 的 Bundle 安装和定制保留；目标仓库已从 v0.1.0
逐组件安装迁移到 v0.1.1 Bundle，Bundle 记录拥有 12 个组件，配置和核心任务定制哈希
保持不变。PR #8 已合并为 `2b8b70d`，main 的 Quality 运行 14/14 成功。
v0.1.2 发布后，目标仓库通过 `bundle update` 升级到 13 个组件（新增 Diagram），六个
扩展配置、核心任务技能和任务模板哈希不变；OpenCode 原生命令由 31 个增加到 33 个。
验证结果记录在 [安装 evidence](../../../harness/evidence/delivery-release-installation.md)。
v0.1.3 经隔离副本验证后通过 `bundle update` 安装，仍为 13 个组件，原生命令 33 → 35；
配置与核心任务定制未变。安装一致性验证与 Doctor 的环境/上游路径阻塞分别记录在
[升级 evidence](../../../harness/evidence/delivery-v013-upgrade.md)。
v0.1.4 为 Doctor Reviewer 路径补丁，经隔离副本验证后安装在 v0.1.3 之上；组件数、命令面
和配置契约不变，环境阻塞仍单独保留。记录见
[v0.1.4 evidence](../../../harness/evidence/delivery-v014-upgrade.md)。
v0.2.0 增加 Slice 计划、Slice Gate 和合并策略；v0.2.1 增加 Handoff 正文落盘与
`PR_BODY_PATH` 契约，并让静态 PR 模板安装保持显式 opt-in；v0.2.2 把随包兜底 PR 模板改为
中文。项目保持 `pr_slicing: "off"` 的单 PR 路径，`stack_provider: manual`、
`use_queue: false`、`final: squash`，以匹配仓库 required linear history；PR 模板使用
v0.2.2 中文兜底及其 `.github` 静态副本。记录见
[v0.2.2 evidence](../../../harness/evidence/delivery-v022-upgrade.md)。
本 ADR 的 Accepted 只表示决策获批；不声明真实 Ralph 循环已运行。

## Revision history

- 2026-10-28：根据用户要求提出固定 Release 组件安装方案，记录 Bundle 的实际失败路径。
- 2026-10-28：`speckit-delivery` 源码已对齐 Workflow Catalog requirements、增加分发契约
  校验和 Bundle 安装回归，并将 Bundle 最低 CLI 设为 1.2.3；v0.1.0 Tag 未改变，仍需新
  Release 后复核，因此本 ADR 保持 Proposed。
- 2026-10-28：v0.1.1 已发布并验证公开 Catalog/Bundle 安装；SpawnJoin 已迁移到 Bundle
  0.1.1，配置与核心定制保留。
- 2026-10-28：PR #8 合并为 `2b8b70d`，main Quality 14/14 成功；ADR 由 Proposed 改为
  Accepted。
- 2026-10-28：v0.1.2 发布后，目标仓库以 `bundle update` 升级到 13 个组件；配置与
  核心定制哈希不变，原生命令 31 → 33，ADR 决策不变。
- 2026-10-29：按维护者要求升级固定 Release 至 v0.1.3；隔离验证、配置保留与来源边界不变，
  保留 Doctor 阻塞，不以安装完成替代交付就绪。
- 2026-10-29：升级至 v0.1.4，修复 Doctor 的 Reviewer 模板引用；来源、授权和证据边界不变。
- 2026-10-30：升级至 v0.2.1，接入 Slice 计划/Gate 与 Handoff 正文路径；项目显式保持
  单 PR 线性历史策略，既有 PR 模板和核心定制保留。
- 2026-10-30：升级至 v0.2.2，使用随包中文 PR 模板及其 `.github` 静态副本；组件数、
  命令面和权限边界不变。
