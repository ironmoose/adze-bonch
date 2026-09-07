# adze-bonch

This repo is a Claude Code plugin marketplace that ships one plugin: `adze-bonch`, workflow discipline for [adze](https://github.com/4lt7ab/adze) projects. Install the marketplace once, then install the plugin.

## Plugin

| Plugin | Command | What it does |
|--------|---------|--------------|
| **[adze-bonch](plugins/adze-bonch/README.md)** | `/adze-bonch:main` | Workflow discipline for [adze](https://github.com/4lt7ab/adze) projects. Setup wizard, decision persistence, the Project Pulse session-resume trailhead, and a full tackle lifecycle: 12 specialized agents, TDD by default, TypeScript/Python conventions overlays, a parallel quality gate, and a repro-verify step that proves or refutes findings before they are fixed. |

## Retired plugins

`tab-workflow` was the original project lifecycle manager, built on [Tab for Projects](https://github.com/4lt7ab/Tab). It is retired and superseded by `adze-bonch`, which does the same job on top of [adze](https://github.com/4lt7ab/adze). If you were running `tab-workflow`, move to `adze-bonch`. The plugin has been removed from the repo; its history is still in git if anyone needs it.

`pr-review` also shipped from this repo and has been retired. It is no longer part of this repo.

## Install

```
# Add the marketplace
/plugin marketplace add ironmoose/adze-bonch

# Install the plugin
/plugin install adze-bonch@ironmoose-marketplace
```

adze-bonch requires a running [adze](https://github.com/4lt7ab/adze) MCP server.

## Update

```
# Pull the latest plugin version
/plugin marketplace update ironmoose-marketplace

# Update the plugin
/plugin update adze-bonch@ironmoose-marketplace
```

## For other editors

The command `.md` files are portable. Agents and rules are Claude Code-specific.

```bash
git clone git@github.com:ironmoose/adze-bonch.git
# Copy plugins/adze-bonch/commands/*.md into your editor's command directory
```

Plugin directory is `plugins/adze-bonch`.

## Credits

Built on [adze](https://github.com/4lt7ab/adze), and previously on [Tab for Projects](https://github.com/4lt7ab/Tab) for the retired `tab-workflow`, both by [@4lt7ab](https://github.com/4lt7ab).
