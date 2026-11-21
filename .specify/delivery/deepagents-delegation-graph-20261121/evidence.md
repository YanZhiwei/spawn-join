# DeepAgents 原生图受控委派回归验证

- feature_id: deepagents-delegation-graph-20261121
- phase_id: pre-publication-validation
- base_revision: 4f5b79c734e027ecbad3c2d999819d529958c80e
- head_revision: 4f5b79c734e027ecbad3c2d999819d529958c80e
- working_directory: D:/Repos/Github/spawn-join
- recorded_at: 2026-11-21
- result: pass
- limitations: 本记录绑定提交前的实际测试字节和独立评审；真实 Provider、其他平台和本次 PR 的远端 CI 尚未在该快照执行。提交后须重新核对实际发布身份，不将父提交冒充包含新增测试的提交。
- **delivery_run**: deepagents-delegation-graph-20261121
- **lane**: lightweight
- **evidence_path**: .specify/delivery/deepagents-delegation-graph-20261121/evidence.md
- **base_revision**: 4f5b79c734e027ecbad3c2d999819d529958c80e
- **reviewed_head**: 4f5b79c734e027ecbad3c2d999819d529958c80e
- **original_pr_head**: not-yet-published
- **pull_request**: pending
- **content_fingerprint**: SHA-256 07bbc7ff3355ef8865ba0a83d4028cde33a451f3c14e850aa9f2d33b478f6034
- **requirements_fingerprint**: SHA-256 3a9eb23868a4522d4aed1032aa3760e34338643355364e3a3c3347339c0f1df5
- **method_identity**: builtin，独立新上下文六维 Review

## 范围与批准

本次沿用已存在的 DeepAgents 受控委派能力，只补充真实原生图执行下的故障回归，
不改变运行时行为、公共 API、依赖、配置、README 或 ADR 状态。
因此使用 Lightweight，不创建 Feature Spec/Plan/Tasks。

用户以「好 开始」批准此前提出的测试范围，随后要求「好了后 创建pr」；
在最终六维 Review 全部通过、零 findings 的报告呈现后，
用户选择「批准并创建 PR」。这授权提交、推送和创建 PR，不授权合并。

唯一产品变更是
`packages/infra/agent-deepagents/tests/test_delegation_graph.py`。
本记录是必要的持久交付证据；run 的 runtime、Review、收据、PR 正文和无候选的
Simplify 报告按 ephemeral 策略保留在本机，不作为可远端下载的报告链接。

## 设计与验收

测试使用已有离线模型 fixture，通过公开 `build_supervisor` 返回的图执行
`ainvoke`，经过真实 LangGraph ToolNode、原生 `task` 工具和包内策略／诊断
middleware，再进入宿主拥有的 compiled worker。未 mock 控制器或策略中间件。

六个收集用例验证：

1. 已有活动任务和排队任务时拒绝第三项，拒绝的 worker 不执行，已排队项仍能完成；
2. 执行期 deadline 取消 worker，并在清理后释放槽位；
3. 活动 worker 正在取消清理、仍持有槽位时，等待者在队列中到期且从未执行；
4. 取消运行中的父图，另一项排队工作仍能完成；
5. 取消排队中的父图，不执行该 worker，也不损害活动图；
6. compiled worker 的失败保留原异常对象和原因链，诊断不泄露原始错误文案。

每个场景结束都检查活动数／等待数归零，再通过共享同一控制器的新图执行一次
成功委派，核对真实 ToolMessage 内容和 supervisor 最终输出。
测试以事件同步准备、入队和清理，不用固定 sleep 推测调度顺序；
0.2 秒是被测 deadline，5 秒是测试活性保护，不是硬抢占保证。

既有 ADR-0010 的图级故障覆盖欠账是本次依据，但本次不声称关闭其中所有历史限制。
fork、声明式 worker 模型错误归一、streaming 专属失败、远程子代理及持久化不在范围内。

## 身份与可复现验证

本快照的 `reviewed_head` 是执行检查时的真实 HEAD。新增测试当时尚未提交，
因此准确内容由以下身份绑定，而不是声称基准提交已经包含测试：

- 新文件模式：`100644`；
- 原始测试字节 SHA-256：
  `21fddd1ee4074f36d5c4b0bb34fbab8965058c06b66adfbc137d5d38d5b914a7`；
- 内容指纹：按路径排序的
  `mode<TAB>source-sha256<TAB>relative-path<LF>` UTF-8 行的 SHA-256；
- 要求指纹：11 个实际批准请求／治理／配置输入，按路径排序的
  `source-sha256<TAB>relative-path<LF>` UTF-8 行的 SHA-256；
- 原生 runtime 输入指纹：
  `03b692a6c54a103f8710a717c99750207733070dc3f18d75860c293f37372cd9`。

环境为 Windows、Python 3.11.13、DeepAgents 0.7.32、LangChain 1.4.8、
langchain-core 1.7.4、LangGraph 1.2.19。以下命令在仓库根目录实际执行：

| 命令／场景 | 退出码 | 实际结果 |
| --- | --- | --- |
| 包环境 `python -B -m pytest -c pyproject.toml packages/infra/agent-deepagents/tests -q -p no:cacheprovider`，修改前 | 0 | 211 passed |
| 同一解释器运行 `tests/test_delegation_graph.py`，修正测试假设后 | 0 | 6 passed |
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-agent-deepagents` | 0 | Black/isort、Ruff、Pyright strict 零诊断、217 tests、wheel/sdist、隔离安装／依赖／导入通过 |
| 新测试的 10 个独立 pytest 进程，`PYTHONASYNCIODEBUG=1` | 全部 0 | 每次 6 passed，总计 60 次用例通过 |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | 151 份文档／414 个本地目标 |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 0 | 0 errors／1 条既有历史 freshness warning |
| `git diff --check` | 0 | 无空白错误；新增未跟踪文件另由格式／lint／类型门覆盖 |
| `codegraph sync`，普通重试 | 0 | 已同步，affected 指向新增测试 |

完整包门禁使用 `UV_PYTHON=3.11`、`UV_LINK_MODE=copy`，
关闭 LangChain/LangSmith tracing。构建使用批准的独立临时目录，
结束后该唯一目录已不存在，没有在源码树留下构建产物。

原始执行回执保留每项命令、工作目录、开始／结束时间、环境／配置指纹、
日志 SHA-256 及执行前后输入身份。保守的检查输入覆盖 663 个文件与 Git index，
聚合身份为
`192f708bee4761856ee5091a7fe1d1a78488d396d8416b002a854bc171c7374c`，
四项配置检查执行前后的身份均相同。稳定性记录另绑定实际测试字节。

## 真实失败与限制

初次新增测试为 6 failed：所有用例都在“原生 `run_id` 必须非空”的额外断言失败。
该字段在公开类型和实际读取逻辑中是可选值，锁定的上游路径未提供它。
测试修正为用真实 `tool_call_id` 关联完整事件序列，并检查可选 run_id 一致性；
原始失败日志和修正后的通过日志均保留。未修改运行时，也未将此测试假设记为已修复 Bug。

首次 CodeGraph 同步遇到活进程锁；没有删除或绕过锁，后续普通重试成功。
Review transport 初次因 Quality／Standards 依赖写成列表而拒绝记录；
保留被拒绝的传输文件，改为原生要求的映射后，以同一 pending ticket 成功记录。
该操作未修改独立 Reviewer 的报告，也未创建或重置修复预算。

既有 `harness/evidence/delivery-v022-upgrade.md` freshness warning 不在本次修复范围。
本次快照未执行真实 Provider、跨平台或全仓包矩阵；后续 PR CI 结果必须另行观察，
不能用本机成功替代 required `Quality Gate`。

## 标准、独立评审与最终门禁

- Quality ticket：`0ba42aec91b14bc09c3a383798aa9b2e`，`QUALITY_VERDICT: pass`；
- Standards ticket：`fd2ea6bb66ec4226987cef2c0fc3a710`，`STANDARDS_VERDICT: pass`；
- 独立 Review ticket：`b33dc52888cb4468af654448a7011570`，
  `REVIEW_VERDICT: pass`，六维覆盖完整、零 findings；
- 原始 Review 报告 SHA-256：
  `1c6213a39c1bd3c5d91fd6bcce9c5a189b2d086fad33bfb96869cca6dbc2b28a`；
- 原生 Review receipt SHA-256：
  `fa706abd903bd04cd642a6989ad6832c5fe0033f3ce76e256039fc8a50358e9f`。

独立 Reviewer 重新计算实际内容／要求指纹，核对原生 snapshot、index、
Quality／Standards 原始回执和日志，并追踪上游 ToolNode 与 task 的异常传播。
没有以实现者自审冒充独立评审，没有运行修复轮次。
runtime `require --kind review` 返回 ready，`needs --kind repair` 为 false；
之后用户明确通过最终人工 Review gate。

Simplify 无候选；Package README 对内部测试改动 no-op；不新增 ADR 或公共规则。
原生图验证经验保留在测试本身，不扩张为通用测试框架。

## 发布边界

本记录是提交前的历史验证快照，不是已发布或已合并声明。
发布前须将两个允许路径提交到独立分支，核对实际提交字节，
在新的 HEAD 上刷新 Quality／Standards／独立 Review，并在 PR 正文记录真实发布身份。
用户仅授权创建 PR；只有在另行授权且提供方报告实际结果后，才能执行 Close 写终态。
