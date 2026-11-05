# Harness Phase Context

[简体中文](#中文) | [English](#english)

## 中文

`harness/context/` 只保存对未来工作有实际影响的材料性上下文。每个已批准阶段最多维护
一个阶段上下文文件，推荐命名为：

```text
phase-<NN>-<phase-slug>-context.md
```

### Create and Update Timing

- 阶段开始且获得所需批准后创建；
- 发生会影响范围、实现方案、接口、依赖、拥有者、验收、验证或风险的发现时更新；
- 阶段交接前复核；
- 不把上下文文件当作聊天记录、进度日志或命令输出转储。

### Materiality Test

只有在遗漏信息可能导致以下结果时才记录：

- 改变已批准的范围或实现方案；
- 让未来阶段重复发现或重新做出决策；
- 影响接口、依赖、不变量或模块拥有者；
- 改变验收条件或所需验证；
- 影响安全、隐私、可靠性、观测、回滚或恢复；
- 隐藏阻塞、未决假设、已接受限制或后续行动。

### Required Provenance

每项材料性记录应尽量关联来源，例如文件、命令、测试结果、评审发现、用户决策或
Spec/Plan/Tasks 路径。不要写入凭据、令牌、密钥或不必要的个人信息。

### Source-of-Truth Boundaries

- 阶段 Build 文件拥有批准范围、非目标、验收和计划验证；
- Context 文件拥有材料性发现、决策、约束和未决问题；
- `harness/build-log.md` 拥有实际进度和观察到的验证证据；
- Review 文件拥有详细评审发现和签核状态；
- 不要把这些文件互相完整复制，只在必要时使用短摘要和链接。

许可证见 [LICENSE](../../LICENSE)。

## English

`harness/context/` stores only material context with a real impact on future work. Maintain at most
one phase-context file per approved phase, preferably named:

```text
phase-<NN>-<phase-slug>-context.md
```

### Create and update timing

- create after the phase starts and required approvals are obtained;
- update when a finding affects scope, implementation approach, interfaces, dependencies, ownership, acceptance, verification, or risk;
- recheck before phase handoff;
- do not treat the context file as a chat log, progress log, or command-output dump.

### Materiality test

Record something only when omitting it could cause:

- a change to approved scope or implementation approach;
- future phases to rediscover or re-decide the same thing;
- impact on interfaces, dependencies, invariants, or module ownership;
- a change to acceptance criteria or required verification;
- impact on security, privacy, reliability, observability, rollback, or recovery;
- hidden blockers, open assumptions, accepted limitations, or follow-up actions.

### Required provenance

Each material record should link to its source where possible, such as a file, command, test result,
review finding, user decision, or Spec/Plan/Tasks path. Never write credentials, tokens, secrets, or
unnecessary personal information.

### Source-of-truth boundaries

- phase Build files own approved scope, non-goals, acceptance, and planned verification;
- Context files own material findings, decisions, constraints, and open questions;
- `harness/build-log.md` owns actual progress and observed verification evidence;
- Review files own detailed review findings and sign-off status;
- do not fully duplicate these files; use short summaries and links only when necessary.

See the repository [LICENSE](../../LICENSE).
