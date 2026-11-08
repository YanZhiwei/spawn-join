# feat(llm): 三协议 YAML 思考强度默认值

## 摘要

为 Chat Completions、Responses 与 Anthropic Messages 的文件配置增加
`low`/`medium`/`high` 思考强度默认值，并支持 Anthropic 显式关闭。

- `ChatCompletionsOptions` 与 `AnthropicMessagesOptions` 末尾新增 `reasoning_effort`；
  Responses 保留既有字段。
- 适配包通过私有 `_input.py` 严格解析，并映射到原生构造（`reasoning_effort` /
  `effort` 别名）。
- 请求分别携带 `reasoning_effort`（Chat Completions）、`reasoning.effort`（Responses）
  与 `output_config.effort`（Anthropic），不产生多余键。
- `AnthropicThinkingDisabled` 是新的 frozen/slotted 公共类型；`thinking.mode: disabled`
  映射为 `{"type": "disabled"}`，并拒绝 `budget_tokens`（包括显式 null）。
- 省略字段与 Python `None` 表示未指定；显式 YAML `null` 被拒绝。
- 逐次调用覆盖不会修改实例默认值。
- `langchain-core` 与 `langchain-anthropic` 下限提升到 `>=1.5.0,<2.0`；下游锁只更新
  本地包元数据。
- 两个包的中英文 README 说明新字段、null 语义、映射、下限和限制。

## 交付形态

栈式切片，每层是独立评审边界：

1. S1 `a117944` — OpenAI 双协议默认值。
2. S2 `f840cc6` — Anthropic 强度、依赖下限与最低版本环境。
3. S3 `25ef100` — 显式 disabled 与模式优先级。

前置治理记录清理为 `24abe2f`。

## 验证

- 全仓 `scripts/quality.ps1`：684 tests（六个包），Pyright 0，构建与隔离安装，
  docs 138/393，governance 0 error（1 条历史 warning），static 0。
- 最低依赖环境：Python 3.11.13 + `langchain-core==1.5.0`、
  `langchain-anthropic==1.5.0`、`langchain-openai==1.0.0`；171 个针对性测试通过，
  `pip check` 干净。
- 任务级与最终 outgoing 的 Quality、Standards 和独立 Review 全部通过。

## 限制

- 仅 Windows 本地验证；未运行远端 CI。
- 无真实 Provider 请求；不声称服务端支持 disabled 或 disabled+effort。
- 最低版本环境只验证声明下限，不覆盖所有中间版本。
- `specs/` 与运行规划/runtime 文件按 artifact policy 保留本地；本 run 的
  `evidence.md` 是持久记录。

## 发布

未执行 push、PR、merge 或发布。按已批准切片顺序分别授权发布；目标分支与标题遵循
切片计划。
