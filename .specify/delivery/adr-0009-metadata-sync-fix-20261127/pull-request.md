Delivery-Evidence: .specify/delivery/adr-0009-metadata-sync-fix-20261127/evidence.md

Delivery-Stack: single

## 摘要

- 解决的问题：修复 ADR-0009 Review 的 F1-F8，包括原始 Pydantic 错误、dry-run 副作用、
  缓存路径、重复渠道事实、依赖/字段文档、metadata_ref 边界和测试缺口。
- 合并后的行为或契约：同步工具返回稳定错误；默认 dry-run 无文件副作用；渠道只输出差异；
  model.yaml metadata projection 和上游事实严格校验。
- 本次不包含：不执行 live models.dev，不自动将 ADR-0009 转为 Accepted。

## 关联问题与变更类型

Part of #<none>；不关闭 Issue。

- [ ] 新功能或新组件
- [x] Bugfix 或契约修正
- [x] 文档或治理
- [ ] 发布准备

## 变更内容

| 位置 | 变更 | 原因 |
|---|---|---|
| `llm-model-sync/_runner.py` | 转换 ValidationError；默认 dry-run 跳过 observability 写入 | F1/F2 |
| `llm-model-sync/_cache.py` | 修正 `appauthor=False` | F3 |
| `llm-model-sync/_merge.py` | 渠道覆盖只保留差异；清理死代码 | F4/F8 |
| `llm-model-sync/_model_file.py` | 严格 metadata_ref/source ID/inline metadata 校验 | F7 |
| `models_dev_schema.py` | 非法日期/类型/模态不再静默发明事实 | residual F11 |
| ADR-0009 / tests | 更新依赖/字段契约，补充回归覆盖 | F5/F6/F8 |

## 验证

| 检查 | 实际结果 |
|---|---|
| 包级质量门 | pass |
| 目标测试 | 62 passed |
| Pyright | 0 errors |
| Ruff | pass |

未执行：live models.dev、远端 CI（由本 PR 执行）。

## 审查身份

- `base_revision`: `b867b68c8aaa8f93bc02afe838f9ce2a248dd040`
- `reviewed_head`: `1e4eea43310a276386fe76038c8aa4b6e5a368a3`
- `content_fingerprint`: `sha256:04e60e728e594bffab1dc39f9a73b59fa32b0388bebe7f8295a80c01827f5f96`
- `requirements_fingerprint`: `sha256:fb5c34e25ac18c73ca654c172f249f79dcd63a9e670bf7a073f4fd4384a1fce8`
- native Review: `.specify/delivery/adr-lifecycle-closure-20261126/reviews/adr-0009-review.md`

## Bugfix

- Finding IDs: ADR-0009 F1-F8
- 根因：错误边界、缓存副作用和 metadata projection 的校验规则未形成一致契约。
- 回归覆盖：`llm-model-sync` 全量 62 tests，含 CLI exit code、dry-run、渠道差异和 inline metadata。

## 回滚

回滚本 PR 的提交即可；不涉及数据迁移或外部服务。
