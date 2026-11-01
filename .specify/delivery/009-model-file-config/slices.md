# Delivery slice plan: 009-model-file-config

## Identity and approval

- Delivery run / canonical path: `.specify/delivery/009-model-file-config/`
- Feature / spec / plan / tasks:
  - `specs/009-model-file-config/spec.md`
  - `specs/009-model-file-config/plan.md`（SHA256 `C7E856C1C8AC9282C78C62CBB28C7EAFEE78C157180E0507C0DFF00648D410DF`）
  - `specs/009-model-file-config/tasks.md`（SHA256 `02101F5ED95D7A976934C9A5E6470A92435DB49C9DA50504C1134DE4A9A96654`；2026-11-01 合并原 T001/T002、拆分 T003/T004 助手后的队列）
- Baseline HEAD: `392aa909bcfe57f47d84d3d5e782ffd5fed4ae1f`；工作树在计划阶段只有本地忽略工件
- Design approval: 用户 2026-11-01 回复“plan 通过”，针对上述 plan 快照
- Artifact policy: ephemeral（`specs/` 本地忽略；本文件与 evidence 在 `.specify/delivery/`）
- Planning timestamp: 2026-11-01

## Merge decision

- PR slicing: `auto`
- Merge mode: **stacked**
- Target branch: `main`
- Integration branch: N/A
- Stack provider: `manual`
- Slice merge method: `squash`
- Final merge method: N/A（stacked 逐片 squash 到 `main`；无 rollup）
- Target sync method: N/A（每个切片直接基于最新 `main`）
- Merge queue: no
- Delete branch after merge: yes
- Freeze integration before final review: yes（沿用配置；无 integration 分支，冻结的是最终评审快照）
- Why this mode: 5 个切片全部为 additive、`standalone`，按线性顺序可逐个 squash 到 `main`；
  仓库要求线性历史，`integration` 的 merge-commit rollup 与策略冲突，因此不使用。

## Slice table

| ID | Goal | Kind | Depends on | Task IDs | Paths | Trunk-safe | Flag | Merge order |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S1 | 依赖与 YAML 解析边界 | foundation | - | T001–T003 | `pyproject.toml`、`uv.lock`、`model_file.py`、`tests/test_model_file.py`、`tests/fixtures/*` | standalone | - | 1 |
| S2 | US1：从文件创建模型与协议选项 | behavior | S1 | T004–T005 | `model_file.py`、`__init__.py`、`tests/test_model_file.py`、`tests/test_public_api.py` | standalone | - | 2 |
| S3 | US2：模型清单与展示名 | behavior | S2 | T006 | `model_file.py`、`__init__.py`、`tests/test_model_file.py`、`tests/test_public_api.py` | standalone | - | 3 |
| S4 | US3：`.env` 与密钥优先级 | behavior | S3 | T007 | `model_file.py`、`tests/test_model_file.py` | standalone | - | 4 |
| S5 | 文档与最终验证 | release | S4 | T008–T010 | `README.md`（两个包）、`docs/architecture/package-boundaries.md`、`.gitignore`、验证记录 | standalone | - | 5 |

## Slice details

### S1 — 依赖与 YAML 解析边界

- Acceptance outcome: 适配包安装 PyYAML/python-dotenv，内部 YAML 解析器能拒绝语法错误、重复键、递归别名、非 UTF-8 和非映射根节点，且不泄露文件内容。
- Task IDs: T001、T002、T003
- Expected paths: `packages/infra/llm-provider-langchain/pyproject.toml`（modify）、`uv.lock`（modify，生成文件）、`src/.../model_file.py`（new）、`tests/test_model_file.py`（new）、`tests/fixtures/model.yaml`（new）、`tests/fixtures/model-invalid-duplicate.yaml`（new）
- Trunk-safe: `standalone`
- Evidence: 只新增内部模块与依赖；不导出新公共名字，现有公共 API 测试不变；目标包测试可独立通过。
- Target verification: `uv lock --check --directory packages/infra/llm-provider-langchain`；`uv sync --locked --directory packages/infra/llm-provider-langchain`；`pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider-langchain`
- Flag: N/A
- Review focus: 是否只使用 `SafeLoader`/`safe_load`；compose 检查是否覆盖嵌套与序列、是否拒绝递归别名；错误消息是否只含行列/problem/path。
- Not in this slice: 公共导出与目录对象（S2）。
- Rollback: revert 切片提交并重新 `uv sync --locked`。
- Diff budget: 约 6 文件 / 300–350 行（`uv.lock` 不计）。

### S2 — US1：从文件创建模型与协议选项

- Acceptance outcome: `load_model_catalog` 返回可按 default/名字创建模型的目录；三种协议的 options 与 thinking 正确映射。
- Task IDs: T004、T005
- Expected paths: `src/.../model_file.py`（modify）、`src/.../__init__.py`（modify）、`tests/test_model_file.py`（modify）、`tests/test_public_api.py`（modify）
- Trunk-safe: `standalone`
- Evidence: 只新增公共名字与行为；现有 `ChatModelConfig`/`create_chat_model` 不变；导出与契约测试在同一任务更新，前缀保持绿色。
- Target verification: 同 S1 的包质量命令，另加 `pytest tests/test_public_api.py tests/test_model_file.py -q`
- Flag: N/A
- Review focus: default/名字解析顺序；options 白名单与现有 dataclass 一致；错误路径带 YAML 路径；无 `.env` 读取。
- Interim public subset: S2 导出 `load_model_catalog` 与 `ModelCatalog`，但 `ModelCatalog.models` 在 S3 增加、`env_file` 参数在 S4 增加。两者都是向后兼容的纯增量；`contracts/public-api.md` 描述的是 S4 之后的最终状态。
- Not in this slice: 清单展示（S3）、`.env`（S4）。
- Rollback: revert 切片；公共面回到 2 个名字。
- Diff budget: 实际 `9678cce..925665c` 新增 1,031 行（源码 493 行），超过 `slice_warn_lines: 400`；已记录为预算例外，理由是一个用户可见能力的完整创建与选项路径。

### S3 — US2：模型清单与展示名

- Acceptance outcome: `catalog.models` 按文件顺序返回 `ModelSummary`，展示名显式值或回退选择名。
- Task IDs: T006
- Expected paths: `src/.../model_file.py`（modify）、`src/.../__init__.py`（modify）、`tests/test_model_file.py`（modify）、`tests/test_public_api.py`（modify）
- Trunk-safe: `standalone`
- Evidence: 纯增量属性与类型；现有创建行为不变；契约测试在同一任务更新到 5 个名字。
- Target verification: 同 S2。
- Flag: N/A
- Review focus: 顺序保持；展示名不参与查找；`repr` 脱敏；非字符串/控制字符拒绝。
- Interim public subset: S3 完成 `ModelSummary` 与 `models`，公共面达到 5 个名字；`env_file` 参数仍在 S4。
- Not in this slice: `.env`（S4）。
- Rollback: revert 切片；清单 API 消失，创建行为不变。
- Diff budget: 约 4 文件 / 100–150 行。

### S4 — US3：`.env` 与密钥优先级

- Acceptance outcome: 显式 `env_file=` 可提供密钥；进程环境优先；空值报错且不回退；不修改 `os.environ`。
- Task IDs: T007
- Expected paths: `src/.../model_file.py`（modify）、`tests/test_model_file.py`（modify）
- Trunk-safe: `standalone`
- Evidence: 默认 `env_file=None` 保持现有行为；新增能力是可选参数；无公共名字变化。
- Target verification: 同 S2。
- Flag: N/A
- Review focus: 快照只保留被引用变量；空值与缺失区分；`environ` 注入不污染全局；错误只含变量名。
- Final contract: S4 完成后 `load_model_catalog(env_file=...)`、`ModelCatalog.models` 与 5 个公共名字全部落地，`contracts/public-api.md` 不再有 interim 差异。
- Not in this slice: 文档（S5）。
- Rollback: revert 切片；`env_file` 参数消失，原行为不变。
- Diff budget: 约 2 文件 / 150–200 行。

### S5 — 文档与最终验证

- Acceptance outcome: 两个 README 与包边界文档反映新能力；完整质量门、docs、governance 和 `git diff --check` 通过。
- Task IDs: T008、T009、T010
- Expected paths: `packages/infra/llm-provider-langchain/README.md`（modify）、`packages/core/llm-provider/README.md`（modify）、`docs/architecture/package-boundaries.md`（modify）、`.gitignore`（modify）、任务 receipt（new）
- Trunk-safe: `standalone`
- Evidence: 只改文档与忽略规则；代码与依赖已在前四片落地；文档检查命令可执行。
- Target verification: `pwsh -NoProfile -File scripts/quality.ps1 -Check docs`；`-Check governance`；包质量命令复跑；`git diff --check`
- Flag: N/A
- Review focus: 文档与契约一致；无真实密钥；链接有效；限制与优先级表准确。
- Not in this slice: 新行为（已在前四片）。
- Rollback: revert 文档提交。
- Diff budget: 约 4 文件 / 150–200 行。

## Coverage and validation

- Task coverage: T001–T010 每个任务恰好映射一次；无跨切片任务。
- Requirement coverage:
  - FR-001/003/004/007/008/017 → S2
  - FR-002 → S2（`schema_version` 校验；S1 只负责 YAML 文档解析）
  - FR-015/016 → S1
  - FR-005/006 → S2
  - FR-009/010/018 → S4
  - FR-011 → S1（未知字段/安全解析）+ S4（无插值）
  - FR-012 → S1/S2
  - FR-013/014 → S3
  - SC-001 → S2；SC-002 → S3；SC-003 → S4；SC-004 → 所有切片；SC-005 → S1/S3/S4；SC-006 → S2
- Dependency order: S1 → S2 → S3 → S4 → S5，无环、单一线性顺序。
- Budget exceptions: S2 预计接近 400 行；理由见 S2 详情，不改变任务映射。
- Policy compatibility: `main` 线性历史 + required `Quality Gate`；manual stacked，逐片 squash；无 merge queue；删除分支；最终评审前冻结快照。
- Open decisions: none。

## Merge plan

- Order: S1 → S2 → S3 → S4 → S5
- Per-slice merge: squash 到最新 `main`
- Final rollup: N/A（stacked）
- Target sync: 每个切片开始前基于最新 `main`；不使用 integration 分支
- Queue/freeze: 无 merge queue；最终评审前冻结工作树，不新增提交
- Issue closure: 本 Feature 未创建 GitHub Issue；PR 描述引用 spec/plan 的用户可见结果，不把任务 ID 当作需求来源
- Rollback per slice: 见各切片 Rollback

## Approval record

- SLICE_PLAN_VERDICT: ready
- SLICE_APPROVAL: approved
- Approved by: 用户 2026-11-01 回复「slice 通过」，随后授权 Ralph 执行
- Choice / accepted risks: stacked；5 个 standalone 切片；接受 S2 接近 400 行的预算说明
- Approved mode / snapshot: stacked；plan SHA256 `C7E856C1C8AC9282C78C62CBB28C7EAFEE78C157180E0507C0DFF00648D410DF`；tasks SHA256 `02101F5ED95D7A976934C9A5E6470A92435DB49C9DA50504C1134DE4A9A96654`
- Queue correction: 2026-11-01 Ralph 预检发现 `uv sync --locked` 使“只改 pyproject”的 T001 无法独立通过；原 T001/T002 合并为新 T001，其余任务顺延一位。切片边界与需求映射不变。
- Design note correction: 2026-11-01 T003 实现时把 `_StrictSafeLoader` 子类改为 `yaml.compose` 节点树检查（重复键/递归别名）+ `safe_load`。行为与安全属性不变；原始方案会触发 Pyright 对未类型化 PyYAML 成员的错误，并遗漏非 UTF-8/递归别名边界。plan/research/data-model 已同步，任务边界不变。
- Delivery deviation: 2026-11-01 为便于用户 Code Review，本次以**单个 Feature PR** 承载 5 个切片；不声称 stacked 交付已完成。合并方式（逐片 squash 或单 PR squash）待用户评审后决定，未授权 push/merge 前不执行。
