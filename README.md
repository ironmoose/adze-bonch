# adze-bonch

A Claude Code plugin that keeps projects tracked in [adze](https://github.com/4lt7ab/adze) disciplined: decisions are written to adze as they happen, each project keeps a one-document resume trail, and tasks run through a review gate whose findings are proven by reproduction before they get fixed.

## Documentation

- **[How it works](plugins/adze-bonch/docs/how-it-works.md)** is the place to start: what the plugin does and what happens at each phase of a task, from loading it through workflow choice, research, planning, tests-first, implementation, the reviewer group, reproduction, fixes, re-proving the fix, regression tests, and the commit check.
- **[Agents guide](plugins/adze-bonch/docs/agents-guide.md)**: one card per agent, including what each one is blind to.
- **[Plugin README](plugins/adze-bonch/README.md)**: commands, setup, and the adze prerequisite in one page.

## Install

```
/plugin marketplace add ironmoose/adze-bonch
/plugin install adze-bonch@ironmoose-marketplace
```

adze-bonch needs a running [adze](https://github.com/4lt7ab/adze) MCP server; the [plugin README](plugins/adze-bonch/README.md) has the server config. Then run `/adze-bonch:setup` once.

## Update

```
/plugin marketplace update ironmoose-marketplace
/plugin update adze-bonch@ironmoose-marketplace
```

## Credits

Built on [adze](https://github.com/4lt7ab/adze) by [@4lt7ab](https://github.com/4lt7ab).
