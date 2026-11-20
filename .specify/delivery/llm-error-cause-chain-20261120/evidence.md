# 模型错误原因链修复证据

- feature_id: llm-error-cause-chain
- phase_id: handoff
- base_revision: 0535e68d49173672de0593b8e7899dc9d5789da7
- head_revision: 0535e68d49173672de0593b8e7899dc9d5789da7
- working_directory: D:/Repos/Github/spawn-join
- recorded_at: 2026-11-20
- result: pass
- limitations: 本快照为提交前 Windows/Python 3.11 离线验证；真实 Provider 与未来 PR 的远端 CI 未计为通过，发布身份另行核对。
- **delivery_run**: llm-error-cause-chain-20261120
- **lane**: bugfix
- **evidence_path**: .specify/delivery/llm-error-cause-chain-20261120/evidence.md
- **exploration_path**: .specify/delivery/llm-error-cause-chain-20261120/exploration.md
- **base_revision**: 0535e68d49173672de0593b8e7899dc9d5789da7
- **reviewed_head**: 0535e68d49173672de0593b8e7899dc9d5789da7
- **content_fingerprint**: SHA-256 92e94d224b6b74bb6591506cc42e35953bc51a968ccd1de7ad86186f8ef270d9
- **requirements_fingerprint**: SHA-256 76f7ec7d0a7671b08cfc5a621dff71257c355ff096e9537b4065664d8e6b89cb
- **method_identity**: builtin
- **original_pr_head**: pending
- **bug_slug**: llm-error-cause-chain
- **assessment_path**: .specify/bugs/llm-error-cause-chain/assessment.md
- **assessment_hash**: SHA-256 f3bf5b4b116ab4d749e600b60404918f54ec1e14ce0d8d46a463cb36e440add6
- **pull_request**: pending

## 范围和审批

用户在正式 Assessment gate 批准修复模型错误的原因链。产品改动只有
`packages/infra/agent-deepagents/src/spawn_join_agent_deepagents/middleware/llm_error_normalization.py`
和 `packages/infra/agent-deepagents/tests/test_llm_errors.py`。
同步和异步入口原样抛出已有 `LLMCallError`；首次归一化继续使用原分类和安全文案。
无需新增 Feature 工件、依赖、配置、公共 API 或 ADR。

## Red 与回归

Windows/Python 3.11.13，DeepAgents 0.7.32、LangChain 1.4.8、LangGraph 1.2.19。
通过 `build_supervisor` 返回的真实原生图使用离线模型，修复前 `invoke` 和 `ainvoke`
均为 `same_error=True, preserved_cause=False, self_cause=True`，探针退出 1。
新回归用例在修复前为 6 failed / 24 passed，失败断言是原始原因身份。
修复后为 30 passed；两条原生图入口都保留原原因且无自引用，探针退出 0。
Agent 包全套 211 项测试、Ruff 与 Pyright strict 已通过。

## 提交前历史验证快照

本节绑定 `reviewed_head=0535e68d49173672de0593b8e7899dc9d5789da7` 及当时两个产品文件
尚未提交的工作区字节。`HEAD` 本身不是修复内容，准确 reviewed 内容由上述指纹和
本地 `runtime/reviewed-product-paths.json` 定义。实际 binary diff 的 SHA-256 为
`51eb8da07cc93d3afdf1fef19a1d0f2bacf3178194720a181c95a432a594779f`，
归档于 `runtime/reviewed-product-diff.patch`。提交后必须对真实发布 HEAD 重新核对。

以下命令均从 `D:/Repos/Github/spawn-join` 实际执行：

| 命令 | 退出码 | 结果 |
| --- | --- | --- |
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-agent-deepagents` | 0 | 锁与独立环境、Black/isort、Ruff、Pyright strict、211 项测试、wheel/sdist、隔离安装、pip check 与隔离导入通过。 |
| `packages/infra/agent-deepagents/.venv/Scripts/python.exe -B .specify/delivery/llm-error-cause-chain-20261120/runtime/reproduce.py` | 0 | 同步和异步原生图均保留原错误与原原因，无自引用。 |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | 151 份文档、414 个本地目标通过。 |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 0 | 0 errors / 1 条既有 `delivery-v022-upgrade.md` freshness warning。 |
| `git diff --check` | 0 | 无空白错误。 |

质量命令使用 `UV_PYTHON=3.11`、`UV_LINK_MODE=copy`，追踪关闭；构建在独立临时目录，
结束后目录已清理。原始执行回执包括起止时间、输入/配置指纹、命令和原始日志 SHA-256；
shell 超时发生在前三项成功之后，恢复未改变它们的原 ticket 或时间。

治理初检拒绝了本记录草稿的 `result: pending` 和中文验证边界标题：项目要求结果使用
`pass|fail|blocked|skipped|not-run` 并存在 `limitations` 字段或对应英文章节。
该失败和 blocked Quality 原记录均保留；修正元数据后治理复验通过，产品代码未追加修复。

## 标准、独立评审和人工批准

- `QUALITY_VERDICT: pass`，ticket `757e810f8031462c9415a73fcb127622`。
- `STANDARDS_VERDICT: pass`，ticket `26e5494ea3324e10b736f5d778d11820`，
  检查模块拥有者、复用、类型、异常传播、依赖方向、范围与文档适用性。
- 独立 `REVIEW_VERDICT: pass`，ticket `206e4ac7b8cb45d9946918ce7f0a2116`。
  六维完整覆盖，零 findings；独立上下文重建代码和要求指纹并校验原始 Quality 回执。
  原始报告保留在 `reviews/outgoing-diff/review.yml`，SHA-256
  `30427d79b187c9877d315a90b50b188a0b19bcfa52c7be97389a71ebd9b2db79`。
  Native receipt SHA-256 为
  `85c7332ae16849912054a25b5f169920e0d38f07ff3775b2a0f449c64ecbc370`。
- runtime `require --kind review` 返回 ready，`needs --kind repair` 为 false。
  当前无 repair reservation 或未关闭 finding，不为重复评审消耗修复预算。
- 用户在正式最终 gate 选择「批准交付并创建 PR」，与此前的「创建pr并监听ci」构成
  本次提交、push、创建 PR 和观察 CI 的授权；不授权 merge。
- Simplify 无候选。Decision Check 沿用 ADR-0010，无需新 ADR。双语 README 现有描述保持准确，
  #59 既有模型错误说明缺口按 `package_readme: auto` 记录，未借本次修复扩大两个产品路径。
- 可复用经验已通过本模块 docstring 和直接回归保留：当 normalizer 按身份返回已有错误时，
  hook 必须原样抛出，避免再次显式设置它自己的原因；不新增项目级通用规则。

## 验证边界

本快照仅涵盖本机离线验证。真实 Provider 和发布后的跨平台 CI 在该快照尚未执行。
本地分支为 `fix/llm-error-cause-chain`。发布时须重新确认实际 PR head、三文件 diff 和
当前 Review/Quality/Standards 身份，远端终态由单独授权的合并或关闭后执行 Close。
