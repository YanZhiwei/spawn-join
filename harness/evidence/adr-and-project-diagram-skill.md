# ADR and Project Diagram Skill Evidence

## Scope and baseline

- Route: Lightweight；文档治理与固定版本开发技能的本地安装，不新增领域行为或公共 API。
- Feature / task: 不适用；不为本次范围创建空 Spec / Plan / Tasks。
- Working directory: `D:\Repos\Github\spawn-join`。
- Base / current HEAD: `bd497d72e928f596e79cdbe5b1466eba4c75ec39`；未提交、未推送。
- Recorded: 2026-10-26。
- 起始工作树已有质量门、包测试、锁和文档改动；不将其算成本次新增实现。
- 修改前保存 94 个已有可见文件的 SHA-256、Git 状态及 HEAD 至批准的临时目录，
  用于确认 Specs、包文件、锁和其他非目标内容保持不变。

## Changed paths

- `.agents/skills/fireworks-tech-graph/`：139 个未修改的上游文件及本地 `SOURCE.md`。
- `docs/decisions/README.md`、`template.md`、`engineering/0001-delivery-and-durable-design.md`：
  唯一 ADR 根、按领域分类、全局编号、状态、引用和首条治理决策。
- `docs/development/technical-diagrams.md`：项目用法、来源和渲染环境隔离。
- `AGENTS.md`、`README.md`、`docs/architecture/repository-map.md`、`harness/README.md`：
  增量更新治理规则与导航，不覆盖已有质量门说明。
- 本 evidence，以及 `harness/build-log.md` 的本次追加记录。
- `.gitignore`：用户后续明确要求加入 `/specs/`；不删除、不取消已有跟踪。
- `docs/development/quality-gates.md`、`harness/build/phase-01-python-quality-gates.md`、
  `harness/context/phase-01-python-quality-gates-context.md`：将指向被忽略 Feature 的本地
  Markdown 链接改为注明本地性质的路径，保留其他内容与共享证据链接。

不修改现有 Specs、Constitution、质量脚本、四包源码/测试/元数据/锁、
CI 或 Delivery 配置。文档规则是人工约定，不宣称已安装完整 ADR 自动化。

## Source and installation

- Source: <https://github.com/yizhiyanhua-ai/fireworks-tech-graph>
- Commit: `1ca1ff9cfcb67893a43d32b9ef3a1b782c44a46f`，版本 `1.2.0`，MIT。
- 从固定提交 archive 中安装 `skills/fireworks-tech-graph/`，139 文件，8,882,626 字节。
- 安装时逐文件比较源与本地 SHA-256；服务器重启后仅补齐 12 个缺失文件，已有文件
  一致时保留，没有覆盖不匹配内容。上游完整副本保留许可证、引用、样例与测试。
- `uv python find` 定位真实 Python 3.13.5；`py -3.13 --version` 尝试失败，launcher
  未发现该 runtime，不安装新 Python。全局 `python` 是 Store alias，未修改。
- `fireworks.py version` 使用真实解释器执行，退出 0，报告本地版本 `1.2.0`。

## Verification

Environment: Windows，uv 管理的 CPython 3.13.5、Node 22.17.0；未安装新工具依赖。
PowerShell 中 `$python = (uv python find).Trim()`，`$cli` 为项目内
`.agents/skills/fireworks-tech-graph/scripts/fireworks.py`；设置
`$env:PYTHONDONTWRITEBYTECODE = '1'` 避免子进程生成缓存。

| Command / check | Exit | Observed result |
|---|---|---|
| `& $python -B $cli version` | 0 | 本地 1.2.0，12 个风格 |
| `& $python -B -m unittest discover -s .agents/skills/fireworks-tech-graph/tests -p test_diagram_ir.py -v` | 0 | 6 tests passed |
| `& $python -B -m unittest discover -s .agents/skills/fireworks-tech-graph/tests -p test_validate_svg.py -v` | 0 | 20 tests passed |
| `& $python -B -m unittest discover -s .agents/skills/fireworks-tech-graph/tests -p test_cli.py -v` | 1 | 9 tests，7 passed / 2 failed；不能宣称全测试通过 |
| `& $python -B $cli doctor` | 1 | SVG/HTML 可用；缺 CairoSVG/rsvg-convert，PNG blocked；缺 Puppeteer，GIF blocked |
| `codegraph sync` | 0 | Already up to date；不代替测试 |
| 139 个导入文件对照固定源逐文件 SHA-256 | 0 | 全部相同，无本地上游补丁 |
| Git-visible 临时副本中执行 `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | 初次 27 文件、66 本地目标；最终重查 27 文件、67 本地目标。不含被忽略的 002 Feature，链接仍有效 |

上游 CLI 的两个 Windows 失败分别是：

- `test_examples_and_validate_are_machine_readable`：实现返回 Windows `fixtures\...`，
  测试期待 POSIX `fixtures/...`；不影响直接传入 fixture 验证和渲染。
- `test_checked_in_interactive_example_matches_current_cli_output`：生成 HTML 为 CRLF，
  checked-in 示例为 LF，逐字节断言失败；不是内容已经完成视觉验收的证明。

不为了取得绿色结果修改上游代码或测试。上述已执行的 35 个测试共 33 通过、2 失败；
完整上游套件、PNG/GIF 和浏览器视觉检查未执行。

另外使用 `fixtures/mem0-style1.json` 完成真实 CLI 冒烟验证：

```powershell
$inputPath = '.agents/skills/fireworks-tech-graph/fixtures/mem0-style1.json'
# $output 为批准临时目录中本次创建的唯一目录。
& $python -B $cli validate memory $inputPath
& $python -B $cli render memory $inputPath "$output/diagram.svg" --report "$output/layout.json"
& $python -B $cli check "$output/diagram.svg"
& $python -B $cli export-html "$output/diagram.svg" "$output/diagram.html"
```

四个命令均退出 0；9 节点、8 边，XML/marker/collision/geometry/composition 检查全部通过，
报告文字完整且没有截断。产物只在临时目录，不写入 ADR，不表示架构事实或视觉验收。
首次误将该 memory fixture 以 architecture mode 验证，退出 1，报告 mode 冲突；
改用 fixture 自身的 memory mode 后通过，没有改输入或绕过校验。

Git 忽略验证：`git check-ignore -v --no-index -- specs/002-python-quality-gates/spec.md
specs/future-feature/spec.md` 退出 0，两者命中 `.gitignore` 的 `/specs/`。
`git ls-files -- specs` 仍列出 001 的 6 个已跟踪文件；未调用取消跟踪命令。
忽略工件仍参与本机质量检查，但本次另外验证了没有它们的 Git-visible 文档副本。

最终检查（工作目录同上，2026-10-26）：

- `pwsh -NoProfile -File scripts/quality.ps1 -Check docs`：退出 0，33 个 Markdown 文件、
  76 个本地目标；保留既有 LF/CRLF 提示，不将其当成失败或自动改写文件。
- `git diff --check`、`git diff --cached --check`：均退出 0。另用补充检查覆盖本次
  未跟踪文档及技能入口，避免只检查 tracked diff 而漏过新文件。
- `& $python -B C:\Users\YanZh\AppData\Local\Temp\opencode\verify-spawnjoin-adr-skill.py`：
  比较修改前 94 文件的哈希，只允许本次列明的 9 个规则/导航文件变化；其他 85 文件
  （含全部既有 Specs、包文件和锁）保持不变。追加前 build log 的原始前缀逐字节不变。
  该补充检查首次发现本地 `SOURCE.md` 链接多了一层 `../`，已修正后复核通过；未改上游文件。
- 技能目录没有生成 `.venv`、`node_modules`、`__pycache__` 或测试产物；冒烟文件只在
  批准临时目录。没有重跑四包格式/类型/测试/构建：业务源码与依赖没有本次变化。
- `codegraph affected .agents/skills/fireworks-tech-graph/scripts/fireworks.py`：退出 0，
  没有找到受影响测试；不能据此跳过测试，实际针对性测试结果已单独列出。
- `git status --short --branch`、`git rev-parse HEAD`：仍在 `main`、HEAD 未变，工作树
  包含原有与本次未提交改动；001 的既有修改仍可见，002 因忽略规则不再出现在普通状态中。

## Standards review and limitations

ADR 的分类树只表达归属，依赖与替代使用显式链接；不预建缓存等不存在的领域。
Accepted 表示本次用户授权的治理选择，不代表业务实现、测试或发布已完成。
上游工具脚本是隔离的第三方开发工具例外；不新增 Distribution，不修改业务依赖，
不将其套入四包格式重写，不额外安装模型 API 或另一个代码索引器。

SVG 结构检查不证明图片内容或视觉正确。PNG 需 renderer 和系统库；GIF、浏览器下载、
收费 API、外部发布均不属于本次安装授权。完整 Delivery、远端 CI 与分支保护未验证。
任何新提交、范围或源版本变化均须重新确认本 evidence。

Standards Review：单一 ADR 主源、按需分类、已有契约/证据职责、第三方工具隔离和
权限边界符合本次蓝图；无 Python 公共 API、业务数据流、运行时依赖或密钥变化。
完整 Delivery/hook/Ralph 仍未配置，不能将本次局部验证表述为完整 Delivery gate。

- `STANDARDS_VERDICT: pass`（人工范围与职责审查）。
- `QUALITY_VERDICT: fail`（上游 Windows CLI 有两项实际失败；文档/SVG 局部检查另列通过，
  PNG/GIF 环境 blocked，不宣称全量质量门通过）。
