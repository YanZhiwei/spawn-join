# SpawnJoin

[简体中文](README.md) | [English](README.en.md)

**面向 LLM 应用与 DeepAgents 产品的可组合 Python 基础设施。**

SpawnJoin 将公共输入读取与校验、类型化模型配置、LangChain 模型构造、模型元数据同步和
受控 Agent 装配放在同一个 monorepo 中。按需选择包，每个包独立管理依赖、锁文件、测试和构建边界。

**状态：**早期开发（`0.1.0`） · **Python：**3.11+ · **许可证：**专有软件
（[条款](LICENSE)）。这些包面向获授权的私有项目，尚未发布到 PyPI；Core 当前为骨架。

[快速开始](#快速开始) · [选择包](#选择包) · [文档导航](#文档导航) ·
[本地开发](#本地开发) · [参与贡献](#参与贡献)

## 为什么使用 SpawnJoin？

- **显式模型配置。** 明确选择协议和 endpoint，校验选项，通过 `model.yaml` 加载命名模型，
  凭据使用环境变量引用。
- **保留框架原生 API。** 直接使用 LangChain 消息、工具、流式输出和 `BaseChatModel`；
  Agent 装配返回原生 LangGraph 图。
- **受控 Agent 组合。** 按用途绑定模型、按作用域配置 Middleware，并为异步委派设置
  并发上限、deadline、取消和诊断。
- **按需同步元数据。** 手动将已引用模型同步为经过校验的快照；运行时显式读取，不触发远程同步。
- **包独立交付。** 每个 Distribution 可以独立安装、测试、构建和版本化。

## 选择包

| 包 | 适用场景 | 主要入口 |
| --- | --- | --- |
| [spawn-join-common](packages/core/common/README.md) | 跨领域公共辅助能力；默认零依赖，Pydantic 校验为可选能力 | `FieldReader`、`validation.validate_with` |
| [spawn-join-llm-provider](packages/core/llm-provider/README.md) | 框架无关的 endpoint/channel 契约、协议选项、元数据与错误 | `EndpointConfig`、`ProtocolKind` |
| [spawn-join-llm-provider-langchain](packages/infra/llm-provider-langchain/README.md) | 经校验的 LangChain 模型构造与命名模型目录 | `create_chat_model`、`ModelCatalog` |
| [spawn-join-llm-model-sync](packages/infra/llm-model-sync/README.md) | 从 models.dev 等数据源手动同步元数据 | `spawn-join-model-sync` |
| [spawn-join-agent-deepagents](packages/infra/agent-deepagents/README.md) | Supervisor 装配、模型绑定、Middleware、委派与恢复接缝 | `build_supervisor` |
| [spawn-join-core](packages/core/spawn-join-core/README.md) | 共享基础；当前为骨架，无可调用的公共 API | `__version__` |

应用组合适配包和 Agent 包；框架类型留在适配层，Core 与 LLM 协议包不依赖 LangChain。
依赖归属见[包边界](docs/architecture/package-boundaries.md)，完整目录见
[仓库地图](docs/architecture/repository-map.md)。

## 快速开始

### 1. 准备一个包的环境

安装 [uv](https://docs.astral.sh/uv/getting-started/installation/)、Git 和 Python 3.11+。
取得仓库访问授权后：

```bash
git clone https://github.com/YanZhiwei/spawn-join.git
cd spawn-join
uv sync --locked --directory packages/infra/llm-provider-langchain
```

下列命令从仓库根目录执行。每个包拥有独立 `.venv` 和 `uv.lock`，仓库根目录没有共享
uv project 或环境。

### 2. 离线构造模型

将以下内容保存为仓库根目录的 `quickstart.py`：

```python
from spawn_join_llm_provider import ChatCompletionsOptions, ProtocolKind
from spawn_join_llm_provider_langchain import ChatModelConfig, create_chat_model

model = create_chat_model(
    ChatModelConfig(
        protocol=ProtocolKind.CHAT_COMPLETIONS,
        endpoint="https://api.example.com/v1",
        model="example-chat-model",
        timeout_seconds=30.0,
    ),
    api_key="example-key-not-a-real-secret",
    options=ChatCompletionsOptions(temperature=0.2, max_output_tokens=1024),
)

print(type(model).__name__)  # ChatOpenAI
```

```bash
uv run --locked --project packages/infra/llm-provider-langchain python quickstart.py
```

构造阶段校验配置，不调用 Provider。真实推理时需填入服务的 endpoint、模型名和来自环境变量
的凭据，再调用 `invoke`、`ainvoke` 或 `astream`；这些调用会向所配置的服务发送数据。
完整异步示例、模型文件、工具调用与错误处理见
[适配包指南](packages/infra/llm-provider-langchain/README.md#快速开始)。

### 3. 运行离线 Agent 示例

```bash
uv sync --locked --directory packages/infra/agent-deepagents
uv run --locked --directory packages/infra/agent-deepagents python examples/basic_supervisor.py
```

该示例使用本地假模型，无需 API key。[Agent 指南](packages/infra/agent-deepagents/README.md)
进一步介绍受控委派，以及由宿主管理的工具、持久化和恢复。

## 文档导航

| 我想要…… | 阅读入口 |
| --- | --- |
| 复用严格字段读取与校验 | [公共辅助能力](packages/core/common/README.md) |
| 加载命名模型与凭据 | [模型文件与凭据](packages/infra/llm-provider-langchain/README.md#模型文件与凭据) |
| 配置模型思考参数 | [思考与思考强度](packages/infra/llm-provider-langchain/README.md#思考与思考强度) |
| 同步价格与能力元数据 | [模型元数据同步](packages/infra/llm-model-sync/README.md) |
| 组合 supervisor 与 worker | [DeepAgents 产品装配](packages/infra/agent-deepagents/README.md) |
| 理解架构 | [包边界](docs/architecture/package-boundaries.md) · [ADR 入口](docs/decisions/README.md#决策索引) |
| 执行本地与 CI 检查 | [质量门](docs/development/quality-gates.md) |
| 理解交付流程 | [协作规则](AGENTS.md) · [Delivery 安装](docs/development/spec-kit-delivery.md) · [Harness](harness/README.md) |
| 导航源码或绘制技术图 | [仓库地图](docs/architecture/repository-map.md) · [技术图说明](docs/development/technical-diagrams.md) |

## 本地开发

包开发需要 uv 0.7.13+、Python 3.11+、PowerShell 7、Git，以及用于 Pyright 的 Node.js 22+。
完整静态检查还需要[前置工具](docs/development/quality-gates.md#prerequisites)中列出的依赖。

```powershell
# 验证单个包，包含测试与隔离构建/安装。
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider-langchain

# 检查文档与治理记录。
pwsh -NoProfile -File scripts/quality.ps1 -Check docs
pwsh -NoProfile -File scripts/quality.ps1 -Check governance

# 运行完整仓库门禁。
pwsh -NoProfile -File scripts/quality.ps1
```

Black/isort 负责格式，Ruff 负责 lint，Pyright 使用 strict 模式，pytest 按包独立测试。
[GitHub Actions](.github/workflows/quality.yml) 配置了 Linux 与 Windows 检查；当前结果
以实际 CI 运行和[验证记录](harness/evidence/README.md)为准。

## 限制与发布状态

- Channel 包只定义契约，不实现 HTTP channel、池化、路由或健康选路。
- 模型工厂不推断 Provider 能力，也不自动切换协议。
- 受控委派仅支持异步执行；持久化、业务权限和外部资源生命周期由宿主管理。
- Core 为骨架，当前没有 database Distribution。
- 各包独立版本化，`0.x` 阶段公共 API 仍可能变化；本地开发使用仓库锁文件。
  当前未配置包 Registry 和自动发布流水线。

## 参与贡献

SpawnJoin 由仓库维护者维护，包作者为 Yan Zhiwei。获授权的贡献者可以通过
[Issues](https://github.com/YanZhiwei/spawn-join/issues)报告可复现问题，附上包名、revision、
运行时版本和不含凭据的最小示例。

遵循 [AGENTS.md](AGENTS.md) 和 [Constitution](.specify/memory/constitution.md)：文档或机械改动
走 Lightweight，可复现缺陷走 Bugfix，新能力先完成 Spec/Plan/Tasks。同一次变更同步维护
`README.md`（默认中文）与 `README.en.md`，提供与实际 diff 匹配的验证。长期决策放入
[ADR](docs/decisions/README.md)，交付记录放入 [Harness](harness/README.md)。

## 许可证

SpawnJoin 及六个 Distribution 均为**专有软件**，保留所有权利。使用、复制、修改、发布、
分发、再许可与销售均须获得版权持有人的书面许可，详见 [LICENSE](LICENSE)。
仓库内第三方工具保留各自的许可证与来源声明。
