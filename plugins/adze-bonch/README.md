# adze-bonch

Four commands, one agent, and one skill for [adze](https://github.com/4lt7ab/adze) projects.

## Commands

| Command | What it does |
|---|---|
| `/adze-bonch:save` | Audits recent turns for decisions, writes the ones you keep to adze, refreshes the project's Pulse in place, and appends a dated entry to its Session Progress Log. |
| `/adze-bonch:status` | Read-only snapshot: the Pulse, then task counts, blockers, open questions, and recent docs. Never writes. |
| `/adze-bonch:main` | Optional front door: resolves the project, shows the Pulse and task counts, routes to save, status, or tackle. |
| `/adze-bonch:tackle` | Works one adze task in the main conversation (see below). |

Every command resolves the project itself: an explicit id or title fragment, then a full-text match on the cwd basename, then a pick-list.

## tackle

1. Resolve the task, read it and the Pulse, read the target repo's `CLAUDE.md`, mark the task `doing`.
2. Settle scope with the user if it is unclear (`grilling` for real design choices).
3. Build: `tdd` for logic, `diagnosing-bugs` for bugs, direct edits for docs and config.
4. Run the repo's own tests and checks.
5. Review only big or risky changes, with `code-review`. `--prove` runs `/prove-it:review` and `/prove-it:follow-up` instead.
6. Commit, mark the task `done`, run `/adze-bonch:save`.

No sub-agent is mandatory. `tdd`, `diagnosing-bugs`, `grilling`, and `code-review` come from [mattpocock-skills](https://github.com/mattpocock/skills); without it, tackle follows the same steps by hand.

## Agent

`pulse-writer` (haiku, read-only) drafts the Pulse for `save`: one paragraph on where work left off, one next move, an optional open question, about 25 lines max. What does not fit comes back as an overflow list that `save` offers to file as tasks.

## Skill

`subagent-edit-verification`: check what an editing sub-agent actually changed before trusting its report.

## Prerequisite: a running adze MCP server

Clone [`4lt7ab/adze`](https://github.com/4lt7ab/adze) and add its server to `~/.claude.json`:

```json
"mcpServers": {
  "adze": {
    "type": "stdio",
    "command": "uv",
    "args": ["run", "--project", "/path/to/adze", "python", "-m", "adze_mcp"],
    "env": {}
  }
}
```

`save` prefers `documents_append` for the session log and falls back to a full-body `documents_update` on older servers.

## Codex

See [codex/README.md](codex/README.md).
