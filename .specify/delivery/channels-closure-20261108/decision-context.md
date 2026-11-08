# Decision Context — channels-closure-20261108

## Scope of this discovery

Implement the deferred real `Channel` capability so that the existing
protocol contract, provider transports, and LangChain model factory form one
usable loop:

`ChannelConfig -> ping/list_models -> ModelInfo -> ChatModelConfig -> create_chat_model`

This is a new capability, not a defect. It requires a Feature lane and a new
ADR because ADR-0006 intentionally deferred real channel HTTP and ADR-0008
intentionally excluded channel configuration.

## Governing instructions read

- `AGENTS.md` sections 0–8: delivery routing, package ownership, dependency
  direction, testing evidence, security, and change-report requirements.
- `.specify/memory/constitution.md`: readability, object design, DRY, testing,
  and workflow gates.
- `docs/architecture/package-boundaries.md`: current six Distributions and the
  rule that framework-independent LLM concepts stay in
  `spawn-join-llm-provider`, while LangChain and provider SDK concerns stay in
  infra packages.
- `docs/development/quality-gates.md`: per-Distribution lock, quality profile,
  build, isolated install, and CI expectations.
- `.specify/extensions/delivery/delivery-config.yml`: Feature lane, ephemeral
  Spec artifacts, Ralph task-only commits, manual stacked publication.
- `.specify/extensions/quality/quality-config.yml`: every changed path must be
  covered by a profile; a new Distribution needs its own profile.
- `.github/workflows/quality.yml`: package matrix currently lists six
  Distributions; a new package needs a matrix entry.

## Active ADR constraints

| ADR | Status | Constraint relevant here |
| --- | --- | --- |
| ADR-0006 | Accepted | LangChain is the inference runtime; `spawn-join-llm-provider` stays framework-independent; channel real HTTP, pool, routing, and health were explicitly deferred to a later ADR/Feature. |
| ADR-0008 | Accepted | `model.yaml` and `.env` ownership stays in the LangChain adapter; the ADR explicitly excludes channel configuration. |
| ADR-0009 | Proposed | Model metadata is descriptive only; it must not become runtime capability negotiation. Channel discovery must not use metadata to auto-route or auto-select. |
| ADR-0010 | Accepted | The agent product consumes `BaseChatModel` through the adapter; it must not read model files or credentials itself. Channel discovery is an infra concern, not an agent concern. |
| ADR-0011 | Proposed | `spawn-join-common` owns cross-domain helpers; it must not depend on provider SDKs or LangChain. Channel transports do not belong in Common. |

## Conflicts and required decision

ADR-0006 says "不做真实 channel HTTP、pool、路由、健康选路". This Feature
does not change the inference runtime, but it does implement the deferred real
channel transport. Therefore:

- ADR-0006 remains the accepted inference-runtime decision.
- A new Proposed ADR (planned `docs/decisions/llm-provider/0013-channel-runtime-and-credentials.md`)
  must state that it extends the deferred channel clause, defines the
  provider transport boundary and credential semantics, and continues to
  exclude pool, routing, health selection, and failover.
- The new ADR must be self-contained and must not depend on ephemeral Spec
  artifacts.

## Open decisions the plan must resolve

1. Distribution boundary: a new `spawn-join-llm-channel` package versus a
   channel subpackage inside `spawn-join-llm-provider-langchain`.
2. Whether to add `ChannelStatus.UNSUPPORTED` and
   `ChannelAuthenticationError` to the protocol package for a complete
   transport error surface.
3. Credential semantics: whether `ChannelConfig.credential_ref` is treated as
   an environment-variable name by the default resolver, while explicit
   `api_key` or client injection remains available.
4. CLI scope: minimal `ping`/`list-models` commands with flags, without a new
   channel YAML file.
5. Verification: unit tests with injected fake SDK clients; live provider tests
   are opt-in and cannot run without credentials in this environment.

## Missing evidence

- No live OpenAI/Anthropic credentials or test endpoints are available in the
  current environment. Live smoke tests will be skipped by default and reported
  as unexecuted, not passed.
- No existing channel consumer exists; the concrete product scenario is the
  user's explicit request to close the channel loop, not an inferred UI flow.

## Decision Context verdict

`DECISION_CONTEXT: ready`

The constraints are readable and sufficient for scope discussion. The
implementation design must add a Proposed ADR and must not silently expand
ADR-0006 into routing or pool behavior.

## Resolved planning decisions (2026-11-08)

- Channel transport owner: new `spawn-join-llm-channel` Distribution. The
  adapter is not the transport owner; the protocol package remains
  framework-independent.
- Protocol completion: add `ChannelStatus.UNSUPPORTED` and
  `ChannelAuthenticationError`; existing members and hierarchy stay intact.
- Credential priority: injected client > explicit `api_key` > environment
  lookup using `credential_ref` as the variable name. No `.env`, no mutation.
- Adapter bridge: `ChatModelConfig.from_channel` and
  `ModelSummary.from_model_info`; `ModelSummary` gains optional display fields;
  `ModelCatalog` gains read-only lookup. `create_chat_model` is unchanged.
- CLI: deferred by the user at the design gate. The closed loop is library-only
  (`ChannelConfig -> ping/list_models -> ChatModelConfig.from_channel ->
  create_chat_model`); a future CLI needs a separate Feature.
- Excluded: pool, routing, health selection, failover, hot reload, secret
  manager, new providers, Agent assembly changes, automatic catalog writes.
- ADR: `docs/decisions/llm-provider/0013-channel-runtime-and-credentials.md`
  is Proposed; it extends ADR-0006's deferred channel clause and does not
  change LangChain-first inference.

`DECISION_CONTEXT_RESOLVE: ready`

