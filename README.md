# adze-bonch

A Claude Code plugin that keeps projects tracked in [adze](https://github.com/4lt7ab/adze) disciplined: decisions are written to adze as they happen, each project keeps a one-document resume trail, and tasks run through a review gate whose findings are proven by reproduction before they get fixed.

This repository is the plugin's marketplace. The full documentation, including setup, the command list, and every step of the tackle lifecycle, lives in the plugin's own README:

**[plugins/adze-bonch/README.md](plugins/adze-bonch/README.md)**

## Install

```
/plugin marketplace add ironmoose/adze-bonch
/plugin install adze-bonch@ironmoose-marketplace
```

adze-bonch needs a running [adze](https://github.com/4lt7ab/adze) MCP server. The [plugin README](plugins/adze-bonch/README.md) has the server config.

## Update

```
/plugin marketplace update ironmoose-marketplace
/plugin update adze-bonch@ironmoose-marketplace
```

## Credits

Built on [adze](https://github.com/4lt7ab/adze) by [@4lt7ab](https://github.com/4lt7ab).

---

Earlier versions of this repository also shipped `tab-workflow` and `pr-review`. Both are retired; their history is in git.
