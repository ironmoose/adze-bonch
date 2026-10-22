# adze-bonch: plugin development context

For developing the plugin itself; it does not affect installed users.

## What this plugin is

Since the 0.8.0 lean rework: four commands (`save`, `status`, `main`, `tackle`), one agent (`agents/pulse-writer.md`), one skill (`subagent-edit-verification`), and Codex wrappers in `codex/`. The commands work in the main conversation and hand test-first work, bug diagnosis, planning interviews, and review to mattpocock-skills (`tdd`, `diagnosing-bugs`, `grilling`, `code-review`). The repro-verified review lives in the separate prove-it plugin and is opt-in through `tackle --prove`. The pre-rework pipeline is in git history at `17544f8` (0.7.1).

Keep it lean: no mandatory entry command, no discipline doc loaded from adze, no forced sub-agent dispatch, no review gate on every change. adze-bonch owns the adze binding (decisions, Pulse, session log, task status); leave generic engineering workflow to other skills.

## Hard rules

1. **Edit this source tree only.** Never edit `~/.claude/plugins/cache/`. Bump `version` in `.claude-plugin/plugin.json`, the root `.claude-plugin/marketplace.json`, and `.codex-plugin/plugin.json` on every change, or installs never update.
2. **No em dashes in prose.** Use commas, semicolons, parentheses, or periods.
3. **Tags only attach to documents in adze.** Projects and tasks cannot be tagged.
4. **`documents_update` and `projects_update` replace the whole `context`.** Re-read before writing if the last read is over 60s old. For the append-only Session Progress Log use `documents_append`.
5. **Pulse lookup:** `tags_list(q="kind:pulse")`, `documents_list(tag_id)`, cross-checked with `documents_for_project`. One pulse per project; halt if there are two.
6. **Codex wrappers stay thin.** `codex/skills/*/SKILL.md` point at `commands/`; never copy a command body into them.

## Checks

- `python3 -m pytest plugins/adze-bonch/codex/test_adapter.py`
- `claude plugin validate .` from the repo root.

## Commit style

Imperative, prefixed: `adze-bonch: <what>`.
