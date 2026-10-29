# Architecture Decision Records

本目录是 SpawnJoin 长期架构决策（ADR）的唯一根目录。当前通过文档约定和治理检查维护；
Delivery 的 ADR/context 配置已指向本目录，但自动 hook 尚未启用；未来启用时必须继续
指向这里，不另建第二套决策库。

## 什么值得记录

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

## 分类和编号

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

## 生命周期

- `Proposed`：设计候选，尚未批准，不代表已经实现。
- `Accepted`：维护者明确批准的决策；实现、质量门和发布是否完成须另附证据。
- `Rejected`：明确未采纳，保留理由。
- `Deprecated`：不再建议采用，说明现有使用者如何处理。
- `Superseded`：被新的 ADR 替代，双方填写相互链接。

维护者批准后才能将 Proposed 改为 Accepted。Accepted 后的拼写、链接和澄清可以原地
修订并记录日期；改变实质取舍时创建新 ADR，不悄悄改写历史。未生效的替代提案不能提前
将旧 ADR 标记为 Superseded。移动分类时保持编号并更新所有引用。

## 设计与图表

ADR 可以包含接口轮廓、数据结构、不变量、异常、副作用、依赖方向和必要图表，但只写
解释决策所需的部分。细节过长时链接同领域设计说明，不复制整份 Plan 或代码。

图表使用 [项目级 Fireworks 技能](../../.agents/skills/fireworks-tech-graph/SKILL.md)，
项目用法和环境隔离见 [技术图说明](../development/technical-diagrams.md)。简单关系也可
直接使用 GitHub 支持的 Mermaid。SVG 是可维护主产物，PNG 是展示副本；有 JSON 输入时
一起保存。相邻资源放在 `assets/NNNN/` 下，正文用相对路径嵌入并给出文本摘要。

每张图说明是“当前实现”还是“目标设计”，注明箭头语义、事实来源和适用 revision。
不要混淆代码依赖、运行时调用和数据流；不把模型绘制的图片当成架构事实或测试证据。
结构检查通过不等于字体、布局和文字可读性通过，最终图片仍需视觉检查。

## 决策索引

| ID | 领域 | 决策 | 状态 |
|---|---|---|---|
| ADR-0001 | engineering | [分离交付工件与长期设计知识](engineering/0001-delivery-and-durable-design.md) | Accepted |
| ADR-0002 | engineering | [取消跟踪历史 Feature 工件](engineering/0002-untrack-historical-feature-artifacts.md) | Accepted |
| ADR-0003 | engineering | [启用 Spec Kit Delivery 与 Ralph 协议](engineering/0003-enable-delivery-and-ralph.md) | Accepted |
| ADR-0004 | engineering | [以固定 Release 管理 Delivery 安装](engineering/0004-release-managed-delivery-installation.md) | Accepted |
| ADR-0005 | llm-provider | [采用协议原生 LLM 契约与独立渠道边界](llm-provider/0005-protocol-native-llm-contracts.md) | Proposed |

新增或变更 ADR 时同时更新索引、关联链接和当前架构视图。模板不是有效决策，不参与编号。
