# Agent index

The `agents/` directory holds the agent definition files for the `adze-bonch` tackle lifecycle. adze-bonch ships five agents, listed below in tackle pipeline order (`scrum-master` routes first; `pulse-writer` sits outside the pipeline). This index lives in docs/ rather than agents/ because Claude Code registers every .md file in agents/ as an agent.

The Step 4c quality gate reviewers and the Step 4c.5/4d.5 repro-verifier are **not** adze-bonch agents. They are dispatched as `prove-it:*` agents from the required companion `prove-it` plugin (10 reviewers on standard, plus `prove-it:repro-verifier`). See `CLAUDE.md`'s Agent roster section for the full `prove-it:*` list and the reasoning behind the relink.

## scrum-master

**What it does.** The agent file's `description` reads: "Read-only workflow advisor that analyzes tasks and recommends which workflow to run (standard/lightweight/docs-only/custom). Returns structured workflow plans to the orchestrator. Spawned at Step 0.5 of every workflow."

It is a read-only advisor: it analyzes tasks, context, and history, then returns a structured workflow plan. It does not execute the plan; the orchestrator does.

File: [`scrum-master.md`](../agents/scrum-master.md)

## researcher

**What it does.** The agent file's `description` reads: "Explores the target repository to build context for an adze task. Traces call paths, identifies affected files, documents current behavior, and proposes approaches before planning begins. Spawned in Step 1 of every workflow that includes research."

It is read-only: it explores code, traces dependencies, and produces structured research summaries. It never modifies files of any kind.

File: [`researcher.md`](../agents/researcher.md)

## implementer

**What it does.** The agent file's `description` reads: "Disciplined implementer that executes plan steps within a locked file surface, audits its own diff against the plan, and reports every deviation honestly. Spawned in Step 4a (implement) and Step 4d (fix QA findings)."

It executes approved plans precisely, directly in the target repo's working tree, and reports what it actually did with full honesty, including every place it deviated from the plan. It does not silently re-architect, does not rewrite implementations to fit tests, and does not expand scope. It is the sole agent that writes implementation code.

File: [`implementer.md`](../agents/implementer.md)

## test-writer

**What it does.** The agent file's `description` reads: "Writes tests for newly implemented code. Follows the target repo's test framework, patterns, and conventions. Co-locates test files per convention. Runs targeted tests to verify they pass before returning. Spawned in Step 3.5 (TDD) or Step 4b (standard) after implementation, and again in Step 4e (promote mode) to translate a Confirmed-and-fixed finding's repro into a permanent regression test."

It follows each repo's established test patterns exactly, does not invent new patterns or deviate from conventions, and runs targeted tests to confirm they pass before returning results.

File: [`test-writer.md`](../agents/test-writer.md)

## pulse-writer

**What it does.** The agent file's `description` reads: "Read-only agent that drafts a project's Pulse doc (session-resume trailhead) in the canonical 3-section shape. Returns the drafted sections to the orchestrator; does NOT write to adze itself. Dispatched by /adze-bonch:save (and /adze-bonch:tackle when starting a project)."

It drafts a project's Pulse doc: the single short note a future agent reads first when re-entering a project, so it knows where work left off and what to do next. It is read-only. It drafts the three sections and returns them; it does not write to adze itself, the orchestrator confirms the draft with the user and persists it.

File: [`pulse-writer.md`](../agents/pulse-writer.md)
