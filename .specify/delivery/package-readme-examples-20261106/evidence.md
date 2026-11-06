<!-- DELIVERY_CURRENT_OUTCOME_BEGIN -->
## Current delivery outcome

- **delivery_run**: package-readme-examples-20261106
- **lane**: lightweight
- **status**: delivered
- **outcome**: merged
- **provider**: github
- **repository**: yanzhiwei/spawn-join
- **number**: 43
- **pull_request**: https://github.com/yanzhiwei/spawn-join/pull/43
- **reviewed_head**: 5e263aa6aaeba10ac81779ea43c01616eead8934
- **original_pr_head**: 5e263aa6aaeba10ac81779ea43c01616eead8934
- **published_head_proof**: tracker-head-mapped
- **base_revision**: b74aa5ac7a516664e6f8079c6978c7116a4a8711
- **merged_revision**: 5ed8db266742fd8abd0206850d0421f98d033efb
- **effective_head**: 5ed8db266742fd8abd0206850d0421f98d033efb
- **merged_at**: 2026-11-06T16:26:05Z
- **observed_at**: 2026-11-06T16:26:09.485780+00:00
- **outcome_recorded_at**: 2026-11-06T16:26:09.485780+00:00
- **verification_file**: .specify/delivery/package-readme-examples-20261106/runtime/observed-pr.json
- **merge_proof**: diff-equivalent
<!-- DELIVERY_CURRENT_OUTCOME_END -->

## Historical validation snapshots

<!-- Existing validation, review, CI, and limitation content below is retained verbatim as historical evidence. -->

# 包级 README 完整示例与中文默认入口交付证据

## Historical evidence-only archival verification

归档 base 为 `5ed8db266742fd8abd0206850d0421f98d033efb`。本次归档只新增本文件，
不更新产品或原始 Review。仓库根目录实际执行：

- `pwsh -NoProfile -File scripts/quality.ps1 -Check docs`：exit 0，59 文件 / 271 本地目标。
- `pwsh -NoProfile -File scripts/quality.ps1 -Check governance`：exit 0，0 errors / 1 既有历史 warning。
- `git diff --check`：exit 0。
- `git diff --exit-code 5e263aa6aaeba10ac81779ea43c01616eead8934 5ed8db266742fd8abd0206850d0421f98d033efb --`：exit 0。
- `gh pr checks 43 --repo YanZhiwei/spawn-join --json name,state`：exit 0，17 项均为 SUCCESS。

产品检查保留在其 reviewed_head 的历史身份；这些归档检查不声称重跑全部包质量门。
后续独立只读归档审查将复核 current block、原始观察、完整树等价与全文身份；
归档发布/CI/合并依照维护者已授权的收尾要求执行，不绕过 required check。

## Historical merge / Close observation — PR 43

- GitHub workflow run: `42252030736`，17 项 checks 全部 SUCCESS，required `Quality Gate` 成功；
  `gh pr checks 43 --repo YanZhiwei/spawn-join --watch --interval 10` 退出 0。
- 受保护合并：`gh pr merge 43 --repo YanZhiwei/spawn-join --squash --match-head-commit 5e263aa6aaeba10ac81779ea43c01616eead8934`，exit 0。
- GitHub 返回 PR `MERGED`，时间 `2026-11-06T16:26:05Z`，merge commit
  `5ed8db266742fd8abd0206850d0421f98d033efb`，历史 head 仍为
  `5e263aa6aaeba10ac81779ea43c01616eead8934`。
- `git fetch origin main` 后以 `origin/main` 创建精确归档分支
  `docs/package-readme-examples-evidence-20261106`，不 reset、不改写共享历史。
- `git diff --exit-code 5e263aa6aaeba10ac81779ea43c01616eead8934 5ed8db266742fd8abd0206850d0421f98d033efb --`，exit 0，无输出：完整树内容相同。
- 实际 GitHub 观察文件由 `gh pr view` 原始 JSON 归一化，未手填 merge SHA。
- `delivery_runtime.py close-record --run package-readme-examples-20261106 --outcome merged --pr 43 --verified --file runtime/observed-pr.json`，exit 0：
  recorded/eligible true；status delivered；published proof tracker-head-mapped；merge proof diff-equivalent。
- `merged` 路由按契约保留本轮 runtime/PR/报告与 evidence，不执行退休删除；本地运行工件继续忽略。

该段记录后续事实，不将本地 reviewed_head 或「当时等待 CI」限制改写为合并提交。
最终 outcome 仅以机器生成的 current block 为准。持久证据通过单独 evidence-only PR 归档；
该归档不是再次变更或重新批准产品内容。

## Historical publication snapshot — PR 43

- **pull_request**: https://github.com/YanZhiwei/spawn-join/pull/43
- **published_head**: 5e263aa6aaeba10ac81779ea43c01616eead8934
- **original_pr_head**: 5e263aa6aaeba10ac81779ea43c01616eead8934
- **tracker_base_revision**: b74aa5ac7a516664e6f8079c6978c7116a4a8711
- **verification**: `gh pr view 43 --repo YanZhiwei/spawn-join --json number,state,url,headRefOid,baseRefOid,mergeCommit,mergedAt,statusCheckRollup` returned OPEN, expected head/base, no merge.
- **publication_commands**: authorized `git push -u origin docs/package-readme-examples-20261106` and `gh pr create --repo YanZhiwei/spawn-join --base main --head docs/package-readme-examples-20261106 --title 'docs: 默认中文 README 并补齐五包完整示例' --body-file .specify/delivery/package-readme-examples-20261106/pull-request.md`, both exit 0.
- **CI observation**: run 42252030736 started at GitHub time 2026-11-06T16:24:11Z; this publication snapshot observed its checks IN_PROGRESS.

PR head 与 reviewed_head 完全相同，无发布时产品内容变化。Review、Evidence、Handoff guards
已通过，最终人工 gate 已批准。这里仍是发布历史，不宣称 CI 成功或已合并；后续 Close 观察
将单独保留原始 GitHub 回应并写入唯一 current outcome block。

## Historical validation snapshot — 本地最终评审

- **observed_at**: 2026-11-06T16:21:50.771520+00:00
- **delivery_run**: package-readme-examples-20261106
- **lane**: lightweight
- **feature_id**: package-readme-examples-20261106 (Lightweight run label; no Feature created)
- **phase_id**: outgoing-diff
- **head_revision**: 5e263aa6aaeba10ac81779ea43c01616eead8934
- **working_directory**: C:/Users/YanZh/.local/share/opencode/worktree/86e56b/witty-island-2
- **recorded_at**: 2026-11-06T16:21:50.771520+00:00
- **result**: pass for local checks, Standards, independent review and actual final human gate
- **evidence_path**: .specify/delivery/package-readme-examples-20261106/evidence.md
- **base_revision**: b74aa5ac7a516664e6f8079c6978c7116a4a8711
- **merge_base**: b74aa5ac7a516664e6f8079c6978c7116a4a8711
- **reviewed_head**: 5e263aa6aaeba10ac81779ea43c01616eead8934
- **original_pr_head**: pending
- **pull_request**: pending
- **content_fingerprint**: SHA256 07a5a4b9b7bb12e34a17b4baad0761dea6ad42467ffd6fbf1dfd8452b3694172
- **requirements_fingerprint**: SHA256 0030e27d7e30a1ee782856ecc2bea9d9dad733eceb9f84050d9d5e0e436a5995
- **method_identity**: builtin independent six-dimensional Review, instructions-only; no external skill method
- **bug_slug**: not-applicable

此历史快照不代表后续 CI/合并已完成。Close 的唯一 current outcome block 才是终态权威。
原始评审、检查日志与 receipt 保留本机同 run runtime；本记录保留可复现命令、摘要、
路径/内容/规则身份。源码原文可从 reviewed_head 获取，不把后来的 squash SHA 改写成评审身份。

## 用户需求、路由与蓝图

用户反馈协议包中文 README 缺少完整示例，追加检查其他代码包，明确选择「README 默认中文」；
随后授权「发 PR、监听 CI、CI 好了合并、按照 SD 收尾」。最终展示当前六维评审、14 项检查、
460 个测试、18 次离线示例和 404 链接/锚点，以及下述限制后，用户实际选择「批准并继续」。
runtime present/decide 将这一选择绑定到本轮 Review/Quality/Standards/snapshot 的真实字节，
没有复用上一轮 readme-bilingual 运行的审批。

采用 Lightweight：文档和规则偏好、机械性文件名适配；无领域源码、API、manifest、lock、
依赖、数据迁移或安全边界新增，不创建空的 Spec/Plan/Tasks，也不把安装 Bundle 当执行证据。

蓝图：先展示完整离线入口、导入、main、运行命令和结果；真实服务前提另列；
LangChain 工具/流式复用 main guard 下的 build_model；Agent 复用既有 offline examples；
同步快照读取只依赖协议，不反向引入适配包运行时依赖。Core 仍仅提供版本号。

全部 13 对自有 README 改为完整中文 README.md / 完整英文 README.en.md，导航优先同语种。
包元数据仍读取 README.md，展示语言改为中文；旧 README.zh-CN.md 路径迁至 README.md。
ADR 唯一可变索引仍由 docs/decisions/README.md 拥有，英文只链接该表。第三方/安装器内容不改。
治理仅精确豁免新语言说明页，README-audit.md 仍须证据字段；Quality profile 覆盖新英文首页，
保留旧名用于删除路径匹配，不放行未归属路径。

## 不变量、兼容性与副作用

- 产品源码、公共 API、异常、序列化、依赖方向和运行时行为不变。
- 无新依赖/权限/密钥/私有 URL/持久化格式；教学假密钥与伪 endpoint 不会用于离线网络调用。
- 用户执行真实 ainvoke/astream 或 sync 时才发起对应服务请求；前提、凭据和输出不确定性已说明。
- 文档旧路径改变是用户明确批准的展示迁移；活动仓库链接已更新，旧历史 evidence 不改写。
- 回滚：通过普通 PR revert 本次 squash，同时还原语言路径、规则、白名单和 profile，重跑治理/导航。

## 机械检查原始证据

以下每项均在同一真实工作目录执行，exit 0、before=after、unchanged=true。
checked-input SHA256: edda56fd1695dcb1f2266e860d204d8e7a798909ec784f5b2337c034fd212914。
Windows/Python 3.13.5、PowerShell 7，各 Distribution 自有 uv project/lock/venv；
PYTHONUTF8=1；SPAWN_JOIN_TEMP_DIR=C:/Users/YanZh/AppData/Local/Temp/opencode。
原始 receipts 记录每个输入文件 SHA、HEAD、时间、cwd、退出码与日志 SHA；独立评审已复核。

| 命令 | Exit | UTC 起止 | 原始日志 SHA256 |
|---|---|---|---|
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-core` | 0 | 2026-11-06T16:06:10.505882+00:00 → 2026-11-06T16:06:24.225411+00:00 | `52e735d7230c62b38cc64d4f532fa32d8841100e994c6a5f0c271368a28a54b4` |
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider` | 0 | 2026-11-06T16:06:24.635484+00:00 → 2026-11-06T16:06:54.333665+00:00 | `eaae84cc8bb869dfa383df5ff9fe9558a3b7aad03d00617b60d69e697531e521` |
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider-langchain` | 0 | 2026-11-06T16:06:54.736142+00:00 → 2026-11-06T16:08:18.034797+00:00 | `ee287e5776e15fb4000b21f1574bd892220066c13385ed79464efde6ee24d730` |
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-model-sync` | 0 | 2026-11-06T16:08:18.487627+00:00 → 2026-11-06T16:09:08.536682+00:00 | `ff1cb174dc967764da0d6d37374190c6997568a8454fbd570ded488114b2c4eb` |
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-agent-deepagents` | 0 | 2026-11-06T16:09:09.022551+00:00 → 2026-11-06T16:10:13.760635+00:00 | `1c5782db54c56ea2595feeb7bf5914688d998d65f72f35cabe4ab300173fc944` |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | 2026-11-06T16:05:55.478489+00:00 → 2026-11-06T16:05:57.830798+00:00 | `337c34dd1d2c45eaea489aac208487bff24696e242678e43154bd753fe0770d1` |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 0 | 2026-11-06T16:05:58.193193+00:00 → 2026-11-06T16:06:43.389986+00:00 | `313d7c26c5b76a403ddb832c329f42fc321299065bf107b8b7c78e669b8ebecc` |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check static` | 0 | 2026-11-06T16:06:43.811138+00:00 → 2026-11-06T16:06:48.077883+00:00 | `a4b8941f04428173f6de40e29e6c624adf6f0b63ff45bf0cdc7f38930e25feb3` |
| `pwsh -NoProfile -File scripts/test-governance.ps1` | 0 | 2026-11-06T16:06:48.543947+00:00 → 2026-11-06T16:07:44.209839+00:00 | `6ac668fe17014346fc18391cc4ccd8da04b1b4b084e595051e2312ebce8d897c` |
| `pwsh -NoProfile -File scripts/test-quality.ps1` | 0 | 2026-11-06T16:07:44.689642+00:00 → 2026-11-06T16:08:55.230188+00:00 | `549adecfc9ecbf013330ffcc3a276cfbe82867fe1e745d5f85623a32f2e20de5` |
| `pwsh -NoProfile -File scripts/test-static.ps1` | 0 | 2026-11-06T16:08:55.683289+00:00 → 2026-11-06T16:09:04.186439+00:00 | `80d80fe4a97972a61035a337818578737118b86c4064d0e3960314bb7717a9d5` |
| `C:\Users\YanZh\AppData\Roaming\uv\python\cpython-3.13.5-windows-x86_64-none\python.exe .specify\delivery\package-readme-examples-20261106\runtime\verify_examples.py` | 0 | 2026-11-06T16:05:55.507244+00:00 → 2026-11-06T16:07:11.182798+00:00 | `d6ca043d4c35bb06663d3a9ad0a95e24cf2c087999693c688b874dd365623914` |
| `C:\Users\YanZh\AppData\Roaming\uv\python\cpython-3.13.5-windows-x86_64-none\python.exe .specify\delivery\package-readme-examples-20261106\runtime\readme_navigation.py` | 0 | 2026-11-06T16:07:11.575130+00:00 → 2026-11-06T16:07:12.307736+00:00 | `0e26f8d396652bd0cd120f5621e3444ef70f49205e9690d0b5e71f87a44bcf49` |
| `git diff --check b74aa5ac7a516664e6f8079c6978c7116a4a8711` | 0 | 2026-11-06T16:07:12.692844+00:00 → 2026-11-06T16:07:13.313238+00:00 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

五包 pytest 分别为 7、154、129、55、115 passed，合计 460；包门还包括 locked sync、
Black/isort、Ruff、strict Pyright、隔离 wheel/sdist 构建、安装、pip check 与 isolated import。
治理/质量门/静态回归分别为 26、11、3 场景通过。文档机械检查为 59 文件、271 本地目标。
专项验证从 README 原文提取执行，18 次离线示例/CLI 成功，13 对/404 个本地链接与锚点通过。
Python 块均可编译；明确的续接片段允许顶层 await，不声称每个配置片段都是独立程序。
工具 mock 校验工具名、参数、ToolMessage 内容及 tool_call_id 关联；并运行真实本地 Agent 图。

## Standards / Docs / Simplify / 独立六维评审

STANDARDS_VERDICT: pass — 目录拥有者、依赖方向、DRY、API 边界与单份 ADR 索引符合规则。
PACKAGE_README_VERDICT: updated — 五包各有明确 updated 表面；源码/manifest 不变的安装、版本、
依赖与错误契约仍准确；未配置投影生成命令，不虚构 docs-sync 执行。
SIMPLIFY_VERDICT: none — 无候选，不引入模板系统、领域抽象或未来能力。
REVIEW_VERDICT: pass — fresh-context 独立只读 reviewer，完整覆盖，无 findings、无未决阻塞。

| 维度 | 结论与关键依据 |
|---|---|
| requirements | pass：五包完整示例、13 对中文默认页、完整英文与导航均满足用户要求 |
| code_quality | pass：清晰教学边界、完整 main、build_model 复用与既有离线程序，无额外公共抽象 |
| architecture | pass：包边界不变；同步读取依赖协议；模型创建属适配层；ADR 索引唯一 |
| correctness | pass：对照 Channel/codec/override/Catalog 源码；工具结果关联正确，活动锚点无缺失 |
| security_compatibility | pass：无新秘密/权限/依赖；旧文档路径迁移明确，精确治理豁免未扩大 |
| test_effectiveness | pass：14 原始 receipts/hash、460 tests、40 回归场景与18执行已独立核对，mock 限制明确 |

评审者独立重算 44 路径和 10 项需求/规则身份，验证当前 input-review 指纹：
46cfae172bea6520a3f8811fb3ec030620798db189acdf20b2aee3997c5690b8。
独立 reviewer session: ses_e4e612646ffeT8HxRGsAMTIItM。
原始 Review YAML 的持久身份如下；它不是后来合并提交的 Review。
- `review.yml` SHA256 `196c2cdad1a8bdc5114d4a6b2e6bf4ae9d71307b7f484e1a04cb981add0a849c`
- `quality.md` SHA256 `a60467ee8b9c27580e57a6bbd298d7bf4c7fb7c1018255928564737447c98af2`
- `standards.md` SHA256 `0d28f7a8131e26a937c6dd6e1e922669f95c54c04e35acb2d225953e4f5bd0bc`
- `docs-refresh.md` SHA256 `7446eb3d6c7f83e8827f4135a92e09c52280b86390c6b013f95f0671e68d6aec`
- `verified-simplify.md` SHA256 `d42b0491cde8ca24673ebbb119b4da9b15fc7a42693651aedb63c06e19f44f31`

## Limitations — 已披露限制、警告与中断恢复

- 真实 Provider 推理与 models.dev 在线源同步未执行；本次不将 mock 声称为真实集成成功。
- 本地 Windows/Python 3.13.5 不能替代后续远端 CI 平台矩阵。
- 治理 0 errors / 1 warning：delivery-v022-upgrade.md 为既有历史 freshness 提示，未用于本轮批准。
- Core 隔离构建的空 requirements 提示来自零依赖事实，不是依赖遗漏。
- CodeGraph status/sync 报未初始化；无可用 code-review-graph，使用源码/导出/消费者 fallback，
  不声称图关系验证通过，也未擅自创建索引。
- 首个示例 helper 曾误把 environ 传给 from_file，已更正为 create_chat_model 参数；产品未改。
- 旧 Quality 在用户改语言要求时输入变化，原 ticket 经显式恢复原始 bytes 后记录 blocked；
  迁移暂存于精确自有路径 stash，已恢复，无用户工作丢弃。旧日志不重标新内容 pass。
- 新英文首页 Profile 缺口单独 blocked 后修复，当前 44 路径逐一匹配真实配置。
- 原始 Simplify/Quality 报告均保留不改写；最终 Review 依赖精确当前 Quality/Standards receipt。
- 本历史快照时尚未创建 PR、未取得远端 CI 或合并结果；后续观察另行追加，Close 才写终态。

## 逐路径内容清单

算法：排序后紧凑 JSON 数组 UTF-8（ensure_ascii=False）SHA256；每条为 path/mode/raw-byte-SHA256，
删除路径以 deleted tombstone 保留。仅同 run runtime/reviews/receipts/evidence/PR 正文为记账排除；
intake.md 仍是绑定需求，不排除规则或产品路径。

| 路径 | Mode | SHA256 / tombstone |
|---|---|---|
| `.specify/delivery/README.en.md` | 100644 | `620fb55033db09023bded5521f072857a69e42e3dea93926d0f5f7c36350d56e` |
| `.specify/delivery/README.md` | 100644 | `bb7665ee37c15f400f96d494e2bce79a854b1c512e6dd1adfe8343e9409ac536` |
| `.specify/delivery/README.zh-CN.md` | deleted | `deleted` |
| `.specify/extensions/quality/quality-config.yml` | 100644 | `5753d55c96f21b9371c53e42cc9a3534b6c4820c06b42628b7beb13db27ca7cf` |
| `AGENTS.md` | 100644 | `7b1e93a2c0881838c915f01aa1d0df59e77d60bcb0884804c1999313d52167ac` |
| `README.en.md` | 100644 | `7b5676ad5180e7477dd9630cbfbb968943c92be145fb6b14b0d5bb41893cff91` |
| `README.md` | 100644 | `ca3c84fa52bbe37a734afef70a85aba9674a3da941221f06c3b0bf37871edbb9` |
| `README.zh-CN.md` | deleted | `deleted` |
| `docs/decisions/README.en.md` | 100644 | `bb9b41efd0047d71f7a368b411d738021d0fa12e04d2962cc71de4606c1e5460` |
| `docs/decisions/README.md` | 100644 | `fa5c17dc9c6eefa2e441241f6e102f853ccdc066aab8fb964e18c4931b0f9aeb` |
| `docs/decisions/README.zh-CN.md` | deleted | `deleted` |
| `docs/development/quality-gates.md` | 100644 | `7a798cebde5423955b4f26d82a3f11625c6baf52cd236e59395d36e61de501d1` |
| `harness/README.en.md` | 100644 | `d1593a51825b2c66fa6543952c9b63025c06fb9c4c73d9165b94a6a462891006` |
| `harness/README.md` | 100644 | `f48eaa1162475180c8ec2068504dc7cc835cb7c644e3185244509f3bc1bf08f0` |
| `harness/README.zh-CN.md` | deleted | `deleted` |
| `harness/build/README.en.md` | 100644 | `d18e15cb5fb0eb21b4b4b412a8b98f31b5dee2f18e5dd7ebb38017e33d1898a7` |
| `harness/build/README.md` | 100644 | `369e239ef5af9a2b1e5bd8bad8cf9463cc6d0ce6cd5c0bea1d00a79d92e5f4e6` |
| `harness/build/README.zh-CN.md` | deleted | `deleted` |
| `harness/code_review/README.en.md` | 100644 | `4c037ac9b3979e22a3ddca5af31e0b42c0d02ef1a9f4c3d2fae197fee5578fb6` |
| `harness/code_review/README.md` | 100644 | `8bda082d9881dfce00c27f11fe9ebf58bded9fd1cfb7d0bf0c21956b431e2412` |
| `harness/code_review/README.zh-CN.md` | deleted | `deleted` |
| `harness/context/README.en.md` | 100644 | `0b49c2d251bf22ce59464305c2071f23c614c97bfca5bd36d4676f2b49302bfc` |
| `harness/context/README.md` | 100644 | `2f2a727a1231355ea21b22e350c795c8b1d15e0699d0ec2756f378fdb7ba0c2e` |
| `harness/context/README.zh-CN.md` | deleted | `deleted` |
| `harness/evidence/README.en.md` | 100644 | `288f46d6eac1a42b24e70acf30d0dab3cc480fb680029939d028b6f9979f55a7` |
| `harness/evidence/README.md` | 100644 | `ed35bae2470eac9dd74cd19688ce1ce5775fc4959994a35537a5e8ab15f76977` |
| `harness/evidence/README.zh-CN.md` | deleted | `deleted` |
| `packages/core/llm-provider/README.en.md` | 100644 | `2d78791021d2257eeb748398c1a0014b13ac38f05a4e0e719947f7d677b89cc1` |
| `packages/core/llm-provider/README.md` | 100644 | `74ddb474d3c30be079fdcc85815a6674aa550db1e05ced8341751697f617b726` |
| `packages/core/llm-provider/README.zh-CN.md` | deleted | `deleted` |
| `packages/core/spawn-join-core/README.en.md` | 100644 | `0fcaecab442a617bf426346e9a842cf8dc666ed93eae4621b92019919624aa6e` |
| `packages/core/spawn-join-core/README.md` | 100644 | `2f801590281168822d1eb244f27127a8777bdee3d5e088e37ef4b6cb21b4aa5e` |
| `packages/core/spawn-join-core/README.zh-CN.md` | deleted | `deleted` |
| `packages/infra/agent-deepagents/README.en.md` | 100644 | `75398bb152c297e9f76b863c89d1650706412fe56dd1a93da999f6f0bbb524d5` |
| `packages/infra/agent-deepagents/README.md` | 100644 | `23521772f441821cbeba3302c5ace20a5d255bcd794661a6cc1f5f58efa347a7` |
| `packages/infra/agent-deepagents/README.zh-CN.md` | deleted | `deleted` |
| `packages/infra/llm-model-sync/README.en.md` | 100644 | `0e4a2d409d741b62b8c46b8f5b606d30dfeb88e1a7047bbeb3564333dc0d72aa` |
| `packages/infra/llm-model-sync/README.md` | 100644 | `557d52e4585f5c27d7d8a12c0cd1e6a9b6189816cb85f478730037f1e8f40815` |
| `packages/infra/llm-model-sync/README.zh-CN.md` | deleted | `deleted` |
| `packages/infra/llm-provider-langchain/README.en.md` | 100644 | `a628ffbf156c537d63f870d1adb72f92462d045310fd6d1c8e69633de5711fb4` |
| `packages/infra/llm-provider-langchain/README.md` | 100644 | `91bca36e7abbd970a0f1f3a635b24dcd423d5f42a85cd796f57b1be69bc329cc` |
| `packages/infra/llm-provider-langchain/README.zh-CN.md` | deleted | `deleted` |
| `scripts/check-governance.ps1` | 100644 | `16ed3e659ae9801b375794bb14326e11dc8a0ad035f4d10e505c5aed43bcf19a` |
| `scripts/test-governance.ps1` | 100644 | `73a419194b3509078060add893cad98eff2ede1a0ea23be28d0bdbe9dbcb532b` |

## 需求与规则清单

| 输入 | SHA256 |
|---|---|
| `.specify/delivery/package-readme-examples-20261106/runtime/intake.md` | `63009645813f6bea5e2f745ed8e65a358e417b686e2414f9a78e1657564ae5b6` |
| `.specify/extensions/delivery/delivery-config.yml` | `617c100a77af5a8a76f9239dc1cc68bbe871576045b6c9e98013274f38affd8a` |
| `.specify/extensions/docs-sync/docs-sync-config.yml` | `c58d0d6b16529848e6983ec62cae35cd7ab6ef09ee5f50c66d387f905341557e` |
| `.specify/extensions/quality/quality-config.yml` | `5753d55c96f21b9371c53e42cc9a3534b6c4820c06b42628b7beb13db27ca7cf` |
| `.specify/extensions/review/templates/reviewer.md` | `32b3b4710f95a7a39925e7b72960560ff131c5e16273cd9d6e86f98344458495` |
| `.specify/memory/constitution.md` | `945401879b4ec63691da47fb68efe7a3f2520cd0bb12802f979f27c313bc155f` |
| `AGENTS.md` | `7b1e93a2c0881838c915f01aa1d0df59e77d60bcb0884804c1999313d52167ac` |
| `docs/architecture/package-boundaries.md` | `f3a793966a0846c97b60ea375a9f6f01d158746d583412b0c9cb5bcdadafdfed` |
| `docs/decisions/README.md` | `fa5c17dc9c6eefa2e441241f6e102f853ccdc066aab8fb964e18c4931b0f9aeb` |
| `docs/development/quality-gates.md` | `7a798cebde5423955b4f26d82a3f11625c6baf52cd236e59395d36e61de501d1` |
