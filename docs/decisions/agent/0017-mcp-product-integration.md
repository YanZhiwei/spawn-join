# ADR-0017: DeepAgents 可选 MCP 产品接入与显式资源范围

- Status: Accepted
- Date: 2026-11-21
- Domain: agent
- Classification: 本决策的主要消费者是 DeepAgents 产品装配，约束可选入口、配置轮廓、工具分配与宿主委托的资源范围，因此复用 agent 分类。
- Decision owner: 仓库维护者
- Accepted by / date: 仓库维护者（设计批准）；2026-11-22
- Depends on: [ADR-0006](../llm-provider/0006-langchain-first-llm-runtime.md)、[ADR-0010](0010-deepagents-product-boundary.md)
- Related: [ADR-0015 个人助理宿主](0015-personal-assistant-host-boundary.md)、[包边界](../../architecture/package-boundaries.md)、[质量门](../../development/quality-gates.md)
- Supersedes: 无；对 ADR-0010 的资源条款作限定增补，不替代其余决策
- Superseded by: 无

## Context and drivers

Agent 包通过 `SupervisorSpec.tools` 和 `SubAgentDefinition.tools` 接收原生 LangChain 工具。产品需要统一的 mcp.json、多服务加载、必需/可选失败与工具分配契约，同时保持 `recovery.py` 不接管 MCP Session 的现有边界。

当前 LangChain 提供 MCPAdapter，FastMCP 提供配置、Client/ClientGroup、传输与命名前缀。这些机制不应复制。它们的默认整组连接失败行为不等于产品的 optional 降级策略；配置模型 extra=allow 也不等于本项目有严格、明确的文件契约。

ADR-0010 的资源条款写明「本包不创建或关闭宿主资源」。本决策限定允许宿主显式委托可选 helper 管理本次 MCP 资源；个人助理的 SQLite、调度、审批与其他业务资源仍归宿主，不自动接入或修改该应用。

## Options considered

1. **宿主继续完全自行接线**：依赖最少，但每个产品需要重复文件校验、必需/可选加载、报告与选择；不能形成用户要求的统一契约。
2. **现有 Agent 包的可选命名空间与 extra（采用）**：真实消费者明确，默认依赖不变，宿主显式使用；代价是同一 Distribution 内多一条可选依赖及生命周期契约。
3. **独立 MCP Distribution**：可供其他框架复用，但当前没有第二个实际消费者；先增加发布、依赖与 CI 边界的收益不足。
4. **完整 Gateway、连接池与检索平台**：当前没有统一 endpoint、集中授权或完全延迟发现需求，超出首版范围。
5. **一个全量官方 ClientGroup**：最少组合代码，但任意必需/可选成员连接失败都会影响全组；不满足已批准范围的部分成功语义。

## Decision

采用选项2，由宿主通过 `spawn_join_agent_deepagents.mcp` 的显式 async context 使用。默认根导出路径、SupervisorSpec、build_supervisor 和现有子代理工具继承语义保持。

### 所属、依赖与资源限定增补

- 不新增 Distribution；`mcp` extra 直接声明 LangChain MCP、FastMCP 和使用到的 Common 能力，默认安装不强制引入 MCP SDK。
- 对 ADR-0010 的限定增补仅限于：宿主可以显式委托该可选 helper 创建、持有和关闭**本次 MCP 接入资源**。资源启用与存续范围仍由宿主 async context 决定。
- build_supervisor 不读取文件或开启连接；Store、Checkpointer、业务工具、外部已存在服务等资源继续由宿主拥有，该 helper 不接管。
- 每服务独立官方 Client、单成员 ClientGroup 和 MCPAdapter；持有 Adapter 实际使用的上下文，复用官方前缀、转换和路由。首版按配置顺序启动、反序关闭。
- 本模块启动的 stdio transport 显式 keep_alive=False，退出时终止本次子进程；不关闭远端 HTTP 服务进程。

### 文件、加载与分配契约

- 显式本地严格 JSON 文件，标准 mcpServers；项目策略置于独立 spawnJoin，不冒充通用 MCP 协议。
- 支持 stdio/Streamable HTTP 的明确字段子集；未知/不支持配置、缺环境引用、重复键等静态错误先于连接失败，不以 optional 豁免。
- 默认所有未禁用服务必需，可通过 optionalServers 和 disabledServers 明确调整；默认每服务启动预算30秒，与 request timeout 分开。
- 合法可选服务加载失败：清理该成员，保留健康工具并返回 degraded 快照。必需失败：整体失败、清理已开资源，后续标为 not_attempted。
- 取消不降级；清理失败不吞掉。执行期工具业务错误/传输异常继续使用官方语义，不自动重试副作用调用。
- 命名工具集可按服务或 server+原工具名选择，复用官方工具与名称；全局公共名称冲突和健康目录未知工具明确失败。
- 未配置工具集时提供 supervisor 全量可用集；显式空集保留。宿主显式注入各 Agent；不自动按标签创建或修改子代理，不将可见性等同权限控制。
- 只在 env/header 值解析明确的环境引用，不隐式加载 .env；敏感值、SDK配置、工具内容与原始异常不进入默认 repr/公共报告。原 cause 供宿主受控诊断。

### 优先复用的固定版本证据

组合以 LangChain 1.4.8 与 FastMCP v4.0.11 为最低基线；固定 commit `e940a2b69ecfad97a3076622e931b8efc3107ce6` 的配置、Client、Group 和 stdio源码。4.0.11 的 from_config 未透传配置 timeout，因此方案使用官方模型后显式构造 Client 并做单位转换；不依赖 main 才有的行为。

`mcp` extra 声明 langchain[mcp]>=1.4.8,<2、fastmcp>=4.0.11,<5、spawn-join-common>=0.1,<0.2。当前锁定 FastMCP4.2.4/MCP2.3.0/LangChain1.4.8；Windows/Python3.11 验证了锁定组合和显式最低客户端组合，不等于全部版本/平台组合。LangChain为MIT，FastMCP为Apache-2.0；未复制第三方实现。

来源：[官方MCP连接](https://docs.langchain.com/oss/python/langchain/mcp/connections)、[固定Group源码](https://github.com/PrefectHQ/fastmcp/blob/e940a2b69ecfad97a3076622e931b8efc3107ce6/fastmcp_slim/fastmcp/client/group.py)、[固定stdio源码](https://github.com/PrefectHQ/fastmcp/blob/e940a2b69ecfad97a3076622e931b8efc3107ce6/fastmcp_slim/fastmcp/client/transports/stdio.py)。

## Consequences and migration

收益是形成配置到产品装配的可复用接缝，保持官方工具生态和现有builder契约。成本是可选依赖体积、beta API兼容和真实资源清理测试，以及对原资源边界的明确限定增补。

没有持久数据迁移，既有调用方无需启用新功能。工具只在宿主上下文内受支持；不提供对象逃逸后的自动撤销、持续健康、热更新或自动重连。首版不含Gateway服务、OAuth存储、自建检索或额外模型策略。

出现第二个非DeepAgents消费者、需要统一服务端入口或并行启动的实测需求时重新评估分包/加载方案，不提前预建平台。

## Verification and implementation status

实现位于现有 Agent 的可选 `mcp` 命名空间；公开入口、字段、错误和使用方式见[包说明](../../../packages/infra/agent-deepagents/README.md)。默认 builder 与原有依赖边界不变。

[配置测试](../../../packages/infra/agent-deepagents/tests/test_mcp_config.py)、[生命周期测试](../../../packages/infra/agent-deepagents/tests/test_mcp_lifecycle.py)和[原生图测试](../../../packages/infra/agent-deepagents/tests/test_mcp_graph.py)验证静态零副作用、失败/超时/取消、原因链、实际路由与资源关闭；[包质量门](../../development/quality-gates.md)执行真实基础/extra wheel 安装与混合协议调用。

## Revision history

- 2026-11-21：提出首版可选MCP产品接入、资源范围限定增补与验证要求。
- 2026-11-22：确认可选 MCP 实现与宿主委托资源范围，保持原装配和继承契约。
