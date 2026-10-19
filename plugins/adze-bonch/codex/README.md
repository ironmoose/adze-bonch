# adze-bonch for Codex

This directory provides native Codex entrypoints for the existing adze-bonch source.
The five skills are thin wrappers around the canonical commands in `../commands/`;
the adapter does not keep a second copy of their prompts. The canonical role cards in
`../agents/` and the separately configured prove-it checkout remain the source for
delegated instructions.

The repository root includes a local marketplace entry. From the repository root,
register and install it with:

```sh
codex plugin marketplace add .
codex plugin add adze-bonch@ironmoose-marketplace
```

## Install role configurations

Run the adapter from a source checkout. It discovers adze-bonch sources relative to
its own location and requires the companion prove-it plugin path explicitly. The
installer uses POSIX `fcntl` file locking and is supported on Fedora/Linux and
macOS. Windows can use native Codex role configuration, but this installer is not
supported there.

```sh
python3 plugins/adze-bonch/codex/adapter.py install \
  --codex-home ~/.codex \
  --companion-root /path/to/prove-it/plugins/prove-it
```

The default inventory is built from the adze-bonch core and the configured prove-it
companion roles. To add explicitly selected local role plugins, pass repeatable
`--role-root PREFIX=PATH` options. Each root contributes its `agents/*.md` cards
under the given namespace; the adapter does not search Claude plugin directories or
load extra roots implicitly.

```sh
python3 plugins/adze-bonch/codex/adapter.py install \
  --codex-home ~/.codex \
  --companion-root /path/to/prove-it/plugins/prove-it \
  --role-root custom=/path/custom-role-plugin
```

Pass the same role-root option to `check` and `inventory` when comparing or listing
that expanded set. Optional local roots can add user-specific roles without copying
their role-card text into this repository.

Add `--dry-run` to preview the install. The other commands are `check`,
`uninstall`, and `inventory`; pass the same `--companion-root` and `--codex-home`
options to each. `check` compares the installed agent files and receipt with the
current source inventory. `uninstall` removes only files the adapter owns and refuses
to remove modified files. `inventory` prints the roles the adapter can build.

The adapter generates TOML role configurations under the chosen Codex home. Their
developer instructions point to absolute canonical role-card paths. Keep this
checkout and the companion prove-it checkout accessible while using the roles. After
moving either checkout or changing source role cards, rerun `install` with the
updated paths, then run `check` to confirm inventory parity. The adapter does not
vendor prove-it.

During Codex setup, first probe adze MCP and inspect the existing bootstrap-state.
When configuring specialized native roles, then run `install` and `check` with the
explicit companion path above. Role installation does not replace the bootstrap
probe or authorize bootstrap or seed writes.

## Runtime behavior

Use `$adze-bonch-main`, `$adze-bonch-status`, `$adze-bonch-save`,
`$adze-bonch-setup`, or `$adze-bonch-tackle`. Each wrapper points to its canonical
command and loads `codex/runtime.md` for platform translations. The tackle
orchestrator preserves canonical scopes, TDD sequencing, the full required reviewer
panel, executable repro verification, confirm-fix, and regression-test promotion.
The parent remains the orchestrator and does not implement code or tests.

Generated TOMLs are valid native Codex CLI configurations where named role selection
is available. A fresh CLI canary dispatched `adze_bonch_scrum_master` with Luna,
medium effort, and `fork_turns: "none"` and returned a final report, though the JSON
result did not independently expose child model metadata. The current desktop
collaboration bridge has no named-agent selector; use the exact source card with
explicit Luna, source effort, and `fork_turns: "none"` there. The generated agent
model is `gpt-6-luna`; the parent conversation's model remains unchanged. `maxTurns`,
tools, and sandbox metadata are advisory workflow constraints and are not enforced
by Codex. Delegated reports return normally to the parent. At longer-role handoff
boundaries, include completed work, remaining work, and verification evidence.

One-turn source roles receive their complete inputs from the parent before dispatch.
Longer source turn budgets guide bounded stage work and are not enforced by Codex.
When resuming an already approved plan, continue from that plan without repeating
its interview; ask again only for a new or unresolved decision.

The quality gate needs the separately installed `prove-it-gate` CLI when available.
Codex edits are not mechanically blocked by Claude hooks, so gate discipline is
workflow-enforced. Repro verification and repro confirmation remain mandatory even
when the CLI is missing.

For setup, inspect the existing bootstrap-state first. It is shared across hosts and
must retain all entries and machine-specific notes. See [runtime.md](runtime.md) for
the operating rules and bootstrap safety details.
