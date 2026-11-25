# Spec Kit Delivery v0.4.10 安装记录

- feature_id: delivery-v0410-upgrade
- phase_id: delivery-v0410-upgrade
- base_revision: 40c194c1d0329d28338dae67a1a2bf318d21a0e7
- head_revision: working-tree
- working_directory: `D:\Repos\Github\spawn-join`
- recorded_at: 2026-11-25
- result: pass

在起始状态干净的 `main` 工作区，将项目已有的 v0.4.9 Bundle 升至 v0.4.10。Windows 使用 Specify CLI 1.2.3（CLI 运行于 Python 3.13.5）。此次操作的持久证据归入 Harness。

## 发布来源与重试

GitHub 于 2026-11-25 22:17（北京时间）发布正式版本。标签对应提交 `a38c02b363fde6c19c52ce2da874b9dd853a6fed`。通过 GitHub CLI 下载 9 个扩展 ZIP、1 个 Bundle ZIP 及标签源码归档。10 个发布资产的大小和 SHA-256 全部与 Release 元数据一致。[上游 Release](https://github.com/YanZhiwei/speckit-delivery/releases/tag/v0.4.10) · [标签提交](https://github.com/YanZhiwei/speckit-delivery/commit/a38c02b363fde6c19c52ce2da874b9dd853a6fed)

按[已有 Bundle 的升级步骤](../../docs/development/spec-kit-delivery.md#从已有-bundle-升级)先备份并在临时项目副本演练，再对目标仓库执行同一套安装命令。三个 Catalog 均固定到 `v0.4.10`，Spec Kit Core 的独立 Catalog 保留原设置。

目标仓库首次运行 `specify bundle update speckit-delivery` 时，GitHub 资产 API 返回 403 限流，命令退出 1。此时 Bundle 记录仍为 0.4.9，磁盘上已有部分更新。通过本机 GitHub CLI 登录仅为重试进程提供下载认证，原生 `bundle update` 退出 0，随后重新登记两个宿主。复核以重试后的磁盘文件及注册清单为准。

## 安装与保留核验

| 核验 | 实际结果 |
| --- | --- |
| `specify bundle list --json` 与两份组件 registry | Bundle 为 0.4.10。9 个自有扩展与 Feature、Bugfix、Lightweight 三条 Workflow 均为 0.4.10。Bug 按 Bundle 固定为 1.0.1，共 13 个组件。 |
| 扩展和 Workflow 文件 | 逐一比对 73 个扩展文件与各自的发布 ZIP 及标签源码，另比对 3 份 Workflow YAML 与标签源码。临时副本和目标仓库各 76 个文件逐字节一致。 |
| `specify integration use codex` → `specify integration use opencode` → `specify integration status` | 三个命令均退出 0。每个宿主登记 30 个扩展入口。两个 `sd` 别名均与各自的完整路由正文一致。两端 Handoff 正文均与新版原生命令一致。默认宿主为 OpenCode。 |
| 安装器前后 SHA-256 | 备份 2,059 个文件。在演练和正式安装后分别核对 1,908 个受保护文件，全部匹配。范围含 8 份扩展配置、共享脚本和核心模板、项目 PR 模板、90 个本地 Spec 文件及 `.specify/delivery/` 下的 1,270 个文件。 |
| 宿主文件诊断 | 与升级前相同，18 个文件带有既有定制，缺失文件、无效清单路径和未检查清单均为 0。`extensions.yml` 保留 `auto_execute_hooks: false` 和 `hooks: {}`。 |
| 重试后的完整性 | 两端共 60 个扩展入口文件与已通过的演练副本逐字节相同。扩展、Workflow、Bundle 和宿主注册数据排除安装及更新时间后逐项一致。 |

哈希比对在安装器完成后、同步项目文档前进行。随后更新安装指南、ADR-0004 的当前固定版本、Harness 双语说明和 build log，并新增本记录。最终复核时，1,908 个原文件中有 1,903 个保持原字节，其余 5 个正是上述项目文档。

## 行为验证

| 命令或场景 | 工作目录 | 退出码 | 实际结果 |
| --- | --- | ---: | --- |
| `python -B -m unittest -v`，使用固定标签的 `test_delivery_runtime.py` 与 `test_delivery_outcome.py` | 临时测试目录 | 0 | 4 项通过。将目标仓库安装的 3 个运行时模块逐字节复制到隔离夹具，使用临时 Git 仓库执行。 |
| `pwsh -NoProfile -File scripts/test-pr-evidence.ps1` | 仓库根 | 0 | 项目现有的 45 个发布证据场景全部通过。 |

四项上游用例覆盖以下行为。

- `test_final_publication_checks_the_actual_commit_without_local_run_state` 验证干净检出可使用 PR 的实际提交核验证据，也会拒绝漏交证据或审查后又改动产品文件的提交。
- `test_runtime_close_record_refreshes_observation_after_success` 验证后续提交和工作区编辑保留已验证的结案状态，证据被改写或缺失时要求重新核验。
- `test_legacy_terminal_label_without_close_proof_remains_snapshot_bound` 验证仅有终态标签的旧记录仍受原快照约束。
- `test_merge_observation_order_uses_instants_and_preserves_offsets` 验证跨时区的观测先后关系，覆盖早于合并和恰好同时两种情况。

## 项目检查

以下命令均从仓库根运行。

| 命令 | 退出码 | 结果 |
| --- | ---: | --- |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | 检查 203 份共享文档和 1,038 个本地链接。 |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 0 | 9 个 Distribution 的覆盖清单一致，0 个错误，3 条既有告警与升级前相同。 |
| `git diff --check` | 0 | Git 提示部分发布文件下次检出时会转换换行符，空白检查通过。另检查新增证据的尾随空白、文件末尾换行和本地链接锚点。 |

三条治理告警均指向历史证据。`delivery-v022-upgrade.md` 落后当前 HEAD 78 个提交，`engineering-governance-integration.md` 和 `pr-delivery-evidence-publication.md` 记录的提交均非当前 HEAD 的祖先。基线首次治理检查受沙箱访问 uv 缓存限制，随后在可访问该缓存的环境执行了升级前后的两次检查。

## Limitations

安装阶段的验证覆盖本机安装、两个宿主的命令登记及离线 Git 场景。真实模型 Workflow、Ralph 和业务包的完整质量矩阵未在本机运行。发布分支的远端 CI 结果可在该升级 PR 的 Checks 中查阅。
