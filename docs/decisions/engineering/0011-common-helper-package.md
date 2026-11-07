# ADR-0011: 用独立 Common 包承载跨领域公共辅助实现

- Status: Proposed
- Date: 2026-11-07
- Domain: engineering
- Classification: 公共基础实现、Distribution 依赖和消费方式约束多个领域，由跨领域工程边界拥有。
- Decision owner: SpawnJoin 维护者
- Accepted by / date: 未批准
- Depends on: 无
- Related: [包边界](../../architecture/package-boundaries.md)、[质量门](../../development/quality-gates.md)、[ADR-0008](../llm-provider/0008-model-file-and-env-boundary.md)
- Supersedes: 无
- Superseded by: 无

## Context and drivers

基准 10b905d46af547330f815498b6f24cfc24449f69：严格 FieldReader 在 LLM 协议包中实现，已有协议 metadata、模型适配和元数据同步消费者。其机制只依赖标准库，但默认异常绑定 LLM ConfigurationError。
适配包与协议 metadata 还分别执行 Pydantic ValidationError 转换；两者的 schema、校验顺序、null 策略和错误文案并不相同。

用户明确希望建立 `spawn-join-common`，今后将时间转换等确有复用需求的公共辅助能力也放在同包。单功能 validation 包无法表达该归属；现有 Core 的稳定契约和零运行时依赖边界仍需保留。

## Options considered

| 方案 | 收益 | 成本与限制 |
|---|---|---|
| 维持 LLM parsing 作为共享层 | 不增加包，现有消费者已工作 | 其他领域被迫依赖 LLM，不满足用户明确定位 |
| 将所有能力放入 Core | 少一个发布单元 | Pydantic 违背 Core 零依赖边界；公共实现与契约混合 |
| 独立 spawn-join-validation | 校验边界窄 | 用户已明确需要多类辅助能力统一归属 |
| 独立 common，按职责组织，框架能力可选 | 多领域可单独安装，保留 Core，依赖显式 | 新增独立锁、测试、构建、版本与消费者迁移成本 |

## Decision

提议建立 `packages/core/common/`，distribution `spawn-join-common`、import `spawn_join_common`。这个包拥有跨领域公共辅助实现，内部按功能职责组织；不提前实现没有明确契约的时间或序列化功能。

common 不依赖其他 SpawnJoin 包、领域异常、Provider SDK 或 Agent。首批提供：

1. 标准库 `FieldReader`，根 `__init__` 显式导出；可提供调用方异常工厂，默认 ValueError。
2. 可选 `spawn_join_common.validation.validate_with`，执行有类型操作，只转换 Pydantic ValidationError；调用方提供异常工厂和文案函数，保留原 cause。`validation` extra 声明 Pydantic >=2.0,<3.0。

common 默认无第三方运行时依赖；root import 不导入 optional validation。Core 不新增依赖。
协议和适配包直接声明 common[validation] 并保留自身 Pydantic；Sync 声明 common base。

## Key design

- FieldReader 的严格值检查、字典复制/顺序、missing/unknown 文本、缺省与 present-null 行为保持。
- 协议 `spawn_join_llm_provider.parsing.FieldReader` 保留薄 frozen/slotted 兼容类，只恢复原默认 ConfigurationError，不复制公共方法。
- Adapter 的 FileInput、Annotated 字段、上下文、null 和首个错误顺序仍属于 adapter；不为仅一处使用的模型继承体系新增公共契约。
- Metadata 的 normalization、详细 formatter 与 nested domain-error 路径包装留在协议包。共用 wrapper 不自动渲染错误输入，也不承诺调用方 formatter 一定脱敏。
- Sync 继续拥有 metadata 投影和外部源 null-as-absent 策略；不因此增加 LangChain runtime 依赖或完整配置校验。
- Common 仅处理内存对象，无文件、凭据、网络、缓存、任务或资源生命周期副作用。

目标依赖关系为：协议、适配和 Sync 指向 common；common 无向领域的反向边，Core 无新边。具体消费者数据类型继续归原领域所有。

## Consequences and migration

新包需要独立 src layout、py.typed、manifest/lock/环境、LICENSE、完整双语 README、契约测试、Quality Profile、CI 与隔离构建接入。
消费者锁与 wheel 构建图必须包含本次 common 产物；不能依赖尚未发布的远端包或可编辑源码掩盖缺包。

迁移是行为保持的委托和导入更新。基础安装不安装 Pydantic；optional validation 安装明确引入框架。用户自定义错误直接穿过公共边界，原异常 cause 得以保留；完整 traceback 仍可能包含输入，这与公开安全错误文案是不同契约。

后续能力进入 common 时需说明真实消费者、功能归属、依赖、错误及验证契约。若某功能形成独立重型依赖或发布周期，再评估 extra 或独立包；本提案不预建该机制。

## Verification and implementation status

**实现已完成并通过独立审查；本 ADR 仍为 `Proposed`，等待决策 owner 正式接受。**

- 2026-11-07 提案时基线：协议 154、适配 240、Sync 55 全部 passed（各 exit 0），仅作为迁移前基线。
- 2026-11-08 当前实现：`spawn-join-common` 与协议/适配/Sync 迁移已提交（T001 `8b1aaf6`、T002 `19930b2`）；公共包 18 项、协议 161 项、适配 240 项、Sync 58 项测试通过；1,536 项解析差分与 8 项 metadata 精确对照均为 0 差异。
- 六个包的本地质量门、两种 Common 隔离安装、文档/治理/静态检查与三套门禁回归均通过；draft PR #47 的 18 个 CI 包任务、governance 和 `Quality Gate` 全部 success。
- 任务级与最终集成 fresh-context 独立 Review 均通过。远端 CI 覆盖 Linux Python 3.11/3.14 与 Windows 3.11；真实 Provider 调用和发布未执行。
- `spawn-join-common` 尚未发布到 Registry；消费者通过仓库本地路径源和锁文件解析。

当前 Feature、任务与运行证据各由其工件拥有；本 ADR 不作第二套执行队列。接受状态需决策 owner 批准，不能由实现或 CI 结果自行改变。

## Revision history

- 2026-11-07：按用户公共辅助包定位提出候选方案；保留域内模型和格式化策略，首批公开 API 限定为真实复用的两项机制。
- 2026-11-08：补充实现、独立审查与本地/远端 CI 验证状态；状态仍为 Proposed，等待决策 owner 接受。
