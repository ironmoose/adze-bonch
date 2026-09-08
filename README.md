# adze-bonch

A Claude Code plugin that keeps projects tracked in [adze](https://github.com/4lt7ab/adze) disciplined: decisions are written to adze as they happen, each project keeps a one-document resume trail, and tasks run through a review gate whose findings are proven by reproduction before they get fixed.

## Install

```
/plugin marketplace add ironmoose/adze-bonch
/plugin install adze-bonch@ironmoose-marketplace
```

adze-bonch needs a running [adze](https://github.com/4lt7ab/adze) MCP server; the [plugin overview](plugins/adze-bonch/README.md) has the server config. Then run `/adze-bonch:setup` once.

## Update

```
/plugin marketplace update ironmoose-marketplace
/plugin update adze-bonch@ironmoose-marketplace
```

## Documentation

Everything is linked here, so you do not have to click through a chain of READMEs.

- **[How it works](plugins/adze-bonch/docs/how-it-works.md)** is the place to start: what the plugin does and what happens at each phase of a task, from loading it through workflow choice, research, planning, tests-first, implementation, the reviewer group, reproduction, fixes, re-proving the fix, regression tests, and the commit check.
- **[Agents guide](plugins/adze-bonch/docs/agents-guide.md)**: one card per agent, including what each one is blind to.
- **[Plugin overview](plugins/adze-bonch/README.md)**: the five commands, setup, and the adze prerequisite on one page.
- **[Quality gate CLI](plugins/adze-bonch/gate/README.md)**: the optional enforcement tool that blocks edits while a finding is still unverified.
- **Conventions the agents work under**: [TypeScript](plugins/adze-bonch/reference/typescript-conventions.md), [Python](plugins/adze-bonch/reference/python-conventions.md), and [prose / no-AI-slop](plugins/adze-bonch/reference/no-ai-slop.md).

## Credits

Built on [adze](https://github.com/4lt7ab/adze) by [@4lt7ab](https://github.com/4lt7ab).
