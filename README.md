# adze-bonch

A Claude Code plugin with two commands for projects tracked in [adze](https://github.com/4lt7ab/adze): one writes decisions and a resume note to adze, the other shows where a project stands.

**Status: the orchestration is retired (0.8.0).** Earlier versions shipped a front-door router (`/adze-bonch:main`), a full task pipeline (`/adze-bonch:tackle`) with its own agents and mandatory review gate, a setup wizard, a SessionStart nudge hook, a discipline doc seeded into adze, and Codex adapters. The per-session overhead outweighed the benefit, so all of that is gone. The last version with it is tag-less commit `17544f8` (0.7.1).

## Install

```
/plugin marketplace add ironmoose/adze-bonch
/plugin install adze-bonch@ironmoose-marketplace
```

Needs a running adze MCP server; the [plugin overview](plugins/adze-bonch/README.md) has the config.

## Update

```
/plugin marketplace update ironmoose-marketplace
/plugin update adze-bonch@ironmoose-marketplace
```

## Credits

Built on [adze](https://github.com/4lt7ab/adze) by [@4lt7ab](https://github.com/4lt7ab).
