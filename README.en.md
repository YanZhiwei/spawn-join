# SpawnJoin

[简体中文](README.md) | [English](README.en.md)

**Composable Python infrastructure for LLM applications and DeepAgents products.**

SpawnJoin brings shared input readers and validation, typed model configuration, LangChain model
construction, model metadata synchronization, and governed agent assembly into one monorepo.
Use the package you need; each has its own dependencies, lockfile, tests, and build boundary.

**Status:** early development (`0.1.0`) · **Python:** 3.11+ · **License:** proprietary
([terms](LICENSE)). The packages are intended for authorized private projects and are not
published to PyPI. Core is currently a scaffold.

[Quick start](#quick-start) · [Packages](#packages) · [Documentation](#documentation) ·
[Development](#development) · [Contributing](#contributing)

## Why SpawnJoin?

- **Explicit model configuration.** Select protocols and endpoints deliberately; validate
  options and load named models from `model.yaml` with referenced environment credentials.
- **Native framework APIs.** Work directly with LangChain messages, tools, streaming, and
  `BaseChatModel`; agent assembly returns a native LangGraph graph.
- **Controlled agent composition.** Bind models by purpose, scope middleware, and apply
  asynchronous delegation limits, deadlines, cancellation, and diagnostics.
- **Metadata on your terms.** Manually synchronize referenced models into a validated snapshot;
  runtime reads are explicit and do not trigger a remote synchronization.
- **Independent packages.** Install, test, build, and version each Distribution separately.

## Packages

| Package | Use it for | Main entry point |
| --- | --- | --- |
| [spawn-join-common](packages/core/common/README.en.md) | Shared helpers across domains; no default dependencies, optional Pydantic validation | `FieldReader`, `validation.validate_with` |
| [spawn-join-llm-provider](packages/core/llm-provider/README.en.md) | Framework-independent endpoint/channel contracts, protocol options, metadata, and errors | `EndpointConfig`, `ProtocolKind` |
| [spawn-join-llm-provider-langchain](packages/infra/llm-provider-langchain/README.en.md) | Validated LangChain model construction and named model catalogs | `create_chat_model`, `ModelCatalog` |
| [spawn-join-llm-model-sync](packages/infra/llm-model-sync/README.en.md) | Manual metadata synchronization from sources such as models.dev | `spawn-join-model-sync` |
| [spawn-join-agent-deepagents](packages/infra/agent-deepagents/README.en.md) | Supervisor assembly, model bindings, middleware, delegation, and recovery seams | `build_supervisor` |
| [spawn-join-core](packages/core/spawn-join-core/README.en.md) | Shared foundations; currently a scaffold with no callable public API | `__version__` |

Applications compose the adapter and agent packages. Framework types stay in the adapters;
Core and the LLM protocol package do not depend on LangChain. See
[package boundaries](docs/architecture/package-boundaries.md) for dependency ownership and
the [repository map](docs/architecture/repository-map.md) for the full layout.

## Quick start

### 1. Set up one package

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), Git, and Python 3.11+.
With authorized repository access:

```bash
git clone https://github.com/YanZhiwei/spawn-join.git
cd spawn-join
uv sync --locked --directory packages/infra/llm-provider-langchain
```

Run the following commands from the repository root. Each package owns its `.venv` and
`uv.lock`; there is no root uv project or shared environment.

### 2. Construct a model without a network request

Save this as `quickstart.py` in the repository root:

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

Construction validates configuration without calling a provider. For real inference, supply
your service's endpoint, model, and environment-based credential, then call `invoke`,
`ainvoke`, or `astream`. Those calls send data to the configured service. See the
[adapter guide](packages/infra/llm-provider-langchain/README.en.md#quick-start) for a complete
async example, model-file configuration, tool calls, and errors.

### 3. Try an offline agent example

```bash
uv sync --locked --directory packages/infra/agent-deepagents
uv run --locked --directory packages/infra/agent-deepagents python examples/basic_supervisor.py
```

The example uses a local fake model and needs no API key. The
[agent guide](packages/infra/agent-deepagents/README.en.md) covers governed delegation and
host-owned tools, persistence, and recovery.

## Documentation

| I want to… | Read |
| --- | --- |
| Reuse strict field readers and validation | [Shared helpers](packages/core/common/README.en.md) |
| Load named models and credentials | [Model file and credentials](packages/infra/llm-provider-langchain/README.en.md#model-file-and-credentials) |
| Configure thinking parameters | [Thinking and reasoning effort](packages/infra/llm-provider-langchain/README.en.md#thinking-and-reasoning-effort) |
| Synchronize pricing and capability metadata | [Model metadata synchronization](packages/infra/llm-model-sync/README.en.md) |
| Compose supervisors and workers | [DeepAgents product assembly](packages/infra/agent-deepagents/README.en.md) |
| Understand the architecture | [Package boundaries](docs/architecture/package-boundaries.md) · [ADR index](docs/decisions/README.en.md#decision-index) |
| Run local or CI checks | [Quality gates](docs/development/quality-gates.md) |
| Understand the delivery process | [Contributor rules](AGENTS.md) · [Delivery setup](docs/development/spec-kit-delivery.md) · [Harness](harness/README.en.md) |
| Navigate code or create technical diagrams | [Repository map](docs/architecture/repository-map.md) · [Technical diagrams](docs/development/technical-diagrams.md) |

## Development

Package development uses uv 0.7.13+, Python 3.11+, PowerShell 7, Git, and Node.js 22+
for Pyright. Full static analysis also needs the tools listed in the
[prerequisites](docs/development/quality-gates.md#prerequisites).

```powershell
# Validate one package, including tests and isolated build/install.
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider-langchain

# Check documentation and governance.
pwsh -NoProfile -File scripts/quality.ps1 -Check docs
pwsh -NoProfile -File scripts/quality.ps1 -Check governance

# Run the complete repository gate.
pwsh -NoProfile -File scripts/quality.ps1
```

Black/isort own formatting, Ruff owns lint, Pyright runs in strict mode, and pytest tests
each package independently. [GitHub Actions](.github/workflows/quality.yml) configures Linux
and Windows checks. Current results belong to the actual CI run and
[verification records](harness/evidence/README.en.md), not to this README.

## Limitations and release status

- The channel package defines contracts; it does not implement HTTP channels, pooling,
  routing, or health-based selection.
- The model factory does not infer provider capabilities or automatically switch protocols.
- Governed delegation supports asynchronous execution; the host owns persistence, business
  permissions, and external resource lifetimes.
- Core is a scaffold. There is no database Distribution.
- Packages are versioned independently. Public APIs may change during `0.x`; use the checked-in
  locks for development. A package registry and automated release pipeline are not configured.

## Contributing

SpawnJoin is maintained by the repository maintainers (package author: Yan Zhiwei). Authorized
contributors can report a reproducible problem through
[Issues](https://github.com/YanZhiwei/spawn-join/issues), including the package, revision,
runtime versions, and a minimal example without credentials.

Follow [AGENTS.md](AGENTS.md) and the [Constitution](.specify/memory/constitution.md): use
Lightweight for documentation/mechanical changes, Bugfix for reproducible defects, and
Spec/Plan/Tasks for new features. Keep `README.md` (Chinese default) and `README.en.md` synchronized in the
same change, and include checks appropriate to the actual diff. Long-lived decisions belong
in [ADRs](docs/decisions/README.en.md); delivery records belong in [Harness](harness/README.en.md).

## License

SpawnJoin and its six Distributions are **proprietary software**, with all rights reserved.
Use, copying, modification, publication, distribution, sublicensing, and sale require written
permission from the copyright holder. See [LICENSE](LICENSE). Vendored tools retain their
own licenses and provenance.
