---
name: adze-bonch-setup
description: Configure or diagnose adze-bonch for Codex, including MCP reachability, native plugin wiring, bootstrap state, profiles, and safe upgrades. Use when the user asks to install, set up, repair, sync, or upgrade adze-bonch in Codex.
---

# adze-bonch setup

Read [the Codex runtime](../../runtime.md), especially its bootstrap safety rules.
Probe the adze MCP and inspect the existing `kind:bootstrap-state` document before
considering writes. Read and follow the canonical workflow at
[commands/setup.md](../../../commands/setup.md), adapting Claude-only paths and
discoverability steps to Codex. Treat an existing bootstrap as diagnosis or upgrade,
preserve all host-keyed install records, and do not rewrite canonical seeds only
because their stored plugin version differs.
