# Agents guide

This plugin breaks the work of finishing a coding task into a team of narrow specialists. adze-bonch itself ships five: `scrum-master` picks the workflow, `researcher` reads the codebase, `test-writer` writes the tests, `implementer` writes the code, and `pulse-writer` drafts the session note outside the tackle flow entirely. Only the implementer and the test writer can change a file in your project; the other three are strictly read-only. That is why the useful question for these five is never "did an agent look at this?" but "which agent was asked the question that would have caught it?" Each card below answers that. Checking the finished result is a separate job, done by a separate plugin: see the pointer section after the implementer and test writer cards for who does that and where they actually live.

### Workflow picker (scrum-master)

**One line:** Decides how much ceremony this task needs before any code is written.

**When it runs:** First, right after the task is loaded from the tracker and before anyone reads the codebase.

**What it looks at:** Only the text it is handed. The task title, description, acceptance criteria, any `kind:` tags, plus a record of how similar past tasks went. It has no Read, Grep, or Glob tools at all and cannot open a single file.

**What you get back:** A short workflow plan naming which agents run, in what order, which ones are skipped and why, whether tests are written first, whether docs need updating, and any risks worth flagging.

**A concrete example of something it would catch:** A task called "Add CSV export for reports" whose description quietly continues "and fix the export timeout while we're in there, and add a `--format` flag to the CLI." That is three separate pieces of work wearing one title. The workflow picker names the seam and proposes splitting it before the branch exists, instead of you finding out at review time that the change touches nine files.

**When it will NOT help:** It is judging a task by its description, not by reality. If the task text says "one-line config change" and the config key turns out to be read in fourteen places, this agent has no way to know. It also cannot veto anything. It recommends, and a person can say "one branch is fine."

### Codebase researcher (researcher)

**One line:** Reads the code around a task and reports what is really there before planning starts.

**When it runs:** After the workflow is chosen, before the plan is written.

**What it looks at:** The repository itself. It reads the project's CLAUDE.md files first, then finds the files the task touches, follows the call chain at least one level past the obvious files to find callers and callees, and checks other services that consume the same API shapes, event payloads, or shared types. When the task depends on how a third-party library actually behaves, it looks the behavior up in real documentation rather than answering from memory.

**What you get back:** A research summary: affected files with reasons, the traced call chain, a description of what the code does today, cross-service impacts, at least two possible approaches with tradeoffs, and an explicit list of risks and things it could not determine by reading. Every claim about a third-party library is labelled as either sourced from docs or an inference.

**A concrete example of something it would catch:** The task says "rename the response field `owner_id` to `ownerId`, it's a one-liner." The researcher greps past the service and finds the admin dashboard in a different repo destructuring `owner_id` off that exact response, plus a background worker keying its dedupe map on it. The rename is not a one-liner, and you learn that before the plan is written rather than after the deploy.

**When it will NOT help:** It never runs anything. Everything it tells you is what the code looks like, not what it does at runtime, so a bug that only appears under real data or real timing is invisible to it. It also does not choose. It hands you two or more approaches and the tradeoffs, and someone else picks.

### Implementer (implementer)

**One line:** Writes the code the plan asked for, and honestly reports every place it did something else.

**When it runs:** After the plan is approved and the branch exists. Under the test-first default the failing tests already exist, and this agent makes them pass. It runs a second time later to fix confirmed review findings.

**What it looks at:** The approved plan, the explicit list of files the plan allows it to edit, the existing code in the area it is changing (so it copies the surrounding style rather than inventing a new one), and the project's CLAUDE.md rules.

**What you get back:** The actual code changes in your working tree, plus a report listing files changed, which plan steps are done or blocked, and two required self-audits: a count of every pattern the repo forbids found in its own changes, and a list of every deviation from the plan with a self-rating of whether a reviewer should accept or push back on it.

**A concrete example of something it would catch:** The plan says to keep an existing streaming hash helper and add a separate small prefix-read for file-type detection, because reading whole multi-megabyte files on every batch operation was measured as too slow. The test that was written first happens to force a full-file read. The easy path is to delete the streaming helper, read the whole file once, and watch everything go green. This agent is required to stop instead, quote the plan, quote the test, and report a plan-versus-test conflict, so nobody merges a performance regression that had a passing test suite.

**When it will NOT help:** It will not touch a file that is not on its approved list, even when that file is obviously where the problem lives. It stops and flags instead, which costs a round trip. It does not review its own code, does not write new tests, does not modify existing tests, and does not run the repo's full lint and typecheck and test suite. If the plan itself is wrong, this agent will faithfully build the wrong thing and tell you it matched the plan.

### Test writer (test-writer)

**One line:** Writes the tests for the change, in the repo's own testing style.

**When it runs:** Usually first, before any code exists, writing tests that are supposed to fail. In non-test-first workflows it runs after the code is written instead. It runs once more at the very end to turn proven bugs into permanent tests.

**What it looks at:** The project's test config to detect the runner and assertion library, and at least one existing test file next to where the new test will live, so imports, mock setup, naming, and structure match what is already there. In test-first mode it works from the planned function signatures rather than from the implementation.

**What you get back:** Test files created or modified, a coverage summary per file, the exact command it ran, and confirmation the tests are green. Anything it noticed but deliberately did not test is listed for the edge case agent.

**A concrete example of something it would catch:** Writing an ordinary error-path test for `createReport` when the template is missing, it discovers the service wraps everything in a `try` that logs and returns `null`. The caller cannot distinguish "no template" from "empty report," and no test can assert the failure because the failure never escapes. It reports that as a production bug rather than quietly writing a test that asserts `null` and calling it covered.

**When it will NOT help:** It is forbidden from touching production code, so when it finds a bug it reports it and moves on. It deliberately stays on the happy path, expected errors, and obvious boundaries like empty arrays and zero counts. Race conditions, timeouts mid-operation, partial writes, and adversarial input are somebody else's job by design. It also will not invent a pattern: if the repo has no mock helper for a new dependency, it flags that rather than building one.

### The quality gate: prove-it's reviewers

`/adze-bonch:tackle` dispatches ten read-only reviewers in parallel at the quality gate, then a repro-verifier that proves or refutes their findings by actually running code, twice: once right after the gate, once more after the fix to confirm the fix holds. None of these eleven live in adze-bonch. They are `code-reviewer`, `acceptance-qa`, `edge-case-qa`, `code-smells-reviewer`, `test-reviewer`, `self-containment-reviewer`, `comment-claim-verifier`, `contract-reviewer`, `security-reviewer`, and `doc-vouching-reviewer`, then `repro-verifier`, all namespaced `prove-it:` and all owned and shipped by the separate **prove-it** plugin. Tackle dispatches them and reads their reports; it does not define their prompts or their catalogue. prove-it is a required companion for the gate: without it installed, tackle has no reviewers or repro-verifier to call. A card on each one lives in prove-it's own documentation. prove-it also runs the same reviewers as a standalone pass over any diff, outside tackle entirely, via `/prove-it:review`.

### Session note writer (pulse-writer)

**One line:** Writes the short note that tells your next session where you left off.

**When it runs:** Never during a coding task. It has no place in the sequence above and will not appear while a change is being written or reviewed. It runs when you save your work on a project, or when you first open one, and that is all.

**What it looks at:** Almost everything is handed to it: the project name, a summary of what just happened this session (task ids, document ids, commit hashes, file paths, decisions, and where you stopped), the previous note if one exists, and the writing voice to match. It can read a file or check a path to confirm something it is about to name, and nothing else. It gets exactly one turn and never asks a follow-up question.

**What you get back:** A note under 25 lines in three parts. "Where we left off" is a short conversational paragraph naming real ids and paths so the detail can be fetched. "Next move" is exactly one concrete action. "Open for user" appears only if a question is genuinely waiting. Separately, it sends back a list of everything it trimmed out, each labelled with why, so those can be filed as tasks. It does not save the note itself; a person confirms it first.

**A concrete example of something it would catch:** You spent an evening finishing a migration, half-starting an unrelated refactor, and leaving a naming question open. The obvious note would mention all three, and three weeks later you would read it and not know which one you were in the middle of. This one keeps the migration thread with its commit hash and the single next action, and pushes the refactor out as an item marked "second thread" and the extra idea out as "extra next action". What you come back to is a lead, not a log.

**When it will NOT help:** It tells you nothing you did not already tell it. It works from the summary it is handed and does not go read your repo or your task tracker, so a thin summary produces a thin note, and it gets no second turn to ask for more. It drops your second thread and your spare ideas out of the note by design, so if nobody files the trimmed list as tasks, those are simply gone. And it is not a status report: architecture, decisions, and backlog belong in other places and it will not carry them.
