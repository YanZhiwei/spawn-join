# Decision Context — deepagents-p1-continuation-20261115

## Governing instructions read

- `AGENTS.md` §1–§5: package ownership, dependency direction, public API, testing, and
  change-report rules; seven-Distribution baseline after channel #58.
- `.specify/memory/constitution.md`: readability, object design, DRY, and workflow gates.
- `docs/architecture/package-boundaries.md`: `spawn-join-agent-deepagents` owns DeepAgents
  product assembly; it may depend on DeepAgents, LangChain, LangGraph and the model
  adapter, and must not be depended on by Core, protocol, or model packages.
- `docs/development/quality-gates.md`: per-Distribution lock, quality profile, build,
  isolated install, docs/governance/static, and CI expectations.
- `.specify/extensions/delivery/delivery-config.yml`: Feature lane, ephemeral Spec
  artifacts, documentation-defined ADRs, single publication, squash merge.

## Active ADR constraints

| ADR | Status | Constraint relevant here |
|---|---|---|
| ADR-0010 | Accepted | DeepAgents product boundary and public contract: assembly owns model-purpose binding, middleware scope, delegation, diagnostics, and recovery seams. P1 additions must stay inside this owner and remain explicit/inspectable. |
| ADR-0012 | Proposed | Official P0 capability wiring; currently Proposed even though P0 shipped. It does not authorize P1 rubric/backend/HITL surface by itself. |
| ADR-0006 | Accepted | LangChain-first runtime; no parallel provider abstraction. P1 may use native LangChain/LangGraph types but must not wrap `BaseChatModel` or duplicate the model factory. |
| ADR-0004 | Accepted | Delivery installation and governance boundary; this run uses the installed commands and project-owned configuration. |

## Constraints derived for this run

1. New public API must be explicit in `__init__.py` and covered by `test_public_api.py`.
2. Rubric support must not activate implicitly; the explicit `allow_experimental_rubric`
   gate is part of the contract.
3. Reports must be safe summaries: no filesystem paths, permission rule text, credentials,
   or raw provider errors.
4. HITL helpers must not persist approvals, create checkpoints, or claim exactly-once.
5. No new Distribution, no dependency direction change, no reverse dependency from model or
   protocol packages.
6. ADR coverage is an open review question; if the P1 public seam is judged durable, the
   owning ADR must be updated or a new ADR proposed before merge.

## Open decision at review

Whether ADR-0010/ADR-0012 already cover the additive P1 surface, or whether a P1-specific
ADR (or revision note) is required. This run does not silently declare ADR coverage; the
independent review and final evidence must state the resolution.
