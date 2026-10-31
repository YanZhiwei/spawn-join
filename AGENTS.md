# SpawnJoin 项目协作与工程规则

本文件是 SpawnJoin 仓库的项目级执行契约，适用于根目录下所有包。它约束的是工作方式、架构边界和验证证据，不替代具体包的 `pyproject.toml`、README 或未来更深层目录中的 `AGENTS.md`。

如果规则之间发生冲突，遵循以下优先级：系统/平台安全规则 > 用户当前明确要求 > 更深层目录的项目规则 > 本文件 > `README.md` 和代码中的既有约定。发现冲突时，先记录冲突及影响，再选择最小、可验证的改动。

## 0. Spec Kit 与 Speckit Delivery 治理分层

本仓库已完成 Spec Kit 初始化，并通过固定 Release 安装 Delivery Bundle v0.2.2。当前默认
OpenCode，入口为 `.opencode/commands/speckit.delivery.route.md`（`/speckit.delivery.route`），
保留 Codex 核心技能。旧项目 sd/speckit-delivery 拷贝门面已移除；不转发到用户级旧技能。
安装与升级以 [`Delivery 安装说明`](docs/development/spec-kit-delivery.md) 为准。
安装文件存在不表示任何 Feature 的 Spec、Plan、Tasks、ADR 或 Evidence 已执行。

当前 `.specify/` 已包含模板、PowerShell 脚本、Codex/Speckit 清单和 bundled workflow；
Constitution 已批准为 `v1.0.0`。已有 Harness Foundation 和 Python Quality Gates Feature，
质量工具及 GitHub Actions 配置已加入；`.specify/extensions.yml` 已登记扩展，但
`auto_execute_hooks: false`、`hooks: {}`，没有可执行 hook。Delivery、Quality 等配置已接入；
v0.2.2 Bundle 已安装并拥有 13 个组件，项目配置和核心任务定制保留。Feature 的 Slice
计划/门禁和 Handoff 正文路径已接入，PR 模板默认使用 v0.2.2 随包中文模板及其
`.github/pull_request_template.md` 静态副本；项目默认启用 `pr_slicing: "auto"` 的 Slice
路径，所有切片为 standalone 或 flagged 时按 stacked 顺序 squash 到 `main`，`tasks.md` 仍是唯一执行队列。
Bundle 安装不等于 Ralph 已执行，也不授权自动 push/merge/发布。
不得把 standalone 质量入口、workflow 配置或本机成功误报为完整自动化或远端强制已通过；
缺失时明确报告，不静默退回一套“看起来像通过”的通用流程。

### 0.1 变更路由

每项工作先选择且只选择一条交付路由：

- **Lightweight**：文档、规则、机械性或行为保持不变的窄范围改动；不默认创建 Feature Spec。
- **Bugfix**：有可复现缺陷、边界明确，并且可以先用失败证据表达期望行为；先建立 red evidence，再修复和回归。
- **Feature**：新增行为、跨模块或跨包改动、公共 API、持久化数据、安全/权限、架构或长期依赖决策；必须走完整的 Spec/Plan/Tasks 和相应审查。

如果路由不明确，先选择更明确的路线，直到范围证据支持降级；不要因为改动看起来很小，就绕过公共契约、安全或架构决策。

### 0.2 工件职责

当项目完成 Spec Kit 初始化后，遵循以下职责分离：

- `.specify/memory/constitution.md`：项目原则、治理和合规约束。
- `specs/<feature-id>/spec.md`：用户价值、场景、范围、需求和验收标准。
- `specs/<feature-id>/plan.md`：技术上下文、设计、依赖、目录布局和验证方案。
- `specs/<feature-id>/tasks.md`：唯一执行队列；任务必须有 ID、依赖、目标文件和可验证的完成条件。
- `research.md`、`data-model.md`、`contracts/`、`quickstart.md`：仅在当前 Feature 确实需要时创建，并由 Plan 引用。
- ADR：只记录会约束多个实现点或未来演进的长期决策；本项目唯一根目录为 `docs/decisions/`，分类、编号、状态和模板以该目录的 README 为准，不自行创建第二套 ADR 目录。Delivery 的 ADR/context 配置已指向同一路径，但自动 hook 未启用，不宣称 ADR 自动化已闭环。
- `.specify/delivery/<feature-id>/evidence.md`：Delivery evidence 配置已启用，记录实际
  outgoing diff 的命令、工作目录、环境、退出码、结果、base/head 和残余风险。

Lightweight 改动不应为了形式创建空的 Spec/Plan/Tasks；但必须保留范围、变更路径和针对性验证证据。Feature 的实现不能绕过 `tasks.md` 直接凭自然语言清单执行；`slices.md` 只提供可独立评审/合并的边界，不得增删或重排任务。

收口前将稳定的设计理由和必要图表提炼到 ADR 或当前架构说明，不将 ADR 变成第二套
任务队列或运行日志。Agent 按主要职责复用领域/子领域分类，并说明理由；归属不明确时
询问维护者。`/specs/` 按用户要求加入 Git 忽略，仍保留本地 Feature 执行职责；
历史 Specs 已按 ADR-0002 取消跟踪但保留本地文件，不得擅自删除；长期契约与证据不得只留在忽略目录。
绘制 ADR 技术图时读取项目内 `.agents/skills/fireworks-tech-graph/SKILL.md`，用法见
[`技术图说明`](docs/development/technical-diagrams.md)；不以全局同名版本替代项目固定副本。

### 0.3 Ralph 与收口规则

在项目启用 Ralph/完整 Delivery 流程后：

- 每次只执行一个依赖已满足的任务；任务重叠、共享公共契约、迁移或未决设计会形成阻塞边。
- Feature 在 `tasks.md` 之后执行 Slice 计划与 Slice Gate；Ralph 在每个 Slice 边界验证声明的 trunk-safe、flag 或 integration checkpoint，失败则回到 Slice 规划，不以继续执行掩盖失败。
- Worker 返回变更路径、命令、结果、残余风险和阻塞，不自行勾选任务或创建收口提交。
- Orchestrator 在任务关闭前验证验收证据、允许路径、当前内容/需求快照、声明的检查、
  `QUALITY_VERDICT`、`STANDARDS_VERDICT` 和独立 `REVIEW_VERDICT`；仅 `HEAD`/路径相同不足以复用旧证据。
- 只有 `RALPH_TASK_GATE: PASS` 才能更新任务状态并创建该任务的提交；所有任务都有当前有效 receipt、工作区干净且收口证据完整后，才能声明全量完成。
- Handoff 必须写出真实 `PR_BODY_PATH` 并给出 `gh pr create --body-file` 提示；仅聊天正文不算可持久化交付。项目默认启用 Slice 计划；stacked 使用手动顺序 PR，integration 仍需单独策略评审并受仓库线性历史约束。

没有对应的 `.specify` 配置、质量命令或运行时证据时，只报告缺口；不要用技能文件存在、命令文本存在或一次静态阅读替代实际执行证据。

### 0.4 质量门与标准审查

- **Quality Gate** 只判断实际配置并实际执行的机械检查：格式、lint、类型、测试、复杂度、构建、包产物、证据结构、ADR 索引和 Spec/Tasks 一致性；缺少工具、配置或环境时结果是 `blocked`/未执行，不是 `pass`。
- **Standards Review** 判断 DRY、模块拥有者、目录归属、公共 API、依赖方向、架构边界和可维护性；它不能用一次测试通过替代，也不能把个人偏好伪装成项目标准。
- **Evidence** 将检查绑定到真实 outgoing diff、工作目录、命令、退出码、base/head 和时间；`HEAD` 或范围变化后，旧证据必须重新确认。
- 质量简报、静态阅读和文档中“应该通过”的描述只能作为准备信息，不能替代 `QUALITY_VERDICT: pass`、`STANDARDS_VERDICT: pass` 所需的实际证据。

## 1. 项目定位与当前基线

SpawnJoin 是一个 Python monorepo。每个包目录都是可以独立构建、测试、版本化和发布的 Python Distribution；每个 Distribution 也是独立的 uv project，拥有自己的 `.venv` 和 `uv.lock`。`packages/core` 与 `packages/infra` 只是架构分组，不是 Distribution；仓库根目录不创建共享 uv 环境或根级 uv workspace。

当前必须保持的命名约定：

- 品牌名：`SpawnJoin`。
- Python Distribution：使用连字符，例如 `spawn-join-core`。
- Python import package：使用下划线，例如 `spawn_join_core`。
- 包使用 `src/` layout；公共 API 通过包的 `__init__.py` 明确导出。

### 1.1 目录结构与文件归属

完整且易变的仓库地图维护在 [`docs/architecture/repository-map.md`](docs/architecture/repository-map.md)，
包职责和依赖方向维护在 [`docs/architecture/package-boundaries.md`](docs/architecture/package-boundaries.md)。
Harness 的阶段计划、上下文、评审和证据入口是 [`harness/README.md`](harness/README.md)。
本文件只保留不会因普通模块增删而频繁变化的边界规则，不复制完整目录树或包职责表。

稳定目录规则：

- `packages/core` 和 `packages/infra` 是架构分组；每个下层 Distribution 必须拥有自己的 `pyproject.toml`、`src/<import_package>/`、独立 uv `.venv`、`uv.lock` 和独立构建边界。
- Python 源码只能放在对应 Distribution 的 `src/` 下；不要在仓库根目录创建共享 `src/`，也不要把源码直接堆在 Distribution 根目录。
- 根 `pyproject.toml` 只允许共享 tool 配置，不定义 project/build-system/dependency-groups
  或 uv workspace；`scripts/` 的 PowerShell 文件只承担开发检查，不是领域运行时代码。
- 测试以 Distribution 为边界放在对应包的 `tests/`；跨包契约测试必须明确依赖的包和安装方式。
- `.agents/skills/` 是项目级 Agent 能力，不是 Python 包；`.codegraph/` 是本机索引，不得提交数据库、日志、daemon 状态或 socket。
- `.agents/skills/fireworks-tech-graph/` 是固定上游提交的第三方工具副本；其自带脚本是开发工具例外，不是领域源码或新增 Distribution。保留原始许可证及来源，不引入包级/根级运行时依赖，也不对其执行本项目的全量格式重写。
- `.specify/` 已作为项目级 Spec Kit 基础设施保留；`specs/` 仅在 Feature 路由实际需要时创建，不要为 Lightweight 文档改动手工制造半套 Feature 工件。
- `harness/` 只维护阶段计划、材料性上下文、评审、验证证据和实际执行日志，不替代 Spec、Plan 或 Tasks，也不是业务源码。
- Python 构建产物不得进入版本控制，包括根目录或包目录下的 `build/`、`dist/`、`*.egg-info/`、缓存和临时报告；`harness/build/` 是应提交的治理文档目录，不属于 Python 构建产物。

### 1.2 包拥有者与依赖方向

详细映射以 `package-boundaries.md` 和各包的 `pyproject.toml` 为准。以下约束属于稳定
架构规则：

1. `spawn-join-core` 不得依赖其他 SpawnJoin 领域包，也不应因一个小工具引入第三方依赖。
2. `spawn-join-llm-provider` 可以依赖 Core，但不得依赖 LangChain 或具体 Provider SDK。
3. `spawn-join-llm-provider-langchain` 负责框架适配和 Provider 实现，不能把框架类型泄漏回协议包。
4. LLM 等领域的抽象留在领域包中，不把所有接口集中到 Core。
5. 新增包、跨领域模块或公共抽象必须有真实复用需求和清晰的依赖理由；不要预先创建 `utils.py`、`helpers.py`、`constants.py` 等收纳模块。
6. 当前没有 `spawn-join-database` 和 `spawn-join-agent`；除非出现明确需求并完成边界设计，不要提前创建它们。

当前配置基线（2026-10-31）：四包各自拥有 uv 本地开发源、锁文件、dev group 和 `tests/`；
共享 Black/isort/Ruff/Pyright/pytest 配置与 `scripts/quality.ps1`、actionlint/PSScriptAnalyzer
静态分析和 GitHub Actions 已加入；Delivery 默认启用 `pr_slicing: "auto"`，standalone 或
flagged 切片按 stacked 顺序 squash 到 `main`。
活动 Feature 以本机 `.specify/feature.json` 为准，不把历史质量门 Feature 当作当前任务。
构建仍有缺少包级 README 的非阻塞警告；Release Delivery 组件与质量 Profile 已接入，
不代表 Ralph 已运行，提交/推送/合并仍需授权；Spec Kit hook 和
发布流水线仍未启用；Ruleset 已启用 PR、线性历史和 required `Quality Gate`。实际验证结果
以当前 Feature 的 Harness evidence 为准，不用配置存在替代运行证据。因此：

- 不得把“构建成功”表述为“测试、类型检查和发布流程全部通过”。
- 后续若修复包级 README 警告，应单独记录为构建元数据改动。
- 新增行为时，应同步补充测试；不要以当前尚未有测试为理由跳过边界覆盖。
- 这是一份会过期的观察快照；当包目录、`pyproject.toml`、测试、CI、类型检查、Spec Kit 或 Delivery 配置发生变化时，必须重新检查并更新，不得用旧快照替代现场证据。

## 2. 变更前先锁定基准

任何重构、模块化或类型改动开始前，先记录：

1. `git status --short --branch` 和当前 `HEAD`。
2. 受影响包的目录、`pyproject.toml`、公共导出和调用入口。
3. 当前可观察行为：返回值、异常类型、日志/事件、序列化格式、导入路径、构建产物或命令行输出。
4. 当前依赖、权限和数据流：输入来自哪里、经过哪些边界、谁拥有副作用、错误如何传播。
5. 与本次范围相关的验证命令及其原始结果。

“不改变行为”必须具体到可观察输出，而不是只描述意图。若基线无法运行，要写明阻塞原因、已尝试的命令和替代证据；不能把未执行的检查标记为通过。

## 3. 小步重构工作流

每次只处理一个独立模块、一个清晰的职责边界或一个可验证的重构目标。不要借重构之名顺便改写无关包、格式化整个仓库或引入未来功能。

按以下顺序执行：

### 3.1 识别边界

- 找出重复模式、过长函数、混合职责、跨层依赖和不清晰的公共 API。
- 先判断候选边界属于 Core、领域协议、基础设施适配还是业务组合层。
- 优先复用已有抽象；只有现有抽象无法表达真实需求时才新增抽象。
- 明确本次不处理的相邻问题，防止范围扩张。
- 对仅凭推测、且现实发生概率极低的竞态条件或安全边界情况，不得悄然引入锁、重试、状态机、隔离、冗余校验等复杂机制。需要处理时，先向用户说明：具体可能出什么问题、触发条件是什么、发生概率及判断依据、影响范围是什么，以及额外复杂度的实现和维护成本；只有得到用户明确同意后，才能扩大本次范围。
- 如果风险已有现实证据、现有契约要求、线上事故记录或可复现案例，就不再把它归类为纯推测风险；应按正常缺陷或安全问题处理，并在变更说明中保留证据和验证结果。

### 3.2 先写蓝图，再写代码

实现前先用简短文字描述目标模块或函数的布局，至少包括：

- 单一职责和不负责的事情；
- 输入、输出、异常和副作用；
- 所属包及依赖方向；
- 公共 API、内部实现和可替换扩展点；
- 关键类型及其边界；
- 需要覆盖的正常、空值、错误、取消、超时或外部依赖场景。

蓝图阶段只规划架构，不提前堆叠具体代码、抽象层或未来 Provider。设计无法用现有需求解释时，优先删除它。

### 3.3 增量实现与回归

- 先做最小代码变更，再补齐必要的类型和测试。
- 一次只移动或重构一个独立模块；若必须同时更新调用方，说明这是保持接口一致性所需的配套改动。
- 先保持旧行为和公共导入路径，再在有明确迁移方案时调整契约。
- 每一小步都运行与范围匹配的验证；不要积累多个无法定位的变化后才统一测试。

### 3.4 收尾复核

完成前检查：

- 依赖方向是否仍然单向；
- 公共 API 是否意外扩大；
- 类型、异常和副作用是否与蓝图一致；
- 测试是否覆盖边界而不是只覆盖 happy path；
- 权限、密钥、网络和数据流是否被改变；
- diff 是否包含无关文件或构建产物；
- README、包元数据和运行说明是否仍然准确。

## 4. 可读性、模块化与可复用性

### 4.1 模块职责

- 一个模块围绕一个稳定职责组织；配置、协议、异常、Provider 适配和观测不要无理由混在一起。
- 领域抽象与具体实现分离：`abstractions/` 或协议模块描述契约，`providers/`、`implementations/` 承载实现。
- 适配层负责转换外部 SDK 的请求、响应和错误；Core 与协议包只看稳定的内部契约。
- 只有至少两个组件存在稳定、真实的复用需求时，才把能力提升到 Core。
- 不用“大而全”的 `utils` 模块隐藏所有依赖；共享代码应有明确的拥有者和命名。
- 公共导出要显式、少而稳定；内部模块不要因为位于可导入路径就自动成为公共契约。

### 4.2 类型提示

优先在以下位置补充精准类型：

- 公共函数、方法、类构造函数和协议成员的参数与返回值；
- 配置对象、跨包 DTO、事件、错误载荷和序列化边界；
- Provider/适配器的输入、输出和可选能力；
- 复杂容器、回调、生成器、异步结果和可空值；
- 具有业务含义的字典结构，优先考虑 `dataclass`、`TypedDict`、`Protocol`、类型别名或枚举。

要求：

- 使用 Python `>=3.11` 支持的清晰写法，例如 `X | None` 和 `collections.abc`。
- 非平凡函数写出返回类型；即使返回 `None` 也写 `-> None`。
- 避免无理由的 `Any`、裸 `dict`/`list`、类型忽略和不加说明的强制转换。
- 外部 SDK、JSON 或环境变量在边界处解析、校验和收窄；不要让不可信的宽类型进入核心逻辑。
- 类型应表达真实约束，不为了“看起来有类型”制造过度泛型或重复包装。
- 类型复杂度超过实现复杂度时，优先简化接口或提取有名字的领域类型。

### 4.3 Python 语法与实现规范

- 运行时最低版本为 Python `>=3.11`；不得使用低于该版本的兼容写法，也不得无理由使用高于最低版本的专属语法。
- 遵循 PEP 8 和 PEP 257：4 个空格缩进、禁止 Tab、每行一个主要语句、禁止用分号拼接语句；默认将 88 列作为格式目标，超出时优先重排表达式或提取有意义的局部变量。
- import 按标准库、第三方依赖、本地包分组；优先绝对导入，禁止通配符导入；只为类型检查使用的依赖放入 `TYPE_CHECKING` 并避免运行时循环依赖。
- 模块、函数和变量使用 `snake_case`，类和异常使用 `PascalCase`，常量使用 `UPPER_SNAKE_CASE`，类型别名使用有语义的名称；不要用单字母或 `data`、`obj`、`result` 等无上下文名称隐藏领域含义。
- 函数保持单一职责和较小的控制流；避免可变默认参数、隐式全局状态、深层嵌套和无理由的魔法数字；复杂分支应提取有名字的谓词或领域函数。
- 文件和路径使用 `pathlib.Path`；资源使用上下文管理器或明确的生命周期函数；异步函数中不得执行未隔离的阻塞 I/O，也不得遗忘 `await`。
- 只捕获能够处理的具体异常；禁止裸 `except` 和静默吞错；重新抛出时使用 `raise NewError(...) from exc` 保留原因链，并在跨包边界定义稳定的异常语义。
- Python 库代码不得用 `print` 作为运行时日志；使用模块级 `logging`，日志中不得出现密钥、令牌、完整私有 URL 或未经脱敏的用户数据。
- 公共 API 通过 `__init__.py` 显式导出；内部模块、临时兼容层和测试辅助函数不得因为可导入就自动成为公共契约。
- 格式门使用 Black/isort，lint 使用 Ruff（不启用 I 或 formatter），类型使用 Pyright strict。
  配置、版本归属、命令及失败终态以 `docs/development/quality-gates.md` 为准；不把检查成功
  当成所有架构/风格原则均被机器验证。

### 4.4 注释与文档

- 命名和结构先承担可读性；注释解释“为什么”、约束、取舍和兼容性，不重复“代码正在做什么”。
- 公共模块、协议和复杂边界使用短 docstring，说明职责、输入输出和重要不变量。
- 复杂设计理由写在 README、设计说明或 ADR 中，不把长篇架构讨论塞进函数体注释。
- 任何会影响使用者的导入路径、依赖、配置、错误语义或运行命令变化，都要更新对应文档。

## 5. 测试与验证

测试首先验证行为契约和边界条件，而不是只验证代码行数：

- 正常路径、空输入、缺失配置、非法输入、重复调用和幂等性；
- 异常类型、错误信息中稳定的部分、取消、超时和资源清理；
- 协议与适配器之间的转换、Provider 差异和不支持能力；
- 包的独立安装/导入、公共导出、依赖隔离和构建产物；
- 观测事件、日志字段或错误可见性（如果它们属于可观察契约）。

测试规则：

1. 行为改动与测试在同一小步中完成，或先有能描述目标行为的失败测试。
2. 单元测试不依赖真实密钥、真实私有服务或不稳定网络；需要外部服务时，单独标记为集成验证并记录权限和环境。
3. 不要只运行“最方便”的测试。验证范围必须覆盖实际 outgoing diff；未运行的测试明确标为未运行。
4. 测试框架为各 Distribution dev group 中的 pytest；统一入口为
   `pwsh -NoProfile -File scripts/quality.ps1 -Check test`，零测试必须失败。
   行为变更必须安排针对性测试，不因用户未特别请求而省略。

完整机械门禁入口是 `pwsh -NoProfile -File scripts/quality.ps1`；门禁回归入口是
`pwsh -NoProfile -File scripts/test-quality.ps1`。具体参数、修复命令与 CI 边界见
[`质量门说明`](docs/development/quality-gates.md)。Standards Review 仍单独执行。

### 5.1 CodeGraph 与源码定位

当仓库存在 `.codegraph/` 时，CodeGraph 是理解 Python 源码的首选导航工具：

1. 先运行 `codegraph status`，确认索引是否为最新；索引过期时先运行 `codegraph sync`。
2. 在使用 `rg`、`grep` 或 `find` 定位代码前，优先使用 `codegraph explore`、`codegraph node`、`codegraph callers`、`codegraph callees` 或 `codegraph impact` 理解符号和调用关系。
3. 修改源码后运行 `codegraph sync`；使用 `codegraph affected <file>` 辅助选择受影响的测试。
4. CodeGraph 只提供导航和关系证据，不等于类型检查、测试、构建或安全验证通过；索引缺失或解析不完整时必须如实报告。
5. README、Spec、ADR 和其他普通文档不属于 CodeGraph 的代码关系证据；检索文档时仍应使用精确的文本搜索和链接检查。

### 5.2 按风险选择质量证据

- 文档或 Lightweight 改动：检查实际 diff、Markdown 结构/链接和 `git diff --check`；只有涉及源码关系时才要求 CodeGraph 同步。
- Python 行为改动：至少执行受影响 Distribution 的构建和针对性测试；跨包公共契约还要验证依赖方向、导入路径和适配器边界。
- 类型或格式规范改动：如果 Ruff、Pyright、mypy 或其他工具已经配置，必须执行项目实际配置的命令；工具未配置时只能报告“规范已写入、自动门禁未启用”。
- 外部服务、权限、持久化、并发或安全边界改动：补充对应的集成、迁移、资源清理或安全证据；没有环境或权限时标记为 blocked/未执行，不得标记为通过。

当前可复现的构建验证目标（要求使用临时输出目录）：

```bash
uv build packages/core/spawn-join-core --out-dir <temporary-output-dir>
uv build packages/core/llm-provider --out-dir <temporary-output-dir>
uv build packages/infra/llm-provider-langchain --out-dir <temporary-output-dir>
uv build packages/infra/spawn-join-observability --out-dir <temporary-output-dir>
```

每个 Distribution 的 uv 环境和锁文件也必须独立验证：

```bash
uv lock --check --directory packages/core/spawn-join-core
uv lock --check --directory packages/core/llm-provider
uv lock --check --directory packages/infra/llm-provider-langchain
uv lock --check --directory packages/infra/spawn-join-observability

uv sync --locked --directory packages/core/spawn-join-core
uv sync --locked --directory packages/core/llm-provider
uv sync --locked --directory packages/infra/llm-provider-langchain
uv sync --locked --directory packages/infra/spawn-join-observability
```

这些命令应从仓库根目录执行；它们分别使用各包目录下的 `pyproject.toml`、`uv.lock`
和 `.venv`，不得改写或创建根级 uv project。

不要把 `<temporary-output-dir>` 当作真实目录提交；验证结束后检查并清理 `dist/`、`build/`、`*.egg-info/` 和其他构建副作用。完成后至少运行：

```bash
git diff --check
git status --short --branch
```

只有实际执行并得到成功结果的命令才能写成“通过”。对于警告、环境缺失、未配置工具或跳过的检查，保留原始现象并说明影响。

## 6. 依赖、权限与数据流

### 6.1 依赖

- 新依赖放在实际拥有该能力的包中，并在对应 `pyproject.toml` 写明合理版本范围。
- 不为了测试一个领域功能把 SDK 带入 Core 或框架无关协议包。
- 引入依赖前检查许可证、维护状态、版本兼容性、传递依赖和已知问题；记录选择理由。
- 如果一个 Provider 需要独立版本、依赖、测试或维护周期，再考虑拆成独立 Distribution。

### 6.2 权限与敏感信息

- 密钥、令牌、私有 URL 和个人凭据不得进入源码、测试 fixture、日志或提交历史。
- 涉及云服务、模型 Provider、私有 Registry 或外部写入时，先说明所需权限、数据范围、读写动作和失败后的状态。
- 默认使用最小权限；没有明确授权时，不执行外部写入、发布、删除或不可逆迁移。

### 6.3 数据流与副作用

实现或重构涉及外部边界时，画出或文字记录：

```text
输入/配置 -> 校验与类型收窄 -> 领域协议 -> 适配器/外部服务
       -> 响应转换 -> 可观察输出/错误 -> 日志、追踪或指标
```

需要明确谁拥有网络、文件、数据库、缓存、线程或任务等副作用；Core 和协议层尽量保持纯粹、可测试和可替换。异常不能被静默吞掉；如果需要转换异常，保留足够的上下文和原始原因。

## 7. 遇到陌生功能时借鉴开源实现

当要实现仓库尚未覆盖、且团队不熟悉的功能时，不要立即从零编码。先检索 GitHub 上维护活跃、许可证明确、与当前 Python 版本和依赖边界相容的同类项目，再做小范围比较：

- 最近提交、发布节奏、Issue/PR 活跃度和维护者响应；
- LICENSE、版权要求和是否允许当前分发方式；
- 模块边界、扩展点、错误处理、测试策略和数据流；
- 运行时依赖、传递依赖、版本约束、性能与资源生命周期；
- 已知限制、安全问题、兼容性风险和迁移成本。

借鉴结果应在设计说明或变更说明中记录来源、版本/提交、许可证、采用的思路和未采用的部分。优先学习经过验证的设计，不直接复制来源不明、许可证不兼容或无法解释的代码；即使许可证允许复制，也必须重新审查其边界、依赖和与本仓库的兼容性。

## 8. 变更说明与可复现交付

每次完成后，交付说明至少包含：

1. 改了什么，以及涉及哪些文件/包。
2. 关键设计：为什么选择这个模块边界、类型和依赖方向；哪些方案被明确排除。
3. 不变量和可观察输出是否保持；若改变，列出迁移影响。
4. 测试、构建、静态检查的精确命令、结果和未执行项。
5. 新增依赖、权限、配置、密钥和数据流变化。
6. 用户或其他开发者可以复现结果的安装、运行和验证步骤。
7. 已知警告、剩余风险和后续建议；不要把计划工作描述成已完成。

交付报告还必须标明当前路由和治理证据：

- Lightweight：说明为什么不需要 Spec/Plan/Tasks，以及针对性验证为什么足够。
- Bugfix：附上缺陷复现、修复前 red evidence、修复后回归结果和未覆盖的环境。
- Feature：列出 `spec.md`、`plan.md`、`tasks.md`、相关 ADR、review 和 evidence 的路径与状态；`tasks.md` 未收口或 evidence 不匹配当前 `HEAD` 时，不得声明完成。
- 所有路由：记录 base `HEAD`、当前 head、实际 changed paths、执行命令、工作目录、退出码和结果；新提交产生后，旧 review/evidence 必须重新确认范围。

提交前检查清单：

- [ ] 工作区基线和最终状态已记录。
- [ ] 本次只处理一个独立模块或明确的配套接口变更。
- [ ] 目标蓝图先于实现确定，且没有引入 YAGNI 抽象。
- [ ] 公共 API、依赖方向、命名和包边界符合本文件与 `docs/architecture/package-boundaries.md`。
- [ ] 关键类型和外部边界已精确标注。
- [ ] 边界条件、异常和资源清理有测试或已记录验证限制。
- [ ] 依赖、权限、敏感信息和数据流已检查。
- [ ] 构建产物未留在工作树，`git diff --check` 已执行。
- [ ] 运行说明足够让他人复现，未将警告或未执行检查写成通过。
