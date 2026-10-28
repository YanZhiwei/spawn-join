# spawn-join-llm-provider-langchain

LangChain 适配层和 Provider 实现。

## 当前状态

`0.1.0` 骨架。`providers.azure_openai` 与 `providers.deepseek` 目前只有包命名空间，
没有客户端、请求转换或错误映射实现。

## 边界

- 依赖 `spawn-join-llm-provider` 和 `langchain-core`。
- LangChain 类型、异常和 SDK 对象只留在本包，不泄漏回协议包或 Core。
- Provider 的请求、响应和错误转换由本包拥有；新增 Provider 前先确认是否需要独立版本或依赖。

## 使用与验证

```python
import spawn_join_llm_provider_langchain
```

```powershell
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider-langchain
```

许可证见 [LICENSE](LICENSE)。
