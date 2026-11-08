## 摘要

- 解决的问题：`spawn-join-llm-provider` 已有 `Channel` 契约，但没有真实 Provider transport；`ChannelConfig`/`ModelInfo` 也无法接入现有 LangChain 模型工厂。
- 合并后的行为：新增 `spawn-join-llm-channel`，实现 OpenAI-compatible 与 Anthropic 的 `ping()`/`list_models()`；适配包提供 `ChatModelConfig.from_channel()` 和只读目录检视，形成 `ChannelConfig -> ping/list_models -> ModelInfo -> ChatModelConfig -> create_chat_model` 的库级闭环。
- 本次不包含：CLI（用户在设计门明确移除）、pool/路由/健康选路、`channels.yaml`、热重载、密钥管理服务、Agent 装配改动。

## 类型

- [x] 新功能或架构变更
- [ ] Bugfix 或回归
- [ ] 文档或治理
- [ ] 质量基线或工程化
- [x] 架构/设计决策（ADR-0013 Proposed）

## 修改点

| 位置 | 变更 | 原因 |
| --- | --- | --- |
| `packages/infra/llm-channel/` | 新增 Distribution：OpenAI/Anthropic channel、凭据解析、SDK 错误映射、模型页校验、测试、中英文 README | 补齐真实 channel transport，且不让 channel 使用者依赖 LangChain |
| `packages/core/llm-provider/src/.../channels.py` | 新增 `ChannelStatus.UNSUPPORTED` | 表达“渠道可达但不提供模型列表” |
| `packages/core/llm-provider/src/.../errors.py` | 新增 `ChannelAuthenticationError` | `list_models()` 的 401/403 需要稳定语义 |
| `packages/infra/llm-provider-langchain/src/.../config.py` | 新增 `ChatModelConfig.from_channel()` | 无网络桥接 channel 配置 |
| `packages/infra/llm-provider-langchain/src/.../model_file/_catalog.py` | `ModelSummary` 增字段、`from_model_info()`、`ModelCatalog.get/names/len/contains` | 支持只读目录检视和 `ModelInfo` 桥接 |
| `scripts/quality.ps1`、CI、quality profile | 加入第 7 个 Distribution | 保持质量门和 CI matrix 完整 |
| `AGENTS.md`、README、架构地图、ADR 索引 | 七包边界、channel 职责和 ADR-0013 | 保持治理文档一致 |

## 验证

| 检查范围 | 实际结果 | 证据 |
| --- | --- | --- |
| 协议包 | 187 passed | `uv run --locked --project packages/core/llm-provider pytest packages/core/llm-provider/tests -q` |
| 适配包 | 309 passed | `uv run --locked --project packages/infra/llm-provider-langchain pytest packages/infra/llm-provider-langchain/tests -q` |
| channel 包 | 99 passed, 2 skipped | `uv run --locked --project packages/infra/llm-channel pytest packages/infra/llm-channel/tests -q` |
| 包级质量门 | 三个包全部 exit 0 | `pwsh -NoProfile -File scripts/quality.ps1 -Package <name>` |
| 全仓库质量门 | exit 0 | `pwsh -NoProfile -File scripts/quality.ps1` |
| docs / governance | docs passed；governance 0 errors / 1 historical warning | `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` / `-Check governance` |
| diff hygiene | exit 0 | `git diff --check` |

- 未执行：真实 Provider live tests（无凭据，默认 skip）；远程 CI 结果由本 PR 的 Actions 运行确认。
- 未把 live skip 写成通过。

## 影响

| 维度 | 影响 | 证据 |
| --- | --- | --- |
| 公共 API | 协议包新增 `UNSUPPORTED`、`ChannelAuthenticationError`；适配包新增 classmethod/字段/目录方法；`create_chat_model` 不变 | 协议/适配 public API 测试；README |
| 持久化/迁移 | 无数据迁移；不新增 `channels.yaml`；`model.yaml` 不变 | ADR-0013；diff |
| 安全/权限 | 密钥只通过显式参数/环境变量解析；公开错误固定文案；测试覆盖 malformed 响应和 sentinel 泄漏 | channel 测试；独立 review |
| 性能/资源 | `ping` 单次 `/models` 请求；`aclose()` 关闭客户端；无隐藏重试 | channel 实现与 README |
| 依赖/发布 | 新增独立 Distribution、锁文件、质量 Profile、CI matrix；未发布 | `pyproject.toml`、`uv.lock`、CI |

## 关联决策

- ADR-0013: `docs/decisions/llm-provider/0013-channel-runtime-and-credentials.md`（Proposed）
- 该 ADR 补齐 ADR-0006 延后的真实 channel transport；不改变 LangChain-first 推理边界。

## AI Code Review 发现与修复

| 轮次 | 问题 | 严重度 | 处理 |
| --- | --- | --- | --- |
| 1 | malformed 200 响应可能误报 `OK` 或泄漏 `TypeError`/`AttributeError` | BLOCKER | 新增 `_page.py` 校验；`INVALID_RESPONSE`/`ChannelResponseError`；真实 SDK `MockTransport` 回归 |
| 1 | Anthropic 空 cursor id 会重复同页 | MINOR | `next_cursor()` 拒绝空/空白 `last_id`，并补测试 |
| 1 | README 仍称 `ChatModelConfig` 不依赖 `ChannelConfig`，且把协议类型归到 channel 包 | NIT | 改为“不存储 `ChannelConfig`，可选 `from_channel()` 转换”，归属改为协议包 |
| 2 | 复审 | — | `NO_BLOCKER` |

## 评审重点

- 阅读顺序：`docs/decisions/llm-provider/0012...` → `packages/infra/llm-channel/src/` → `packages/infra/llm-provider-langchain/src/.../config.py` 与 `_catalog.py` → tests。
- 关键行为边界：channel 包不得依赖 LangChain；协议包不得引入 SDK；适配包不包装 `BaseChatModel`。
- 需要人工确认：OpenAI-compatible/Anthropic 真实 endpoint 的行为、Anthropic `base_url` 是否按文档使用源站而非 `/v1`、以及是否接受 ADR-0013 的 Proposed 基线。

## 检查清单

- [x] 代码与测试已提交到分支
- [x] 全仓库质量门通过
- [x] 文档/治理检查通过
- [x] 独立 review 无 blocker
- [ ] 真实 Provider live 验证（无凭据，未执行）
- [ ] 人工 Code Review
- [ ] 合并/发布授权
