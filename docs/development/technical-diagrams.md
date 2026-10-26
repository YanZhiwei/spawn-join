# 项目级技术图

仓库内置 [Fireworks Tech Graph](../../.agents/skills/fireworks-tech-graph/SKILL.md)，无需依赖
某位开发者的全局 skill。固定版本、许可证和更新边界见
[来源记录](../../.agents/skills/fireworks-tech-graph/SOURCE.md)。这是文本生成 SVG 技术图，
不是调用图像模型生成照片或概念插画，不需要图像 API Key。

## 使用约定

向 Agent 提出例如：“使用项目级 Fireworks，为该 ADR 绘制模块依赖图，保留 SVG 和 PNG。”
Agent 应读取仓库内的技能及匹配风格参考；默认 Style 1，除非用户要求其他风格。
宿主若同时提供同名全局技能，明确使用本仓库路径，不自动覆盖或更新全局安装。

1. 先核对现有代码或批准方案，标明当前实现/目标设计、箭头语义和事实来源。
2. 仅绘制与本次决策相关的模块，不臆造调用、协议、指标或未来组件。
3. ADR 资源放在同领域 `assets/NNNN/`，保存 SVG、必要的 JSON 输入及 PNG 展示副本。
4. 运行结构检查，再查看实际 PNG 的文字、中文字体、对比度、裁剪和箭头关系。
5. 缺少 renderer 或无法视觉查看时，明确写 blocked / 未检查，不声称“图已验证”。

普通说明也可使用 Mermaid；HTML/GIF 只在用户需要时生成，不默认引入交互展示或动画。
已有明确授权的绘图任务允许本地渲染；安装技能本身不授权发布、外传源码或收费调用。

## 环境隔离

SVG 生成和检查使用 Python >=3.11 标准库。优先使用现有解释器；Windows 的 `python`
可能指向 Store alias，可用 `uv python find` 找到真实路径。以下命令从仓库根执行：

```powershell
$python = (uv python find).Trim()
$cli = Join-Path (Get-Location) '.agents/skills/fireworks-tech-graph/scripts/fireworks.py'
& $python -B $cli version
& $python -B $cli validate architecture path/to/input.json
& $python -B $cli render architecture path/to/input.json path/to/diagram.svg
& $python -B $cli check path/to/diagram.svg
```

将 `path/to/...` 替换为实际路径；不要原样执行占位命令。`-B` 避免在 vendored 工具目录
生成字节码缓存。生成器检查的是布局/结构规则，不证明图与代码事实一致。

PNG 另需 CairoSVG 及可用的 Cairo 系统库，或 `rsvg-convert`。不要为绘图修改四包的
dev group/锁文件，也不创建根级 `.venv`。确有 PNG 任务且缺少依赖时，可在批准的临时
工具目录创建环境后安装 CairoSVG（需要公开包索引网络）：

```powershell
$toolEnv = Join-Path $env:LOCALAPPDATA 'Temp/opencode/spawnjoin-diagram-tools'
# 仅首次且路径不存在时创建；不要覆盖已有环境。
if (-not (Test-Path -LiteralPath $toolEnv)) { uv venv $toolEnv }
$renderPython = Join-Path $toolEnv 'Scripts/python.exe'
uv pip install --python $renderPython cairosvg
& $renderPython -B $cli export-png path/to/diagram.svg path/to/diagram.png --width 1920
```

这是按需安装说明，不表示该工具环境已建立。Windows 若缺 Cairo DLL，应明确报告环境
阻塞，或按技能参考使用已有 Chromium 渲染；不要自动下载浏览器、关闭 sandbox 或安装
系统软件。Node/Chromium、Puppeteer、FFmpeg 和 GIF 全风格验证都不是基本 SVG 的前提。

## 更新与验收

只在明确更新任务中替换上游副本；固定完整 commit、保留 MIT 许可证并更新来源说明。
先在临时目录检查新版，再验证项目入口和上游针对性测试，不因全局版本变化自动更新。
不要修改 vendored 代码来迎合仓库格式规则；若需本地补丁，必须单独记录差异与理由。

本次实际执行记录见 [evidence](../../harness/evidence/adr-and-project-diagram-skill.md)；
ADR 的分类、状态和索引规则见 [决策入口](../decisions/README.md)。
