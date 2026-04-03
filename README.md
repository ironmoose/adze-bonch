# paulCodes Marketplace

Personal Claude Code plugin marketplace. Install once, get all the plugins.

## Quick Install

```bash
claude plugin marketplace add paulCodes/marketplace
claude plugin install tab-workflow
```

## Plugins

| Plugin | Entry Point | Description |
|--------|-------------|-------------|
| **tab-workflow** | `/tab` | Tab for Projects workflow — one command to brainstorm, refine, implement, verify, and save. Always Tab-first. |

See the [tab-workflow README](plugins/tab/README.md) for full documentation.

## How It Works

The tab-workflow plugin turns [Tab for Projects](https://github.com/4lt7ab/Tab) into a complete project lifecycle manager for Claude Code. You say `/tab` and the system figures out what you need:

```
/tab I want to build a CLI tool     → brainstorm flow
/tab work on doot                   → implementation flow
/tab verify                         → lint/test/fix loop
/tab save                           → save progress to Tab
/tab                                → show project status
```

Everything is persisted to Tab — projects, tasks, KB documents, session progress logs. If your session crashes, Tab has the full state to resume from.

## Credits

Built on [Tab for Projects](https://github.com/4lt7ab/Tab) by [@4lt7ab](https://github.com/4lt7ab). Tab provides the MCP server and project management primitives — this plugin adds workflow automation on top.

## For Cursor / Copilot Users

The command `.md` files are portable to other editors. Agents and rules are Claude Code-specific.

```bash
git clone git@github.com:paulCodes/marketplace.git
# Copy plugins/tab/commands/*.md into your editor's command directory
# Note: Full functionality (agents, rules, sub-agent dispatch) requires Claude Code
```
