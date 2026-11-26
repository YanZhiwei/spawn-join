Delivery-Evidence: .specify/delivery/adr-0014-p1-fix-20261126/evidence.md

Delivery-Stack: single

## 摘要

- 解决的问题：修复 ADR-0014 Review 发现的 F1-F8，包括 rubric beta gate 绕过、
  原生工具计数错误、`SupervisorSpec` 位置参数兼容性和测试覆盖缺口。
- 合并后的行为或契约：所有公开 middleware 作用域统一受 beta gate/排他规则约束；
  native rubric 报告正确读取工具数；旧位置参数保持兼容；sandbox 分类覆盖 `BaseSandbox`。
- 本次不包含：不执行真实 provider rubric，不将 ADR-0014 自动转为 Accepted。

## 关联问题与变更类型

Part of #<none>；不关闭 Issue。

- [ ] 新功能或新组件
- [x] Bugfix 或契约修正
- [ ] 重构或简化
- [x] 文档或治理
- [ ] 发布准备

## 变更内容

| 位置 | 变更 | 原因 |
|---|---|---|
| `packages/infra/agent-deepagents/src/.../supervisor.py` | gate/排他扫描全部公开 middleware scope；native `_tools` 计数；rubric 字段 keyword-only | 修复 F1-F3 |
| `packages/infra/agent-deepagents/src/.../backends.py` | `BaseSandbox` 统一分类为 `sandbox` | 修复 F5 |
| `packages/infra/agent-deepagents/tests/` | 增加多 scope、工具数、disabled rubric、generic sandbox、位置参数测试 | 修复 F6/F8 |
| `docs/decisions/agent/0014-deepagents-p1-capabilities.md` | 更新契约、迁移说明和复评状态 | 修复 F4/F7 |

## 验证

| 检查 | 实际结果 |
|---|---|
| 包级完整质量门 | 通过：315 tests、构建、隔离安装、pip check、MCP probe |
| 独立六维复评 | pass；F1-F8 无新问题 |
| 目标回归 | 50 passed |

未覆盖：真实 provider structured-output rubric 执行；由远端 CI 验证最终 PR 树。

## 审查身份

- `base_revision`: `be26baeb4148445f1c486531844aa90eadfd3ed4`
- `reviewed_head`: `8880a6d9281e8cfde6a5828aff28e78cbdc17ce9`
- `content_fingerprint`: `sha256:66074f5eee97b06c3b8bd09f1da6dbd13da847b914671224d6077472e62f1e88`
- `requirements_fingerprint`: `sha256:c7a26da49c4e69e84c020fba98c5c8ed3d354db82afd708b6bb1c27db03933b2`
- native Review: `.specify/delivery/adr-0014-p1-fix-20261126/evidence.md`

## Bugfix

- Finding IDs: ADR-0014 F1-F8
- 根因：scope 扫描仅覆盖 supervisor，upstream 工具字段位于 `_tools`，rubric 字段插入旧位置参数序列，测试未覆盖这些边界。
- 回归覆盖：`test_rubric.py`、`test_backends.py`、`test_supervisor.py`，共 50 项目标回归；包全量 315 项通过。

## 回滚

回滚本 PR 的提交即可；不涉及数据迁移或外部服务。

