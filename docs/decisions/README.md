# Architecture Decision Records

[English](README.md) | [简体中文](README.zh-CN.md)

This directory is the single root for SpawnJoin long-term architecture decisions (ADRs). It is
currently maintained through documentation conventions and governance checks; Delivery's ADR/context
configuration already points here, but automatic hooks are not enabled. If enabled in the future,
they must continue to point here rather than create a second decision store.

**Contents**

- [What deserves an ADR](#what-deserves-an-adr)
- [Classification and numbering](#classification-and-numbering)
- [Lifecycle](#lifecycle)
- [Design and diagrams](#design-and-diagrams)
- [Decision index](#decision-index)

## What deserves an ADR

Write an ADR only for a decision that constrains multiple implementation points or future evolution,
involves a real trade-off, and would be confusing without context. Ordinary code cleanup, one-off
debugging, and easily reversible details stay in change descriptions; do not create an ADR for every
task.

- Spec / Plan / Tasks: requirements, solution, and the sole execution queue for one Feature.
- ADR: why a boundary or approach was chosen, what was rejected, long-term constraints and consequences.
- `docs/architecture/`: current architecture navigation and package boundaries; reference ADRs instead of copying full decisions.
- Harness: actual reviews, execution logs, and verification evidence; ADRs link evidence and never present plans as verified results.
- Public contracts and tests: stay in the owning package's code, contracts, or usage docs, not entirely in ADRs.

A Spec is a delivery-oriented working artifact, not a long-term architecture knowledge base. Before
closing, distill still-important design into ADRs or architecture documents. The root `.gitignore`
ignores new local artifacts under `/specs/` without changing Feature execution requirements. Ignore
rules do not untrack already tracked files, and this change neither deletes files nor runs
`git rm --cached`. Existing untracked Features are ignored but remain local; before committing,
confirm that durable contracts, design, and valid evidence do not exist only in ignored Specs.
Migration or untracking of existing tracked content requires separate confirmation and protection.

## Classification and numbering

Filenames use `NNNN-short-kebab-title.md`; numbers increase globally across the whole recursive
directory, are never reused, and do not change with status or classification. Copy the
[template](template.md) and then assign the next available number.

Before creating an ADR, an Agent chooses a classification as follows and states the reason in one
sentence under `Classification`:

1. Find the primary responsibility and owner constrained by the decision; reuse an existing domain directory where possible.
2. Add a first-level directory only when that domain genuinely has subdomain decisions; do not pre-build an empty tree.
3. Cross-domain rules belong to the nearest common responsibility; engineering governance belongs in `engineering/`.
4. If ownership is unclear or the classification would change a public boundary, ask first instead of inventing architecture from a directory name.

For example, caching strategy could belong in `cache/`, while a specific in-memory cache decision
could belong in `cache/memory/`; these are classification examples only and do not imply the
repository already has cache packages. The classification tree is neither a strict binary tree nor
a dependency tree. One ADR may reference multiple prior decisions through `Depends on`, associate
other domains through `Related`, and express replacement through `Supersedes`. Keep one body per
decision and link across domains instead of duplicating files.

## Lifecycle

- `Proposed`: design candidate, not approved, not evidence of implementation.
- `Accepted`: a decision explicitly approved by maintainers; implementation, quality gates, and release completion need separate evidence.
- `Rejected`: explicitly not adopted, with the reason retained.
- `Deprecated`: no longer recommended, with guidance for existing users.
- `Superseded`: replaced by a new ADR, with mutual links.
Only maintainers may change Proposed to Accepted. After acceptance, spelling, links, and
clarifications may be revised in place with a recorded date; changing the substantive trade-off
requires a new ADR and never silently rewrites history. An ineffective replacement proposal must not
mark the old ADR as Superseded early. When moving classification, keep the number and update all
references.

## Design and diagrams

An ADR may include interface outlines, data structures, invariants, exceptions, side effects,
dependency direction, and necessary diagrams, but only the parts needed to explain the decision.
Link same-domain design notes for lengthy details rather than copying an entire Plan or code.

Diagrams use the [project-level Fireworks skill](../../.agents/skills/fireworks-tech-graph/SKILL.md);
project usage and environment isolation are documented in
[technical diagrams](../development/technical-diagrams.md). Simple relationships may use Mermaid
supported by GitHub. SVG is the maintainable primary artifact and PNG is a display copy; save JSON
input when present. Keep adjacent assets under `assets/NNNN/`, embed them by relative path in the
body, and include a textual summary.

State whether each diagram shows "current implementation" or "target design", including arrow
semantics, evidence source, and applicable revision. Do not conflate code dependency, runtime calls,
and data flow; do not treat a model-generated image as architectural fact or test evidence. Passing
structural checks does not prove font, layout, or text readability; final images still need visual
inspection.

## Decision index

This is the single machine-recognized decision index.

| ID | Domain | Decision | Status |
|---|---|---|---|
| ADR-0001 | engineering | [Separate delivery artifacts and durable design](engineering/0001-delivery-and-durable-design.md) | Accepted |
| ADR-0002 | engineering | [Untrack historical Feature artifacts](engineering/0002-untrack-historical-feature-artifacts.md) | Accepted |
| ADR-0003 | engineering | [Enable Spec Kit Delivery and Ralph](engineering/0003-enable-delivery-and-ralph.md) | Accepted |
| ADR-0004 | engineering | [Release-managed Delivery installation](engineering/0004-release-managed-delivery-installation.md) | Accepted |
| ADR-0006 | llm-provider | [LangChain-first LLM runtime](llm-provider/0006-langchain-first-llm-runtime.md) | Accepted |
| ADR-0007 | engineering | [Enable slice delivery by default](engineering/0007-default-slice-delivery.md) | Accepted |
| ADR-0008 | llm-provider | [Model catalog and credential boundaries](llm-provider/0008-model-file-and-env-boundary.md) | Accepted |
| ADR-0009 | llm-provider | [Model metadata and manual synchronization](llm-provider/0009-model-metadata-and-sync.md) | Proposed |
| ADR-0010 | agent | [DeepAgents product boundaries and public contracts](agent/0010-deepagents-product-boundary.md) | Accepted |

When adding or changing an ADR, update the index, related links, and current architecture view at the
same time. The template is not a valid decision and does not participate in numbering.

See the repository [LICENSE](../../LICENSE).
