# Evidence — Untrack Historical Specs (Lightweight)

## Identity and scope

- **route**: Lightweight（治理与分发规则，无运行时行为或公共 API 变化）
- **feature_id**: 不适用（按 ADR-0002 执行一次性索引变更）
- **phase_id**: `untrack-historical-specs`
- **task_id**: 不适用（无 Ralph receipt）
- **base_revision**: `99f69078b6957e401c5f079890e3bccb2c7ee8d7`
- **head_revision**: `99f6907` 加未提交工作树
- **working_directory**: `D:\Repos\Github\spawn-join`
- **recorded_at**: 2026-10-27
- **environment**: Windows；PowerShell 7.6.9；git 2.55.0.windows.3；uv 0.7.13
- **result**: pass

## Changed paths

- 仅从索引移除、本地保留：`specs/001-harness-foundation/` 下 6 个文件；
- `docs/decisions/engineering/0002-untrack-historical-feature-artifacts.md`（新增 ADR）；
- `docs/decisions/README.md`（索引）、`docs/decisions/engineering/0001-...`（Related 与修订记录）；
- `docs/architecture/repository-map.md`、`harness/README.md`、`README.md`、`AGENTS.md`、`.gitignore`；
- 本 evidence 与 `harness/build-log.md` 追加条目。

未删除任何本地文件，未改写历史提交，未修改 002 或 Python 源码。

## Observed commands

| Command | Exit | Observed result |
|---|---|---|
| `git rm --cached -r specs/001-harness-foundation` | 0 | 6 个索引条目移除，本地文件保留 |
| `git ls-files specs` | 0 | 空输出 |
| 本地文件计数（`specs/001-harness-foundation`） | 0 | 6 个文件仍存在 |
| `git check-ignore -v --no-index specs/001-harness-foundation/spec.md` | 0 | 命中 `.gitignore` 的 `/specs/` |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | 36 个 Markdown / 99 个本地目标通过 |
| 干净检出模拟（230 个跟踪/未忽略文件，无 `specs/`）中的 `-Check docs` | 0 | 24 个 Markdown / 87 个本地目标通过 |
| `git diff --check` | 0 | 无空白错误 |

初始干净检出模拟曾因 `harness/README.md` 仍保留 3 个 001 链接而失败
（`Missing Markdown target`）；移除链接并改为本地路径说明后重跑通过。该失败不是环境问题，
说明干净检出检查确实能发现只在本地存在的引用。

## Limitations and blockers

- 远端 CI 尚未运行；提交推送后须按 freshness 规则重新确认。
- 本 evidence 绑定未提交工作树；新提交产生后需要重新锚定。
- 001 仅从索引移除，内容仍在本机与历史提交中；本地删除后不可恢复。
- 002 仍为本地工件，不随仓库分发。
