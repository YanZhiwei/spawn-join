<!--
Sync Impact Report
- Version change: unratified template -> 1.0.0
- Modified principles:
  - Principle 1 placeholder -> I. Readability First
  - Principle 2 placeholder -> II. Cohesive Object-Oriented Design
  - Principle 3 placeholder -> III. DRY with Clear Ownership
  - Principle 4 placeholder -> IV. Testable Contracts and Precise Types
  - Principle 5 placeholder -> V. Simplicity, Incremental Delivery, and Evidence
- Added sections:
  - Architecture, Package, and Security Constraints
  - Development Workflow and Quality Gates
  - Amendment, versioning, and compliance rules under Governance
- Removed sections: none; all template placeholders were replaced.
- Follow-up TODOs:
  - Configure executable Ruff, Pyright, pytest, pre-commit, CI, and Spec Kit
    extension hooks in a separate Feature; this Constitution defines the
    required outcomes but does not install those tools.
-->

# SpawnJoin Constitution

## Core Principles

### I. Readability First

代码必须优先服务于理解和维护，而不是追求压缩、炫技或抽象数量。公共接口、
业务规则和副作用必须通过清晰的命名、合理的函数长度、明确的控制流和必要的
类型表达出来。注释主要解释选择某种实现的原因、约束和不变量，不重复描述代码
本身已经显式表达的内容。任何无法在局部代码中可靠理解的隐式约定，都必须被
改成命名、类型、测试或文档中的显式契约。

理由：可读性降低修改成本、评审成本和错误定位成本，是 SpawnJoin 作为基础设施
组件长期复用的首要质量属性。

### II. Cohesive Object-Oriented Design

面向对象用于表达有状态对象、不变量、生命周期、策略替换或稳定扩展点；对象必须
拥有清晰的职责和边界，并负责维护自己的有效状态。优先使用组合、依赖注入和小型
协议，避免为了形式强行把简单的数据转换包装成类，也避免没有真实变化理由的深层
继承层次。无状态、独立且易于验证的逻辑可以使用函数或模块表达。每个类、模块和
包都必须有清晰的拥有者，并且只能承担可解释的变化原因。

理由：适度 OOP 可以封装状态和变化点，但无目的的对象层次会隐藏数据流、增加认知
负担，因此“面向对象优先”不等于“所有代码都必须是类”。

### III. DRY with Clear Ownership

必须消除重复的业务知识、协议定义、校验规则和会随需求变化而同步修改的实现；同一
条规则应尽量只有一个权威来源。抽象必须同时具备明确的语义、稳定的边界、合理的
拥有者和可独立验证的契约。仅仅因为代码文本相似，不得提前创建无语义的
`utils.py`、`helpers.py`、`constants.py` 或万能基类；当重复模式尚未稳定，保留少量
局部重复比制造错误抽象更可取。至少出现两处稳定且真实的复用需求后，才考虑把能力
提升到 Core 或共享模块。

理由：DRY 应减少知识重复，而不是为了减少字符数牺牲内聚性和可读性。

### IV. Testable Contracts and Precise Types

任何行为、公共 API、数据结构或模块边界改动，都必须先识别当前不变量和可观测输出，
再说明目标行为。公共函数、公共类方法、跨包协议、外部输入边界和非平凡内部逻辑
必须提供精准的参数与返回值类型；优先使用有语义的类型别名、`dataclass`、
`TypedDict`、`Protocol` 或枚举表达约束，避免无理由的 `Any`、裸 `dict`/`list` 和
无说明的类型忽略。

新增或修改行为必须覆盖成功路径、边界条件、异常、取消、超时和资源清理中与本次
变更相关的部分。测试必须验证契约和可观察结果，而不是只追求代码行覆盖率。外部
SDK、JSON、环境变量、文件、网络和用户输入必须在边界处解析、校验和收窄，不能让
不可信的宽类型直接进入核心逻辑。

理由：明确的类型和可执行测试共同构成模块化设计的安全网，使重构、复用和跨包演进
能够被验证。

### V. Simplicity, Incremental Delivery, and Evidence

必须遵循 KISS 和 YAGNI，只实现当前需求所需的最小正确方案。重构或模块化开始前，
先完成目标模块蓝图、依赖和数据流分析；每次只修改一个独立模块或一个可验证的交付
切片。每一步都必须保留可复现的运行说明、实际执行的命令、工作目录、退出码和
结果；未执行的检查必须明确标记为未执行或 blocked，不得表述为通过。

遇到不熟悉的功能时，先检索维护活跃、许可证明确且与当前 Python 版本和依赖边界
相容的开源项目，比较其模块边界、依赖、错误处理、测试策略和已知问题，再决定是否
借鉴。对于推测性的、几乎不可能发生的竞态条件或安全边界情况，在增加复杂度之前，
必须先向用户说明具体问题、发生概率以及实现、测试和维护成本，并获得明确同意；
不得为了理论上的健壮性悄悄扩大范围。

理由：小步变更和真实证据能缩小回归范围；明确的风险审批能防止基础设施代码被
低概率场景和过度设计拖慢。

## Architecture, Package, and Security Constraints

- 仓库是 Python monorepo；每个 Distribution 必须可以独立安装、测试、构建、版本化
  和发布。Distribution 名称使用连字符，例如 `spawn-join-core`；Python import
  package 使用下划线，例如 `spawn_join_core`。
- Python 源码必须位于对应 Distribution 的 `src/` layout 中，测试以 Distribution
  为边界放在对应的 `tests/` 目录；不要在仓库根目录创建共享源码目录。
- `packages/core` 和 `packages/infra` 是架构分组，不是 Distribution。`spawn-join-core`
  只承载跨领域稳定的配置机制、异常、类型和基础协议，不得依赖领域包。
- 与框架无关的领域抽象必须留在领域包；LangChain、Provider SDK、Redis、数据库等
  外部适配和副作用应留在对应的 infra 或适配器包，不得泄漏回协议和 Core。
- 依赖方向必须保持单向：业务应用可以组合基础设施包，领域包可以依赖 Core，Core
  不得反向依赖领域包。新增跨包依赖必须说明领域理由和验证方式。
- 公共 API 必须通过包的 `__init__.py` 显式导出；内部模块、测试辅助函数和临时兼容层
  不得因为可导入就自动成为公共契约。
- 外部输入、配置、凭据和 SDK 返回值必须在边界处校验和收窄。密钥、令牌、私有 URL
  和未经脱敏的个人数据不得进入源码、fixture、日志或提交历史。
- 网络、文件、数据库、缓存、线程和任务等副作用必须有明确的拥有者；Core 和协议层
  应保持尽可能纯粹、可替换和可测试。异常不得被静默吞掉，转换异常时必须保留原始
  原因和足够上下文。

## Development Workflow and Quality Gates

每项工作必须先选择与风险匹配的交付路线：

- **Lightweight**：文档、规则、机械性或行为保持不变的窄范围改动；不为了形式创建
  空的 Feature Spec。
- **Bugfix**：有可复现缺陷且范围明确；先建立失败证据，再修复、回归和评审。
- **Feature**：新增行为、跨模块或跨包改动、公共 API、持久化、安全、架构或长期
  依赖决策；必须通过 Spec、Plan、Tasks 和相应的质量与标准审查。

开始修改前必须记录：

1. 当前分支、工作区状态和基准 `HEAD`。
2. 受影响的 Distribution、目录、公共导出、调用入口和依赖方向。
3. 当前不变量、返回值、异常、日志/事件、序列化格式、构建产物或命令行输出。
4. 计划修改的路径、验证命令和不在范围内的内容。

Feature 的 `tasks.md` 是唯一执行队列；实现不得绕过任务直接凭自然语言清单推进。
任务必须有唯一 ID、依赖、目标路径和可验证的完成条件。任务之间存在路径重叠、
共享公共契约或未决设计时，必须先解决冲突再并行执行。

每个交付切片至少应根据实际风险选择以下证据：

- 格式和 lint 检查；
- 类型检查；
- 受影响 Distribution 的单元、契约或集成测试；
- 独立构建和安装/导入验证；
- `git diff --check`、变更路径和构建副作用检查；
- 对外部服务、权限、持久化、并发或安全边界的专项验证。

质量门禁只能依据已经配置并实际执行的命令判定。工具尚未配置、环境或权限不可用、
测试未运行时，结果必须标为未执行或 blocked，不得标记为 pass。标准审查还必须单独
检查 DRY、模块拥有者、目录归属、公共 API、依赖方向、类型表达、边界测试和无关改动。

交付证据必须绑定真实 outgoing diff、工作目录、命令、退出码、结果、base/head 和
时间。`HEAD` 或变更范围发生变化后，旧 evidence 必须重新确认。CodeGraph 只提供
源码导航和关系证据，不能替代类型检查、测试、构建或安全验证。

## Governance

本 Constitution 是 SpawnJoin 的项目级治理原则，约束 Spec、Plan、Tasks、代码评审和
交付证据。`AGENTS.md`、包级 README 和 `pyproject.toml` 可以补充执行细节，但不得
削弱本文件中的 MUST 规则；更深层目录规则只在不冲突时生效。

修订本 Constitution 必须：

1. 说明修改原因、影响范围、迁移成本和是否改变现有交付行为。
2. 更新顶部 Sync Impact Report，并按语义化版本规则递增版本号：原则新增或实质扩展
   使用 MINOR，原则删除或重新定义使用 MAJOR，纯文字澄清使用 PATCH。
3. 同步检查 `AGENTS.md`、Spec Kit 模板、hook、质量配置和测试是否仍然一致；必要时
   创建后续 Feature 或迁移任务，不在本次修订中隐式扩大范围。
4. 在评审中明确标记已验证、未执行和 blocked 的检查结果。

任何违反 MUST 原则的实现都必须在合并或交付前修复，或者由用户明确批准例外并记录
原因、影响、临时措施和失效条件。项目不得把静态阅读、工具存在或命令文本存在当作
实际通过证据。

**Version**: 1.0.0 | **Ratified**: 2026-10-25 | **Last Amended**: 2026-10-25
