# adze-bonch: plugin development context

For developing the plugin itself; it does not affect installed users.

## What this plugin is

Since 0.8.0, two commands and one agent: `/adze-bonch:save` (decision capture, Pulse refresh, Session Progress Log append), `/adze-bonch:status` (read-only snapshot), and `agents/pulse-writer.md`. The orchestration (main, tackle, setup, scrum-master, researcher, implementer, test-writer, discipline seeds, conventions overlays, voice templates, Codex adapters) was retired. It lives in git history at `17544f8` (0.7.1). Do not reintroduce a mandatory entry command, discipline-doc load, or review gate.

## Hard rules

1. **Edit this source tree only.** Never edit `~/.claude/plugins/cache/`. Bump `version` in both `.claude-plugin/plugin.json` and the root `.claude-plugin/marketplace.json` on every change, or installs never update.
2. **No em-dashes in prose.** Use commas, semicolons, parentheses, or periods.
3. **Tags only attach to documents in adze.** Projects and tasks cannot be tagged.
4. **`documents_update` and `projects_update` replace the whole `context`.** Re-read before writing if the last read is over 60s old. For the append-only Session Progress Log use `documents_append`.
5. **Pulse lookup:** `tags_list(q="kind:pulse")`, `documents_list(tag_id)`, cross-checked with `documents_for_project`. One pulse per project; halt if there are two.

## Commit style

Imperative, prefixed: `adze-bonch: <what>`.
