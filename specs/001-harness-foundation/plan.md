# Implementation Plan: Harness Foundation

**Branch**: `main` (working tree feature; no branch created) | **Date**: 2026-10-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-harness-foundation/spec.md`

## Summary

建立一个文档优先、职责清晰、可逐步自动化的 Harness 基础层。Harness 只负责阶段计划、
阶段上下文、评审记录、验证证据和实际执行日志；Constitution、AGENTS、Spec、Plan、Tasks
和各包的 `pyproject.toml` 继续保留各自的权威职责。第一阶段不引入 Python 代码、依赖、
CI 或 hook 执行器。

## Technical Context

**Language/Version**: Markdown 文档；仓库源码运行时为 Python `>=3.11`

**Primary Dependencies**: 已初始化的 Spec Kit、Git、现有 `uv` 构建命令；本 Feature 不新增依赖

**Storage**: Git 版本控制下的 Markdown 文件；`.specify/feature.json` 仅作为本机活动 Feature 指针

**Testing**: 本地 Markdown 相对链接检查、`git diff --check`、职责重复检查；不需要 Python 单元测试

**Target Platform**: Windows 开发环境；文档中的路径使用仓库相对路径，命令优先提供 PowerShell 可复现形式

**Project Type**: Python monorepo 的交付治理和开发 Harness

**Performance Goals**: 文档导航和检查应在本地秒级完成；本 Feature 不引入运行时性能目标

**Constraints**: 只修改治理文档和 Harness 文档；不修改应用源码、包清单、依赖、CI、分支、提交、推送或外部系统

**Scale/Scope**: 当前四个独立 Distribution；面向单个仓库、单个 Feature 和单个阶段的可追踪记录

## Constitution Check

*GATE: Must pass before implementation.*

- **Readability First**: PASS — 文件按职责拆分，使用中文说明和稳定的英文路径/标识符，避免把全部规则堆进一个文件。
- **Cohesive Object-Oriented Design**: N/A — 本 Feature 不新增运行时代码或对象模型。
- **DRY with Clear Ownership**: PASS — Spec/Plan/Tasks、架构地图、AGENTS 和 Harness 各自拥有明确事实，不复制完整目录树。
- **Testable Contracts and Precise Types**: PASS — 文档工件有明确验收条件，验证范围为链接、路径和文本一致性。
- **Simplicity, Incremental Delivery, and Evidence**: PASS — 只实现最小 Harness 骨架，不提前实现 hook、CI 或质量工具；记录实际验证命令和未执行项。

## Research Summary

研究结论记录在 [research.md](research.md)：成熟做法是把稳定规则、功能设计、阶段计划、
上下文和实际证据分开，并用链接建立关系，而不是让目录树成为多个文档的重复真相。

## Architecture and Ownership

```text
Constitution
  -> 项目级不可妥协原则

AGENTS.md
  -> Agent 工作约定、稳定边界和导航入口

specs/001-harness-foundation/
  -> 本 Feature 的 Spec、Plan、Tasks、研究和验证说明

harness/
  -> 阶段计划、上下文、评审、证据和实际执行日志

docs/architecture/
  -> 当前仓库地图和包边界导航
```

权威边界：

- `spec.md` 拥有用户场景、需求、边界和成功标准；
- `plan.md` 拥有本 Feature 的技术布局、设计决策和验证方案；
- `tasks.md` 拥有唯一执行队列；
- `harness/build/` 拥有一个阶段的批准范围和执行计划，不代替 `plan.md`；
- `harness/context/` 拥有材料性发现、决策和未解决事项；
- `harness/build-log.md` 拥有实际进度和观察到的验证结果；
- `harness/code_review/` 拥有详细评审发现和收口状态；
- `harness/evidence/` 拥有与真实 base/head 和 changed paths 绑定的验证材料；
- `docs/architecture/` 拥有仓库导航和包边界，不拥有 Feature 状态或执行证据。

## Implementation Phases

1. **Harness contract**: 创建 Harness 总说明和各子目录职责说明。
2. **Initial records**: 创建初始 build log，并明确当前 Feature 的证据边界和限制。
3. **Repository integration**: 更新 `repository-map.md`、README 和 AGENTS 的导航入口。
4. **Validation**: 检查链接、尾随空格、重复完整目录树和变更范围。

## Project Structure

### Documentation (this feature)

```text
specs/001-harness-foundation/
├── spec.md
├── plan.md
├── research.md
├── quickstart.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Harness Files

```text
harness/
├── README.md
├── build/
│   └── README.md
├── context/
│   └── README.md
├── code_review/
│   └── README.md
├── evidence/
│   └── README.md
└── build-log.md
```

### Repository Documentation Updates

```text
AGENTS.md
README.md
docs/architecture/
├── repository-map.md
└── package-boundaries.md
```

## Complexity Tracking

本 Feature 没有 Constitution 违规，也没有引入额外复杂度。没有创建机器可读的第二份仓库
地图、自动同步器、hook 执行器或质量工具配置，因为当前项目还没有真实需求和稳定命令
支撑这些组件。
