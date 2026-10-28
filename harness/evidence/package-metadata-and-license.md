# Evidence — Package metadata and proprietary license (Lightweight)

## Identity and scope

- **route**: Lightweight（包元数据与许可证治理，无运行时行为变化）
- **feature_id**: 不适用（独立治理改动）
- **phase_id**: `package-metadata-and-license`
- **task_id**: 不适用（无 Ralph receipt）
- **base_revision**: `0f67f44eb5fb7bd76f85ac9ce2b701dd15e3cbf1`
- **head_revision**: `working-tree (0f67f44 plus uncommitted worktree)`
- **working_directory**: `D:\Repos\Github\spawn-join`
- **recorded_at**: 2026-10-28
- **environment**: Windows；PowerShell 7；uv；Spec Kit CLI 1.2.3；Python 3.13.5（验证用解释器）
- **result**: pass

## Changed paths

- 新增根 `LICENSE`（Proprietary，版权持有人确认）与四个包的 `LICENSE` 副本、`README.md`。
- 四个 `pyproject.toml`：`readme`、`license = "LicenseRef-Proprietary"`、`license-files`、
  `authors`、`[project.urls]`，构建后端提升到 `setuptools>=77`。
- 新增 `.github/pull_request_template.md`（中文，含当前设计、改动、影响范围、设计图、
  AI 披露与验证小节）。
- `README.md` 增加许可证说明。
- `.specify/extensions/quality/quality-config.yml`：治理 Profile 覆盖 `LICENSE` 与根 PR 模板，
  避免这两类路径成为 unprofiled。
- `docs/development/quality-gates.md`：移除“包级 README 缺失警告不在本 Feature 修复”的旧说明。

## Verification

| Actual command/check | Exit | Result |
|---|---:|---|
| `uv lock --check --directory <four packages>` | 0 | 四个锁文件仍与元数据一致 |
| `uv build packages/core/spawn-join-core --out-dir <temp>` | 0 | 构建成功，无 `sdist: standard file not found` |
| Wheel METADATA inspection | 0 | `License-Expression: LicenseRef-Proprietary`；`License-File: LICENSE`；`Description-Content-Type: text/markdown` |
| sdist inspection | 0 | 包含 `README.md` 与 `LICENSE` |
| `pwsh -NoProfile -File scripts/quality.ps1` | 0 | 四包构建、隔离安装、测试、文档、治理与静态检查通过 |
| `git diff --check` | 0 | 无空白错误 |

## Limitations

- 没有发布到私有 Registry，也没有创建 Tag；本次只验证可构建和元数据可读。
- 许可证选择由维护者确认（Proprietary）；未引入第三方代码，因此没有新增许可证兼容性审查。
- 远端 CI 在本提交产生后另行运行；本记录不把本地成功当成远端通过。
