# Ralph 协议

Spec Kit 是结构化事实来源；Ralph 是有边界的执行循环。可移植契约是：每次迭代只执行一个依赖已满足的任务，并在干净的 Git 工作区中完成。只有当执行环境为每个 Worker（执行者）提供隔离 worktree 和明确的集成契约时，才允许并行 Worker。

在选择任务、派发 Worker（执行者）、进行质量简报或第一次编辑之前，先解析当前 Feature，记录干净基线，并执行 branch gate：创建或复用 `ralph/<feature-slug>`（或项目配置的分支前缀），然后确认它确实是当前分支。声明“稍后会创建分支”不算执行。不得 stash、reset、clean 或 stage 用户已有的改动。缺少 Git 仓库、基线不干净或分支切换不安全时，必须阻塞。

任务选择前，Ralph 先输出简洁的运行级治理摘要，包括当前 Feature、分支、base `HEAD`、适用的 Constitution/ADR/quality/standards 来源、收口门禁和停止条件。只报告相关摘录和路径，不要倾倒全部策略文本。每次迭代还要输出任务治理包，其中包含任务验收标准、允许修改的路径、适用的代码风格与架构规则，以及精确检查命令。缺少策略来源或质量配置时必须阻塞；Ralph 不得静默退回通用规则。

每次迭代都要解析任务 ID、依赖、`[P]` 标记、用户故事标签、文件目标和验证说明。即使任务带有 `[P]`，以下情况仍会形成阻塞边：文件重叠、共享公共契约、迁移和未解决的设计决策。每个 Worker（执行者）只接收一个任务，并同时得到验收条件以及相关的 Spec/Plan/ADR 摘录。

Worker（执行者）返回变更路径、命令、结果、残余风险和阻塞项。Worker 不修改任务复选框，也不创建收口提交。Orchestrator（编排器）运行任务检查以及 Quality 和 Standards 两类判定。在修改任务状态前，Orchestrator 必须验证验收证据、所有声明的检查、当前的 `QUALITY_VERDICT: pass`、当前的 `STANDARDS_VERDICT: pass`、未变化的 `HEAD`、允许修改的路径，以及所需检查和策略来源的可用性。只有所有项目都通过时，才能报告 `RALPH_TASK_GATE: PASS`。之后 Orchestrator 才能将任务标记为 `[X]` 并持久化 receipt（任务收据）。

任务状态变更必须紧接着发生以下动作：暂存已验证的任务路径和声明的状态文件，并创建且只创建一个提交；在勾选任务和提交之间不得插入下一个任务或无关改动：

~~~sh
git add -- <verified-task-path> <task-state-path> [<progress-path>]
git diff --cached --check
git commit -m "feat(ralph): <task-id> - <task-title>"
~~~

Orchestrator 还必须验证 `HEAD` 确实前进、提交包含任务结果和任务状态变更，并且工作区在记录提交身份前保持干净。干净提交之后，Orchestrator 不得再修改已跟踪的任务状态。失败或阻塞的任务保持打开状态，并阻塞其依赖任务。

只有当每个任务都有当前有效且通过的 receipt（任务收据）、Ralph 分支处于活动状态、工作区干净，并且循环输出 `<promise>ALL_TASKS_DONE</promise>` 时，才算完成。
