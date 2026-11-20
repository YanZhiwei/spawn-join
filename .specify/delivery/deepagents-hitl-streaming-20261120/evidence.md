# DeepAgents 原生流式 HITL 交付证据

- **delivery_run**: deepagents-hitl-streaming-20261120
- **lane**: lightweight
- **evidence_path**: .specify/delivery/deepagents-hitl-streaming-20261120/evidence.md
- **base_revision**: 069517e4956d4d4954ff62191bbd6aeaf3ed6dfd
- **reviewed_head**: 069517e4956d4d4954ff62191bbd6aeaf3ed6dfd
- **original_pr_head**: pending
- **content_fingerprint**: 80f3fe7609ec0bd65864be8fddb7c8c13e8a431858b7fe0fa43caf7ffa3c3de4
- **requirements_fingerprint**: 52aa04d04bb342bebb8d59f76e501134479c371a73317963d7dab9b9b523ea58
- **method_identity**: builtin
- **pull_request**: pending
- feature_id: deepagents-hitl-streaming-20261120
- phase_id: verification
- head_revision: 069517e4956d4d4954ff62191bbd6aeaf3ed6dfd
- merge_base: 069517e4956d4d4954ff62191bbd6aeaf3ed6dfd
- working_directory: D:/Repos/Github/spawn-join
- recorded_at: 2026-11-20T08:06:16Z
- result: pass

## 已评审范围

用户批准在 `spawn-join-agent-deepagents` 补充原生流式 HITL 回归、离线示例和双语接入说明。此 Lightweight 快照由 `docs/deepagents-hitl-streaming` 的工作区提供。测试和示例使用宿主提供的内存 checkpointer、同一 `thread_id`、原生图和已有 HITL helpers。

| 路径 | 可验证交付 |
| --- | --- |
| `packages/infra/agent-deepagents/tests/test_interrupts.py` | 真实图的 batched 顺序与 per-call 中断 ID 恢复。审批前执行零次，恢复后仅获批调用执行一次。 |
| `packages/infra/agent-deepagents/examples/hitl_streaming.py` | `astream` 读到审批请求，提交一项批准及一项拒绝并同进程恢复。 |
| `packages/infra/agent-deepagents/README.md` | 中文运行命令和两种模式的接入说明。 |
| `packages/infra/agent-deepagents/README.en.md` | 对等英文说明。 |

内容指纹是 Delivery runtime 对 Git index、工作区的路径、模式、内容哈希及绑定请求计算的 SHA-256。变更文件的原始字节清单保存在本地 `runtime/reviewed-paths.json`，清单 SHA-256 为 `e6cd3cf04979a0e04f1786d35062ec346207cb18f6f6d05b3f8d615cf2e99e07`。需求指纹是本地 `runtime/requirements-manifest.json` 的 SHA-256，覆盖指定范围、适用策略、ADR 和 builtin 评审方法。原始快照包含当时尚未跟踪的示例。

## 验证快照

工作目录为仓库根目录。包级检查和示例在 Windows、Python 3.11.13、uv 0.7.13、Node 22.17.0 执行。锁定依赖为 DeepAgents 0.7.32、LangChain 1.4.8、LangGraph 1.2.19。检查使用 `UV_PYTHON=3.11` 和 `UV_LINK_MODE=copy`，模型追踪关闭，构建使用隔离的临时目录。

| 命令 | 退出码 | 结果 |
| --- | --- | --- |
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-agent-deepagents` | 0 | 锁与环境、Black/isort/Ruff、Pyright 零错误、206 项测试、文档链接、wheel/sdist、隔离安装、依赖和导入检查通过。 |
| `uv run --locked --directory packages/infra/agent-deepagents python examples/hitl_streaming.py` | 0 | 两个审批请求，审批前执行列表 `[]`，恢复后 `['keep']`，最终响应 `Review complete.`。 |
| `git diff --check` | 0 | 通过。 |
| `py -3 -B .specify/extensions/docs-sync/scripts/readme_structure.py README.md --base 069517e4956d4d4954ff62191bbd6aeaf3ed6dfd --docs-root docs` | 0 | 根 README 结构通过。包 README 的 HITL 小节已同步更新。 |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | 151 份文档和 414 个本地目标通过检查。 |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 0 | 快照初检和证据写入后均为零错误。各报告一条 `harness/evidence/delivery-v022-upgrade.md` 历史版本告警。 |

前三项原始命令、工作目录、配置指纹、原始日志、执行时间与退出码由 Quality ticket `7ce1b069b03d4f07b199e9b987070a78` 保存在本地 `runtime/`。环境、日志和检查回执已按内容校验。包级工作完成后，隔离构建目录已清理。

## 标准与评审

- `QUALITY_VERDICT: pass`，`STANDARDS_VERDICT: pass`。范围集中在该包的测试、仓库示例和双语说明。宿主职责遵循 ADR-0010 与 ADR-0014 所述边界。
- `REVIEW_VERDICT: pass`。独立评审验证了需求、代码质量、架构、正确性、安全与兼容性、测试有效性。阻塞项和修复轮数均为 0。
- 原始独立报告在本地 `reviews/outgoing-diff/review.yml`，SHA-256 为 `98c7a830776d88f888a5cfca0dfd26ac661dd57ed4febbe4d4a4995b80c68779`。机器回执位于本地 `runtime/native-receipt-review-9c2468343bbc42038b65bd5337b014e0.json`，SHA-256 为 `e03e816d02702220bb4c008a0a7f72f82332e5b85a9b93ece853ba63cdba654c`。
- 用户对已呈现报告、范围和路径清单选择「批准交付」。同一快照的 `review` 决定已记为 `approve`，决定后再次通过 runtime Review guard。

## 发布前提交对应关系

2026-11-20，用户授权「创建pr」。四个产品路径已提交为 `a06b4c344e4106d5fc2de4528db796e5ff92aa1c`，其父提交是本记录的 `base_revision`。逐文件复核显示，工作区原始字节与已批准 Review 清单相同，Git blob 与这些原始字节经 CRLF→LF 规范化后的内容完全一致。该转换来自仓库已有的 `core.autocrlf=true`，正文与运行行为保持一致。

已保存从 base 到该产品提交的真实 Git binary diff，路径、模式、正文可由 Git 提交独立核验。归档 SHA-256 为 `be109f19f1abde86992635e8bcd5cb93d82ccea716a583f747e45047dbe061c9`，本地归档位置为 `runtime/reviewed-diff-prepublication.patch`。本记录的初始 `reviewed_head` 与原始评审报告保持不变；发布前会在最终提交上重新确认 Quality、Standards 与独立 Review，实际发布身份由观察到的 PR head 单独绑定。

## Limitations

- 本快照的执行覆盖 Windows 和锁定 Python 3.11。跨平台矩阵和远端 `Quality Gate` 由发布后的 GitHub Actions 验证。
- 恢复验证基于同进程 `InMemorySaver` 与离线模型。实际宿主管理审批记录与持久化。
- 本机 shell 缺少用于派发 Workflow 命令的 `opencode` 可执行文件。本次在当前会话按已安装 v0.4.7 Lightweight 的命令契约执行，使用同一 runtime 记录并校验 owner 回执和人工决定。
