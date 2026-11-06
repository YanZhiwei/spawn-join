# Delivery evidence — v0.4.5 与治理文档 PR

- **delivery_run**: delivery-v044-governance-context-20261107
- **feature_id**: delivery-v044-governance-context-20261107（Lightweight 证据标签，不是新 Feature）
- **lane**: lightweight
- **phase_id**: outgoing-pr
- **evidence_path**: .specify/delivery/delivery-v044-governance-context-20261107/evidence.md
- **base_revision**: e292f0e3b746fec266e71dca142fc20356841978
- **head_revision**: working-tree
- **reviewed_head**: e292f0e3b746fec266e71dca142fc20356841978
- **original_pr_head**: pending
- **pull_request**: pending
- **recorded_at**: 2026-11-07
- **working_directory**: C:\Users\YanZh\.local\share\opencode\worktree\86e56b\mighty-harbor
- **content_fingerprint**: sha256:98e29d87e5dc59750ee86a858d4692afb56dedaf4ab106bc6216ef1c0a0c0a84
- **requirements_fingerprint**: sha256:3e0c2cebd8bf6944e6c8ee1262750ee35a73b6bbcabdb6a3383a14c99cc2ab8f
- **method_identity**: builtin
- **result**: pass — 本节记录提交前初轮独立 Review 的真实快照；后续修正、提交和发布仍须复核对应身份

## 范围与授权

用户要求升级到 v0.4.5 后创建 PR，并保留已完成的 SD/Harness 治理优化。范围为固定 Release
组件/Catalog、静态 PR 模板、角色导航、Context/Review 中英文指南及实际 evidence。未改包源码、
依赖、公共 API、数据、权限或 Hook。无需 Feature Spec/Plan/Tasks，不增加审批或执行队列。

当前 run 为此前 PR 请求创建，名称含 v044 仍保留同一身份；在 v0.4.5 后继续，不重置预算。
此前被中断的独立 Review 没有报告；它不是通过轮次。安装的权威事实位于 Harness 的
`harness/evidence/delivery-v045-upgrade.md`；本文件仅拥有 PR 的验证/交接身份，不复制安装流水。

## 历史验证快照 — 提交前

`reviewed_head` 为检查时实际 HEAD，检查对象还包含当时未提交的 51 个实际变更路径，
以内容/要求指纹区别于该基准原始树。算法：按路径排序的 UTF-8 canonical JSON，记录每个
path/mode/raw SHA-256/Git-normalized blob，再做 SHA-256；清单和原始执行 receipt 在本 run
本地 `runtime/review-manifest.json` 和各 ticket 文件。native runtime 另绑定 HEAD/index/worktree
及显式请求来源。runtime/reviews/receipts、本 canonical evidence、PR 正文属于声明的 bookkeeping；
无候选 Simplify 报告按 runtime 契约作 no-op，不从要求中排除生产/测试/策略文件。

| 检查 | 实际结果 | 证据归属 |
|---|---|---|
| 项目 docs | exit=0，63 文件 / 322 本地目标 | 当前 Quality ticket 原始日志 |
| 项目 governance | exit=0，0 errors / 1 历史 warning | 当前 Quality ticket 原始日志 |
| 项目 static | exit=0，0 failures | 当前 Quality ticket 原始日志 |
| governance regression | exit=0，26 场景 | 当前 Quality ticket 原始日志 |
| 安装内容/配置 | 73 个上游文件、13 组件、39 命令和模板一致；164 个定制路径保留 | Harness v0.4.5 evidence |
| 上游 runtime / distribution | 实际 37 / 67 项测试通过 | 同一安装 evidence、固定上游 Tag |
| Standards | pass，现有职责/权限/依赖/规则保留 | 本 run 原生 standards-current.md |
| 独立六维 Review 1 | pass，完整复核 51 路径/496 输入哈希；1 个非阻断 minor | 本 run reviews/review-1.yml 与原始 reviewer 会话 |
| Simplify | none，无额外候选 | 本 run 原生 simplifications.md |
| Package README | 无变更面，no-op 有具体原因 | 本 run admission.md |

初次 Quality 的 governance exit=1（本次 v0.4.5 evidence 的中文限制标题未被机器识别），
blocked receipt 保留；修正为 `Limitations` 标题后实际重跑通过，不用新哈希冒充旧成功。

初轮独立 Review 的唯一发现 `D045-DOC-001` 为 ADR-0004 新履历中两个字面 `+`，minor、
非阻断；已仅删除这两个前缀，初轮报告保留原样。本快照不把已修改当作 reviewer 已关闭，
提交后的原生检查和同一 reviewer 将核对新内容/要求身份再独立确认关闭。完整原始报告在
本地 reviewer 会话，`review-1.yml` 是 coordinator 保留的结构化摘要，无删改发现或 verdict。
本次 Review 的第一次机器封装遗漏 Quality/Standards dependency receipts，被 helper 拒绝；
补齐准确的当前原始依赖后 record/require 通过，没有绕过验证或改写检查结果。

## Limitations

此提交前快照尚未观察远端 PR、CI 或合并结果，不能读成当前终态。包未变，未重跑五包矩阵；
真实 SD/Ralph、模型 eval、多宿主交接效果未验证。已有 32 个 managed files 定制提示及
v0.2.2 evidence freshness warning 保留，均非本次新增失败。原生 reports/runtime/PR 正文为
本机 ephemeral 工件，不能当作 GitHub 上的可用链接；本记录保留自包含结果摘要。

只有当前独立 Review 完成、机器守门通过、提交/发布内容身份核验后才创建 PR；不合并。
后续修改 head/内容需重新确认对应 evidence，不改写此前原始报告或冒充用户审阅。
