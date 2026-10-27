# ADR-0001: 分离交付工件与长期设计知识

- Status: Accepted
- Date: 2026-10-26
- Domain: engineering
- Classification: 本决策约束全仓库的交付文档与设计知识归属，不属于单一领域包。
- Decision owner: 仓库维护者
- Accepted by / date: 用户在本次会话要求按建议落地 ADR 与项目级图表技能，2026-10-26
- Depends on: 无
- Related: [Constitution](../../../.specify/memory/constitution.md)、[包边界](../../architecture/package-boundaries.md)、[ADR-0002](0002-untrack-historical-feature-artifacts.md)
- Supersedes: 无
- Superseded by: 无

## Context and drivers

Feature 的 Spec / Plan / Tasks 负责需求、设计方案和执行队列，Harness 保存评审与验证。
这些交付工件中的长期设计理由不易按领域检索；将所有内容搬进 ADR 又会混淆需求、
决策和证据。仓库需要按职责分类、可关联的决策记录，以及不依赖个人全局安装的绘图技能。

本次基准为 `bd497d72e928f596e79cdbe5b1466eba4c75ec39` 加已有未提交质量门工作。
该 revision 不包含全部工作树内容；现有 Specs 不能假设已在提交历史中备份。

## Options considered

1. 全部长期保留在 Feature 目录：交付上下文集中，但同领域设计分散，难以发现长期约束。
2. 只保留 ADR：检索简单，但 ADR 会变成需求、任务和运行日志的大杂烩，削弱交付契约。
3. 分层记录并互相链接：保留交付职责，将稳定决策提炼为按领域组织的 ADR；采用此方案。

## Decision

- ADR 唯一根为 `docs/decisions/`，采用领域/子领域目录、全局稳定编号及显式关联。
- Agent 根据主要职责自动建议分类；新领域按需创建，边界不明确时询问维护者。
- ADR 保留背景、选项、决定、关键设计、必要图表、后果和验证入口，不替代正式契约与测试。
- 收口前提炼长期知识；按用户后续要求以 `/specs/` 忽略本地交付工件，现有文件原样
  保留，不取消已跟踪文件的跟踪，也不改变 Feature 对本地 Spec / Plan / Tasks 的要求。
- Fireworks 固定版本内置于 `.agents/skills/fireworks-tech-graph/`，以本地 SVG/PNG 技术图
  为主要用途，不引入图像模型 API、密钥或收费调用。

## Key design and diagrams

这是文档职责分离，不新增运行时模块或公共 API。ADR 中的图说明决策，当前架构文档
说明系统现状；两者链接而非复制。依赖关系用链接表达，不要求决策形成严格分类树。

Fireworks 保留上游 MIT 许可证、固定提交和来源记录。辅助脚本属于第三方开发工具，
不是第五个 Distribution，不进入四包运行时依赖；不对其套用本项目源码格式化或修改
其实现。渲染依赖在独立工具环境中按需安装，不放入根级或业务包 uv project。

本决策不涉及复杂系统流，无需为形式增加图；将来有真实领域设计时再附对应图表。

## Consequences and migration

收益是设计知识可按领域检索、决策可跨领域关联、技能可以随仓库共享。成本是维护索引、
引用和上游工具版本；图中的事实仍须人工核对，安装技能并不保证 PNG 渲染环境齐全。

不批量迁移旧文档或追认历史决策，不更改 Constitution、Feature 路由、现有任务状态或
Delivery 自动化。未来启用 Delivery 必须复用同一个 ADR 根，明确配置后才能声称已集成。

## Verification and implementation status

本 ADR 的 Accepted 仅表示治理选择已获用户授权，不表示所有 Feature 或质量门已通过。
本次安装、文档、保留性验证和残余环境限制见
[ADR/技能 evidence](../../../harness/evidence/adr-and-project-diagram-skill.md)。

## Revision history

- 2026-10-26：根据用户授权采纳文档分层与项目级技术图技能；保留已有 Specs。
- 2026-10-26：用户明确要求 Specs 文件夹设置 Git 忽略；仅增加忽略规则，不删除或取消跟踪。
- 2026-10-27：后续 [ADR-0002](0002-untrack-historical-feature-artifacts.md) 部分取代本决策中
  “不取消已跟踪文件跟踪”的条款；001 已取消跟踪并保留本地文件，分层记录决策继续有效。
