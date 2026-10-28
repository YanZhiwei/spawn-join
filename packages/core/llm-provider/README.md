# spawn-join-llm-provider

与框架无关的 LLM 协议和领域抽象。

## 当前状态

`0.1.0` 骨架。`abstractions` 只有命名空间，尚未定义 Provider 协议或请求/响应类型。
协议确定前不要引入 LangChain 或具体 Provider SDK。

## 边界

- 只依赖 `spawn-join-core`。
- 不依赖 LangChain、OpenAI、Azure 或其他 Provider SDK。
- 框架适配和 Provider 实现属于
  [`spawn-join-llm-provider-langchain`](../../infra/llm-provider-langchain/)。

## 使用与验证

```python
import spawn_join_llm_provider
```

```powershell
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider
```

许可证见 [LICENSE](LICENSE)。
