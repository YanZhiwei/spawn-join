## 摘要

为 LangChain 适配包增加显式 `model.yaml` 模型目录：文件保存协议、endpoint、模型标识、超时/重试、协议选项和展示名；API key 只通过 `api_key_env` 引用，从进程环境或显式传入的 `.env` 解析。新增 5 个公共名字，复用现有 `ChatModelConfig`、协议选项和 `create_chat_model`。

## 动机

当前模型配置只能写在代码里，切换模型/端点/选项需要改代码；密钥读取方式分散；模型列表没有展示名。该变更把模型元数据与密钥分离，并提供可校验、可测试的文件边界。

## Slice / Stack

- Slice 与目标：S1 解析边界、S2 US1 创建模型、S3 US2 清单/展示名、S4 US3 `.env`、S5 文档与验证
- Base 分支：`main`
- 依赖：无外部 Feature 依赖；ADR-0008 依赖 ADR-0006
- 合并顺序 / 方式：**本 PR 为便于评审的单 Feature PR，未按 5 个 stacked PR 拆分**；合并方式待维护者评审后决定
- 不包含在本层：channel 配置、多文件合并、自动发现、热重载、插值、Provider 路由/池
- 回滚：revert 本 PR；文件格式与公共 API 均为纯增量

## 变更类型

- [x] 新功能
- [ ] Bugfix
- [ ] 重构或简化
- [x] 文档或治理
- [ ] 发布准备

## 当前设计（变更前）

- 入口或组件：`ChatModelConfig` + `create_chat_model`
- 归属与依赖方向：协议包框架无关；适配包依赖协议包与 LangChain
- 当前约束与不变量：密钥只在工厂调用时传入并包 `SecretStr`；公共面只有 2 个名字

## 变更内容

| 位置 | 变更 | 原因 |
| --- | --- | --- |
| `packages/infra/llm-provider-langchain/src/.../model_file.py` | 新增 YAML/`.env` 加载、严格校验、目录与展示名 | 提供文件配置边界 |
| `.../__init__.py` | 导出 `ModelCatalog`、`ModelSummary`、`load_model_catalog` | 公共契约 |
| `.../tests/test_model_file.py` | 新增 75 个解析/目录/密钥测试 | 行为与失败路径覆盖 |
| `.../pyproject.toml`、`uv.lock` | 新增 PyYAML、python-dotenv | 显式解析依赖 |
| `README.md`（两个包） | 用法、优先级、错误、安全、边界 | 可复现文档 |
| `docs/decisions/llm-provider/0008-...md` | ADR（Proposed） | 长期决策记录 |
| `.gitignore` | 忽略 `/.env` | 防止密钥误提交 |

## 影响

| 维度 | 影响 | 证据 |
| --- | --- | --- |
| 公共 API、命令、配置 | 适配包公共面由 2 个名字扩为 5 个；新增 `model.yaml` schema v1 | `contracts/public-api.md`、`test_public_api.py` |
| 持久化或迁移 | 无数据库；新增本地配置文件格式 | 无迁移 |
| 兼容性与升级路径 | 现有 `ChatModelConfig`/`create_chat_model` 行为不变；纯增量 | 旧测试全通过 |
| 安全与权限 | key 仅以变量名入库；`.env` 显式、`interpolate=False`；不写 `os.environ`；错误/repr 脱敏 | `test_model_file.py` 安全用例 |
| 性能与资源 | 加载时两次 YAML 解析（compose + safe_load）；创建模型无网络 | 本地 quickstart |
| 依赖与供应链 | PyYAML 6.0.3（MIT）、python-dotenv 1.2.4（BSD-3-Clause），仅适配包 | `research.md`、`uv.lock` |

## 架构决策

- [x] 已链接相关 ADR，并与 HEAD 的实现一致：ADR-0008（Proposed）扩展 ADR-0006。
- [ ] 没有架构决策变化。

## 行为与验收

| 需求 | 结果 | 证据 |
| --- | --- | --- |
| FR-001–FR-008：加载、schema、条目、协议、选项、thinking、default/名字解析 | 通过 | `test_model_file.py` |
| FR-009–FR-012、FR-018：密钥引用、优先级、空值、无插值、错误脱敏 | 通过 | `.env` 与安全测试 |
| FR-013–FR-014：清单、顺序、展示名回退/校验 | 通过 | `ModelSummary` 测试 |
| FR-015–FR-017：重复键、安全解析、复用选项契约 | 通过 | 解析边界与工厂复用测试 |
| SC-001–SC-006 | 通过 | 目标包 110 tests；quickstart |

## 验证

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| 构建 | pass | 目标包隔离构建/安装/导入 |
| 测试 | pass | `pytest` 110 passed（目标包），75 个目标测试 |
| 规范与 Spec 审查 | pass | 最终独立评审（fresh-context） |
| ADR 一致性 | pass（ADR-0008 Proposed，等待评审） | ADR-0006 日期注释 |
| 变更范围的简化检查 | pass | 复用现有配置/选项/工厂；无新 Distribution |

```powershell
pwsh -NoProfile -File scripts/quality.ps1
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider-langchain
pwsh -NoProfile -File scripts/quality.ps1 -Check docs
pwsh -NoProfile -File scripts/quality.ps1 -Check governance
```

## 文档

- [x] 源文档已更新（两个 README、包边界、ADR 索引）。
- [ ] 生成文档已同步（无生成文档）。
- [ ] 不需要文档变更。

## 回滚

revert 本 PR 即可；文件格式和公共 API 为纯增量，现有代码内配置不受影响。

## AI 辅助

- [ ] 未使用 AI 辅助。
- [x] 使用了 AI 辅助，且每一行变更都已审阅和验证（任务级与最终独立评审）。

## 评审说明

- 本 PR 将 5 个已计划的切片合并为一个评审单元；未声称 stacked 交付已完成，合并方式待维护者决定。
- S2 实际新增 1,031 行（源码 493 行），超过 400 行切片预算，已在 `slices.md` 记录例外。
- ADR-0008 保持 `Proposed`，等待本次 Code Review 后再决定是否 Accepted。
- 远端 CI 尚未运行；创建 PR 后监听并修复失败。

## 检查清单

- [x] 验收条件已覆盖。
- [x] 阻断性评审问题已解决。
- [x] ADR 与 HEAD 的实现一致（ADR-0008 Proposed）。
- [x] 已附相关验证证据。
- [x] 外发 diff 与已审阅范围一致。
