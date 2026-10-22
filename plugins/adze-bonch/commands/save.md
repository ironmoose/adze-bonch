---
name: save
description: "Synchronous decision capture. Audits the last N conversation turns, surfaces unpersisted decisions, asks which to capture, dispatches the writes immediately. The 'save our work' hammer."
---

# adze-bonch -- Save

The "save our work" hammer. Conversation context evaporates and adze persists, so decisions are written as soon as they land, not batched at session end. This command audits recent turns, surfaces decisions that should be captured, asks the user which ones to write, and dispatches the writes IMMEDIATELY.

## Step 0: Resolve Project

Resolve the active adze project directly (first hit wins). There is no discipline doc to load; the rules this command needs are written inline below.

1. **Session-cached project id.** If a prior `/adze-bonch:*` call this session resolved a project, reuse it.
2. **Explicit user arg.** A project id via `mcp__adze__projects_get`, or a slug or title fragment via `mcp__adze__projects_list({ q: <arg> })`.
3. **FTS over the cwd basename** via `mcp__adze__projects_list({ q: <basename> })`. Single hit only.
4. **Ask the user** to pick from a short list of active projects. Cache the answer for the session.

Then `mcp__adze__projects_get({ id })` for the project title and context. Keep the id handy; Step 3.5 updates the project's Pulse.

If no project resolves, print "Save needs a project. Pass a project id or a title fragment." Stop.

## Step 1: Audit Conversation Context

Walk back through the last 10-20 turns of conversation. Categorize each candidate against this trigger list:

**Triggers (write happens):**
- Direction pivot ("we're going X instead of Y") → project context update + supersede conflicting docs
- New playbook / pipeline / workflow defined → new dated doc
- Open question resolved → update relevant doc, remove the question
- Reference / artifact captured (image, file, link the user shared) → save to `~/workspaces/notes/<project>-*` + adze doc pointing to it
- Tooling chosen / rejected → update authoritative playbook + Decisions Locked
- Approach abandoned → supersede the prescribing doc

**Non-triggers (skip):**
- Exploratory chatter that didn't land
- Read-only research
- Implementation details inside an already-decided approach
- Reversible UI tweaks

For each trigger, draft:
- One-line summary
- Type (project_context_update / new_doc / supersede / task_create / task_update / artifact_capture)
- Target (project / doc id / file path)
- Proposed write payload (title, body, tags, supersedes)

## Step 2: Present and Ask

Print:

```
Decisions surfaced from recent turns:

  1. [type] {summary}
     -> {target}

  2. [type] {summary}
     -> {target}

  ...

Capture which? (all [default -- press enter] / numbers like '1,3' / none)
```

Wait for input.

**Default is ALL.** An empty/blank answer (or "all") captures every surfaced item -- this user always captures all. Only a subset ('1,3') or the literal 'none' narrows it.

If `none`: print "Skipped. Nothing written." Stop.

## Step 3: Dispatch Writes Synchronously

For each accepted item, in order:

| Type | Action |
|------|--------|
| `project_context_update` | `mcp__adze__projects_update({ id, context: <merged> })` |
| `new_doc` | `mcp__adze__documents_create(...)` then `mcp__adze__documents_attach({ project_id, document_id })` |
| `supersede` | (1) Read existing doc. (2) Prepend a SUPERSEDED notice block naming the replacement and date. (3) Rename title to `[SUPERSEDED <YYYY-MM-DD>] <Original>`. (4) `mcp__adze__documents_update`. (5) Create the new authoritative doc (dated header, TL;DR, Open Questions, Decisions Locked). |
| `task_create` | `mcp__adze__tasks_create(...)` |
| `task_update` | `mcp__adze__tasks_update(...)` |
| `artifact_capture` | Write artifact to `~/workspaces/notes/<project-slug>-<artifact>-<YYYY-MM-DD>.{ext}`, then create an adze doc that links to it. |

**Concurrency rule** (adze `documents_update` and `projects_update` replace the whole body):
- For docs tagged `concurrency:strict`: re-read with `documents_get` before writing IF last read was >60s ago. Skip re-read otherwise.
- For tasks (default `concurrency:lax`): skip the re-read.

**After each write succeeds, print:** `wrote: {type} -> {id-or-path}`

**If a write fails:** print the error, ask the user whether to retry, skip, or stop.

## Step 3.5: Update the Project Pulse

Every save refreshes the Project Pulse: a per-project resume trailhead, updated IN PLACE (never superseded; the pulse is transient). The pulse has a hard size budget (<=25 lines, about 1500 characters, one active thread, one next action). Anything that does not fit is filed as a task, not crammed into the pulse; that is why the `pulse-writer` returns an overflow list.

1. **Compile recent context.** Gather what just happened this session: the decisions captured in Step 3, active task IDs, relevant doc IDs, commit hashes, and file paths.
2. **Load the existing pulse** via the standard lookup:
   - `mcp__adze__tags_list({ q: "kind:pulse" })` -> tag id.
   - `mcp__adze__documents_list({ tag_id })` for candidates.
   - `mcp__adze__documents_for_project({ project_id })` to cross-check attachment; the pulse is the doc present in BOTH sets.
   - `mcp__adze__documents_get({ id })` for its body.
   - **One-per-project rule:** if more than one `kind:pulse` doc attaches to this project, HALT and ask which is authoritative.
3. **Dispatch the `pulse-writer` sub-agent** (model haiku, read-only). Pass it: the project title, the compiled context, and the existing pulse body (if any). It DRAFTS the 3 canonical sections (Where we left off / Next move / Open for user) and RETURNS them inside a machine-parseable envelope (`===PULSE===` / `===OVERFLOW===` / `===END===`); it does not write to adze itself.
4. **Parse the envelope.** Split the returned message on the `===PULSE===`, `===OVERFLOW===`, and `===END===` markers:
   - The text between `===PULSE===` and `===OVERFLOW===` is the **pulse body**.
   - The text between `===OVERFLOW===` and `===END===` is the **overflow list**: zero or more items the writer trimmed to keep the pulse within budget, or the literal `(none)`.
5. **Show the pulse body** and ask the user to confirm.
6. **On confirm, write the pulse:**
   - If a pulse exists: `mcp__adze__documents_update` it IN PLACE. Concurrency is strict: re-read with `documents_get` first if the last read was >60s ago.
   - If none exists: `mcp__adze__documents_create` with tags `kind:pulse` and `provenance:user`, then `mcp__adze__documents_attach({ project_id, document_id })`.
7. **Print** `wrote: pulse -> {id}`.
8. **File overflow as tasks.** If the overflow list is `(none)`, skip this step. Otherwise print the trimmed items as a numbered list and ask:

   ```
   These didn't fit the pulse budget; file as tasks? (all / numbers / none)
   ```

   Wait for input. For each accepted item, call `mcp__adze__tasks_create({ project_id, title, context: body })` and print `wrote: task -> {id}`. This closes the loop: excess becomes tasks, not pulse bloat.

## Step 4: Append to the Session Progress Log

After all writes, append a dated entry to the project's ONE canonical "Session Progress Log" doc, summarizing what was captured this turn. This append is synchronous, not background.

1. **Find the canonical doc.** Resolve the `kind:session-log` tag id (`tags_list`), list its docs (`documents_list`), and cross-check attachment with `documents_for_project`; the session log is the doc present in both sets whose title is "Session Progress Log". If more than one `kind:session-log` doc is attached to this project and not yet merged, HALT and ask which is canonical (the one-per-project rule that tag exists to enforce). If none exists, `documents_create` it (tags `kind:session-log` and `provenance:user`) with this turn's dated entry as its body, then `documents_attach`, and you are done with this step.

2. **Append with `documents_append`, never a full-body rewrite.** Call `mcp__adze__documents_append({ id, text })`. It concatenates `text` onto the doc server-side and returns a lean summary (id, appended_chars, context_length, updated_at) without echoing the body, so it neither risks a hand-retype of a long archive nor blows the tool-result token cap. The append is VERBATIM with no separator inserted, so `text` MUST begin with its own blank-line separator and a dated H2 header, for example: `"\n\n## <YYYY-MM-DD> (<one-line session theme>)\n\n- <what was captured> ..."`. Empty `text` is rejected, so never call it with nothing.

3. **Do NOT create a continuation or fragment doc.** The reason fragments used to accumulate, that `documents_update` replaces the whole body so appending to a long log meant retyping it, is exactly what `documents_append` removes. Append to the single canonical doc every time.

4. **Print** `wrote: session-log -> {id}`.

**Fallback when `documents_append` is unavailable** (an older adze-mcp server that does not expose the tool): `documents_get` the doc, then `documents_update` it with the full existing body plus the new entry appended (concurrency is strict: re-read if the last read was over 60s ago). This legacy path is a full-body rewrite; use it only when `documents_append` genuinely is not present, and prefer the append tool whenever it exists.

## Hard Rules

- **Synchronous, always.** Never queue writes. Never batch into one giant doc dump at session end. The whole point of this command is to defeat that pattern.
- **Supersede, never delete.** If you rejected an approach, the doc that prescribed it gets superseded (SUPERSEDED notice plus renamed title). Never `documents_delete`.
- **Project context updates aren't optional.** If a pivot landed, `projects_update` runs.
- **Memory vs adze split:** user-level facts go to memory (don't write under `~/.claude/` during a work session; instead, surface them in `~/workspaces/notes/`). Project facts go to adze.
- **No em-dashes** in any captured doc body or commit message.

## Style

- One question per turn when soliciting accept/reject.
- Show the diff or the new content before the write, briefly. The user should know what they're saying yes to.
