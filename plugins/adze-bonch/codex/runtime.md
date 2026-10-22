# Codex runtime adapter

The canonical workflows stay in the adze-bonch source tree:

- `commands/` holds the one maintained copy of each workflow (`main`, `status`, `save`, `tackle`).
- `agents/pulse-writer.md` is the only adze-bonch role card.

Resolve the adze-bonch source root from the checkout containing this file. The
checkout must stay readable while workflows run; if a required file is missing, stop
and name the path. The wrappers in `codex/skills/` are routing only, not alternate
prompt bodies.

## Runtime translations

- Treat `mcp__adze__*` calls in canonical files as the matching adze MCP tools.
  Discover deferred tools from `ALL_TOOLS` and invoke them through the current bridge.
- Translate `/adze-bonch:main`, `:status`, `:save`, and `:tackle` to the matching
  `$adze-bonch-*` skill. When a workflow routes to another, read that command and
  continue in the same conversation.
- Claude skills named in `tackle` (`tdd`, `diagnosing-bugs`, `grilling`,
  `code-review`) come from the mattpocock-skills plugin. Use the Codex equivalent if
  one is installed; otherwise follow the approach the step describes directly.
- `/prove-it:review` and `/prove-it:follow-up` (only for `tackle --prove`) come from
  the separate prove-it checkout. If it is not available, say so and fall back to a
  single review pass; never claim a repro-verified review that did not run.
- For the pulse-writer, gather its inputs in the parent first and include the full
  role card plus inputs in one self-contained dispatch, with `gpt-6-luna` and
  `fork_turns: "none"`. Its report returns normally; do not recreate Claude's
  `SendMessage` pattern. Drafting the Pulse inline is also fine.
- Replace `AskUserQuestion` with a concise question in the conversation.
- Read applicable target-repository `AGENTS.md` files, and `CLAUDE.md` when present.
  Codex instructions win on direct conflicts.
- Never change Claude configuration as a side effect of a Codex workflow.

## Role adapter

`adapter.py` converts role cards to native Codex agent TOMLs (name, description,
developer instructions, model, effort). Source `maxTurns`, tools, and sandbox
fields are advisory text; Codex does not enforce them. Installing roles is optional;
no lean workflow requires a named role.
