# Evidence — Phase 01 Delivery Enablement

## Identity and scope

- **feature_id**: `005-delivery-enablement`
- **phase_id**: `phase-01-delivery-enablement`
- **task_id**: T001–T007
- **base_revision**: `48fb3a73b48b366c1958171217ff0494be907843`
- **head_revision**: `8d9c59c7b3fd961d0b319c1a9628b4a87312fcac`（PR #6 squash 合并提交）
- **working_directory**: `D:\Repos\Github\spawn-join`
- **recorded_at**: 2026-10-27
- **environment**: Windows；PowerShell 7.6.9；uv 0.7.13；PSScriptAnalyzer 1.25.0（临时模块路径）
- **result**: pass (配置、检查器、回归与全量门禁；远端 CI not-run until PR)

## Changed paths

- 新增 `.specify/extensions/delivery/delivery-config.yml`、`.specify/delivery/README.md`；
- 新增 `docs/decisions/engineering/0003-enable-delivery-and-ralph.md` 并更新 ADR 索引；
- `scripts/check-governance.ps1`：校验 Delivery 配置安全设置与引用路径；
- `scripts/test-governance.ps1`：不安全配置拒绝场景（12 场景）；
- `README.md`、`AGENTS.md`、`harness/README.md`、`docs/development/quality-gates.md`：
  Delivery 已启用、hook/自动 push/merge 未启用的表述；
- `harness/evidence/phase-01-static-analysis.md`：再锚定到 `9fab77d`；
- 本 evidence、review 和 `harness/build-log.md`。

`specs/005-delivery-enablement/` 是 Git 忽略的本地 Feature 工件。

## Observed commands

| Command | Exit | Observed result |
|---|---|---|
| `scripts/check-governance.ps1` | 0 | 0 error / 0 warning；Delivery 设置和 8 条引用路径全部通过 |
| `scripts/test-governance.ps1` | 0 | 12 场景；`auto_push: true` 被拒绝 |
| `quality.ps1 -Check static` | 0 | actionlint/PSScriptAnalyzer 0 finding |
| `quality.ps1 -Check docs` | 0 | 52 文件 / 123 目标（含本 evidence 与 review） |
| `quality.ps1`（全量） | 0 | 四包 + 文档 + 治理 + 静态分析 |
| pwsh 7 AST 解析 `check-governance.ps1` / `test-governance.ps1` | 0 | 0 parse error |

## Failed attempts and corrections

- PR #5 以 squash 合并为 `48fb3a7`，静态 evidence 的 `ba8993d` 不再属于 main 历史；
  在 `9fab77d` 重跑静态分析与文档检查后重新锚定，warning 清零。
- 初次编写 delivery 配置校验时，测试夹具缺少 constitution/architecture 等路径，
  负例会同时报告路径缺失；保留该行为，断言聚焦 `auto_push` 安全设置。

## Limitations and blockers

- 本 Feature 不运行完整 Ralph 循环；首次实际交付仍需用户逐步授权提交/推送/合并。
- `.specify/extensions.yml` 和可执行 hook 仍未安装；Delivery 是手动路由 + 协议。
- `delivery-config.yml` 的 schema 由项目维护；检查器只验证安全相关字面设置和路径存在，
  不做完整 YAML schema 校验。
- 远端 CI 尚未运行；PR 推送后需确认并重新锚定。
- 本 evidence 绑定实现提交 `8d9c59c`；后续纯文档提交不触发 freshness warning。

## Remote confirmation

- PR [#6](https://github.com/YanZhiwei/spawn-join/pull/6) 以 squash 合并为 `8d9c59c`；
- PR 运行 `40534650197`、main 运行 `40535092200` 均 14/14 success；
- governance 日志：`0 error / 0 warning`、`Static analysis: 0 failing check(s).`、
  12 场景通过。
