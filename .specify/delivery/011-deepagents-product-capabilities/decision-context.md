# Decision context: 011-deepagents-product-capabilities

## Discovery mode

- Context mode: `discover` before Feature specification.
- Baseline HEAD: `5e8eb7e4029d5a2ae4835e59ef3759c2abc26d82`.
- Feature: `specs/011-deepagents-product-capabilities/`.
- Canonical exploration packet: `.specify/delivery/011-deepagents-product-capabilities/exploration.md`.

## Active constraints

1. **Distribution and source boundaries** — `.specify/memory/constitution.md` §§ Architecture, Package, and Security Constraints; `AGENTS.md` §§ 1, 4, 5. A new package must be independently installable, buildable, testable, versionable, and publishable with `src/` layout, explicit `__init__.py` exports, package-local `uv.lock`, and tests. Core/protocol packages must not receive LangChain or Provider SDK dependencies.
2. **LangChain-first runtime** — ADR-0006 (Accepted), especially §§ Decision, Key design and diagrams, and Dependency direction. Application-facing messages and models remain LangChain-native; `spawn-join-llm-provider` remains framework-agnostic; the adapter owns `BaseChatModel` creation.
3. **Model file and credential ownership** — ADR-0008 (Accepted), especially §§ Decision and Key design. `model.yaml`, `.env`/environment resolution, secret validation, and `ModelCatalog` remain in `spawn-join-llm-provider-langchain`; no duplicate YAML/secret layer may be introduced in the Agent package.
4. **Model metadata/sync separation** — ADR-0009 (Proposed). Metadata contracts/snapshots and manual synchronization remain separate from runtime model creation. The Agent package must not become a model synchronization or network/cache owner.
5. **Side-effect ownership** — Constitution and package-boundaries.md require explicit owners for network, file, database, cache, thread, task, and external SDK effects. Host-created Store, Checkpointer, MCP Session, sandbox and business tools must remain valid for the returned graph and be closed by their owner.
6. **Quality and delivery** — Constitution §§ Development Workflow and Quality Gates; `docs/development/quality-gates.md`; `.specify/extensions/quality/quality-config.yml`. New behavior requires targeted tests, independent build/install verification, quality profile/CI registration, and separate Standards Review. Tasks remain the only execution queue.
7. **Security** — Credentials, tokens, private URLs and unredacted user data must not enter source, fixtures, logs, diagnostics or committed evidence. Boundary inputs and SDK returns must be validated and narrowed; transformed exceptions retain their cause.

## Superseded or historical context

- The unmerged PR #16 / Proposed ADR-0005 framework-independent message design is not an implementation baseline; ADR-0006 explicitly supersedes that candidate direction.
- NovaClaw `lead-agent` is a reference implementation at `deepagents==0.7.7`, not a SpawnJoin dependency or compatibility contract. Its 57 offline tests are historical comparison evidence only.
- Datawhale's tutorial is community material, not the SDK authority. Its chapters use different 0.7.x versions and application-template assumptions; DeepAgents `0.7.32` fixed source and LangChain official documentation govern this Feature.
- `.specify/feature.json` previously pointed to `008-langchain-first-llm-runtime`; the Feature creation step has now updated it to `011-deepagents-product-capabilities`. Historical Specs and Delivery records are not active context for this Feature.

## Conflicts and open decisions

- **No direct conflict with accepted ADRs is currently identified.** The proposed explicit runtime dependency on `spawn-join-llm-provider-langchain` is consistent with ADR-0006/0008 because the Agent package consumes the adapter's public factory/catalog rather than moving its responsibilities.
- **Model policy resolved:** supervisor/coordinator must be directly bound; worker and summarization may use only an explicit `inherit_from` declaration. No implicit fallback to another model or the ModelCatalog default is allowed.
- **Execution policy resolved:** use a host-injected or explicitly created reusable controller with no process-global implicit state; enforce a bounded FIFO queue, a deadline covering queue wait and execution, parent cancellation propagation, and distinct timeout/cancel/rejection/failure outcomes. Concrete public types and cancellation mechanics remain Plan work.
- **Resource/recovery resolved at boundary level:** the host creates, keeps valid, and closes Store, Backend, Checkpointer, MCP Session, sandbox and related resources. Agent only validates required resource/identity inputs and passes through native Checkpoint/interrupt/resume/streaming semantics; exact validation details remain Plan work.
- **Diagnostics resolved at API level:** return an immutable structured assembly report and offer optional synchronous/asynchronous callbacks for redacted lifecycle records. The host owns logging, tracing, UI, persistence and backpressure; exact record fields remain Plan work.
- **Beta feature resolved:** isolated and compiled subagents are stable contract; forked subagents require explicit experimental opt-in, fixed `0.7.32` tests and separate version-risk documentation.
- **ADR open:** whether the new Agent package boundary is a durable cross-feature decision requiring a Proposed ADR. Decision Propose must compare keeping the boundary in Plan/docs with adding an ADR; no ADR is created at discovery time.

## Missing evidence and effect

- No 0.7.32 SpawnJoin package implementation or offline execution evidence exists yet. This blocks implementation claims, not the scope decision; Plan/Tasks must create it.
- New package quality profile and CI mapping do not exist. A changed-code family with no profile would block final quality; Plan/Tasks must add and test them.
- Current repository-wide docs quality is blocked by a historical broken link in `specs/007-llm-protocol-abstraction/plan.md`; historical `.specify/delivery/010-model-metadata-sync/evidence.md` is active although PR #31 is merged; the installed Doctor contains an old package README template path. These are pre-existing delivery blockers and are not silently repaired under this Feature.

## Resolve mode (pre-plan)

- Mode: `resolve` after Feature specification and clarification approval.
- Re-read sources: ADR-0006, ADR-0008, ADR-0009, `package-boundaries.md`, `repository-map.md`, current model adapter public API, current quality script/CI configuration, DeepAgents 0.7.32 `graph.py`/subagent/summarization source, and LangChain 1.4.7 middleware type source.
- ADR-0006 comparison: current code exposes `BaseChatModel` and native message/tool types; the proposed Agent package consumes those types and does not introduce a second runtime. **No conflict.**
- ADR-0008 comparison: current `ModelCatalog` resolves YAML and environment credentials; the proposed Agent package accepts `ModelCatalog` or `BaseChatModel` and does not read model files or secrets. **No conflict.**
- ADR-0009 comparison: current metadata sync package is independent of runtime construction; the proposed Agent package will not depend on `spawn-join-llm-model-sync` or perform network/cache writes. **No conflict.**
- Package-boundary comparison: a new `infra` Distribution is justified because DeepAgents is a framework adapter, the package will have its own dependencies/tests/release cadence, and host applications should not import a monorepo-internal module. **Boundary extension, not a conflict.**
- Dependency direction proposed: `spawn-join-agent-deepagents -> deepagents/langchain/langchain-core`, `spawn-join-agent-deepagents -> spawn-join-llm-provider-langchain -> spawn-join-llm-provider -> spawn-join-core`. No reverse dependency and no Agent dependency from Core/protocol packages.
- Open decision for Decision Propose: whether the package boundary, model-purpose ownership, and delegation/resource contracts require a durable ADR. Candidate domain `agent`, next global number is `0010`. Plan may reference this candidate but must not create or accept an ADR before `speckit.decision.propose`.
- Remaining Plan-level decisions (not user scope decisions): exact frozen dataclass names, event field names, synchronous deadline limitation, whether `create_summarization_middleware` is applied to declarative subagents as well as the supervisor, and error/callback exception behavior. These are resolved in `plan.md`/`research.md` with tests, not by reopening the approved Feature scope.

## Sources read

- `.specify/memory/constitution.md`
- `AGENTS.md`
- `docs/architecture/package-boundaries.md`
- `docs/architecture/repository-map.md`
- `docs/development/quality-gates.md`
- `docs/decisions/README.md`
- `docs/decisions/llm-provider/0006-langchain-first-llm-runtime.md`
- `docs/decisions/llm-provider/0008-model-file-and-env-boundary.md`
- `docs/decisions/llm-provider/0009-model-metadata-and-sync.md`
- `D:\Repos\NovaTech\NovaClaw\backend\packages\lead-agent\` and related contract/app-api paths via CodeGraph
- DeepAgents `0.7.32` fixed source and official docs
- Datawhale Deep Agents in Action chapters via `defuddle`
