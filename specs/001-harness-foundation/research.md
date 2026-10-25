# Harness Foundation Research

## Decision 1: Separate stable rules from changing repository navigation

- **Decision**: Constitution 和 `AGENTS.md` 只保留稳定原则、边界和导航入口；当前目录地图放在
  `docs/architecture/repository-map.md`；包职责放在 `docs/architecture/package-boundaries.md`。
- **Rationale**: 目录和包会变化，完整目录树不应在 README、AGENTS 和治理文件中重复维护。
- **Sources**:
  - [Spec Kit discussion: purpose of `.specify/` directories](https://github.com/github/spec-kit/discussions/2660)
  - [Spec Kit extension and project hook configuration](https://github.com/github/spec-kit/blob/main/docs/reference/extensions.md/)

## Decision 2: Keep Harness artifacts separate by ownership

- **Decision**: `harness/build/`、`harness/context/`、`harness/code_review/`、
  `harness/evidence/` 和 `harness/build-log.md` 各自负责一种记录，不复制 Spec、Plan、Tasks
  或架构地图。
- **Rationale**: 计划、材料性上下文、评审发现和实际证据的生命周期不同；分开后可以区分
  “计划要做什么”和“实际发生了什么”。
- **Sources**:
  - [OpenAI Cookbook: iterating development workflows with Codex](https://github.com/openai/openai-cookbook/blob/main/examples/codex/iterating-development-workflows-with-codex.md)
  - [Superpowers writing skills](https://github.com/obra/superpowers/blob/main/skills/writing-skills/SKILL.md?plain=1)

## Decision 3: Documentation-first before executable automation

- **Decision**: 本 Feature 只建立可审查的 Harness 合同和记录目录，不实现 hook 执行器、CI、
  自动提交、质量工具或外部状态写回。
- **Rationale**: 当前仓库尚未有统一的 Ruff、类型检查、pytest 和 CI 命令；先定义记录边界，
  再在后续 Feature 中把稳定规则转成可执行检查，避免引入没有真实输入输出契约的自动化。
- **Known limitation**: 当前 Harness 的约束主要由文档表达，尚不能声称已经被机器强制执行。
