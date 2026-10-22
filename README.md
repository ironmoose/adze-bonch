# adze-bonch

A Claude Code (and Codex) plugin for projects tracked in [adze](https://github.com/4lt7ab/adze). It keeps adze in step with the work: decisions are written as they land, each project has a short resume note (the Pulse), and tasks move from todo to done as you finish them.

0.8.0 is a lean rework. The old pipeline (a mandatory router, a routing agent, research/implement/test agents, a ten-lane review gate on every change, a setup wizard, seeded discipline docs) is gone. The commands now do the work in the main conversation and hand test-first work, bug diagnosis, and review to [mattpocock-skills](https://github.com/mattpocock/skills). The full repro-verified review is still there, opt-in, through [prove-it](https://github.com/ironmoose/prove-it).

## Commands

| Command | What it does |
|---|---|
| `/adze-bonch:save` | Finds decisions in recent turns, writes the ones you keep to adze, refreshes the project's Pulse, appends the session log. |
| `/adze-bonch:status` | Read-only snapshot, Pulse first. |
| `/adze-bonch:main` | Resume a project: show its Pulse and task counts, route to the others. |
| `/adze-bonch:tackle` | Work one adze task: mark it doing, build it, run the repo's checks, review if big or risky, commit, mark it done, save. `--prove` adds `/prove-it:review`. |

## Install

```
/plugin marketplace add ironmoose/adze-bonch
/plugin install adze-bonch@ironmoose-marketplace
```

Needs a running adze MCP server; the [plugin overview](plugins/adze-bonch/README.md) has the config. `tackle` works best with mattpocock-skills installed; `--prove` needs prove-it. Codex setup is in [plugins/adze-bonch/codex/README.md](plugins/adze-bonch/codex/README.md).

## Update

```
/plugin marketplace update ironmoose-marketplace
/plugin update adze-bonch@ironmoose-marketplace
```

## Credits

Built on [adze](https://github.com/4lt7ab/adze) by [@4lt7ab](https://github.com/4lt7ab).
