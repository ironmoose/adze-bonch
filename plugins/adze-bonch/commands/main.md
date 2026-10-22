---
name: main
description: "Front door for an adze project: resolves the project, shows its Pulse and task counts, and routes to save, status, or tackle. Optional; nothing requires it."
---

# adze-bonch -- Main

Resume an adze project and route. Optional: `save`, `status`, and `tackle` each resolve the project on their own.

## Step 1: Resolve the project

First hit wins; cache the id for the session.

1. A project id, slug, or title fragment the user passed: `mcp__adze__projects_get` or `mcp__adze__projects_list({ q })`.
2. The cwd basename: `mcp__adze__projects_list({ q: <basename> })`, single hit only.
3. Ask the user to pick from a short list of active projects.

No match: if the user described a new idea, offer `mcp__adze__projects_create`; otherwise ask which project they mean and stop.

## Step 2: Show where things stand

1. `mcp__adze__projects_get({ id })` and `mcp__adze__tasks_list({ project_id })`.
2. Load the Pulse: `tags_list({ q: "kind:pulse" })`, `documents_list({ tag_id })`, cross-checked with `documents_for_project({ project_id })`; then `documents_get`. More than one pulse on the project: halt and ask which is authoritative.
3. Print the Pulse (Where we left off, Next move, Open for user), then one line of task counts (todo / doing / done / blocked) and any stale `doing` tasks. No pulse: say "no pulse yet; /adze-bonch:save creates one."

## Step 3: Route

| Intent | Route |
|---|---|
| save, checkpoint, persist | `/adze-bonch:save` |
| status, where are we, bare `/adze-bonch:main` | stop after Step 2 and ask what's next |
| tackle X, work on X, implement, fix | `/adze-bonch:tackle` with the user's message |

Do not start work on your own after showing the Pulse. No em dashes in output.
