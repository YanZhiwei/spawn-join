# SpawnJoin 项目协作与工程规则

本文件是 Agent 在 SpawnJoin 仓库的工作入口。[Constitution](.specify/memory/constitution.md) 定义所有贡献者和交付路线共同遵守的工程原则。
Spec Kit 的 Plan 和 Analyze 按宪法检查设计与任务。Agent 按本文件选择入口、查找约束、执行检查并交付结果。

## 0. Spec Kit 与 Speckit Delivery 治理分层

**先确认范围和授权。** 规则冲突时，按系统/平台安全规则、用户当前明确要求、Constitution、适用的更深层项目规则、本文件、README 和代码既有约定的顺序处理。记录冲突和影响，选择可验证的最小改动。
宪法 MUST 的例外须经用户明确批准，并按 [Governance](.specify/memory/constitution.md#governance) 记录原因、影响、临时措施和失效条件。

涉及云服务、模型 Provider、私有 Registry 或外部写入时，先说明所需权限、读写的数据和失败后的状态，按最小权限执行。所有外部写入，以及提交、推送、创建或合并 PR、发布、删除和不可逆迁移，均须用户明确授权。
安装 Delivery、生成 Handoff 和 CI 通过均不会授予这些权限。密钥、令牌、私有 URL 和未脱敏用户数据不得进入源码、夹具、日志、证据或提交历史。

### 0.1 选择交付路线

按宪法的[开发流程与质量门](.specify/memory/constitution.md#development-workflow-and-quality-gates)选择一条与风险匹配的路线。
范围不明时先调查，有证据再降级。公共 API、持久化、安全和架构变化应显式识别。

| 路线 | Agent 的起步动作 | 交付时核对 |
|---|---|---|
| Lightweight | 对文档、规则或行为保持的窄改动，锁定路径和可观察结果。 | 记录实际差异和针对性检查。 |
| Bugfix | 对有界缺陷，先复现并取得能区分修复前后的失败证据，再修复。 | 附 red evidence、回归结果和未覆盖环境。 |
| Feature | 对新增行为、跨模块/跨包变更、公共 API、数据、安全或长期架构决策，按 Spec、Plan、Tasks 和审批推进。 | 核对任务、Slice、审查、ADR 和真实交付证据。 |

OpenCode 使用 `/sd` 或 `/speckit.delivery.route`，Codex 使用 `$speckit-sd` 或 `$speckit-delivery-route`。
两者共用[项目配置](.specify/extensions/delivery/delivery-config.yml)。
先从[角色阅读导航](docs/architecture/repository-map.md#role-based-reading)定位本次工作所需材料。
版本、安装、升级和宿主入口由 [Delivery 安装说明](docs/development/spec-kit-delivery.md) 与 [ADR-0004](docs/decisions/engineering/0004-release-managed-delivery-installation.md) 维护。
保留项目配置与模板定制，安装器管理的组件、命令和协议由安装器更新。项目的[自动 Hook 配置](.specify/extensions.yml)保持关闭。

### 0.2 规划、执行与证据

- Feature 以本机 `.specify/feature.json` 指向的实际目录为准。`spec.md` 记录用户场景和验收，`plan.md` 记录设计及验证，`tasks.md` 是唯一执行队列。
  每项任务写明 ID、依赖、目标文件和验收。研究、模型、契约等附属工件按需由 Plan 引用。Lightweight 使用本路线的范围和证据即可。
- 生成 Tasks 后规划 Slice 并通过 Slice Gate，按批准的映射执行。任务重叠、共享契约、迁移和未决设计形成依赖。Ralph 每次只执行一个依赖已满足的任务。边界校验失败时回到 Slice 规划。
  Worker 返回变更、命令、结果和阻塞，由协调者核对允许路径、当前内容及需求快照、Quality、Standards 和独立 Review 回执。
  只有 `RALPH_TASK_GATE: PASS` 才可勾选任务并在已获授权时提交。全量完成还要求任务回执有效、工作区干净、收口证据齐全。
- Spec Kit 的规划工件按[既定策略](docs/decisions/engineering/0002-untrack-historical-feature-artifacts.md)留在 Git 忽略的 `specs/`，保留历史文件。
  长期决策归入 [ADR 索引](docs/decisions/README.md)对应领域，说明归属理由，归属不明时询问维护者。
  绘制 ADR 技术图时按[技术图说明](docs/development/technical-diagrams.md)读取[项目固定的 Fireworks 技能](.agents/skills/fireworks-tech-graph/SKILL.md)。
  持续有效的要求、决策和证据应能从可共享材料查到。
- [Harness](harness/README.md#source-of-truth-boundaries) 保存阶段计划、材料性上下文、审查、证据和实际进度。
  调查交接复用 [Context](harness/context/README.md#investigation-continuity)，可复用经验写回[对应知识的维护位置](harness/code_review/README.md#closure-and-reusable-learning)。
  本次 Delivery 的持久证据写入 `.specify/delivery/<delivery_run>/evidence.md`，运行与恢复沿用同一 run 的 runtime。
- Handoff 产出实际 `PR_BODY_PATH` 和 `gh pr create --body-file` 提示。按批准的发布分组填写[项目 PR 模板](.github/pull_request_template.md)，单 PR 或最后一层必须在 PR 的 Git 树中带上本次共享证据。
  standalone/flagged 切片采用 stacked 方式时按顺序手工 squash 到 `main`，integration 方式另核对线性历史约束和获批策略。
  按[交付收尾步骤](docs/development/spec-kit-delivery.md#pr-结果与交付收尾)用原运行执行 Close。PR 合并或关闭时核对 GitHub 结果，运行被替代时核对替代记录。相关 ADR 的采纳以维护者记录的明确决定为准。

## 1. 确认包与架构归属

先从[仓库地图](docs/architecture/repository-map.md)找目标 Distribution，再按[包职责与依赖方向](docs/architecture/package-boundaries.md#dependency-direction)、适用 ADR、该包的 `pyproject.toml` 和公共导出核实边界。
新增、移动或退役包时同步维护这些拥有清单的文件及消费它们的质量配置。

- 品牌名为 SpawnJoin。Distribution 名用连字符，import package 用下划线。每个包独立使用 uv、`pyproject.toml`、`uv.lock` 和 `.venv`。
  源码放在该包的 `src/`，测试放在 `tests/`，公共接口由 `__init__.py` 显式导出。跨包测试说明依赖和安装方式。
  根 `pyproject.toml` 只承载共享工具配置，根目录不建 uv workspace。
- 按[宪法 III](.specify/memory/constitution.md#iii-dry-with-clear-ownership)审查抽取。拟提升到 Core 或 Common 时，列出真实消费者并核对依赖方向。
  区分领域协议、框架适配、网络 transport、离线同步和宿主装配的拥有者。新包或公共抽象须有已证实的需要及边界设计。
- 涉及持久化、队列、后台执行或常驻循环的可复用运行时/基础设施包，默认实现须能在无外部服务的桌面运行，公共契约须能经端口切换服务端存储和消息队列。服务端档位禁用 SQLite，多租户由宿主或可选适配器提供。
  产品宿主选择部署档位并依赖相应包。
  先核对 [ADR-0016 的适用范围](docs/decisions/engineering/0016-desktop-first-service-ready-packages.md)和具体包已经接受的 ADR。
  纯协议、类型、辅助包及调用方拥有的资源装配沿用各自边界。
- `scripts/` 放开发检查，`.agents/skills/` 放 Agent 技能。固定的 Fireworks 副本保留来源与许可证，隔离其工具依赖，并排除项目级格式重写。
  本机 CodeGraph 数据库、日志和 daemon 状态、Python 缓存及构建产物不入库。`harness/build/` 保存应跟踪的阶段文档。

## 2. 修改前锁定基准

1. 记录 `git status --short --branch` 和 `git rev-parse HEAD`，识别已有改动。按任务记录受影响的包、导出、调用入口、依赖方向以及所需权限。
2. 对重构、模块或类型变更，固定可观察行为，例如返回值、异常及原因链、序列化、导入路径、事件、CLI 输出或产物。记录相关检查的原始结果。基线跑不通时写出具体命令、阻塞和替代证据。
3. 仓库有 `.codegraph/` 时，理解源码先运行 `codegraph status`，过期则 `codegraph sync`。
   优先用 `codegraph explore`、`node`、`callers` 或 `impact` 查关系，再按需做文本检索。源码修改后同步，用 `codegraph affected <file>` 辅助选测试。
   文档使用文本和链接检查。索引缺失时直接使用源码检索，有解析缺口时记录限制。

## 3. 设计、实施与回归

- 重构前写出本次蓝图，说明职责与范围、所属包、输入输出、异常、副作用、关键类型、公共接口或扩展点，以及需要验证的边界。涉及 I/O 时，沿输入校验、协议、适配器、观测与清理追踪拥有者。
  引入依赖前核对许可证、维护状态、版本范围、传递依赖和实际消费方。
- 遇到陌生能力时，按[宪法 V](.specify/memory/constitution.md#v-simplicity-incremental-delivery-and-evidence)核对同类开源项目。
  记录来源与版本、许可证、边界、错误处理、测试、已知限制及采纳取舍。使用上游代码前复核其来源、许可与本项目适配性。
- 每步处理一个可验证目标，先复用已有实现，保留旧调用方依赖的行为、公开导入和异常语义。改变既有公共契约或导入路径前，须有明确的迁移方案。必须连带改调用方时说明原因，并同步运行回归。
  删除错误处理、资源释放、取消/超时、锁等并发保护、上下文传播或异常原因链之前，须有证据证明相应保护已无必要。
- 拟为纯推测的低概率竞态或安全场景增加锁、重试、隔离等机制前，向用户说明触发条件、发生概率及依据、影响和维护成本，取得明确同意。有已知契约、可复现案例或事故证据时，按正常缺陷处理并保留证据。

## 4. 代码与文档审查

### 4.1 模块职责

用[宪法 I–III](.specify/memory/constitution.md#core-principles)核对命名、内聚和复用。把配置、协议、异常、适配与观测放在各自的拥有者处。
提取函数或类型应能解释它命名的概念、隔离的边界或稳定复用点。按真实消费者审查公共导出，避免无职责的 `utils.py`、`helpers.py` 或 `constants.py`。

### 4.2 类型提示

按[宪法 IV](.specify/memory/constitution.md#iv-testable-contracts-and-precise-types)检查公共 API、非平凡函数、协议成员、构造器、回调与异步返回类型，包括 `-> None`。
在 SDK、JSON 与环境变量边界解析校验并收窄类型。有业务语义的结构选用合适的 dataclass、TypedDict、Protocol 或枚举。使用 `Any`、裸容器、类型忽略或强制转换时说明理由。

### 4.3 Python 实现

遵循项目最低 Python 3.11、PEP 8 与 PEP 257。使用四空格、一行一个主要语句和 88 列格式目标。
import 按标准库、第三方、本地包分组，优先绝对导入，纯类型依赖用 `TYPE_CHECKING`，避免通配导入及循环依赖。命名使用 Python 约定，表达式、控制流或泛型难读时优先写清中间步骤。

用 `pathlib.Path` 管理路径，显式管理资源生命周期，异步路径隔离阻塞 I/O 并正确 await。仅捕获能处理的具体异常，转换异常时用 `raise ... from ...`。
库日志用模块级 `logging` 并脱敏。复核可变默认值、隐式全局状态及隐藏关键条件的推导式。
格式、lint、严格类型和复杂度使用[仓库实际配置](docs/development/quality-gates.md#tools-and-ownership)。

### 4.4 注释与文档

- 注释解释原因、约束和兼容性。公共模块、协议及复杂边界用短 docstring 说明职责和不变量。长期设计理由写入拥有它的文档或 ADR。
- 自有 README 同目录维护 UTF-8 的完整简体中文 `README.md` 和英文 `README.en.md`。
  两份标题下均放 `[简体中文](README.md) | [English](README.en.md)`，互相对齐示例、语义与同语言导航。机器索引只维护一份，由译文链接。安装器管理的扩展和固定上游技能适用其来源约定。
- 包 README 按“使用者 → 维护者”组织。前半说明用途、适用范围、状态与兼容性、安装、最短可运行示例、真实 API/CLI/配置及默认值、错误、限制和相邻包。
  后半说明职责与边界、目录、开发/测试/质量命令、版本和发布、所有权、贡献及许可证。不适用的小节注明理由。长文提供目录，仓库首页用包选择表和链接分流。
- 新增包或改变导入、依赖、配置、错误或命令时，同步更新双语 README，对照 manifest、实际导出、CLI 和测试复核。迁移时检查标题锚点及本地链接。
  Review 前运行 `speckit.docs-sync.package-readme`，以[包 README 模板](.specify/extensions/docs-sync/templates/package-readme.md)为结构基线。
  项目要求受影响包的文档齐全，缺口阻塞交付。以已核实材料说明能力、版本与发布状态。避免空模板、占位符及无依据的徽章、性能或验证结论。

## 5. 验证与交付

从仓库根执行[质量入口](docs/development/quality-gates.md#local-entry-point)。
全量检查用 `pwsh -NoProfile -File scripts/quality.ps1`。单包传 `-Package` 和该包 manifest 的 Distribution 名，单项传 `-Check`。
门禁自身的故障回归入口为 `pwsh -NoProfile -File scripts/test-quality.ps1`。

| 改动 | 选择证据 |
|---|---|
| 文档或规则 | 核对实际 diff、Markdown 结构、链接和 `git diff --check`。治理文件运行 `-Check docs` 及 `-Check governance`。 |
| Python 行为或公共契约 | 在同一步补充针对性测试并独立构建受影响包。按实际风险覆盖正常、空值、异常、重复调用、取消/超时和清理。跨包核对依赖方向、公开导入和真实消费者。pytest 零测试属于失败。 |
| 格式、类型或质量配置 | 执行已配置的相关检查。涉及产物时用临时输出目录，核实 wheel 安装、导入和构建副作用。各包独立执行 `uv lock --check` 与 `uv sync --locked`。 |
| 外部服务、权限、持久化、并发或安全边界 | 使用独立的集成、迁移、清理或安全证据。单元测试使用离线输入和测试凭据。需要真实服务时写明权限、环境和未覆盖内容。 |

Quality 记录机械检查的结果。Standards 核对职责、依赖、可读性和公共 API，独立 Review 检查当前完整变更。以实际 base/HEAD、工作区内容、需求和检查配置核对证据身份，变化后重新确认。
区分本机、远端 CI 和未执行的检查。

交付时列出路径、设计取舍、行为或迁移影响、命令与工作目录、退出码、结果、权限或数据流变化、复现步骤及剩余风险。报告中保留警告与阻塞。
最后运行 `git diff --check` 和 `git status --short --branch` 核对实际范围。
