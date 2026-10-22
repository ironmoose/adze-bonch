---
name: tackle
description: "Work one adze task end to end in the main context: mark it doing, build it (mattpocock tdd or diagnosing-bugs where they fit), run the repo's checks, review only when the change is big or risky, commit, mark it done, and save. --prove adds a /prove-it:review pass."
argument-hint: "[<task id or title fragment>] [--prove]"
---

# adze-bonch -- Tackle

Do one adze task and keep adze in step with it. You do the work yourself, in the main context. No sub-agent is mandatory; dispatch one only when work is genuinely parallel or large.

## Step 1: Resolve the task

1. Resolve the project as in `/adze-bonch:main` Step 1 (reuse a session-cached id).
2. Resolve the task: a passed id via `mcp__adze__tasks_get`, a title fragment via `mcp__adze__tasks_list({ project_id, q })`, else ask which open task.
3. Read the task fully and the project's Pulse (lookup in `/adze-bonch:main` Step 2).
4. Read the target repo's `CLAUDE.md`. It is the ruleset for the work and wins over anything here.
5. `mcp__adze__tasks_update({ id, status: "doing" })`.

## Step 2: Settle scope

If what "done" means is clear from the task, go. If not, ask the user, one question at a time; for a plan with real open design choices, use the `grilling` skill. Do not write a plan doc unless the user wants one.

## Step 3: Build

Pick by task shape:

| Task | Approach |
|---|---|
| Feature or change with logic to test | `tdd` skill: failing test first, then green |
| Bug, failure, regression, slowness | `diagnosing-bugs` skill: build a loop that goes red, then fix |
| Docs, config, dependency bump | Edit directly |

Branch only if the repo's `CLAUDE.md` asks for one; otherwise work where the user is.

## Step 4: Prove it runs

Run the repo's own tests and checks (whatever its `CLAUDE.md` names). For visual changes, render and look. Report the real results; a failing check is reported with its output, never glossed.

## Step 5: Review (conditional)

- **Small, low-risk change:** no review. Tests passing is the bar.
- **Big or risky change** (public API, security, data migration, wide refactor): run the `code-review` skill once against the starting commit.
- **`--prove`, or the user asks for proof:** run `/prove-it:review local --goal "<task title and acceptance criteria>"`. Fix its Confirmed findings, then run `/prove-it:follow-up` so each finding's own repro is re-run against the fix.

Fix what the review confirms, then re-run Step 4.

## Step 6: Commit and close

1. Commit following the repo's conventions (author, message style, trailers). Never push or open a PR unless the user says so.
2. `mcp__adze__tasks_update({ id, status: "done" })`, or leave it `doing` and say why if work remains.
3. Run `/adze-bonch:save` to capture decisions, refresh the Pulse, and append the session log.

## Rules

- Never `git reset --hard` or `git clean`; discard file by file with `git restore`, after showing the user the diff.
- Write decisions to adze as they land, not batched at the end.
- No em dashes in commits, docs, or adze writes.
