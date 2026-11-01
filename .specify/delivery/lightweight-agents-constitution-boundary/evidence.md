# Delivery evidence: AGENTS.md 与 Constitution 边界对齐

- **feature_id**: `lightweight-agents-constitution-boundary`
- **phase_id**: `documentation`
- **lane**: Lightweight
- **base_revision**: `392aa909bcfe57f47d84d3d5e782ffd5fed4ae1f`
- **head_revision**: `working-tree`
- **working_directory**: `C:\Users\YanZh\.local\share\opencode\worktree\86e56b\neon-nebula`
- **recorded_at**: 2026-11-01
- **status**: active
- **result**: pass for local documentation and governance checks; PR CI and user review pending

## Request and scope

Align `AGENTS.md` with the ratified Constitution and add the concrete readability/refactor rules accepted from the reviewed prompt. This is a documentation-only Lightweight change: no Python source, dependency, public API, architecture, credential, permission or runtime data-flow change.

Changed paths:

- `AGENTS.md`: add Constitution to the conflict-precedence chain; cross-reference
  Constitution in §0.1, §4 and §5; add AI-refactor safety, readability review and
  control-flow/extraction rules.
- `.specify/delivery/lightweight-agents-constitution-boundary/evidence.md`: this
  durable record.
- `.specify/delivery/lightweight-agents-constitution-boundary/.gitignore`: keep
  the run workspace local under the ephemeral policy.

## Governing context

- Constitution v1.0.0 remains the project principle source; `AGENTS.md` is the
  execution contract and may not weaken Constitution MUST rules.
- The change does not amend the Constitution, so no version bump or Sync Impact
  Report update is required.
- Delivery, Quality, Review and Docs Sync configuration files were inspected;
  hooks remain disabled and no automatic push/merge is configured.
- No package README surface changed; package-readme outcome is `not-applicable`.

## Verification

All commands run from the recorded working directory.

| Command | Exit | Observed result |
| --- | --- | --- |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | 45 files, 175 local targets checked; final rerun includes this evidence file |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 0 | 0 errors, 1 pre-existing historical evidence-freshness warning; final rerun includes this evidence file |
| `git diff --check` | 0 | No whitespace errors; Git reports normal LF/CRLF conversion warnings |

## Review

- `QUALITY_VERDICT: pass` for the documentation/governance scope.
- `STANDARDS_VERDICT: pass` for the self-review: the change only clarifies
  existing rules, adds no duplicate source of truth, and preserves
  package/API/architecture boundaries.
- `REVIEW_VERDICT: pending` — independent/user code review is intentionally
  pending per the request; do not merge before it.

## Limitations

- No Python package, runtime, dependency, build, type or test surface changed;
  package-level and full-suite checks are not applicable.
- No independent reviewer has run yet. The PR is opened for user code review;
  CI results will be recorded separately.
- The historical governance warning for
  `harness/evidence/delivery-v022-upgrade.md` is pre-existing and outside this
  scope.
- No commit, push, PR, merge or release was performed when this record was
  created; publication follows the separately authorized PR step.
