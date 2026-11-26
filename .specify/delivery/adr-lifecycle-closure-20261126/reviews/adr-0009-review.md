# Independent Review — ADR-0009: 模型元数据与手动同步边界

- **reviewer**: 独立只读子代理（fresh context）
- **repository / HEAD**: `D:\Repos\spawn-join` / `79425090f442506663c0024bde02c62f1f5c7ea6`
- **reviewed_at**: 2026-11-26
- **scope**: ADR-0009 的决策文本与当前实现、测试、依赖边界是否一致，是否可转为 `Accepted`
- **REVIEW_VERDICT**: **blocked**
- **acceptance recommendation**: **keep Proposed**

## Inputs read

- `docs/decisions/llm-provider/0009-model-metadata-and-sync.md`
- `docs/decisions/llm-provider/0008-model-file-and-env-boundary.md`
- `docs/decisions/llm-provider/0006-langchain-first-llm-runtime.md`
- `.specify/delivery/010-model-metadata-sync/{evidence.md,decision-context.md,slices.md}`
- `docs/architecture/package-boundaries.md`
- `packages/core/llm-provider/src/spawn_join_llm_provider/metadata/*` 与 `__init__.py`
- `packages/core/llm-provider/{pyproject.toml,tests/test_metadata.py,tests/test_public_api.py}`
- `packages/infra/llm-provider-langchain/src/.../model_file/{_schema,_catalog,_metadata,_input,_validation,__init__}.py`
- `packages/infra/llm-provider-langchain/{pyproject.toml,tests/test_model_metadata.py,tests/test_schema_validation.py,tests/test_public_api.py}`
- `packages/infra/llm-model-sync/` 全部源码与测试

## Commands actually run

| Command | Result |
|---|---|
| `uv run --locked --directory packages/core/llm-provider pytest -q tests/test_metadata.py tests/test_public_api.py tests/test_package.py` | 34 passed |
| `uv run --locked --directory packages/infra/llm-provider-langchain pytest -q tests/test_model_metadata.py tests/test_schema_validation.py tests/test_public_api.py` | 115 passed |
| `uv run --locked --directory packages/infra/llm-model-sync pytest -q` | 58 passed |
| `uv lock --check --directory`（core/provider、langchain、model-sync） | 三个均 exit 0 |
| `git diff --check` | exit 0 |
| Inline `run_sync(..., apply=False, check=False)`，fixture 输入 | `changed=True`、`written=False`、exit 2；快照未写，但创建了 `cache/cache/models.dev.json` 与 `cache/reports/*.md` |
| Inline `default_cache_dir()` | 返回 `%LOCALAPPDATA%\SpawnJoin\SpawnJoin\Cache`，与 ADR 记录的路径不一致 |
| Inline 非法上游文本/日期/`metadata_source` | 抛出原始 `pydantic.ValidationError`，不是稳定同步/配置错误 |

## Findings

| ID | Severity | Location | Issue | Required disposition |
|---|---|---|---|---|
| F1 | blocker | `packages/infra/llm-model-sync/src/spawn_join_llm_model_sync/sources/models_dev_schema.py:106-129,225-235`；`.../_model_file.py:123-135`；`.../_runner.py:59,77-80`；`.../_cli.py:132-137` | 非法上游文本/日期和非法 `metadata_source` 直接抛 `pydantic.ValidationError`。`run_sync` 只转换 `ConfigurationError`，CLI 只捕获 `ConfigurationError`/`SyncError`，因此可能输出 traceback，而不是文档化的退出码 3（上游）或 1（配置）。 | 将源与 model.yaml 的校验失败转换为 `SourcePayloadError`/`ConfigurationError`，保留 `raise ... from exc`；增加 padded text、非法日期、非法 source ID 的回归测试；验证 CLI 退出码。 |
| F2 | major | `.../_runner.py:165-171,342-358`；ADR-0009:134-135；`packages/infra/llm-model-sync/README.md:77-79` | ADR 说默认只计算差异、“不写文件”；实现始终调用 `_persist_observability`，在既无 `--apply` 也无 `--check` 时仍写缓存和报告。README 已收窄为“不写快照”，与 ADR 不一致。 | 仅在显式模式写缓存/报告，或修改 ADR 说明 dry-run 会写缓存/报告但不写快照；增加枚举 dry-run 副作用的测试。 |
| F3 | major | `.../_cache.py:14-16`；ADR-0009:131-133 | `platformdirs.user_cache_dir("SpawnJoin")` 在 Windows 默认把 appauthor 也设为 `SpawnJoin`，实际路径为 `%LOCALAPPDATA%\SpawnJoin\SpawnJoin\Cache`；ADR 记录的是 `%LOCALAPPDATA%\SpawnJoin\cache\`。 | 使用 `appauthor=False` 或明确记录实际布局；增加路径契约测试（至少断言没有重复 `SpawnJoin`）。 |
| F4 | major | `.../sources/models_dev_schema.py:131-145`；`.../_snapshot.py:184-208`；ADR-0009:94-96,193-199 | ADR 不变量 3 要求“渠道只写差异”；models.dev adapter 把 provider 级 `pricing`、`limits`、`capabilities`、`modalities`、`status` 全量复制到每个渠道覆盖，fixture 中 `fast` 重复了共享 facts。 | 写入渠道覆盖前与共享模型做 diff；或修改 ADR 说明渠道可以重复共享 facts；增加 provider/shared 相同数据的测试。 |
| F5 | major | ADR-0009:107-111,171,183-188,216；`packages/infra/llm-model-sync/pyproject.toml:14-19`；`packages/core/llm-provider/pyproject.toml:14-18`；`docs/architecture/package-boundaries.md:45-49,72-73` | ADR 的依赖声明过时：sync 直接依赖并导入 `spawn-join-common`，但 ADR 说运行时只需要 `spawn-join-llm-provider`、PyYAML 和 `platformdirs`；设计图还写“复用适配包”读取 `model.yaml`，实现使用自己的 `_model_file` 投影且不导入 LangChain adapter。 | 更新 ADR 的依赖列表和设计图，匹配 provider/common/PyYAML/platformdirs 边界。 |
| F6 | minor | ADR-0009:122-126；`packages/infra/llm-provider-langchain/src/.../_catalog.py:32-48`；ADR-0013:148-149 | ADR 说 `ModelSummary` 只新增 `metadata_ref` 和 `metadata`；实现还暴露 `metadata_source` 及 ADR-0013 的渠道字段（`protocol`、`endpoint`、`timeout_seconds`、`max_retries`、`options`）。 | 更新 ADR 引用 ADR-0013 并列出实际 summary 字段，保留默认 `None` 的兼容性说明。 |
| F7 | minor | `packages/infra/llm-provider-langchain/src/.../_schema.py:108-117`；`.../model_file/_metadata.py:43-61`；`.../llm-model-sync/src/.../_model_file.py:107-120` | `metadata_ref` 只检查斜杠和首尾空白，内部空白/控制字符可通过；无 `metadata_ref` 的内联 `metadata` 被静默忽略；共享 fact 缺失时不再检查渠道 `base_model` 是否匹配。 | 在两个 loader 复用 core 的 `<lab>/<model>` 校验；要求 `metadata_ref` 与内联 metadata 同时出现或明确文档化忽略；增加边界测试。 |
| F8 | major | `packages/infra/llm-model-sync/tests/test_runner.py:44-61`；`.../test_package.py:34-35`；`.../llm-provider-langchain/tests/test_model_metadata.py`；`.../llm-model-sync/tests/test_snapshot.py:59-69` | 测试未覆盖 F1–F4 的契约：dry-run 只断言快照不存在，未断言缓存/报告副作用；“不访问网络”断言近似空转；缺 malformed upstream、非法 sync metadata_source、共享 fact 缺失、渠道差异、`os.replace` 失败测试。 | 增加 F1–F4、共享 fact 缺失和原子替换失败的回归测试，并重跑包质量门。 |
| F9 | minor | `.../_merge.py:136-157` | `existing_source_ref`/`validate_channel_source` 是未使用的私有死代码，`ConfigurationError` 仅为后者导入。 | 删除或接入 runner。 |
| F10 | minor | `packages/core/llm-provider/src/.../metadata/types.py:519-522`；`.../llm-model-sync/src/.../_url.py:9-35` | `ModelSource.url` 在快照解析时接受任意非空字符串，手改快照可包含 userinfo 或非 HTTP(S) URL；URL 校验也未拒绝 `code` 等部分凭据类查询名。运行时不会抓取这些 URL，泄漏风险有限，但持久快照边界弱于 ADR 规则。 | 用同一套 HTTP(S)/无 userinfo/无敏感查询规则校验快照 source URL，或明确快照 provenance 属可信输入；增加测试。 |
| F11 | minor | `.../sources/models_dev_schema.py:248-260,273-284,538-546` | adapter 对缺失 input modalities 静默默认为 `text`、丢弃非法日期、把未知 model type 回退为 `CHAT`/`EMBEDDING`，可能发明或误报事实。 | 优先失败或记录显式 unknown 状态；增加缺失/非法 modalities、日期、类型的 fixture 测试。 |
| F12 | nit | ADR-0009:16；`.specify/delivery/010-model-metadata-sync/evidence.md:5-15` | ADR 上下文仍写“当前 `model.yaml` schema v1”，但 v2 已实现；evidence 的 `head_revision` 仍是 `5e8eb7e`，本次 Review 在 `7942509`。 | 将上下文标记为历史，并在接受时更新 evidence/review 映射。 |

## Dimension results

1. **Requirements/decision consistency — blocked.** 核心契约大多已实现，但 F2、F3、F4、F5、F6 是 ADR 文本与当前代码的直接矛盾。
2. **Code quality and cohesion — blocked.** 模块拆分合理，但 sync 的 metadata 投影重复了 adapter 的 YAML/元数据校验，且缺少 adapter 的错误包装（F1/F7）；`_merge.py` 有死代码（F9）。
3. **Architecture/dependency direction — pass, with documentation finding.** 协议包不导入 LangChain/OpenAI/Anthropic；sync 无 LangChain 运行时依赖；没有包反向依赖 sync。ADR 的依赖说明遗漏 `spawn-join-common`（F5），但实际方向正确。
4. **Correctness/failure behavior — blocked.** 确定性输出、v1/v2 兼容、覆盖优先级、多源保留、收缩保护和原子替换逻辑存在；但 F1 是真实未处理异常路径，F2/F3/F4 违反文档化的副作用/存储/差异不变量，F7 仍有边界缺口。
5. **Security/compatibility — pass with minor findings.** sync 只读 metadata 投影，不读 `api_key_env` 的值或进程环境；内置 models.dev 源无认证；URL 校验拒绝 userinfo 和常见凭据查询名；运行时元数据加载不抓取。残留风险为 F1（原始 Pydantic 错误可能回显上游输入）和 F10（快照 URL 信任边界）。
6. **Test effectiveness — blocked.** 目标套件 34/115/58 全部通过，但未覆盖 F1–F4、共享 fact 缺失和原子替换失败；“不访问网络”断言近似空转。

## Required before acceptance

1. 修复 F1，并用回归测试证明 malformed upstream 和非法 `model.yaml` 投影产生文档化退出码而不是 traceback。
2. 解决 F2/F3：要么代码匹配 ADR，要么明确修改 ADR/README 的 dry-run 与缓存路径契约，并加测试。
3. 决定 F4：实现“渠道只写差异”，或修改 ADR 的不变量。
4. 修正 F5/F6 以及过时的跨 ADR 依赖/类型描述。
5. 补 F8 的契约测试，清理 F9，重跑适用的包质量门。
6. 在最终 reviewed HEAD 上重新执行独立六维 Review，再更新 ADR 状态、接受日期、revision history 与决策索引。

## Limitations of this review

- 现有 Delivery evidence 记录于 `5e8eb7e`；当前 HEAD 是 `7942509`，中间包含 Common 提取和 ADR-0013 渠道工作。未在 HEAD 运行完整仓库质量矩阵、docs/governance、隔离 wheel 安装或远端 CI。
- 只运行了上述目标测试加完整 sync 测试目录；未执行真实 models.dev live 同步，也未枚举全部 provider。
- 未测试并发、文件权限或真实 `os.replace` 失败；dry-run、缓存路径、非法 payload、非法 source、渠道重复行为通过临时 fixture 复现。
- `uv run` 在三个包中创建/刷新了被忽略的 `.venv`；没有修改任何 tracked 文件。
