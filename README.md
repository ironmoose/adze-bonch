# paulCodes Marketplace

Personal Claude Code plugin marketplace. Install the marketplace once, then pick the plugins you want.

## Plugins

| Plugin | Command | What it does |
|--------|---------|--------------|
| **[tab-workflow](plugins/tab/README.md)** | `/tab-workflow:main` | Project lifecycle manager built on [Tab for Projects](https://github.com/4lt7ab/Tab). Brainstorm, refine, implement, verify, and track progress with multi-agent quality gates. All state persists to Tab, so crashed sessions pick up where they left off. |
| **[pr-review](plugins/pr-review/README.md)** | `/pr-review:review` | Multi-agent PR review pipeline. 5-7 specialized agents review in parallel, findings walked through one at a time, comments posted with human voice. Optional Tab integration. |

## Install

```
# Add the marketplace
/plugin marketplace add paulCodes/marketplace

# Install a plugin
/plugin install tab-workflow@paulCodes-marketplace
```

tab-workflow requires a running [Tab for Projects](https://github.com/4lt7ab/Tab) MCP server.

## What's New in v2.0

- **Quality Gates**: Commit gate checks that all review findings, verification failures, and tasks are resolved before allowing a commit.
- **Workflow Routing**: The `/tab-workflow:main` router detects intent and dispatches to the appropriate pipeline (brainstorm, refine, implement, verify). PR review intent routes to the pr-review plugin.
- **pr-review plugin**: PR reviews are now a standalone plugin (`/pr-review:review`). Multi-agent review pipeline with 5-7 parallel specialist agents, voice-controlled comment posting, and optional Tab integration.

## Update

```
# Pull latest plugin versions
/plugin marketplace update paulCodes-marketplace

# Update a specific plugin
/plugin update tab-workflow@paulCodes-marketplace
```

## For other editors

The command `.md` files are portable. Agents and rules are Claude Code-specific.

```bash
git clone git@github.com:paulCodes/marketplace.git
# Copy plugins/tab/commands/*.md into your editor's command directory
```

## Credits

Built on [Tab for Projects](https://github.com/4lt7ab/Tab) by [@4lt7ab](https://github.com/4lt7ab).
