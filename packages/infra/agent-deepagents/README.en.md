# spawn-join-agent-deepagents

[简体中文](README.md) | [English](README.en.md)

`spawn-join-agent-deepagents` is the DeepAgents product assembly package for SpawnJoin. It turns
recurring Agent wiring problems in real products into testable public contracts while preserving
native DeepAgents, LangChain, and LangGraph execution, checkpointing, interrupt, resume, and
streaming capabilities.

**Contents**

- [Status and compatibility](#status-and-compatibility)
- [Capabilities](#capabilities)
- [Installation](#installation)
- [Quick start](#quick-start)
  - [1. Run the complete offline examples first](#1-run-the-complete-offline-examples-first)
  - [2. Connect your own model service](#2-connect-your-own-model-service)
- [Model purposes](#model-purposes)
- [Subagents](#subagents)
  - [AsyncSubAgent (remote subagent)](#asyncsubagent-remote-subagent)
  - [AsyncSubAgent field reference](#asyncsubagent-field-reference)
  - [Remote execution flow](#remote-execution-flow)
  - [Local vs remote subagents](#local-vs-remote-subagents)
- [Middleware scopes](#middleware-scopes)
- [Memory, skills, and profiles](#memory-skills-and-profiles)
  - [Complete runnable example](#complete-runnable-example)
- [Delegation](#delegation)
- [Diagnostics](#diagnostics)
- [Resources and recovery](#resources-and-recovery)
- [Public API](#public-api)
- [Errors and failure behavior](#errors-and-failure-behavior)
- [Compatibility and limitations](#compatibility-and-limitations)
- [Development and verification](#development-and-verification)
- [Release and versioning](#release-and-versioning)
- [Maintenance and contribution](#maintenance-and-contribution)
- [Related documentation](#related-documentation)
- [License](#license)

## Status and compatibility

- Version and stability: `0.1.0`, preview; public API may still change in documented ways during
  `0.x`.
- Runtime: Python `>=3.11`; DeepAgents `0.7.x`; LangChain/LangGraph 1.x.
- Publication: local repository development only; not published to PyPI or a private registry.

## Capabilities

- build a supervisor from explicit model purposes, returning a native LangGraph graph and an
  immutable assembly report;
- declarative, compiled, and remote async subagents; compiled/async subagents keep their own
  execution boundary;
- three middleware scopes: supervisor, workers, and per-subagent override;
- memory/skills configuration objects, including an explicit memory cache-control choice;
- explicit registration, reserved-name validation, and reporting for upstream Harness/Provider
  profiles;
- an explicit async-first delegation controller: concurrency limit, bounded FIFO, deadline,
  cancellation, and failure semantics;
- optional sync/async diagnostic callbacks and redacted assembly/lifecycle records;
- the host owns Store, Checkpointer, MCP Session, sandbox, business tools, and any host-provided
  Backend;
- independent wheel/sdist, `py.typed`, package tests, quality profile, and CI matrix.

## Installation

From the repository root, use this Distribution's own environment:

```powershell
uv lock --check --directory packages/infra/agent-deepagents
uv sync --locked --directory packages/infra/agent-deepagents
```

Runtime dependencies:

- `deepagents>=0.7.32,<0.8`
- `langchain>=1.4.7,<2.0`
- `langchain-core>=1.7.0,<2.0`
- `langgraph>=1.2,<2`
- `spawn-join-llm-provider-langchain>=0.1.0,<0.2.0`

This package does not re-parse `model.yaml`, `.env`, or Provider SDKs; configured models are created
by [`spawn-join-llm-provider-langchain`](../llm-provider-langchain/README.en.md).

## Quick start

### 1. Run the complete offline examples first

Run from the repository root; no model file or credentials are needed:

```powershell
uv run --locked --directory packages/infra/agent-deepagents python examples/basic_supervisor.py
uv run --locked --directory packages/infra/agent-deepagents python examples/governed_delegation.py
uv run --locked --directory packages/infra/agent-deepagents python examples/p0_capabilities.py
```

Complete source: [basic supervisor](examples/basic_supervisor.py),
[governed delegation](examples/governed_delegation.py), and
[official P0 capabilities](examples/p0_capabilities.py). They use the adjacent
[`fake_model.py`](examples/fake_model.py) for deterministic offline responses; run them in the
repository rather than copying just one file. The first prints an assembly report, the worker's
`research result` and `The supervisor's final answer.`; the second also prints an `Events:`
lifecycle list; the third prints `Context`, `Profiles`, `Subagents`, and the same final answer.
The full report repr is not a stable output contract.

### 2. Connect your own model service

The host can inject an existing `BaseChatModel` or pass a `ModelCatalog`. For this complete
Catalog example, save `model.yaml` at the repository root, replace the endpoint/model placeholders
with your service's values, and set `LLM_API_KEY` in the process environment (shared by both purposes):

```yaml
schema_version: 1
default: coordinator
models:
  coordinator:
    protocol: chat_completions
    endpoint: https://api.example.com/v1
    model: your-supervisor-model
    api_key_env: LLM_API_KEY
  worker:
    protocol: chat_completions
    endpoint: https://api.example.com/v1
    model: your-worker-model
    api_key_env: LLM_API_KEY
```

The models must support tool calling. Save the following as `supervisor_demo.py` at the repository
root and run `uv run --locked --project packages/infra/agent-deepagents python supervisor_demo.py`.
Executing the graph sends prompts to the configured service; response content depends on that service.

```python
import asyncio

from langchain_core.messages import HumanMessage
from spawn_join_llm_provider_langchain import ModelCatalog

from spawn_join_agent_deepagents import (
    ModelBinding,
    ModelBindings,
    ModelPurpose,
    SubAgentDefinition,
    SupervisorSpec,
    build_supervisor,
)

async def main() -> None:
    catalog = ModelCatalog.from_file("model.yaml", env_file=None)
    models = ModelBindings(
        catalog=catalog,
        bindings=(
            ModelBinding(ModelPurpose.SUPERVISOR, catalog="coordinator"),
            ModelBinding(ModelPurpose.WORKER, catalog="worker"),
            ModelBinding(
                ModelPurpose.SUMMARIZATION,
                inherit_from=ModelPurpose.SUPERVISOR,
            ),
        ),
    )
    assembly = build_supervisor(
        SupervisorSpec(
            models=models,
            name="coordinator",
            subagents=(
                SubAgentDefinition(
                    name="researcher",
                    description="Research a bounded question and return findings.",
                    system_prompt="Return a concise, source-grounded result.",
                ),
            ),
        )
    )
    result = await assembly.graph.ainvoke(
        {"messages": [HumanMessage(content="Research the topic.")]}
    )
    print(assembly.report)
    print(result["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
```

Assembly only reads configuration and creates a graph; it does not execute the graph, open external
connections, or close host resources. Running `ainvoke`/`astream` uses the host's own models, tools,
Store, Checkpointer, and business resources.

Configuration snippets below are composed into `SupervisorSpec`, not standalone programs.
The complete governed-delegation example above shows how delegation and diagnostics are wired
into assembly and execution.

## Model purposes

| Purpose | Rule |
|---|---|
| `SUPERVISOR` | must be bound directly; cannot inherit |
| `WORKER` | used by declarative subagents and the default controlled `general-purpose`; may explicitly `inherit_from`; binding required by default |
| `SUMMARIZATION` | required by default; may explicitly `inherit_from` |

- No implicit fallback to the supervisor, the Catalog default, or another purpose.
- One model instance is resolved per purpose and reused across all consumers.
- Inheritance must be explicit; cycles, missing bindings, unknown Catalog entries, and creation
  failures fail before assembly.
- Compiled subagents own their models; this package neither inspects nor replaces them.

`SUMMARIZATION` is required by default because the DeepAgents default stack always includes
summarization. The generated `SummarizationMiddleware` replaces the default instance in place rather
than appending a duplicate.

## Subagents

- `SubAgentDefinition`: declarative worker supporting `tools`, `middleware`, `interrupt_on`,
  `response_format`, `skills`, `permissions`, and context schema;
- `CompiledSubAgentDefinition`: a host-provided runnable that keeps its own graph, model, and
  internal middleware;
- `AsyncSubAgentDefinition`: a remote Agent Protocol worker forwarded with the native
  `graph_id`/`url`/`headers`/`webhook` fields; it requires
  `SupervisorSpec(allow_experimental_async_subagents=True)`, and `mode="fork"` also requires
  `allow_experimental_fork=True`; only the async execution path is supported;
- names must be unique across all three forms;
- `tools=None` means inherit upstream tools; `tools=()` means explicitly provide no extra tools;
- by default, if `general-purpose` is not declared, the package injects a controlled
  `general-purpose` using the `WORKER` model and `workers` middleware, and reports it;
- `SupervisorSpec(control_default_subagent=False)` preserves the upstream supervisor-owned
  `general-purpose`; the report marks it `upstream_default` and warns that `WORKER` and worker
  middleware do not apply. If a model harness profile disables that default subagent, the report
  entry represents the upstream default contract and the actual graph is authoritative;
- `mode="fork"` is DeepAgents beta and requires explicit
  `SupervisorSpec(allow_experimental_fork=True)`; it is outside the stable compatibility promise.

### AsyncSubAgent (remote subagent)

`AsyncSubAgentDefinition` does not create another agent in this process. It registers a
subagent that runs on a remote Agent Protocol service. That service owns its model, tools, and
runtime; this package only validates the declaration, converts it to the native DeepAgents
`AsyncSubAgent`, and reports it.

#### What Agent Protocol is

Agent Protocol is an HTTP contract for agent services: clients can look up
assistants/graphs, create threads, start runs, and query status/results. LangGraph Platform
implements it; a self-hosted FastAPI service can implement the same contract. DeepAgents'
`AsyncSubAgentMiddleware` calls it through `langgraph_sdk`, so:

- `url` is the remote service address;
- `graph_id` is the agent/graph/assistant on that service.

#### AsyncSubAgent field reference

| Field | Required | Default | Plain meaning |
| --- | --- | --- | --- |
| `name` | yes | none | Local name the supervisor uses to select this remote worker |
| `description` | yes | none | Tells the model what the worker is good at |
| `graph_id` | yes | none | Graph/assistant ID on the remote service |
| `url` | no | SDK default | Agent Protocol service URL; omit for the LangGraph SDK default or local ASGI transport |
| `headers` | no | none | Extra HTTP headers, usually auth; never included in the report |
| `webhook` | no | none | URL the remote service calls when a run finishes |
| `update_strategy` | no | `"interrupt"` | Follow-up while running: `interrupt` stops the current run, `enqueue` waits behind it |
| `notify_parent` | no | upstream `True` | Whether the worker may wake the parent when done; set `False` when the app delivers via webhook |
| `mode` | no | `"isolated"` | `isolated` uses separate context; `fork` copies parent history (beta, remote config must match) |

The minimal form needs only the first three fields:

```python
AsyncSubAgentDefinition(
    name="remote-researcher",
    description="Research a bounded question on the remote deployment.",
    graph_id="research_agent",
)
```

A real deployment usually adds the URL and auth headers (keep secrets in the host environment):

```python
AsyncSubAgentDefinition(
    name="remote-researcher",
    description="Research a bounded question on the remote deployment.",
    graph_id="research_agent",
    url="https://my-deployment.langsmith.dev",
    headers={"Authorization": f"Bearer {token_from_host}"},
    update_strategy="enqueue",
    notify_parent=False,
    webhook="https://my-app.example.com/agent-events",
)
```

#### Remote execution flow

1. `build_supervisor` validates and converts the declaration; it does **not** connect.
2. `create_deep_agent` sees `graph_id` and installs `AsyncSubAgentMiddleware`.
3. The supervisor model gains async tools: `start_async_task`, `check_async_task`,
   `update_async_task`, `cancel_async_task`, `list_async_tasks`.
4. The model calls `start_async_task`, receives a `task_id` immediately, and can continue.
5. The remote service runs the actual agent in its own process.
6. The model later checks status/results, or receives completion via webhook / `notify_parent`.
7. This path requires `ainvoke` / `astream` and an Agent Protocol service.

The key difference from a normal subagent: a normal subagent delegates and waits; an async
subagent gets a ticket ID first and checks progress later.

#### Local vs remote subagents

| | `SubAgentDefinition` | `AsyncSubAgentDefinition` |
| --- | --- | --- |
| Model location | current process | remote service |
| Result timing | wait | get `task_id`, check later |
| Package injects middleware | yes | no |
| Reported model source | `purpose:worker`, etc. | `remote:<graph_id>` |
| Remote service needed | no | yes, Agent Protocol |
| Beta switch | only for `fork` | `allow_experimental_async_subagents=True` |

Note: `url="https://example.invalid"` in `examples/p0_capabilities.py` only demonstrates the
field. The example never calls the remote subagent, so it needs no network and does not fail on
an unreachable address.

## Middleware scopes

Here `supervisor_audit`, `worker_rate_limit` and `research_trace` are host-provided LangChain
middleware instances. Pass the resulting configuration as `SupervisorSpec(middleware=middleware, ...)`.

```python
from spawn_join_agent_deepagents import MiddlewareConfiguration

middleware = MiddlewareConfiguration(
    supervisor=(supervisor_audit,),
    workers=(worker_rate_limit,),
    worker_overrides={"researcher": (research_trace,)},
)
```

Requested order: definition-level middleware, global worker middleware, named override, generated
summarization middleware. DeepAgents replaces the default summarization in place by `.name`, so the
final base-stack position is upstream-determined; the report records requested names and
`replaced_defaults` without claiming summarization always executes last. Compiled subagents receive
no injection.

- Duplicate `.name` values within one scope are rejected;
- `"SummarizationMiddleware"` and internal package middleware names are reserved;
- upstream `.name` replacement semantics are preserved; the package implements no second registry;
- the assembly report records effective names and scopes.

## Memory, skills, and profiles

```python
from spawn_join_agent_deepagents import (
    HarnessProfileBinding,
    MemoryConfiguration,
    ProfilesConfiguration,
    SkillsConfiguration,
)
from deepagents import HarnessProfile

spec = SupervisorSpec(
    models=models,
    memory=MemoryConfiguration(sources=("AGENTS.md",), add_cache_control=False),
    skills=SkillsConfiguration(sources=("skills",)),
    profiles=ProfilesConfiguration(
        harness=(
            HarnessProfileBinding(
                "openai:gpt-5.4",
                HarnessProfile(system_prompt_suffix="Be concise."),
            ),
        )
    ),
    allow_experimental_profiles=True,
)
```

- `MemoryConfiguration` / `SkillsConfiguration` reject empty, blank, and duplicate sources; the
  package does not read the sources during assembly.
- `add_cache_control=True` (the default) keeps the upstream `MemoryMiddleware`; `False` makes the
  package construct its own same-name instance and pass `memory=None`, so there is no upstream
  default to replace and fork subagents do not inherit this memory.
- `ProfilesConfiguration` calls upstream `register_harness_profile` /
  `register_provider_profile` before `create_deep_agent`; this is beta process-wide state and
  requires `allow_experimental_profiles=True`. Provider profiles only affect upstream
  string-model construction; this package always passes a `BaseChatModel`, so they do not
  reshape resolved instances.
- A profile cannot exclude package-reserved middleware names (`SummarizationMiddleware`,
  `spawn_join_delegation_policy`, `spawn_join_diagnostics`).
- The `context` report records only source counts and management mode; the `profiles` report
  records only registered keys. Paths, URLs, headers, and credentials are never reported.

### Complete runnable example

The script below matches [`examples/p0_capabilities.py`](examples/p0_capabilities.py). It uses a
temporary `FilesystemBackend` for memory/skills, runs offline with fake models, and declares a
remote async subagent without invoking it.

```powershell
uv run --locked --directory packages/infra/agent-deepagents python examples/p0_capabilities.py
```

```python
from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from typing import Any, cast

from deepagents import HarnessProfile
from deepagents.backends import FilesystemBackend
from fake_model import FakeChatModel
from langchain_core.messages import AIMessage, HumanMessage

from spawn_join_agent_deepagents import (
    AsyncSubAgentDefinition,
    HarnessProfileBinding,
    MemoryConfiguration,
    ModelBinding,
    ModelBindings,
    ModelPurpose,
    ProfilesConfiguration,
    SkillsConfiguration,
    SubAgentDefinition,
    SupervisorSpec,
    build_supervisor,
)


def _task_call() -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[
            {
                "name": "task",
                "args": {
                    "description": "Research the topic.",
                    "subagent_type": "researcher",
                },
                "id": "call-researcher",
                "type": "tool_call",
            }
        ],
    )


async def main() -> None:
    with tempfile.TemporaryDirectory() as raw_root:
        root = Path(raw_root)
        (root / "AGENTS.md").write_text(
            "# Agent memory\n\nReturn concise answers.\n",
            encoding="utf-8",
        )
        skill = root / "skills" / "web-research"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\n"
            "name: web-research\n"
            "description: Research a bounded question.\n"
            "---\n\n"
            "Use the available research tools and cite the result.\n",
            encoding="utf-8",
        )

        supervisor = FakeChatModel(
            responses=[
                _task_call(),
                AIMessage(content="The supervisor's final answer."),
            ]
        )
        worker = FakeChatModel(responses=[AIMessage(content="research result")])
        models = ModelBindings(
            catalog=None,
            bindings=(
                ModelBinding(ModelPurpose.SUPERVISOR, model=supervisor),
                ModelBinding(ModelPurpose.WORKER, model=worker),
                ModelBinding(
                    ModelPurpose.SUMMARIZATION,
                    inherit_from=ModelPurpose.SUPERVISOR,
                ),
            ),
        )

        assembly = build_supervisor(
            SupervisorSpec(
                models=models,
                backend=FilesystemBackend(root_dir=root),
                memory=MemoryConfiguration(
                    sources=("/AGENTS.md",),
                    add_cache_control=False,
                ),
                skills=SkillsConfiguration(sources=("/skills",)),
                profiles=ProfilesConfiguration(
                    harness=(
                        HarnessProfileBinding(
                            "example:fake-model",
                            HarnessProfile(system_prompt_suffix="Be concise."),
                        ),
                    )
                ),
                allow_experimental_profiles=True,
                subagents=(
                    SubAgentDefinition(
                        name="researcher",
                        description="Research a bounded question.",
                        system_prompt="Return a concise result.",
                    ),
                    AsyncSubAgentDefinition(
                        name="remote-researcher",
                        description="A remote Agent Protocol worker.",
                        graph_id="research_agent",
                        url="https://example.invalid",
                    ),
                ),
                allow_experimental_async_subagents=True,
                name="coordinator",
            )
        )

        result = cast(
            dict[str, Any],
            await assembly.graph.ainvoke(
                {"messages": [HumanMessage(content="Start the research.")]}
            ),
        )

        print("Report:", assembly.report)
        print("Context:", assembly.report.context)
        print("Profiles:", assembly.report.profiles)
        print("Subagents:", [(item.name, item.kind) for item in assembly.report.subagents])
        for message in cast(list[Any], result["messages"]):
            print(type(message).__name__, getattr(message, "content", ""))


if __name__ == "__main__":
    asyncio.run(main())
```

Key points:

- `MemoryConfiguration(add_cache_control=False)` exercises the package-managed
  `MemoryMiddleware` path; the `FilesystemBackend` is host-owned and cleaned up by
  `TemporaryDirectory`.
- `SkillsConfiguration(sources=("/skills",))` points at a directory containing
  `web-research/SKILL.md`; invalid frontmatter is skipped by upstream with a warning.
- `AsyncSubAgentDefinition` participates only in assembly and the report; the example never
  invokes the remote worker and needs no network.
- The harness profile is beta process-wide state. Its key does not match the fake model, so it
  demonstrates registration, validation, and reporting without changing offline output.

## Delegation

```python
from spawn_join_agent_deepagents import (
    DelegationConfiguration,
    DelegationPolicy,
)

delegation = DelegationConfiguration(
    policy=DelegationPolicy(
        max_concurrency=4,
        max_queue=16,
        deadline_seconds=120,
    )
)
```

- The controller is injected by the host or created explicitly and can be reused across runs in the
  same event loop; no process-global state.
- Bounded FIFO queue; exceeding `max_queue` immediately raises `DelegationQueueFullError`.
- `deadline_seconds` covers queueing and execution; expiry raises `DelegationTimeoutError` and frees
  the slot.
- Parent cancellation clears queued/active state and propagates `asyncio.CancelledError`.
- Worker failures preserve the original exception; timeout, cancellation, and failure are
  distinguishable in diagnostics.
- **The delegation policy supports asynchronous execution only.** With a policy configured, using
  `invoke`/`stream` explicitly raises `UnsupportedSyncDelegationError` at the `task` call rather than
  pretending to offer a preemptible synchronous deadline. Without a policy, synchronous execution
  keeps native behavior.

## Diagnostics

```python
from spawn_join_agent_deepagents import DiagnosticEvent, DiagnosticsConfig

def on_event(event: DiagnosticEvent) -> None:
    print(event.event_type, event.subagent_name, event.outcome)

diagnostics = DiagnosticsConfig(sync_callback=on_event)
```

- The assembly report is immutable and contains safe labels only.
- Lifecycle records distinguish selected, queued, started, completed, failed, timed_out, cancelled,
  interrupted, and rejected.
- Correlation comes from native `tool_call_id`, `run_id`, and optional `thread_id`.
- Failures record only stable error categories/class names, never exception messages.
- Synchronous execution calls the sync callback; asynchronous execution calls the sync callback then
  awaits the async callback.
- With only an async callback configured but synchronous execution used, no event loop is fabricated;
  the assembly report records a warning.
- Callback exceptions propagate; the host owns logging, tracing, UI, persistence, and backpressure.

## Resources and recovery

```python
from spawn_join_agent_deepagents import RecoveryContext

config = RecoveryContext(thread_id="conversation-1").to_graph_config()
```

- Store, Checkpointer, MCP Session, sandbox, business tools, and a host-provided Backend are created,
  kept alive, and closed by the host.
- When the host omits `backend`, the package creates an in-memory `StateBackend` with no external
  close path, reported as `default_state`.
- The package validates that explicit `interrupt_on`, declarative subagent `interrupt_on`, and
  `FilesystemPermission(mode="interrupt")` require a checkpointer, and passes native LangGraph
  semantics through.
- Recovery uses native `Command(resume=...)` and the same `thread_id`.
- The package does not create or close host resources and does not promise exactly-once side effects.
- Callers should use `to_graph_config()` to generate native config or provide an equivalent
  `configurable.thread_id` themselves.

## Public API

Public exports are defined by `spawn_join_agent_deepagents.__all__`, mainly:

- `build_supervisor`, `SupervisorSpec`, `SupervisorAssembly`;
- `ModelPurpose`, `ModelBinding`, `ModelBindings`, `ResolvedModelBindings`;
- `SubAgentDefinition`, `CompiledSubAgentDefinition`, `AsyncSubAgentDefinition`,
  `SubAgentKind` (including `UPSTREAM_DEFAULT` and `ASYNC`), `SubAgentMode`;
- `MemoryConfiguration`, `SkillsConfiguration`;
- `ProfilesConfiguration`, `HarnessProfileBinding`, `ProviderProfileBinding`;
- `MiddlewareConfiguration`, `MiddlewareScopeReport`;
- `DelegationPolicy`, `DelegationController`, `DelegationConfiguration`;
- `DiagnosticsConfig`, `DiagnosticCallback`, `AsyncDiagnosticCallback`, `DiagnosticEvent`,
  `DiagnosticEventType`, `AssemblyReport`, `SubagentReport`, `DelegationReport`,
  `ResourceReport`, `ContextReport`, `ProfileReport`;
- `RecoveryContext`;
- stable error types (`AgentConfigurationError` and subclasses, including
  `ContextConfigurationError` and `ProfileConfigurationError`).

Internal modules do not become public contracts merely because they are importable.

## Errors and failure behavior

- `AgentConfigurationError` is the assembly-time configuration error base; models, subagents,
  middleware, recovery, memory/skills, profiles, and delegation have stable subclasses.
- Configuration errors are raised before `create_deep_agent`, never returning a half-configured
  graph; upstream assembly/registration exceptions preserve `__cause__`.
- Async subagents and profile registration fail before assembly unless their beta switch is set.
- Unknown subagent forms, blank `graph_id`, duplicate keys, and reserved-middleware exclusions
  produce stable configuration errors instead of upstream `AttributeError` or silent ignores.
- Delegation queue-full, deadline, parent cancellation, worker failure, and interrupt have
  distinguishable semantics; worker exceptions are never converted to success.
- Diagnostic callback exceptions propagate and are never silently swallowed; async callbacks are
  awaited only during async execution.

## Compatibility and limitations

- Python `>=3.11`;
- DeepAgents `>=0.7.32,<0.8`; upgrading to 0.8 needs separate compatibility verification;
- `fork` subagents are beta and outside the stable compatibility promise;
- async subagents are beta and depend on a remote Agent Protocol service and the async path;
- Harness/Provider profiles are upstream beta and register process-wide state;
- governed delegation is asynchronous only; synchronous policies explicitly error;
- no MCP Server, database, sandbox, Web/SSE, production observability backend,
  tenant/authorization/billing, artifact ledger, or UI;
- no automatic PR, publication, or background scheduling.

## Development and verification

```powershell
uv lock --check --directory packages/infra/agent-deepagents
uv sync --locked --directory packages/infra/agent-deepagents
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-agent-deepagents
```

- Layout: `src/spawn_join_agent_deepagents/` is runtime source, `tests/` holds offline tests, and
  `examples/` contains executable examples; the package ships its own `uv.lock`, `py.typed`, and
  `LICENSE`.
- Required tools: uv `>=0.7.13`, PowerShell 7, Git, Node.js 22+ (Pyright wrapper), and the package
  dev group's Black/isort/Ruff/Pyright/pytest.
- The package quality gate runs Black/isort, Ruff, Pyright strict, pytest, wheel/sdist, isolated
  installation, `pip check`, and isolated import. Offline tests use no real keys and connect to no
  external service.

## Release and versioning

This package uses an independent version and independent wheel/sdist; it is not implicitly released
with other Distributions. The current version is `0.1.0` and is unpublished; publication requires the
repository quality gates, independent review, and separate publication authorization. Breaking
public API changes should update version, documentation, and compatibility notes and rerun package
and repository gates.

## Maintenance and contribution

This package is owned by the SpawnJoin repository maintainers; changes follow `AGENTS.md`,
[package boundaries](../../../docs/architecture/package-boundaries.md), and
[ADR-0010](../../../docs/decisions/agent/0010-deepagents-product-boundary.md). New capabilities or
public-contract changes use the Feature delivery route; defects use Bugfix; pure documentation or
mechanical changes use Lightweight. Before committing, provide quality, standards, and review evidence
bound to the current diff.

## Related documentation

- [ADR-0010: DeepAgents product boundary](../../../docs/decisions/agent/0010-deepagents-product-boundary.md)
- [Package boundaries](../../../docs/architecture/package-boundaries.md)
- [Repository map](../../../docs/architecture/repository-map.md)
- [Quality gates](../../../docs/development/quality-gates.md)

## License

This package is proprietary software. All rights reserved. See [LICENSE](LICENSE).
