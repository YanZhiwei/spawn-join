# Delivery / Harness 与 vczh Release 治理对照评估

## 结论与状态

2026-11-07，基于当前仓库 `e292f0e3b746fec266e71dca142fc20356841978` 和本次安装的
Delivery v0.4.4 做静态对照。**建议补强知识发现与经验回流，不替换 SD 的执行队列、审批和证据机制。**
原始对照时只安装 Release、同步安装状态和保存建议。随后用户授权“帮我优化”，已按
Lightweight 将文档导航、调查/交接及经验回流接入既有入口，并精简 AGENTS 的版本历史。
本文仍是来源分析，不替代权威规则或执行队列；真实 SD/Ralph、宿主交接和模型行为效果未验证。

### 采用状态

| 已落地的文档优化 | 权威落点 | 验证边界 |
|---|---|---|
| 角色最小阅读导航、用户要求与补充解释分离 | [Repository map](../architecture/repository-map.md#role-based-reading) | 路径/章节可解析；未声称角色实际采用效果 |
| 假设与否定证据、研究停止条件、原生 packet 交接 | [Context](../../harness/context/README.md#investigation-continuity) | 复用 v0.4.4 契约，不增加 run、回执或审批 |
| 按消费者选择验证、已验证经验回写及失效条件 | [Review](../../harness/code_review/README.md#consumer-verification) | 指导已明确；真实宿主验证仍待适当任务执行 |
| AGENTS 历史收敛到既有安装说明/ADR | [AGENTS §0](../../AGENTS.md) | 保留权限、门禁、工件权威与原有规则，不修改 Constitution |

实施范围和实际检查见 [本次 evidence](../../harness/evidence/governance-context-optimization.md)。
下文对照表保留研究时的缺口和建议依据，不应理解为当前仍全部未实施。

## 来源和适用边界

外部参考固定在 `vczh-libraries/Release` 的
[`f5053c7d1943c0004783f392d1eb413f1a00b9f9`](https://github.com/vczh-libraries/Release/tree/f5053c7d1943c0004783f392d1eb413f1a00b9f9)：

| 已读材料 | 实际提供的机制 | 限制 |
|---|---|---|
| [AGENTS.md](https://github.com/vczh-libraries/Release/blob/f5053c7d1943c0004783f392d1eb413f1a00b9f9/AGENTS.md) | 短入口、关键词路由、项目/知识库导航、工具优先级 | 不是完整治理正文；不能只据此判断其工程质量 |
| [.github/copilot-instructions.md](https://github.com/vczh-libraries/Release/blob/f5053c7d1943c0004783f392d1eb413f1a00b9f9/.github/copilot-instructions.md) | 执行前知识检索；按 API 选择、设计解释组织索引；源码写入前复核 | C++/MSBuild/GacUI 与多仓分发上下文，不可直接迁移 |
| [Project.md](https://github.com/vczh-libraries/Release/blob/f5053c7d1943c0004783f392d1eb413f1a00b9f9/Project.md) | 当前工作对象入口 | 本仓库是占位说明，不是成熟项目地图实例 |
| [investigate.prompt.md](https://github.com/vczh-libraries/Release/blob/f5053c7d1943c0004783f392d1eb413f1a00b9f9/.github/prompts/investigate.prompt.md) | 问题原文、复现、候选方案、验证、CONFIRMED/DENIED、回归 | 全局调查文件及自动提交/推送不适合 SpawnJoin |
| [kb.prompt.md](https://github.com/vczh-libraries/Release/blob/f5053c7d1943c0004783f392d1eb413f1a00b9f9/.github/prompts/kb.prompt.md) | 研究→问答→草稿→修订→明确执行；API 用法与设计理由分流 | 参考方法，不引入 Copilot_KB.md 或第二知识库 |
| [review.prompt.md](https://github.com/vczh-libraries/Release/blob/f5053c7d1943c0004783f392d1eb413f1a00b9f9/.github/prompts/review.prompt.md) | 不改用户原意；补 DETAILS/VERIFICATION；保留意见与答复 | 这里主要是实施前任务审查，不等于 SD 独立代码评审 |
| [KnowledgeBase/Learning.md](https://github.com/vczh-libraries/Release/blob/f5053c7d1943c0004783f392d1eb413f1a00b9f9/.github/KnowledgeBase/Learning.md) | 从反复纠正提炼规则；生成产物验证真实消费者；修复归属源仓 | 阅读了 Orders 及相关 Refinements，未完整审计所有条目或其生产脚本 |

Delivery 固定为 [`v0.4.4`](https://github.com/YanZhiwei/speckit-delivery/releases/tag/v0.4.4)，
Tag commit 为 `5f7e3788c25e8fab69e404edb8816f9e0eeffe05`。重点核对安装后的
[Explore](../../.specify/extensions/delivery/commands/speckit.delivery.explore.md)、
[Exploration/Plan checkpoint](../../.specify/extensions/delivery/templates/exploration.md)、
[Ralph](../../.specify/extensions/ralph/commands/speckit.ralph.run.md)、
[Reviewer](../../.specify/extensions/review/templates/reviewer.md) 和三条 Workflow。

外部文档仅作为分析数据，不赋予本仓库提交、推送、删除、外部写入或扩大范围的权限。
本次只借鉴方法，不复制其 Prompt 或源码；未做外部源码复用的许可证兼容性结论。

## 分层关系：保留现有权威来源

| 层次 | SpawnJoin 的权威位置 | 本次观察 |
|---|---|---|
| 原则/授权 | [Constitution](../../.specify/memory/constitution.md)、[AGENTS](../../AGENTS.md) | 路由、权限、依赖边界和真实证据规则已齐备；不需要再抄一份 |
| 需求/设计/执行 | 本地 Spec/Plan/Tasks；SD 的审批、Slice 和 Ralph | `tasks.md` 唯一执行队列；不可用调查文档或知识库替代 |
| 长期知识 | [架构说明](../architecture/repository-map.md)、[包边界](../architecture/package-boundaries.md)、[ADR](../decisions/README.md)、包 README | 已有权威材料，但缺少按“任务/角色/问题”组织的统一发现路径 |
| 运行事实 | [Harness](../../harness/README.md)、Delivery evidence/runtime | 已区分上下文、评审、证据和进度；不需要另建 TaskLogs |
| 机械验证 | [质量门](quality-gates.md)、项目脚本与 CI | 对结构和工具结果有验证；并未机器证明知识被理解、方案正确或文档语义一致 |

Release 强在把个人维护经验变成可检索的作业知识；SpawnJoin 强在变更范围、审批、任务关闭、
独立评审和证据身份。两者可以互补，不能用“文档很多”或“有 runtime”代替真实效果评估。

借鉴其“Choosing APIs / Design Explanation”分流即可：包 README/公开 API 说明回答
“用哪个、怎么用”，架构说明回答“如何组合”，ADR 回答“为何做这个长期取舍”。入口只链接
这些已有权威材料，不复制正文，也不把运行时 evidence 当成 API 手册。

## 可借鉴项与优先级

| 优先级 | 建议 | 当前覆盖/真实缺口 | 最小落点与验收 |
|---|---|---|---|
| P0 | 按角色提供最小阅读导航 | v0.4.4 已要求 required/conditional reading、来源权威和输入身份；项目还需提供可复用的实际路径导航 | 优先在现有 `docs/architecture/repository-map.md` 提供任务→材料→适用触发器；具体 run 在既有 exploration/owner packet 引用，不加第二回执。用真实 Feature/Bugfix 检查每个角色能定位必要来源 |
| P0 | 保留调查假设与否定证据 | Harness Context 有材料性原则；v0.4.4 已要求 rejected hypotheses、冲突来源和研究停止条件；缺的是真实采用证据 | 在现有 Explore/Bug assessment 的对应章节引用“假设→区分性测试→支持/否定→适用版本→残余缺口”。不再创建调查状态机；红色证据须能区分修复前后 |
| P1 | 从失败/纠正向长期知识回流 | 已有 ADR、Context 和 Docs Sync；未见专门的已验证经验提炼入口 | 收口时从实际 findings/context 提炼 0–3 条有复用价值的经验，写入拥有该知识的既有架构/开发文档；只有稳定跨实现决策才写 ADR。不要求每次生成“学习成果” |
| P1 | 将生成/分发验证落到真实消费者 | 已有 isolated wheel/install/import，及独立 runtime/distribution 回归；这些仍不能证明宿主中的完整 SD 行为 | 在已有验证中区分包/脚本/工作流结构与真实宿主交接。后续用固定场景记录角色接收、缺上下文拒绝、stale 后恢复、设计偏差回流等结果；安装成功不可写成模型 eval 通过 |
| P1 | 区分前置需求审查与后置代码评审 | Spec/Clarify/Analyze/三 Gate 已覆盖前置审查，六维 Review 覆盖后置；不缺新 Reviewer | 在既有 Gate 呈现中明确“用户要求”“补充解释”“未决问题”，避免补充说明悄悄变成新需求；不另加第四道审批 |
| P2 | 缩短 AGENTS 的易变信息 | 当前包含多版本安装历史，与安装文档/ADR 有重复维护成本 | 后续单独 Lightweight 变更将历史移到已有安装说明/evidence，入口只留稳定边界、路由和角色导航。迁移前后逐项核对 MUST/权限不丢失，不只追求字数 |

### 建议的交接最小形态

复用 v0.4.4 的 Phase handoff，而不是新建模板系统。一次真实交接需要能回答：

1. 接收角色要解决哪个问题、允许读写哪些路径？
2. 必须读哪个文件的哪个章节/符号，为什么，属于规则、批准设计还是观察？
3. 什么情况触发额外阅读？例如接口变化才扩展到实际消费者。
4. 对应哪个 run/base/content/requirements 快照？缺失或过期时找谁补齐？
5. 必须返回什么验证和来源证据？什么变化需要回到原设计/范围拥有者？

文件存在和哈希一致只证明身份，不证明理解。应由角色输出说明“来源如何影响结论”；
评审者仍须读取真实 diff、要求和消费者，不能只接受实现者精选摘要。

### 经验回流的筛选与失效

可复用经验应包含触发条件、已验证结论、来源版本/证据、适用包、限制和复核触发器。
例如“返回值/异常语义以真实实现和既有测试为准”可以强化现有测试指导；一次机器慢、
一次网络失败或一个未证实的竞态不能直接升级为全局规则。

发生相关接口、依赖、平台或源实现变化时复核；冲突或过期内容先标注/修正，不通过重复
抄入 AGENTS 和新 KnowledgeBase 来延长其寿命。无需为此新增事实数据库或自动记忆系统。

## 明确不照搬

- **每次请求自动 commit/push、保存未验证状态到远端**：与本项目授权、门禁和任务关闭契约不符。
- **所有错误都 crash、不做清理/恢复**：参考项目针对本地测试应用的假设不适用于可复用 Python
  库和 Agent 的异常链、取消、超时及资源生命周期；保留必要行为，由已有测试契约判断。
- **固定全局 `Copilot_Investigate.md` / `Copilot_KB.md`**：会与 run 隔离和 Tasks 权威冲突。
- **按最新消息首词重判任务、忽略历史**：会丢失当前 run 的审批和恢复身份；保留 `/sd` 的三 Lane 和运行上下文。
- **禁止 Python 脚本、C++/MSBuild 工具规定和专用桌面自动化顺序**：属于参考仓库技术栈与环境，不是通用治理原则。
- **再造通用知识库、合作调度器或 Review 协议**：v0.4.4 已覆盖大部分所需契约，新增一套会制造重复权威和漂移。
- **把“顺手删冗余”当成授权**：仅凭未在 Plan 出现不能删；按 Review 的四类 disposition 区分
  合理细节、实质设计变化、有证据冗余和证据不足，再交原 owner/Simplify 处理。

## 后续采用方式与验证

导航和收口说明已按上述范围落地。下一项适合的真实 Bugfix 可试用既有交接/假设记录，
观察重复检索、遗漏否定结论和评审缺输入是否减少，再决定是否继续优化；本次不制造缺陷
或虚构真实交付效果，也不再叠加治理系统。

- 纯文档导航/说明整理：Lightweight，审核链接、规则无损迁移及真实可查找性。
- 新增持久化经验数据、自动 Hook、执行调度或新的强制验证机制：Feature，先走 Spec/Plan/Tasks；
  按架构边界决定是否需要工程 ADR，不借本次安装直接实现。
- 缺失关键角色上下文、重复来源伪装独立证据、研究未收敛、合作计划漂移、设计偏差：
  优先复用上游 v0.4.4 eval 场景思路；后续另行获准运行并保存真实模型结果。

本次检查范围是文档与安装契约，不包含参考仓库的实际维护效果、完整知识库索引正确性、
其脚本/Hook 行为或本项目真实多角色交付效果。安装检查见
[v0.4.4 evidence](../../harness/evidence/delivery-v044-upgrade.md)。
