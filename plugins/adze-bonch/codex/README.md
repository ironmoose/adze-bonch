# adze-bonch for Codex

Native Codex entrypoints for the adze-bonch commands. The four skills in `skills/`
are thin wrappers around `../commands/`; [runtime.md](runtime.md) covers the
platform translations.

Register and install from the repository root:

```sh
codex plugin marketplace add .
codex plugin add adze-bonch@ironmoose-marketplace
```

Then use `$adze-bonch-main`, `$adze-bonch-status`, `$adze-bonch-save`, or
`$adze-bonch-tackle`.

## Optional: native role configs

`adapter.py` turns role cards into Codex agent TOMLs under a Codex home. Nothing in
the lean workflows needs them; they are there if you want `pulse-writer` (or a
companion plugin's roles) selectable by name.

```sh
python3 plugins/adze-bonch/codex/adapter.py install --codex-home ~/.codex
```

Pass `--companion-root /path/to/prove-it/plugins/prove-it` to include prove-it's
roles, and repeatable `--role-root PREFIX=PATH` for other local role plugins. Other
commands: `check`, `uninstall`, `inventory`; add `--dry-run` to preview. The
installer uses POSIX `fcntl` locking (Fedora/Linux and macOS). Generated TOMLs point
at absolute role-card paths, so rerun `install` after moving a checkout.

Tests: `python3 -m pytest plugins/adze-bonch/codex/test_adapter.py`.
