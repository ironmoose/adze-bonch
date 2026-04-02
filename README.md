# marketplace

Personal Claude Code plugin marketplace. Install once, get all the plugins.

## Quick install

```bash
claude plugin marketplace add paulCodes/marketplace
claude plugin install tab-workflow
```

## Plugins

| Plugin | Commands | Description |
|--------|----------|-------------|
| **tab-workflow** | `/tab-brainstorming`, `/tab-refinement`, `/tab-work`, `/tab-verify`, `/tab-feedback`, `/listen` | Tab for Projects workflow — brainstorm, refine, implement, verify, feedback. Includes planner, QA, and documenter agents. |

More plugins coming soon.

See each plugin's README for full documentation:
- [tab-workflow](plugins/tab/README.md)

## Credits

The tab-workflow plugin is built on [Tab for Projects](https://github.com/4lt7ab/Tab) by [@4lt7ab](https://github.com/4lt7ab). Tab provides the MCP server and project management primitives — this plugin adds workflow automation on top.

## For Cursor / Copilot users

Clone the repo and copy the command files into your editor's configuration:

```bash
git clone git@github.com:paulCodes/marketplace.git
# Copy plugins/tab/commands/*.md into your editor's command directory
```
