# Decision Context: 010-model-metadata-sync

- Mode: pre-plan resolve
- Scope: 模型元数据 schema、手动同步、运行时可选读取、源注册扩展点
- ADR root: `docs/decisions/`
- Code area: `packages/core/llm-provider`、`packages/infra/llm-provider-langchain`
- Feature spec: `specs/010-model-metadata-sync/spec.md`
- Exploration packet: `.specify/delivery/010-model-metadata-sync/exploration.md`

## Sources read

- `.specify/memory/constitution.md`（Core Principles、Architecture/Package/Security、Workflow）
- `AGENTS.md`、`docs/architecture/package-boundaries.md`、`docs/architecture/repository-map.md`
- `docs/decisions/README.md`
- `docs/decisions/engineering/0001-delivery-and-durable-design.md`
- `docs/decisions/engineering/0002-untrack-historical-feature-artifacts.md`
- `docs/decisions/engineering/0007-default-slice-delivery.md`
- `docs/decisions/llm-provider/0006-langchain-first-llm-runtime.md`
- `docs/decisions/llm-provider/0008-model-file-and-env-boundary.md`
- 当前代码：`model_file/_schema.py`、`model_file/_catalog.py`、`channels.py`、
  `config.py`、`factory.py` 及对应测试

## Active constraints

| 来源 | 约束 | 对本 Feature 的影响 |
| --- | --- | --- |
| ADR-0006 | 协议包保持框架无关；应用直接使用 LangChain 类型；不定义运行时 `ModelCapabilities` 协商抽象 | 元数据类型必须是纯描述，不参与路由/降级/能力协商；`ChatModelConfig` 不依赖 `ChannelConfig` |
| ADR-0006 | `ChatModelConfig` 不依赖渠道名称或凭据引用 | 渠道覆盖不能强制 `model.yaml` 声明 `ChannelConfig`；映射必须可选且显式 |
| ADR-0006 | 不做 pool、路由、健康选路 | 元数据只描述事实，不驱动选型 |
| ADR-0008 | `model.yaml` v1 是严格契约；未知字段拒绝；显式路径；`.env` 只存密钥 | v2 必须显式版本化并保持 v1 可读；不引入隐式多文件搜索 |
| ADR-0008 | 明确排除远程配置中心、热重载、多文件合并 | 同步必须是离线快照 + 手动命令，不是运行时远程配置 |
| ADR-0001 | 长期设计提炼到 ADR；Spec/Plan/Tasks 面向交付 | 本 Feature 需要 ADR-0009，且 ADR 必须自包含 |
| ADR-0002 | `specs/` 只在本地，不随仓库分发；文档不得链接本地 Spec | ADR-0009 不依赖 `specs/` 链接；证据放 `.specify/delivery/` 或 `harness/` |
| ADR-0007 | 默认 Slice；`tasks.md` 是唯一执行队列 | 后续 Plan/Tasks 必须按 Slice 边界组织，`slices.md` 不替代任务队列 |
| Constitution | 领域抽象留在领域包；网络/文件副作用有明确拥有者；公共 API 显式导出；YAGNI | 元数据类型放 `llm-provider`；同步 I/O 放 infra 工具包；不预建无消费者抽象 |

## Superseded / historical context

- ADR-0001 中“不取消已跟踪 Specs 跟踪”的条款已被 ADR-0002 部分取代；文档分层决策仍然有效。
- ADR-0006 提到的未合并 ADR-0005 不是 `main` 上的有效决策，不能作为实现依据。
- 历史 Feature `009-model-file-config` 的 Spec/Plan 只在本地；其长期约束已提炼为 ADR-0008。

## Conflicts with the proposed work

1. **`ModelCapabilities` 命名冲突（需要 ADR-0009 明确）**
   ADR-0006 明确不定义运行时 `ModelCapabilities`。本 Feature 使用 `ModelMetadata` 描述
   价格、模态、限制和推理控制，不参与能力协商。Plan 和 ADR 必须写明这一区别，并禁止
   基于元数据自动切换协议、降级参数或选路。

2. **ADR-0008 的“远程配置”排除（兼容，但需要边界说明）**
   本 Feature 的同步是维护者手动执行的离线快照生成，不是运行时远程配置、热重载或
   多文件合并。`model.yaml` 仍是唯一手写配置；快照是生成数据。ADR-0009 需要明确：
   - 同步命令不在库导入或模型创建时运行；
   - 运行时只读显式路径的快照；
   - 不自动刷新、不搜索 AppData；
   - `model.yaml` schema v2 是显式版本升级，v1 继续可读。

3. **`ChatModelConfig` 与渠道解耦（设计约束）**
   多渠道价格不能要求 `model.yaml` 引入强制的 `ChannelConfig`。渠道覆盖的键和关联方式
   必须在 Plan 中固定为可选映射，不能改变 `ChatModelConfig` 的构造契约。

4. **新 Distribution 的治理成本（可接受，但需记录）**
   新增 `spawn-join-llm-model-sync` 会带来独立 `pyproject.toml`、`uv.lock`、`.venv`、
   构建、README、quality profile 和维护责任。当前只有一个消费者，必须证明该边界
   优于把同步工具塞进 LangChain 适配包：元数据不是 LangChain 专属，且同步网络副作用
   不应进入运行时包。

## Open decisions for Plan

- 渠道覆盖的键：`model.yaml` 条目名、独立 `channel` 字段，还是 endpoint 归一化标识。
  推荐条目名，保持 `ChatModelConfig` 与 `ChannelConfig` 解耦。
- 价格字段形状：按模态分组（`text.input` / `text.output` / `image.output`）还是扁平字段。
  推荐按模态分组，单位显式，未知单位拒绝。
- 新包最终名称：`spawn-join-llm-model-sync` 还是更短的 `spawn-join-model-sync`。
  倾向前者，明确 LLM 领域归属。
- models.dev 端点与字段映射：`catalog.json` 还是 `api.json` + `models.json`；
  单位换算、缺失字段和 base_model 解析需要用 fixture 验证。
- 快照 schema 版本策略：整数版本 + 新增可选字段；未知字段拒绝还是向前兼容。
  当前倾向严格校验 + 显式版本升级。
- 新包 quality profile、README、repository-map 更新和构建验证命令。

## Missing evidence

- models.dev 实际响应尚未抓取并用 fixture 验证；字段名、单位和缺失值处理仍是假设。
- 当前没有第二个运行时消费者；`ModelSummary.metadata` 的实际使用场景未在仓库内验证。
- 本 worktree 的 CodeGraph 索引未初始化，源码关系依据逐文件阅读和测试，不是图索引证据。
- 新包的构建、锁文件、隔离安装和 CI 成本尚未实际测量。

## Resolution summary

- 没有阻塞性 ADR 冲突。
- 需要新增 **ADR-0009：模型元数据与手动同步边界**，状态先 Proposed，最终评审后
  Accepted；正文必须自包含，不链接本地 `specs/`。
- Plan 必须显式处理上述 open decisions，并在 plan gate 展示最终文件树、接口、测试路径
  和验证命令。
- 运行时行为保持默认关闭；不传快照时与当前版本一致。

```text
DECISION_CONTEXT: resolved
BLOCKING_CONFLICTS: none
REQUIRED_ADR: ADR-0009（Proposed → 评审后 Accepted）
NEXT: speckit.plan
```
