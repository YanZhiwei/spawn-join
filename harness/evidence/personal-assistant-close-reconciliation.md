# Evidence — personal-assistant Close 终态收敛 (Lightweight)

## Identity and scope

- **route**: Lightweight（只收敛 Delivery 运行态与本地指纹，无产品源码、公共契约或运行时行为变化）
- **feature_id**: 不适用（独立治理收敛，不是新的 Feature/Bugfix run）
- **phase_id**: `personal-assistant-close-reconciliation`
- **base_revision**: `9ce1a1f1eb08a68a15289d3a7298d6278248f7eb`
- **head_revision**: `working-tree (9ce1a1f1eb…)`
- **working_directory**: `D:\Repos\spawn-join`
- **recorded_at**: 2026-11-21
- **environment**: Windows；PowerShell 7；uv 管理的 CPython 3.13.5；Git for Windows
- **result**: pass

## Observed inconsistency

`personal-assistant-20261121` 的持久记录（`.specify/delivery/personal-assistant-20261121/evidence.md`
当前结果块）已声明 `delivered` / `merged` / PR #73 / `merged_revision: be49da9…`，与真实
PR 结果一致；但运行态 `runtime/state.json` 停在 `phase: handoff`，`status` 为
`verification-required`，blocker 为 “Previously recorded canonical Evidence changed”。

根因：Close 当次直接改写了 `evidence.md`，没有经过机器写入器，因此 runtime 的
hash 绑定 observation 仍是旧值（记录 `924f4d7c…`，文件实际 `946d7c79…`），
`close` 也从未写入运行态。这不是需要重新交付的产品缺陷，而是运行态与持久记录未对齐。

## Actual action

1. 用 Delivery 自带机器写入器复核并刷新 observation（不重写 Close 块）：

   ```text
   <uv-cpython-3.13.5> .specify/extensions/delivery/scripts/delivery_runtime.py close-record \
     --run personal-assistant-20261121 --outcome merged --pr 73 --verified \
     --file runtime/observed-pr.json
   ```

   结果 `recorded: true`、`eligible: true`、`changed: false`、`writes_performed: false`，
   即 Close 块字节未变，校验的是既有事实。

2. 机器写入器校验项：`observed-pr.json` 身份一致；合并提交 `be49da9…` 本地可达；
   归档 `runtime/reviewed-diff-archive.diff` 的 sha256 `ea59f249…` 与记录一致；
   `published_head_proof: published-evidence-archive`、`merge_proof: evidence-archive`。

3. 工作区预存的 `.specify/delivery/personal-assistant-20261121/slices.md` “修改”经字节
   比对与 `HEAD` 完全相同（仅 Git stat 缓存脏）；用单路径 `git checkout --` 复原，
   未改动任何内容。

4. `runtime/state.json` 位于 `.git/info/exclude` 排除的本地运行工作区，因此本次
   **没有 tracked 源码或持久记录字节变化**；本文件与 `harness/build-log.md` 是本次
   唯一新增的持久记录。

## Verification

| Actual command/check | Exit | Result |
|---|---:|---|
| `delivery_runtime.py close-record --run personal-assistant-20261121 --outcome merged --pr 73 --verified --file runtime/observed-pr.json` | 0 | `changed: false`，Close 块未改写 |
| `delivery_runtime.py status --run personal-assistant-20261121 --json` | 0 | `status: delivered`、`blockers: []` |
| 对比 `state.json` observation 与 `evidence.md` 的 sha256 | — | 均为 `946d7c79b5b55f835a23ca6a8c1ac415c2133a7c6e3c6666bb8c0ace3698955c` |
| `git status --porcelain=v1 -uall` | — | 仅 `readme-dual-audience-20261121` 的 2 个预存未跟踪 PR 正文 |
| `git diff --check` | 0 | 无输出 |

## Limitations

- 本次不修改产品源码、manifest、锁文件、CI 或质量 Profile，因此不重跑包构建/测试矩阵。
- 其余 9 个 `verification-required` run 均为无 `runtime/state.json` 的 legacy 目录，其
  “Terminal legacy Evidence identity is missing or corrupt” 来自历史证据头部缺身份字段；
  修复它们等于补造运行历史，本次明确不做，保持原样。
- `harness/evidence/delivery-v022-upgrade.md` 的历史 freshness warning 属于既有记录，
  不在本次范围，未重新锚定。
- 本次未执行 push 或创建 PR；发布动作需另行授权。
- `.specify/delivery/readme-dual-audience-20261121/` 下的 2 个未跟踪 PR 正文是既有遗留物，
  本次未提交、未删除。
