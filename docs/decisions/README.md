# Architecture Decision Records

[简体中文](#中文) | [English](#english)

## 中文

本目录是 SpawnJoin 长期架构决策（ADR）的唯一根目录。当前通过文档约定和治理检查维护；
Delivery 的 ADR/context 配置已指向本目录，但自动 hook 尚未启用；未来启用时必须继续
指向这里，不另建第二套决策库。

### 什么值得记录

只为会约束多个实现点或未来演进、存在真实取舍且缺少背景会令人困惑的决策写 ADR。
普通代码整理、一次性调试和可随时撤销的细节留在变更说明中；不要为每个任务创建 ADR。

- Spec / Plan / Tasks：一次 Feature 的需求、方案和唯一执行队列。
- ADR：为什么选择这个边界或方案、拒绝了什么、长期约束及其后果。
- `docs/architecture/`：当前架构的导航视图和包边界；引用 ADR，不复制决策全文。
- Harness：实际评审、执行日志和验证证据；ADR 链接证据，不把计划写成已验证结果。
- 公共契约与测试：留在对应包的代码、契约或使用文档中，不全部塞入 ADR。

Spec 是面向交付的工作工件，不是长期架构知识库。收口前将仍然重要的设计提炼为 ADR
或架构文档；根 `.gitignore` 以 `/specs/` 忽略新建的本地工件，不改变 Feature 执行要求。
忽略规则不会取消已跟踪文件的跟踪，本次也不删除文件或执行 `git rm --cached`。
未跟踪的现有 Feature 会被忽略但仍在本地；提交前须确认长期契约、设计与有效证据不只
存在于被忽略的 Specs 中。既有已跟踪内容的迁移或取消跟踪需要另外确认和保护。

### 分类和编号

文件名为 `NNNN-short-kebab-title.md`，编号在整个目录递归范围内全局递增，不重复使用，
不随状态或分类变化重新编号。复制 [模板](template.md) 后再分配下一个可用编号。

Agent 在创建前按以下步骤选择分类，并在 ADR 的 `Classification` 中用一句话说明理由：

1. 找到决策约束的主要职责及拥有者，优先复用已有领域目录。
2. 只有该领域确实出现子领域决策时才增加一级目录，不预建空的分类树。
3. 跨领域规则归最接近的共同职责；工程治理放在 `engineering/`。
4. 无法判断拥有者或分类将改变公共边界时，先询问，不凭目录名替项目发明架构。

例如缓存策略可归 `cache/`，内存缓存的具体决策可归 `cache/memory/`；这些只是分类示例，
不表示仓库已有缓存包。分类树不是严格二叉树，也不是依赖树。一个 ADR 可以通过
`Depends on` 引用多个前置决策，通过 `Related` 关联其他领域，通过 `Supersedes` 表示替代。
同一决策只保留一个正文，跨领域时用链接而不是复制文件。

### 生命周期

- `Proposed`：设计候选，尚未批准，不代表已经实现。
- `Accepted`：维护者明确批准的决策；实现、质量门和发布是否完成须另附证据。
- `Rejected`：明确未采纳，保留理由。
- `Deprecated`：不再建议采用，说明现有使用者如何处理。
- `Superseded`：被新的 ADR 替代，双方填写相互链接。

维护者批准后才能将 Proposed 改为 Accepted。Accepted 后的拼写、链接和澄清可以原地
修订并记录日期；改变实质取舍时创建新 ADR，不悄悄改写历史。未生效的替代提案不能提前
将旧 ADR 标记为 Superseded。移动分类时保持编号并更新所有引用。

### 设计与图表

ADR 可以包含接口轮廓、数据结构、不变量、异常、副作用、依赖方向和必要图表，但只写
解释决策所需的部分。细节过长时链接同领域设计说明，不复制整份 Plan 或代码。

图表使用 [项目级 Fireworks 技能](../../.agents/skills/fireworks-tech-graph/SKILL.md)，
项目用法和环境隔离见 [技术图说明](../development/technical-diagrams.md)。简单关系也可
直接使用 GitHub 支持的 Mermaid。SVG 是可维护主产物，PNG 是展示副本；有 JSON 输入时
一起保存。相邻资源放在 `assets/NNNN/` 下，正文用相对路径嵌入并给出文本摘要。

每张图说明是“当前实现”还是“目标设计”，注明箭头语义、事实来源和适用 revision。
不要混淆代码依赖、运行时调用和数据流；不把模型绘制的图片当成架构事实或测试证据。
结构检查通过不等于字体、布局和文字可读性通过，最终图片仍需视觉检查。

### 决策索引

| ID | 领域 | 决策 | 状态 |
|---|---|---|---|
| ADR-0001 | engineering | [分离交付工件与长期设计知识](engineering/0001-delivery-and-durable-design.md) | Accepted |
| ADR-0002 | engineering | [取消跟踪历史 Feature 工件](engineering/0002-untrack-historical-feature-artifacts.md) | Accepted |
| ADR-0003 | engineering | [启用 Spec Kit Delivery 与 Ralph 协议](engineering/0003-enable-delivery-and-ralph.md) | Accepted |
| ADR-0004 | engineering | [以固定 Release 管理 Delivery 安装](engineering/0004-release-managed-delivery-installation.md) | Accepted |
| ADR-0006 | llm-provider | [以 LangChain 作为 LLM 运行时，保留渠道与协议选项](llm-provider/0006-langchain-first-llm-runtime.md) | Accepted |
| ADR-0007 | engineering | [默认启用 Slice 交付](engineering/0007-default-slice-delivery.md) | Accepted |
| ADR-0008 | llm-provider | [模型目录文件与凭据边界](llm-provider/0008-model-file-and-env-boundary.md) | Accepted |
| ADR-0009 | llm-provider | [模型元数据与手动同步边界](llm-provider/0009-model-metadata-and-sync.md) | Proposed |
| ADR-0010 | agent | [DeepAgents 产品增强包的边界与公共契约](agent/0010-deepagents-product-boundary.md) | Accepted |

新增或变更 ADR 时同时更新索引、关联链接和当前架构视图。模板不是有效决策，不参与编号。

许可证见 [LICENSE](../../LICENSE)。

## English

This directory is the single root for SpawnJoin long-term architecture decisions (ADRs). It is
currently maintained through documentation conventions and governance checks; Delivery's ADR/context
configuration already points here, but automatic hooks are not enabled. If enabled in the future,
they must continue to point here rather than create a second decision store.

### What deserves an ADR

Write an ADR only for a decision that constrains multiple implementation points or future evolution,
involves a real trade-off, and would be confusing without context. Ordinary code cleanup, one-off
debugging, and easily reversible details stay in change descriptions; do not create an ADR for every
task.

- Spec / Plan / Tasks: requirements, solution, and the sole execution queue for one Feature.
- ADR: why a boundary or approach was chosen, what was rejected, long-term constraints and consequences.
- `docs/architecture/`: current architecture navigation and package boundaries; reference ADRs instead of copying full decisions.
- Harness: actual reviews, execution logs, and verification evidence; ADRs link evidence and never present plans as verified results.
- Public contracts and tests: stay in the owning package's code, contracts, or usage docs, not entirely in ADRs.

A Spec is a delivery-oriented working artifact, not a long-term architecture knowledge base. Before
closing, distill still-important design into ADRs or architecture documents. The root `.gitignore`
ignores new local artifacts under `/specs/` without changing Feature execution requirements. Ignore
rules do not untrack already tracked files, and this change neither deletes files nor runs
`git rm --cached`. Existing untracked Features are ignored but remain local; before committing,
confirm that durable contracts, design, and valid evidence do not exist only in ignored Specs.
Migration or untracking of existing tracked content requires separate confirmation and protection.

### Classification and numbering

Filenames use `NNNN-short-kebab-title.md`; numbers increase globally across the whole recursive
directory, are never reused, and do not change with status or classification. Copy the
[template](template.md) and then assign the next available number.

Before creating an ADR, an Agent chooses a classification as follows and states the reason in one
sentence under `Classification`:

1. Find the primary responsibility and owner constrained by the decision; reuse an existing domain directory where possible.
2. Add a first-level directory only when that domain genuinely has subdomain decisions; do not pre-build an empty tree.
3. Cross-domain rules belong to the nearest common responsibility; engineering governance belongs in `engineering/`.
4. If ownership is unclear or the classification would change a public boundary, ask first instead of inventing architecture from a directory name.

For example, caching strategy could belong in `cache/`, while a specific in-memory cache decision
could belong in `cache/memory/`; these are classification examples only and do not imply the
repository already has cache packages. The classification tree is neither a strict binary tree nor
a dependency tree. One ADR may reference multiple prior decisions through `Depends on`, associate
other domains through `Related`, and express replacement through `Supersedes`. Keep one body per
decision and link across domains instead of duplicating files.

### Lifecycle

- `Proposed`: design candidate, not approved, not evidence of implementation.
- `Accepted`: a decision explicitly approved by maintainers; implementation, quality gates, and release completion need separate evidence.
- `Rejected`: explicitly not adopted, with the reason retained.
- `Deprecated`: no longer recommended, with guidance for existing users.
- `Superseded`: replaced by a new ADR, with mutual links.
Only maintainers may change Proposed to Accepted. After acceptance, spelling, links, and
clarifications may be revised in place with a recorded date; changing the substantive trade-off
requires a new ADR and never silently rewrites history. An ineffective replacement proposal must not
mark the old ADR as Superseded early. When moving classification, keep the number and update all
references.

### Design and diagrams

An ADR may include interface outlines, data structures, invariants, exceptions, side effects,
dependency direction, and necessary diagrams, but only the parts needed to explain the decision.
Link same-domain design notes for lengthy details rather than copying an entire Plan or code.

Diagrams use the [project-level Fireworks skill](../../.agents/skills/fireworks-tech-graph/SKILL.md);
project usage and environment isolation are documented in
[technical diagrams](../development/technical-diagrams.md). Simple relationships may use Mermaid
supported by GitHub. SVG is the maintainable primary artifact and PNG is a display copy; save JSON
input when present. Keep adjacent assets under `assets/NNNN/`, embed them by relative path in the
body, and include a textual summary.

State whether each diagram shows "current implementation" or "target design", including arrow
semantics, evidence source, and applicable revision. Do not conflate code dependency, runtime calls,
and data flow; do not treat a model-generated image as architectural fact or test evidence. Passing
structural checks does not prove font, layout, or text readability; final images still need visual
inspection.

### Decision index

The single machine-recognized index is the bilingual table in the Chinese section above
([Decision index](#决策索引)); it is intentionally not duplicated here so each ADR ID appears exactly
once. The same table links every decision, its domain, and its current status.

When adding or changing an ADR, update the index, related links, and current architecture view at the
same time. The template is not a valid decision and does not participate in numbering.

See the repository [LICENSE](../../LICENSE).
