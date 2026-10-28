# spawn-join-core

SpawnJoin 生态共享的稳定契约与基础原语。

## 当前状态

`0.1.0` 骨架。`config`、`exceptions`、`protocols` 和 `types` 目前只有模块契约，
尚无实现或公开导出。只有出现至少两个组件的稳定复用时，才向 Core 添加能力。

## 边界

- 不依赖其他 SpawnJoin 包。
- 不引入第三方运行时依赖。
- 不存放单领域辅助函数、Provider 适配或副作用。

## 使用与验证

```python
import spawn_join_core
```

```powershell
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-core
```

许可证见 [LICENSE](LICENSE)。
