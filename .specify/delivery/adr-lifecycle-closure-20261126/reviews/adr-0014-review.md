# Independent Review — ADR-0014: DeepAgents 官方 P1 能力的公共边界

- **reviewer**: 独立只读子代理（fresh context）
- **repository / HEAD**: `D:\Repos\spawn-join` / `79425090f442506663c0024bde02c62f1f5c7ea6`
- **reviewed_at**: 2026-11-26
- **scope**: ADR-0014 的 P1 公共边界与当前实现、测试、依赖方向是否一致，是否可转为 `Accepted`
- **REVIEW_VERDICT**: **blocked**
- **acceptance recommendation**: **keep Proposed**

## Inputs read

- `docs/decisions/agent/0014-deepagents-p1-capabilities.md`
- `.specify/delivery/deepagents-p1-continuation-20261115/{evidence.md,slices.md,decision-context.md}`
- `docs/decisions/agent/0010-deepagents-product-boundary.md`
- `docs/decisions/agent/0012-deepagents-official-p0.md`
- `docs/architecture/package-boundaries.md`
- `docs/decisions/README.md` 及未提交的 ADR diff
- `packages/infra/agent-deepagents/src/spawn_join_agent_deepagents/{rubric.py,interrupts.py,supervisor.py,diagnostics.py,backends.py,errors.py,middleware/scopes.py,__init__.py}`
- `packages/infra/agent-deepagents/{pyproject.toml,tests/test_rubric.py,tests/test_interrupts.py,tests/test_backends.py,tests/test_public_api.py,tests/test_supervisor.py,tests/test_diagnostics.py,tests/test_upstream_contract.py}`
- `packages/infra/agent-deepagents/examples/{p1_capabilities.py,fake_model.py}`
- 包 `README.md` / `README.en.md` 的 P1 小节

## Commands actually run

| Command | Result |
|---|---|
| `uv run --locked --directory packages/infra/agent-deepagents pytest -q tests/test_rubric.py tests/test_interrupts.py tests/test_backends.py tests/test_public_api.py` | 45 passed |
| `... pytest -q tests/test_supervisor.py tests/test_diagnostics.py tests/test_upstream_contract.py` | 48 passed |
| `deepagents 0.7.32` 内省 | `RubricMiddleware` 暴露 `max_iterations`，工具存在 `_tools`，不是 `tools` |
| 原生 rubric 报告探针 | `RubricMiddleware(tools=[lookup], max_iterations=4)` 产生 `RubricReport(enabled=True, max_iterations=4, model_source='host_middleware', tool_count=0)`，而 `native._tools` 包含 `['lookup']` |
| 作用域探针 | `rubric=` 与 `middleware.workers` 中的原生 `RubricMiddleware` 同时存在被允许 |
| 作用域探针 | 无 `allow_experimental_rubric` 时，`middleware.workers` 中的原生 `RubricMiddleware` 被允许，报告 `enabled=False`，没有 rubric experimental feature |
| 兼容性探针 | 旧的 `SupervisorSpec(..., backend, store)` 位置参数现在把 `backend` 映射为 `allow_experimental_rubric`、`store` 映射为 `rubric`，真实 `backend/store` 为空 |
| 兼容性探针 | 旧的 `ResourceReport(...)` 与 `AssemblyReport(...)` 位置参数仍可用 |
| `git diff a06eb2e..HEAD --stat -- rubric.py interrupts.py backends.py diagnostics.py supervisor.py` | 无输出；P1 实现源码自 merge `a06eb2e` 未变 |

## Findings

| ID | Severity | Location | Issue | Required disposition |
|---|---|---|---|---|
| F1 | blocker | `supervisor.py:282-298,511-524,829-833,943-944`；ADR-0014:51-53,108 | rubric beta gate 与 `rubric=` 排他规则只检查 `spec.middleware.supervisor`。原生 `RubricMiddleware` 放进 `middleware.workers`、`worker_overrides` 或 `SubAgentDefinition.middleware` 时不要求 `allow_experimental_rubric`，也不会被报告为 rubric，还能与 `rubric=` 共存。与 ADR 的无条件“beta 能力必须显式开启”和“不能同时传 `rubric=` 与原生 `RubricMiddleware`”矛盾。 | Gate 所有能承载 upstream beta middleware 的公开作用域；或明确把 ADR 收窄为 supervisor-only，并说明 worker/override/subagent 原生 rubric 由宿主负责且不报告；补 workers/overrides/subagent middleware 测试。 |
| F2 | major | `supervisor.py:315-324`；ADR-0014:55-56；`README.md:611`；`README.en.md:639` | 宿主提供的原生 `RubricMiddleware`，`_rubric_report()` 读取 `native_rubric.tools`；upstream 0.7.32 用 `_tools`，导致有工具时 `tool_count` 仍为 0。`test_rubric.py:142-166` 只断言 `enabled`/`model_source`，未覆盖 `tool_count`。 | 使用受支持的上游访问方式并加 pinned contract test；或明确文档化原生 `tool_count` 不可用/恒为 0，并加测试。 |
| F3 | major | `supervisor.py:99-130`（新字段 `:115-116`）；ADR-0014:125-134 | `allow_experimental_rubric`、`rubric` 插在 `backend` 之前，所有后续位置参数错位。旧的 `SupervisorSpec(..., backend, store)` 会把 `backend` 映射为 `allow_experimental_rubric`、`store` 映射为 `rubric`，真实 backend/store 为空。ADR 说“既有调用方不需要修改”，只警告了 report 类的位置参数。 | 把新字段追加到末尾或设为 keyword-only；否则记录明确的破坏性迁移。增加位置参数兼容测试。 |
| F4 | minor | ADR-0014:125-127,131-132；`diagnostics.py:118-128,176-193` | `ResourceReport`/`AssemblyReport` 新字段追加在末尾，旧位置构造仍可用（已验证）；ADR 说位置参数调用方“需要改用关键字参数”是错误/过时的。真正的位置参数破坏在 `SupervisorSpec`（F3）。 | 修正迁移文字；report 类本身无需改代码。 |
| F5 | minor | `backends.py:27-30`；`test_backends.py:39`；ADR-0014:61-62 | `sandbox` 标签只赋给 `LangSmithSandbox`，其他官方 `SandboxBackendProtocol`/`BaseSandbox` 落入 `custom`。ADR 把 `sandbox` 列为稳定标签，却未定义是否仅限 LangSmith。 | 将通用 sandbox backend 归为 `sandbox`（在 `local_shell` 之后），或文档化 LangSmith-only 映射并加测试。 |
| F6 | minor | `test_rubric.py:80-189`；`test_interrupts.py:113-213`；`test_backends.py:32-45` | 测试对 HITL 端到端和 backend 标签/计数覆盖强，但缺原生 rubric tool count、原生 rubric max-iterations/tools 报告、未配置 rubric 不产生 warning/feature、非法 `on_evaluation`、worker/override 作用域 rubric、通用 sandbox 分类、edit/respond 端到端。 | 补对应契约测试。 |
| F7 | minor (process) | `.specify/delivery/deepagents-p1-continuation-20261115/evidence.md:26-28,62-67,88-94,99-102`；ADR-0014:138-142 | evidence 绑定 merge head `a06eb2e`，完整包门禁在 `035d618` 执行，不是当前 reviewed HEAD `7942509`。P1 实现源码未变且目标测试通过，但 ADR 的“最终 reviewed HEAD 与 evidence 一致”条件未字面满足；evidence 仍写没有独立 Review。 | 将 evidence 重绑到最终 reviewed HEAD，重跑包质量门（含 build/隔离导入），记录本次独立 Review 的范围/结论，再改状态。 |
| F8 | nit | `diagnostics.py:154-161`；ADR-0014:55-56 | 禁用的 `RubricReport` 报告 `model_source="none"`，而 ADR 只列了 `injected:<class>` 和 `host_middleware`。 | 文档化禁用状态的 `none`，或禁用时省略 source 字段。 |

## Dimension results

1. **Requirements/decision consistency — blocked.** rubric 校验、supervisor 作用域 gate、backend 标签/计数、HITL 形状和公共导出大多存在；但 F1–F4 是直接矛盾或过时的兼容性声明。
2. **Code quality and cohesion — pass with minor concern.** `rubric.py`、`interrupts.py`、`backends.py` 小而内聚；HITL helper 无隐藏副作用；report dataclass 为 frozen/slots。`_rubric_report()` 原生分支脆弱且当前错误（F2）；`_native_rubric_middleware()` 对 ADR 的无条件规则过窄（F1）。
3. **Architecture/dependency direction — pass.** 无新 Distribution 或运行时依赖；`pyproject.toml` 仍匹配 ADR-0010；无反向依赖。公共面匹配文档化 seam：`RubricConfiguration`、`RubricReport`、`PermissionReport`、`PendingInterrupt` 和 HITL helper 导出；`backend_kind()`/`permission_report()` 不在 `__all__`。报告不可变且脱敏。唯一架构相邻问题是 F1 的 worker 作用域未报告 rubric。
4. **Correctness/failure behavior — blocked.** HITL 强：malformed payload 返回空 tuple、真实 batched/per-call streaming resume 工作、未知 permission mode 计入 `other`、测试的 backend 标签正确。rubric 在 F1/F2 失败；`SupervisorSpec` 位置构造在 F3 失败。`resume_batched` 本身不校验 count/order，但 upstream `HumanInTheLoopMiddleware` 会报错；包级契约应明确说明。`pending_interrupts` 对非 `Mapping` state 仍抛错，evidence 记录了该有意收窄，签名声明 `Mapping`，属已记录残留风险。
5. **Security/compatibility — blocked.** 报告/helper 未发现 secret/path/prompt 泄漏；但 F1 是 beta gate bypass，F3 是 ADR 未记录的公共 API 兼容性破坏，F4 是错误迁移声明。
6. **Test effectiveness — blocked.** HITL 测试是真正端到端，backend 测试枚举标签和未知 mode；但 rubric 测试缺原生 tool count 和多作用域 gate（F1/F2），也没有位置参数兼容测试（F3）。套件不能证明所有实质 ADR 声明。

**关于缺失的六维 Review**：本次 Review 覆盖了六个维度，因此补上了 continuation 的流程缺口；但它不是一次 passing Review，发现了 blocker/major 矛盾。在 F1–F3 修复并复评前，不能把 evidence 更新为“已通过独立 Review”。

## Required before acceptance

1. 解决 F1：gate/排他规则覆盖全部公开 middleware 作用域，或明确收窄 ADR 并让报告不再暗示覆盖。
2. 解决 F2：原生 `RubricReport.tool_count` 必须准确，或 ADR/README/测试明确说明不可用。
3. 解决 F3：`SupervisorSpec` 保留旧位置顺序，或记录破坏性迁移；增加兼容测试。
4. 修正 F4：删除 `ResourceReport`/`AssemblyReport` 位置参数需改关键字的错误声明。
5. 将 evidence 重绑到最终 reviewed HEAD，重跑完整包质量门，并记录新的独立六维 Review。

`accept with recorded limitations` 不适用：F1–F3 是未解决的矛盾，不只是已知限制。

## Limitations of this review

- 未运行完整包质量门、build、隔离 wheel 安装、governance/docs 或远端 CI；只运行了上述目标测试。
- 未执行真实 rubric grader（provider structured output）、跨进程 HITL/checkpointer 所有权、远程 async subagent、provider profile。
- 未测试通用 `BaseSandbox`/`SandboxBackendProtocol` 分类；代码显示会落到 `custom`。
- 未测试 `pending_interrupts` 的非 `Mapping` state；evidence 记录会抛错。
- 未测试 `resume_batched` 的 decision-count 不匹配；upstream 校验是实际执行点。
- 当前 evidence 仍绑定 `a06eb2e` 和 pre-merge 质量门，不是 `7942509` 的证据。
- 本次未修改任何 tracked 源码或文档。
