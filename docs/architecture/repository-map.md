# SpawnJoin Repository Map

> 本文件是仓库导航视图，不是项目治理原则。
> 包的真实名称、依赖和构建边界以对应 Distribution 的 `pyproject.toml` 为准；
> Feature 的具体影响路径以 `specs/<feature-id>/plan.md` 和 `tasks.md` 为准。

## 当前仓库结构

```text
spawn-join/
├── .github/workflows/             # GitHub Actions 质量检查；无发布或远端设置
├── .agents/
│   └── skills/                    # Spec Kit 与固定版本 Fireworks 技能
├── .codegraph/                    # 本机源码索引；只提交 .gitignore
├── .opencode/commands/             # CLI 生成的项目原生命令，当前默认宿主
├── .specify/                      # Spec Kit 基础设施
│   ├── integrations/              # Codex、OpenCode、Speckit 集成清单
│   ├── extensions/                # Release 组件、registry 与项目配置
│   ├── memory/                    # 项目 Constitution
│   ├── scripts/                   # Spec Kit 辅助脚本
│   ├── templates/                 # Spec、Plan、Tasks 等模板
│   └── workflows/                 # 已安装的 Spec Kit workflow
├── docs/
│   ├── architecture/              # 仓库地图和包边界说明
│   ├── decisions/                 # 按领域分类的长期 ADR、模板和索引
│   └── development/               # 质量工具、技术图和运行说明
├── harness/                        # 阶段计划、上下文、评审和验证证据
│   ├── build/
│   ├── context/
│   ├── code_review/
│   ├── evidence/
│   └── build-log.md
├── packages/
│   ├── core/
│   │   ├── spawn-join-core/          # 独立 uv project、环境和锁文件
│   │   ├── common/                   # 公共辅助实现；默认零依赖、可选校验
│   │   └── llm-provider/             # 独立 uv project、环境和锁文件
│   └── infra/
│       ├── agent-deepagents/           # 独立 uv project、环境和锁文件
│       ├── llm-channel/                # 真实 Provider channel transport
│       ├── llm-model-sync/            # 独立 uv project、环境和锁文件
│       └── llm-provider-langchain/    # 独立 uv project、环境和锁文件
├── AGENTS.md                      # Agent 工作约定和治理入口
├── pyproject.toml                 # tool-only 配置，不是根级 Python/uv project
├── README.md                      # 面向使用者的项目概览
├── scripts/                       # PowerShell 质量入口及其故障回归
├── specs/                         # 本地交付工件；活动 Feature 由本机指针选择
```

本地 `specs/` 按需保存 Feature；`/specs/` 已加入 Git 忽略，
历史工件已按 [ADR-0002](../decisions/engineering/0002-untrack-historical-feature-artifacts.md)
取消跟踪但保留本机文件，未跟踪工件仅保留在本地，不代表任务已经完成。`harness/` 保存阶段约定及实际
记录；质量入口、CI 和 Release Delivery 组件已加入，但没有自动化 Spec Kit hook 或发布。
远端 CI 和分支保护必须另有运行/配置证据，不把配置路径存在当作通过。

## 导航入口

| 主题 | 权威入口 |
|---|---|
| 首页分类导航与项目概览 | [`README.md`](../../README.md) |
| 项目原则和治理 | [`.specify/memory/constitution.md`](../../.specify/memory/constitution.md) |
| Agent 工作约定 | [`AGENTS.md`](../../AGENTS.md) |
| Package 职责和依赖方向 | [`package-boundaries.md`](package-boundaries.md) |
| 长期架构决策、分类和模板 | [`docs/decisions/README.md`](../decisions/README.md) |
| 项目级技术图技能和环境隔离 | [`technical-diagrams.md`](../development/technical-diagrams.md) |
| Feature 规范和任务 | `specs/<feature-id>/`（按需创建） |
| Harness 阶段记录和证据 | [`harness/README.md`](../../harness/README.md) |
| Spec Kit 模板、脚本和 workflow | [`.specify/`](../../.specify/) |
| Python 包元数据和构建配置 | 各 Distribution 的 `pyproject.toml` |
| 质量工具和运行命令 | [`quality-gates.md`](../development/quality-gates.md) |
| Delivery 安装、配置和升级 | [`spec-kit-delivery.md`](../development/spec-kit-delivery.md) |
| Python 源码关系和影响范围 | CodeGraph 索引 |

## Role-based reading

本节是按任务定位知识的导航，不替代适用的 Constitution、根/局部 AGENTS 或当前 run 的
批准工件。先确认路由和真实 base/head；下表的角色是职责，不授权创建子 Agent 或并行写入。
只读研究并行与实现并行仍受项目配置、宿主能力和已批准合作计划约束。

| 角色 / 当前问题 | 最小相关阅读 | 触发后追加 | 返回给既有 owner 的内容 |
|---|---|---|---|
| 协调者：走哪条 Lane、交给谁？ | [AGENTS §0](../../AGENTS.md)、[Harness 权威边界](../../harness/README.md#source-of-truth-boundaries)、当前请求/批准范围 | 进入 SD 时读已安装的 [Route](../../.specify/extensions/delivery/commands/speckit.delivery.route.md) 与本 run runtime 契约；安装问题读 [安装说明](../development/spec-kit-delivery.md) | 路由、非目标、角色读写边界、实际审批/待确认项；补充解释不得悄悄变成用户要求 |
| Explore / Bug assessor：现有行为是什么，哪个假设有证据？ | 目标包 README、当前实现/测试和相关历史、[Context 调查延续](../../harness/context/README.md#investigation-continuity) | 跨包时读 [包边界](package-boundaries.md) 的相关职责/依赖；涉及依赖缺陷或新机制时按 Explore 契约调研上游 | 支持/否定/未决结论、可区分假设的证据、来源版本、残余缺口；Bug assessment 仍拥有根因判断 |
| Plan / Decision：如何设计、为什么这样取舍？ | 当前批准 Spec/Explore、[包边界](package-boundaries.md)、[ADR 索引](../decisions/README.md) 及适用 ADR | 跨组件长期取舍用既有 Decision 流程；技术图读 [固定技能说明](../development/technical-diagrams.md) | 设计响应、约束来源、验证拥有者/缺口、合作/上下文计划，写回既有 Plan/ADR |
| Worker：本任务允许改什么、如何验证？ | 当前任务验收和允许路径、相关 Plan/Brief、目标源文件/测试、[质量命令](../development/quality-gates.md#local-entry-point) | SD Feature 还须按 [Ralph 前置条件](../../.specify/extensions/ralph/commands/speckit.ralph.run.md) 读取准确 checkpoint/task packet；接口变化追踪实际消费者 | 变更路径、精确命令/结果、限制和设计偏差；不自行扩大范围或关闭任务 |
| Quality / Standards / Reviewer：检查什么，证据是否当前？ | 实际完整 diff/需求快照、适用规则、相关消费者、当前 receipts；[六维 Reviewer 契约](../../.specify/extensions/review/templates/reviewer.md) | 按具体风险追踪调用方、异常/取消/清理和兼容性；读前次未关闭 Finding ID | 各自负责的检查/结论及依据；缺输入不是 pass，测试绿不替代语义审查 |
| 收口 / Docs Sync：哪些知识需要保留？ | 当前 findings/context、实际 evidence、受影响包文档；[经验回流](../../harness/code_review/README.md#closure-and-reusable-learning) | 改动生成物/发布边界时核对真实消费者；确有长期决策才进入 ADR | 文档更新或有依据的不更新、已验证经验/无适用经验、未验证环境；不创建第二队列 |

同一角色不必每次重读全部历史。具体 run 的 coordinator 在既有 packet 中指定准确路径与
章节/符号、权威性质、必读原因和条件阅读触发器；已批准后遵循既有快照刷新规则，不为
例行派发改写批准工件。Context 保存材料性摘要/引用，不复制 owner 的原生报告。

知识按用途查找：包 README/公开 API 说明回答“用哪个、怎么用”，架构说明回答“如何组合”，
ADR 回答“为何做长期取舍”；实际成功或失败只在 evidence 中证明。角色应解释来源如何支持
结论，不能把“文件存在/哈希相同”当成已经理解或正确实现。

## 路径语义

- `packages/core` 和 `packages/infra` 是架构分组，不是 Python Distribution。
- 每个下层 Distribution 都拥有自己的 `pyproject.toml`、`src/` layout 和独立构建边界。
- Distribution 名称使用连字符，例如 `spawn-join-core`；Python import package 使用下划线，
  例如 `spawn_join_core`。
- `docs/architecture/` 只维护架构和导航说明，不记录 Feature 的临时任务状态。
- `docs/decisions/` 是唯一 ADR 根，按职责分类，保存长期理由与必要设计图，不替代 Feature 或实际证据。
- `.agents/skills/fireworks-tech-graph/` 保留固定提交的第三方技能及原始辅助脚本，不是领域源码或 Python Distribution。
- `harness/` 只维护阶段计划、材料性上下文、评审、证据和实际执行日志，不替代 Spec/Plan/Tasks。
- `.specify/` 维护 Spec Kit 自身的模板、脚本、集成和 workflow，不存放普通业务设计。
- `.codegraph/` 是本机开发辅助数据，不是 Python 包，也不是业务源码。
- 每个 Distribution 都是独立的 uv project，拥有自己的 `pyproject.toml`、`.venv` 和 `uv.lock`；仓库根目录不创建共享 uv workspace。
- 根 `pyproject.toml` 只包含 tool 表；开发依赖仍由七个保留 Distribution 各自锁定。
- `scripts/` 只存放开发治理 PowerShell 脚本，不承载 Python 领域源码。
- Python 构建产物不得进入版本控制，包括根目录或包目录下的 `build/`、`dist/`、`*.egg-info/`、缓存和临时报告；`harness/build/` 是应提交的治理文档目录。

## 更新规则

当发生以下变化时，必须更新本文件：

- 新增、删除或重命名顶层治理目录；
- 新增、删除或移动 Distribution；
- `packages/core` 或 `packages/infra` 的架构归属发生变化；
- `.specify/`、`docs/architecture/` 或 `harness/` 的职责发生变化；
- README 或 AGENTS 中的导航入口发生变化。

普通模块新增、类新增或同一 Distribution 内部文件移动，不需要把每个文件追加到本地图。
这类变更使用 CodeGraph、IDE 和 Feature 的计划文件导航。

更新本文件时，应同时检查：

1. 目标路径是否真实存在，或者是否明确标记为“Feature 时创建”；
2. 每个 Distribution 的 `pyproject.toml` 是否仍然与包名、源目录和依赖一致；
3. 本文件、README、AGENTS 和包边界文档之间是否出现重复或矛盾；
4. `git diff --check` 和相关文档链接检查是否通过。
