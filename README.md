# paulCodes Marketplace

Personal Claude Code plugin marketplace. Install the marketplace once, then pick the plugins you want.

## Plugins

| Plugin | Command | What it does |
|--------|---------|--------------|
| **[tab-workflow](plugins/tab/README.md)** | `/tab` | Project lifecycle manager built on [Tab for Projects](https://github.com/4lt7ab/Tab). Brainstorm, refine, implement, verify, and track progress. All state persists to Tab, so crashed sessions pick up where they left off. |

## Install

```bash
# Add the marketplace
claude plugin marketplace add paulCodes/marketplace

# Install a plugin
claude plugin install tab-workflow
```

tab-workflow requires a running [Tab for Projects](https://github.com/4lt7ab/Tab) MCP server.

## Update

```bash
# Pull latest plugin versions
claude plugin marketplace update paulCodes-marketplace

# Update a specific plugin
claude plugin update tab-workflow
```

## For other editors

The command `.md` files are portable. Agents and rules are Claude Code-specific.

```bash
git clone git@github.com:paulCodes/marketplace.git
# Copy plugins/tab/commands/*.md into your editor's command directory
```

## Credits

Built on [Tab for Projects](https://github.com/4lt7ab/Tab) by [@4lt7ab](https://github.com/4lt7ab).
