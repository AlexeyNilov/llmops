# Compaction Workflow

Use this workflow before context compaction or when handing the task to another Codex session.

## Sources of truth

Resolve conflicts in this order:

1. Current repository files and Git state.
2. `AGENTS.md` instructions.
3. `docs/migration.md` for approved scope, architecture, decisions, and risks.
4. `docs/codex-task-state.md` for the transient execution checkpoint.

`docs/codex-task-state.md` is tracked and committed so the checkpoint survives cross-machine and cross-session handoffs. It must not become a second migration plan. Rewrite it at each checkpoint; do not append a session diary.

## Before compacting

Use this prompt:

```text
Prepare this task for context compaction.

1. Update docs/migration.md first with any newly approved decisions, evidence,
   deferred questions, or changed risks.
2. Rewrite docs/codex-task-state.md as a concise checkpoint containing:
   - current objective and migration phase;
   - branch, HEAD commit, and working-tree status;
   - completed work not already obvious from the current diff;
   - current edits and their purpose;
   - verification commands and exact results;
   - blockers, security issues, user-owned actions, and external state;
   - unresolved and explicitly deferred questions;
   - exact next action, including the first file or command;
   - files and specific migration sections that must be re-read;
   - any running command or background process that must be resumed.
3. Run git diff --check and inspect git status --short.
4. Include docs/codex-task-state.md in the next repository commit; do not leave
   a handoff depending only on an untracked local checkpoint.

Rules:
- Base the checkpoint only on verified repository state and explicit user decisions.
- Do not copy source files, long logs, command histories, or the decision log.
- Never store credentials, tokens, private response bodies, or secret-bearing URLs.
- Label assumptions and unverified external state explicitly.
- Record what must not be repeated or mutated.
- Keep the checkpoint below 120 lines.
```

Then run:

```text
/compact
```

## After compacting

Use this prompt:

```text
Resume the HappySCR migration task.

Before changing files:
1. Read AGENTS.md.
2. Read docs/codex-task-state.md.
3. Read the referenced sections of docs/migration.md.
4. Inspect git status --short, git diff, and the current HEAD commit.
5. Reconcile the checkpoint with actual repository state; repository state wins.
6. Restate the objective, blockers, deferred questions, and exact next action
   in one concise progress update.

Do not repeat completed work, expose recorded secrets, perform external mutations,
or resume a deferred question without the required evidence.
```

After resuming, update the checkpoint only when state materially changes or before the next compaction.
