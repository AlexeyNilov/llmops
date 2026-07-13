# Codex Delegation Workflow

## Authority and model split

- The planning chat is the control plane. It owns requirements, architecture, compatibility decisions, task decomposition, final review, and commits.
- The user selects `gpt-5.6-sol` for planning sessions; the repository does not override that selection.
- Project subagents use `gpt-5.6-terra` for bounded exploration, implementation, and review.
- `docs/migration.md` remains the canonical migration plan. Task packets cannot override it.

## Roles

| Agent | Access | Purpose |
| --- | --- | --- |
| `migration_explorer` | Read-only | Trace legacy behavior and identify evidence, risks, and test seams. |
| `migration_worker` | Workspace write | Implement one approved task with TDD; never commit or push. |
| `migration_reviewer` | Read-only | Review the resulting diff for correctness, compatibility, security, and test quality. |

## Task lifecycle

1. The planning agent reconciles Git state and creates a task packet from `docs/tasks/TEMPLATE.md`.
2. An explorer investigates only when behavior or the test seam is not already clear.
3. The planning agent resolves questions and makes the packet implementation-ready.
4. One worker writes the failing test, implements the smallest complete behavior, and reports verification results.
5. One or more independent reviewers inspect the completed diff in parallel.
6. The same worker may receive a focused follow-up to address accepted findings.
7. The planning agent inspects the final diff, runs proportional verification, updates migration/checkpoint documentation, and commits accepted work.

Each delegation prompt should include a proportional timebox and request a concise handoff. The planning agent may interrupt work whose cost exceeds the value of the remaining evidence.

## Parallelism rules

- Use only one write-enabled worker in the shared worktree.
- Parallelize independent read-only exploration, test analysis, documentation checks, or security review.
- Do not start reviewers until the writer has stopped changing files.
- Do not delegate broad phases, architecture choices, or unresolved behavior questions as implementation tasks.
- Prefer tasks that change one observable behavior and can be reviewed independently.

## Required worker handoff

- Status: completed, partial, or blocked.
- Files changed and why.
- Test-first evidence and exact verification results.
- Assumptions made within the approved packet.
- Compatibility or security risks.
- Unresolved questions and recommended next action.

Raw logs belong in tool output or temporary artifacts, not the planning chat or task packet.

## Prohibited delegated actions

- Git commit, push, merge, or history rewrite.
- Consul, ADS, Oracle, GitLab, Kubernetes, or production mutation.
- Reading or reproducing credentials beyond the minimum needed for an explicitly approved remediation task.
- Expanding task scope silently.
- Approving intentional behavior changes.
