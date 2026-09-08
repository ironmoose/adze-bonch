# adze-bonch

A Claude Code plugin that adds workflow discipline to [adze](https://github.com/4lt7ab/adze) projects: it captures decisions as they are made, resumes a project from a saved trailhead, and runs coding tasks through a lifecycle that proves every review finding by reproduction before fixing it, then re-proves it after.

## What it is

adze-bonch sits on top of adze, a local project tracker Claude reaches through an MCP server. Because adze is a real store rather than chat history, what the plugin writes there is still readable next week, in a new session, by a different Claude.

It exists to fix three failure modes that show up in real work:

- **Decisions evaporate.** `/adze-bonch:save` writes decisions to adze the moment they are made, not in a batch at the end that never happens.
- **Reviews produce plausible fiction.** In the tackle lifecycle a finding is not real until a script has reproduced it against your actual code. Confident review text that no script can reproduce is dropped, not fixed.
- **Fixes are declared done without proof.** The same script that proved the bug is run again after the fix and must pass. A green test suite does not count: it was already green while the bug existed.

## Commands

| Command | What it does |
|---------|--------------|
| `/adze-bonch:main` | Front door. Loads discipline, resolves the project, reads its Pulse, routes intent. |
| `/adze-bonch:tackle` | Runs an adze task end to end: research, plan, branch, tests, code, review, repro, fix, re-prove, regression tests, commit. Never writes code itself. |
| `/adze-bonch:status` | Read-only snapshot of a project. Never writes. |
| `/adze-bonch:save` | Audits recent turns, surfaces unpersisted decisions, writes the ones you keep, and refreshes the Pulse. |
| `/adze-bonch:setup` | First-time wizard. Bootstraps reference docs into adze, creates your profile, offers optional hooks. Idempotent. |

## Install

```
/plugin marketplace add ironmoose/adze-bonch
/plugin install adze-bonch@ironmoose-marketplace
```

Then run `/adze-bonch:setup` once.

### Prerequisite: a running adze MCP server

Everything depends on adze. Clone [`4lt7ab/adze`](https://github.com/4lt7ab/adze) and add its server to `~/.claude.json`, pointing `--project` at wherever you cloned it:

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

With no reachable server, setup stops at step one.

## Agents

`/adze-bonch:tackle` runs 12 specialized agents through the lifecycle (a 13th, `pulse-writer`, drafts the Pulse outside tackle). Ten are read-only; only the implementer and test-writer touch your code, and only the repro-verifier runs it. One card per agent, including what each one is blind to, is in [`docs/agents-guide.md`](docs/agents-guide.md). The step-by-step lifecycle is in [`docs/how-it-works.md`](docs/how-it-works.md) section 3.

## What it will NOT do

- **No isolated copy of your repo.** Every step works in your real working tree on your real branch, so a run that goes wrong leaves partial edits behind. It shows you the diff and restores file by file; it never reaches for `git reset --hard` or `git clean`.
- **It never pushes, and it does not review pull requests.** Commit is the last thing it does; pushing and pull request review are yours.
- **Enforcement is opt-in and fails open.** The edit-blocking hook is installed only if you say yes at setup, sees only the main session's own edits, and lets edits through on any error. The verification steps are mandatory regardless; the hook is not a sandbox.
- **Several flows are not built.** brainstorm, refine, and verify are named in the routing table but not shipped; create adze projects directly for now.

The full list, with the reasoning behind each, is in [`docs/how-it-works.md`](docs/how-it-works.md) section 5.

## How it fits together

Every command loads a canonical discipline document from adze: synchronous decision persistence, the supersede pattern for history, the authoritative-doc shape, the memory-vs-adze split, and four named protocols that agents emit as literal tokens (`[GOVERNANCE]`, `[PLAN-TEST-CONFLICT]`, `[SCOPE-EXPANSION]`, `[UNVERIFIED]`). Any workflow setting resolves through a lookup chain, first hit wins: session override, then the project's `workflow_overrides`, then your user profile, then the canonical default. The five conventions are listed in `seeds/discipline.md`; [`docs/how-it-works.md`](docs/how-it-works.md) covers the protocols, the lookup chain, and the seed-file-versus-adze-document split that decides which edits change behavior.

## Credits

Built on [adze](https://github.com/4lt7ab/adze) by [@4lt7ab](https://github.com/4lt7ab).
