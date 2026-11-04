# spawn-join-agent-deepagents

Product assembly and execution contracts for DeepAgents applications in
SpawnJoin.

This Distribution is under active implementation. The first delivered surface
will provide:

- an explicit supervisor assembly that returns a native DeepAgents/LangGraph
  graph plus an inspectable report;
- model-purpose bindings for supervisor, worker, and summarization models,
  with configured models created through `spawn-join-llm-provider-langchain`;
- scoped middleware composition without reimplementing DeepAgents rules;
- a bounded, asynchronous delegation controller with deadline and cancellation
  semantics;
- host-owned resources with native checkpoint/interrupt/resume pass-through;
- redacted assembly and lifecycle diagnostics.

The package version is `0.1.0`. The distribution is not yet published; use the
repository's package-local uv environment:

```powershell
uv lock --directory packages/infra/agent-deepagents
uv sync --locked --directory packages/infra/agent-deepagents
```

Run the package quality entry from the repository root:

```powershell
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-agent-deepagents
```

The package does not own business tools, tenant/authorization/billing policy,
MCP servers, databases, sandboxes, UI events, or a production observability
backend. See the package's published API and examples when the implementation
slices land.
