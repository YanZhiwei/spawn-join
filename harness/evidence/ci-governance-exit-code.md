# Evidence — CI Governance Regression Exit Code (Bugfix)

## Identity and scope

- **route**: Bugfix（CI 已有可复现失败，先建立 red evidence）
- **feature_id**: 不适用（未创建 Feature Spec；缺陷属于已提交的质量门脚本）
- **phase_id**: `bugfix-ci-governance-exit-code`
- **task_id**: 不适用（无 Ralph receipt）
- **base_revision**: `0e2b10ea176ca9411fa8a7bcb5f34a27a28d1e4f`
- **head_revision**: `0e2b10e` 加未提交工作树（`scripts/test-quality.ps1`、本 evidence、`harness/build-log.md`）
- **working_directory**: `D:\Repos\Github\spawn-join`
- **recorded_at**: 2026-10-27T13:51:29Z
- **environment**: Windows；PowerShell 7.6.9；uv 0.7.13；Node 22.17.0；git 2.55.0.windows.3
- **result**: pass

## Defect and red evidence

GitHub 上仅有的两次 Quality 运行（push `3b0aaf9`、push `0e2b10e`）均为失败：

- 12 个 `packages` 矩阵任务全部通过；
- `Quality Gate` 按设计因依赖失败而失败；
- `governance` job 的 `Test gate failure paths` 步骤打印 **9/9 场景 PASS** 和
  `Gate regression checks passed: 9 scenarios; no root project artifacts.` 后，
  以 `Process completed with exit code 1` 结束，日志中没有任何异常或错误文本。

根因：`scripts/test-quality.ps1` 的最后一个断言故意运行失败的门禁（预期 exit 1），
使 `$LASTEXITCODE` 停留在 1；脚本成功路径没有显式退出码。GitHub Actions 对 `pwsh`
步骤使用 `pwsh -command ". '{0}'"`，并在脚本末尾追加：

```text
if ((Test-Path -LiteralPath variable:\LASTEXITCODE)) { exit $LASTEXITCODE }
```

来源：`actions/runner` 的 `src/Runner.Worker/Handlers/ScriptHandlerHelpers.cs`
（`FixUpScriptContents`，2026-10-27 读取 `main`）。因此 9 个场景全部通过，步骤仍被
残留的 `$LASTEXITCODE=1` 判为失败。

本地直接 `pwsh -File scripts/test-quality.ps1` 不追加该检查，所以历史本机验证结果为 0，
掩盖了 CI 终态缺陷。这与平台无关，Linux 只是 governance job 唯一运行环境。

`red` 复现（修复前，2026-10-27，Windows）：

```powershell
# 与 runner 等价的包装：dot-source 后追加 LASTEXITCODE 检查
pwsh -NoProfile -File C:\Users\YanZh\AppData\Local\Temp\opencode\runner-wrapper-probe.ps1
# 9 个场景全部 PASS，随后 exit 1
```

对照：同一脚本直接以 `pwsh -NoProfile -File scripts/test-quality.ps1` 运行时 exit 0，
证明失败只来自 CI 包装的退出码，不是断言失败。

## Change

- `scripts/test-quality.ps1`：在 `finally` 清理之后显式 `exit 0`，并注释说明原因。
- 未删除或放宽任何断言；未修改 `quality.ps1`、workflow、Python 源码、依赖或公共 API。
- `scripts/quality.ps1` 的所有成功路径当前都以 exit 0 的原生命令结束，本次不改动，
  避免扩大范围；若未来出现同类“容忍非零”逻辑，需要同样显式终态。

## Verification

| Command / check | Exit | Observed result |
|---|---|---|
| runner 等价包装运行 `scripts/test-quality.ps1`（修复前） | 1 | 9 个场景全部 PASS，随后因 `$LASTEXITCODE=1` 失败 |
| runner 等价包装运行 `scripts/test-quality.ps1`（修复后） | 0 | 9 个场景全部 PASS，包装退出 0 |
| `pwsh -NoProfile -File scripts/test-quality.ps1`（修复后） | 0 | 9 个场景全部 PASS |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | Markdown 链接、尾随空白与 `git diff --check` 通过 |
| 临时 fixture 残留检查 | 0 | 未发现 `spawn join gate fixture *` 目录 |

## Limitations and blockers

- 本地只有 Windows；Linux 上的 pwsh 未实际执行。缺陷机制与平台无关，但仍需远端
  ubuntu job 复跑确认。
- 远端 CI、Ruleset/分支保护仍未验证；本次未提交、未推送，未做任何远端写入。
- 本 evidence 绑定的是未提交工作树；产生新提交后必须按 freshness 规则重新确认。
- `phase-01-python-quality-gates` 与 ADR 证据仍锚定在 `bd497d7`，本次不追认旧范围；
  该再锚定是独立待办。
- 现有 build-log 仍未记录 `0e2b10e` 的 README 重写；本次不夹带处理。

## Remote confirmation

- 修复提交：`4c69609667a482e27271ee5a63633c6d0e17fec4`（父提交 `0e2b10e`）。
- 运行：[Quality #40515982522](https://github.com/YanZhiwei/spawn-join/actions/runs/40515982522)，
  创建于 2026-10-27T13:52:51Z，结论 `success`。
- 14/14 job 成功：12 个 packages 矩阵、`Governance and gate regression`、`Quality Gate`。
- 上文写于推送前，本节补记远端结果；本记录随后以 docs-only 提交发布，该后续提交自身的
  CI 结果不在本节声称范围内。
