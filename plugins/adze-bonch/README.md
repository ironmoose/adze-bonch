# adze-bonch

Two commands for [adze](https://github.com/4lt7ab/adze) projects. The workflow orchestration that used to live here (main, tackle, setup, their agents, hooks, discipline seeds, and Codex adapters) was retired in 0.8.0.

## Commands

| Command | What it does |
|---------|--------------|
| `/adze-bonch:save` | Audits recent turns for decisions, writes the ones you keep to adze, refreshes the project's Pulse doc in place, and appends a dated entry to its Session Progress Log. |
| `/adze-bonch:status` | Read-only snapshot: the Pulse first, then task counts, blockers, open questions, and recent docs. Never writes. |

Both resolve the project from an explicit id or title fragment, then a full-text match on the cwd basename, then a pick-list.

## Agent

`pulse-writer` (haiku, read-only) drafts the Pulse for `/adze-bonch:save`: one paragraph on where work left off, one next move, an optional open question, about 25 lines max. Anything that does not fit comes back as an overflow list that save offers to file as tasks.

## Skills

- `subagent-edit-verification`: check what an editing sub-agent actually changed before trusting its report.
- `interview-prep-sheet-rehearsal-audit`.

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

`/adze-bonch:save` prefers `documents_append` for the session log and falls back to a full-body `documents_update` on older servers.
