# spawn-join-observability

SpawnJoin 应用的日志、追踪和指标基础。

## 当前状态

`0.1.0` 骨架。包目前只提供导入入口；日志、追踪、指标和导出器尚未实现，也没有
外部服务依赖。

## 边界

- 只依赖 `spawn-join-core`。
- 不反向成为 Core 或其他领域包的依赖。
- 外部导出器（OTLP、日志后端等）属于适配层；加入前需要明确副作用所有权和失败语义。

## 使用与验证

```python
import spawn_join_observability
```

```powershell
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-observability
```

许可证见 [LICENSE](LICENSE)。
