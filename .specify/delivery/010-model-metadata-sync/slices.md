# Delivery slice plan: 010-model-metadata-sync

## Identity and approval

- Delivery run / canonical path: `010-model-metadata-sync` / `.specify/delivery/010-model-metadata-sync/`
- Feature / spec / plan / tasks: `specs/010-model-metadata-sync/{spec.md,plan.md,tasks.md}`
- Baseline HEAD / relevant working-tree changes: `f717f71b5360b1c4e8b421301359787b0e41db9e`；当前规划只新增 `specs/`（忽略）、`.specify/delivery/010-model-metadata-sync/` 和 `docs/decisions/llm-provider/0009-model-metadata-and-sync.md`（Proposed）。
- Design approval: 用户 2026-11-02 回复“好”，批准 `plan.md` 所示设计；本次 slice 重新规划是在 `speckit.analyze` 发现 C1/C2 后进行的任务重排，设计范围未变。
- Artifact policy: ephemeral
- Planning timestamp: 2026-11-02

## Merge decision

- PR slicing: `auto`
- Merge mode: `stacked`
- Target branch: `main`
- Integration branch: N/A
- Stack provider: `manual`
- Slice merge method: `squash`
- Final merge method: `squash`（每个切片独立 squash；无最终 rollup）
- Target sync method: N/A
- Merge queue: no
- Delete branch after merge: yes
- Freeze integration before final review: no（无 integration 分支）
- Why this mode: 所有切片均为 `standalone`，按线性顺序可独立构建/测试；仓库要求线性历史，`pr_slicing: auto` 在全部 standalone 时使用 stacked；`stack_provider: manual` 是已记录的 provider fallback，不声称原生 stacked PR 或 merge queue。

## Slice table

| ID | Goal | Kind | Depends on | Task IDs | Paths | Trunk-safe | Flag | Merge order |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S0 | 新包骨架、质量入口和 CI 矩阵 | foundation | - | T001-T005 | `packages/infra/llm-model-sync/`、`scripts/quality.ps1`、`scripts/test-quality.ps1`、`.specify/extensions/quality/quality-config.yml`、`.github/workflows/quality.yml` | standalone | - | 1 |
| S1 | 元数据契约、快照文档和覆盖合并 | foundation | S0 | T006-T011 | `packages/core/llm-provider/src/.../metadata.py`、`__init__.py`、`tests/test_metadata.py`、`tests/test_public_api.py` | standalone | - | 2 |
| S2 | `model.yaml` v2 解析（仅解析） | foundation | S1 | T012-T013 | `packages/infra/llm-provider-langchain/src/.../model_file/_schema.py`、`tests/test_model_file.py` | standalone | - | 3 |
| S3 | 源契约和注册表核心 | foundation | S2 | T014-T016 | `packages/infra/llm-model-sync/src/.../_source.py`、`_registry.py`、`tests/test_registry.py` | standalone | - | 4 |
| S4 | models.dev adapter 和 fixture | behavior | S3 | T017、T018、T025 | `packages/infra/llm-model-sync/src/.../sources/models_dev.py`、`tests/fixtures/`、`tests/test_models_dev.py` | standalone | - | 5 |
| S5 | 快照/合并/缓存/runner | behavior | S4 | T019、T021-T024、T026 | `.../_snapshot.py`、`_merge.py`、`_cache.py`、`_runner.py`、`tests/test_snapshot.py`、`tests/test_runner.py` | standalone | - | 6 |
| S6 | 手动同步 CLI 和 README | behavior | S5 | T020、T027-T029 | `.../_cli.py`、`__init__.py`、`tests/test_cli.py`、`README.md` | standalone | - | 7 |
| S7 | 运行时可选读取和多渠道价格 | behavior | S2 | T030-T035 | `packages/infra/llm-provider-langchain/src/.../model_file/*`、`tests/test_model_metadata.py`、`tests/test_public_api.py`、`README.md` | standalone | - | 8 |
| S8 | 源注册公共面和 `sources` 命令 | behavior | S6 | T036-T041 | `.../_registry.py`、`sources/__init__.py`、`__init__.py`、`tests/test_registry.py`、`tests/test_cli.py`、`README.md` | standalone | - | 9 |
| S9 | 文档、ADR 索引、质量门和端到端验证 | release | S0-S8 | T042-T049 | `docs/`、`README.md`、`AGENTS.md`、`packages/*/README.md`、`scripts/`、工作区验证 | standalone | - | 10 |

## Slice details

### S0 — 新包骨架、质量入口和 CI 矩阵

- Acceptance outcome: `spawn-join-llm-model-sync` 可独立安装、导入、构建和运行 `scripts/quality.ps1 -Package spawn-join-llm-model-sync`；最小 CLI 返回“尚未实现”，不改变现有包行为。
- Task IDs: T001, T002, T003, T004, T005
- Expected paths: `packages/infra/llm-model-sync/{pyproject.toml,README.md,src/spawn_join_llm_model_sync/__init__.py,src/.../_cli.py,tests/test_package.py}`（新）；`scripts/quality.ps1`、`scripts/test-quality.ps1`、`.specify/extensions/quality/quality-config.yml`、`.github/workflows/quality.yml`（改）。
- Trunk-safe: standalone
- Evidence: 新包不改变任何现有 Distribution 的公共面；最小测试保证零测试门禁不失败；现有质量门可继续通过。
- Target verification: `uv lock --check --directory packages/infra/llm-model-sync`；`uv sync --locked --directory packages/infra/llm-model-sync`；`pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-model-sync`。
- Flag: N/A
- Integration checkpoints: N/A
- Review focus: `pyproject.toml` 依赖/本地源/console script 正确；quality profile 与脚本映射一致；CI matrix 没有改变现有平台/Python 组合。
- Not in this slice: 元数据契约、v2 解析、源注册、同步实现、运行时读取。
- Rollback: revert S0 commit；新包不被其他包依赖，删除不影响现有功能。
- Diff budget: 预计约 8 files / 120 lines；无例外。

### S1 — 元数据契约、快照文档和覆盖合并

- Acceptance outcome: `spawn-join-llm-provider` 提供严格校验的元数据值对象、快照文档解析和整段覆盖合并；现有公共 API 和 CLI 行为不变。
- Task IDs: T006, T007, T008, T009, T010, T011
- Expected paths: `packages/core/llm-provider/src/spawn_join_llm_provider/metadata.py`（新）、`__init__.py`（改）、`tests/test_metadata.py`（新）、`tests/test_public_api.py`（改）。
- Trunk-safe: standalone
- Evidence: 只新增模块和导出；现有消费者不引用新类型；`llm-provider` 测试和构建在切片后通过。
- Target verification: `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider`。
- Flag: N/A
- Integration checkpoints: N/A
- Review focus: 价格单位/非负/有限、日期、未知字段、阶梯排序、覆盖整段替换、无 I/O；确认没有引入运行时能力协商语义。
- Not in this slice: `model.yaml` v2 解析、运行时读取、同步工具。
- Rollback: revert S1 commit；新类型无消费者。
- Diff budget: 预计约 3 files / 600 lines；**预算例外**：单一公共契约文件 + 边界测试，拆成两个 PR 会在同一文件上制造半套公共 API 和重复评审；请求 slice gate 接受。

### S2 — `model.yaml` v2 解析（仅解析）

- Acceptance outcome: `model.yaml` v2 可被解析为内部条目，`metadata_ref`/`metadata_source`/`metadata` 校验生效；v1 行为不变；此切片不读取快照，不改变 `ModelCatalog` 公共行为。
- Task IDs: T012, T013
- Expected paths: `packages/infra/llm-provider-langchain/src/.../model_file/_schema.py`（改）、`tests/test_model_file.py`（改）。
- Trunk-safe: standalone
- Evidence: 只扩展解析器；v2 字段解析后暂未被 `ModelCatalog` 消费；v1 回归测试保持通过。
- Target verification: `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider-langchain`。
- Flag: N/A
- Integration checkpoints: N/A
- Review focus: v1 兼容、`metadata_source` 必须有 `metadata_ref`、未知字段、错误路径不含密钥、解析器仍无快照 I/O。
- Not in this slice: 快照读取、`ModelSummary.metadata`、同步工具。
- Rollback: revert S2 commit；v2 文件会退回未知字段错误，但 v1 行为不变。
- Diff budget: 预计约 2 files / 200 lines；无例外。

### S3 — 源契约和注册表核心

- Acceptance outcome: 新包提供 `MetadataSource` 契约、`SourceRegistry` 和重复/未知源错误；可用假源独立测试。
- Task IDs: T014, T015, T016
- Expected paths: `packages/infra/llm-model-sync/src/.../_source.py`、`_registry.py`（新）；`tests/test_registry.py`（新）。
- Trunk-safe: standalone
- Evidence: 新模块无外部消费者；测试不访问网络；包构建/测试通过。
- Target verification: `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-model-sync`。
- Flag: N/A
- Integration checkpoints: N/A
- Review focus: 协议方法、源 ID 校验、重复/替换语义、实例化注册表无全局状态、无网络 import 副作用。
- Not in this slice: models.dev adapter、runner、CLI。
- Rollback: revert S3 commit；无消费者。
- Diff budget: 预计约 4 files / 200 lines；无例外。

### S4 — models.dev adapter 和 fixture

- Acceptance outcome: `ModelsDevSource` 能从 `catalog.json` 按请求翻译共享模型和 provider 覆盖；空/畸形 payload 失败；fixture 覆盖价格、限制、模态和 reasoning。
- Task IDs: T017, T018, T025
- Expected paths: `packages/infra/llm-model-sync/src/.../sources/models_dev.py`（新）、`tests/fixtures/catalog.json`、`tests/fixtures/model.yaml`、`tests/test_models_dev.py`（新）。
- Trunk-safe: standalone
- Evidence: adapter 不被 CLI 调用前不影响任何现有命令；fixture 测试可独立运行；无 live 网络依赖。
- Target verification: `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-model-sync`；可选 `pytest .../test_models_dev.py`。
- Flag: N/A
- Integration checkpoints: N/A
- Review focus: `canonical_model_id` 映射、`cost` 单位、`reasoning_options` 未知类型警告、只翻译请求 refs/hosts、错误不含敏感内容。
- Not in this slice: runner、快照写入、CLI。
- Rollback: revert S4 commit；无消费者。
- Diff budget: 预计约 5 files / 350 lines；无例外。

### S5 — 快照/合并/缓存/runner

- Acceptance outcome: 同步核心可读取 `model.yaml` 引用、抓取/翻译、合并、校验、diff、原子写和失败保护；CLI 尚未暴露。
- Task IDs: T019, T021, T022, T023, T024, T026
- Expected paths: `.../_snapshot.py`、`_merge.py`、`_cache.py`、`_runner.py`（新）；`tests/test_snapshot.py`、`tests/test_runner.py`（新）。
- Trunk-safe: standalone
- Evidence: 新模块只被新测试调用；现有包和 CLI 行为不变；fixture 可验证 dry-run/apply/check 和失败保护。
- Target verification: `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-model-sync`。
- Flag: N/A
- Integration checkpoints: N/A
- Review focus: 确定性序列化、原子写、空/截断/全部未匹配保护、单模型缺失保留、报告包含未引用上游计数、`model.yaml` 字节不变、来源 provenance。
- Not in this slice: CLI、`sources` 命令、运行时读取。
- Rollback: revert S5 commit；无用户可见入口。
- Diff budget: 预计约 7 files / 650 lines；**预算例外**：快照、合并、缓存和 runner 构成一条不可分割的数据路径，拆开会留下不可运行或不可验证的中间态；请求 slice gate 接受。

### S6 — 手动同步 CLI 和 README

- Acceptance outcome: `model-sync sync` 可执行 dry-run/apply/check，退出码和存储位置符合契约；README 给出可复现用法。
- Task IDs: T020, T027, T028, T029
- Expected paths: `.../_cli.py`（改）、`__init__.py`（改）、`tests/test_cli.py`（新）、`README.md`（改）。
- Trunk-safe: standalone
- Evidence: 新命令是纯增量；现有包和运行时行为不变；CLI 测试覆盖 0/1/2/3 退出码。
- Target verification: `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-model-sync`；`model-sync sync --help`。
- Flag: N/A
- Integration checkpoints: N/A
- Review focus: 默认 dry-run、`--apply`/`--check` 互斥、输出/缓存路径、错误不含密钥、无交互提示。
- Not in this slice: `sources` 命令、运行时读取。
- Rollback: revert S6 commit；删除 CLI 入口即可，快照格式不受影响。
- Diff budget: 预计约 4 files / 250 lines；无例外。

### S7 — 运行时可选读取和多渠道价格

- Acceptance outcome: `ModelCatalog` 可选读取显式快照；`ModelSummary` 暴露 `metadata_ref`/`metadata`；同一模型两个渠道返回不同价格；不传快照时 v1 行为不变。
- Task IDs: T030-T035
- Expected paths: `packages/infra/llm-provider-langchain/src/.../model_file/{_metadata,_catalog,__init__}.py`（改/新）；`packages/infra/llm-provider-langchain/src/.../__init__.py`（改）；`tests/test_model_metadata.py`（新）；`tests/test_public_api.py`（改）；`README.md`（改）。
- Trunk-safe: standalone
- Evidence: 默认 `metadata_file=None`，现有 v1 测试全部保留；新行为只在显式路径时启用；加载不联网。
- Target verification: `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider-langchain`。
- Flag: N/A
- Integration checkpoints: N/A
- Review focus: v1 兼容、`base_model` 一致性、覆盖优先级、缺失 ref 返回 `None`、未知字段/版本错误、公共 API 精确导出。
- Not in this slice: 同步工具、源注册。
- Rollback: revert S7 commit；不传快照的调用方不受影响。
- Diff budget: 预计约 8 files / 550 lines；**预算例外**：schema 已在 S2、运行时 loader/catalog/public API 是一个读取契约；拆开会留下未验证的半套读取路径；请求 slice gate 接受。

### S8 — 源注册公共面和 `sources` 命令

- Acceptance outcome: 维护者可注册假源；`model-sync sources` 列出源；重复 ID/未知源错误明确；新增源不需要改 runner/schema/runtime。
- Task IDs: T036-T041
- Expected paths: `.../_registry.py`（改）、`sources/__init__.py`（新）、`__init__.py`（改）、`tests/test_registry.py`（改）、`tests/test_cli.py`（改）、`README.md`（改）。
- Trunk-safe: standalone
- Evidence: 只增加公共注册面和只读 `sources` 命令；现有 `sync` 命令保持可用；假源测试不访问网络。
- Target verification: `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-model-sync`。
- Flag: N/A
- Integration checkpoints: N/A
- Review focus: 注册表无全局单例、`replace=True` 仅显式使用、`sources --json` 字段、未知源错误、契约测试覆盖翻译边界。
- Not in this slice: 第二个真实源、调度、自动 PR。
- Rollback: revert S8 commit；内置 models.dev 仍由 S4/S6 注册路径可用。
- Diff budget: 预计约 6 files / 250 lines；无例外。

### S9 — 文档、ADR 索引、质量门和端到端验证

- Acceptance outcome: 包边界、仓库地图、README、质量门文档与 ADR 索引一致；quickstart（含回滚）和全仓库门禁有可复现证据；ADR-0009 在 review 后由 `decision.finalize` 处理。
- Task IDs: T042-T049
- Expected paths: `docs/architecture/package-boundaries.md`、`repository-map.md`、`docs/development/quality-gates.md`、`docs/decisions/README.md`、`docs/decisions/llm-provider/0009-*.md`、根 `README.md`、`AGENTS.md`、相关包 README、`.gitignore`（按需）。
- Trunk-safe: standalone
- Evidence: 文档/ADR/治理更新不改变运行时行为；全仓库质量门和 docs/governance 通过后有证据；ADR-0009 只在 reviewed HEAD 匹配后由 `decision.finalize` 改为 Accepted。
- Target verification: `pwsh -NoProfile -File scripts/quality.ps1`；`pwsh -NoProfile -File scripts/test-quality.ps1`；`pwsh -NoProfile -File scripts/quality.ps1 -Check docs`；`-Check governance`；`git diff --check`。
- Flag: N/A
- Integration checkpoints: N/A
- Review focus: 包数量从四个改为五个、依赖边正确、ADR 索引状态一致、quickstart 含回滚、无构建产物、无密钥。
- Not in this slice: 新功能、第二源、调度。
- Rollback: revert S9 commit；源码功能保持。
- Diff budget: 预计约 12 files / 350 lines；无例外。

## Coverage and validation

- Task coverage: T001-T049 全部映射；每个任务恰好出现一次；没有跨切片任务。
- Requirement coverage:
  - FR-001 ~ FR-006 → S1（契约）、S2（v2 解析）、S7（运行时）
  - FR-007 ~ FR-013 → S1（文档/校验）、S5（快照/合并）
  - FR-014 ~ FR-024 → S4/S5/S6/S8（同步、CLI、源注册）
  - FR-025 ~ FR-028 → S7（运行时）
  - FR-029 ~ FR-031 → S9（安全/文档）
  - SC-001 ~ SC-010 → S5/S6/S7/S9 的验证项
- Dependency order: S0 → S1 → S2 → S3 → S4 → S5 → S6 → S7 → S8 → S9；线性、无环。S7 只依赖 S2，放在 S6 之后是为了保持线性 stacked 顺序。
- Budget exceptions: S1、S5、S7 预计超过 400 行；理由分别为单一公共元数据契约、不可分割的同步数据路径、不可分割的运行时读取契约。其余切片在 20 files / 400 lines 以内。
- Policy compatibility: `pr_slicing: auto` + 全 standalone → stacked；目标 `main` 线性历史；`stack_provider: manual`；slice/final 均为 squash；不使用 merge queue；不声称原生 stacked PR 能力。
- Open decisions: 无。`metadata_source`、价格费率形状、包名和 models.dev 端点已在 Plan 固定；预算例外需 slice gate 明确接受。

## Merge plan

- Order: S0 → S1 → S2 → S3 → S4 → S5 → S6 → S7 → S8 → S9
- Per-slice merge: 每个切片从 `main` 的当前 head 创建手动分支，squash 到 `main`；前一个切片合并后再创建下一个。
- Final rollup: 无 rollup；每个切片是独立 squash，保持线性历史。
- Target sync: N/A（无 integration 分支）。
- Queue/freeze: 不使用 merge queue；最终 review 前不冻结（无 integration 分支）。
- Issue closure: 当前没有绑定 Issue；如创建，lower slices 使用 `Part of #...`，release slice 使用 `Closes #...`。不得在 durable PR 文本中用 T### 作为需求来源。
- Rollback per slice: 见各切片 Rollback；均为 revert 单个 squash commit。

## Approval record

- SLICE_PLAN_VERDICT: ready
- SLICE_APPROVAL: approved
- Approved by: 用户 2026-11-02
- Choice / accepted risks: 批准更新后的 10 个切片；接受 S1/S5/S7 预算例外；用户明确要求不创建本地 git commit，代码留在工作树供晚间 code review。
- Approved mode / snapshot: stacked；`tasks.md` T001-T049 + 修订后的 `plan.md`/`spec.md`；`main` 线性历史。
- Commit policy: 本次运行跳过本地提交（用户 override）。不执行 Ralph 的 per-task commit gate，不声明 `ALL_TASKS_DONE`；代码、测试和证据以工作树快照为准，等待用户 code review。`delivery-config.yml` 的 `auto_commit: task-only` 在本次运行不适用，影响是任务复选框和 Ralph receipt 不能作为最终完成证据，后续需由 review/evidence 补足。
