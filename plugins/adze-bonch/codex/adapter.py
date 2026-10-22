#!/usr/bin/env python3
"""Convert canonical Claude role cards into managed Codex agent TOML files."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import stat
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


RECEIPT_NAME = ".adze-bonch-agents.json"
NATIVE_NAME = re.compile(r"^[a-zA-Z0-9_]+$")
ROLE_NAME = re.compile(r"^[a-zA-Z0-9_-]+$")
ALLOWED_METADATA = {
    "name",
    "description",
    "model",
    "effort",
    "maxTurns",
    "tools",
    "permissionMode",
}
SUPPORTED_EFFORTS = {"low", "medium", "high", "xhigh", "max"}
ROLE_PREFIX = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
RESERVED_PREFIXES = {"adze_bonch", "prove_it"}


def read_role(path: Path) -> dict[str, str | int]:
    """Parse a role card's supported scalar frontmatter and instruction body."""
    role_path = Path(path)
    if role_path.is_symlink() or not role_path.is_file():
        raise ValueError(f"Role card must be a regular file: {role_path}")
    source_bytes = role_path.read_bytes()
    text = source_bytes.decode("utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError(f"Role card has no opening frontmatter delimiter: {role_path}")
    try:
        closing = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError(f"Role card has no closing frontmatter delimiter: {role_path}") from exc

    metadata: dict[str, str | int] = {}
    index = 1
    while index < closing:
        line_number = index + 1
        line = lines[index]
        if not line.strip() or line.lstrip().startswith("#"):
            index += 1
            continue
        if line.startswith((" ", "\t")) or ":" not in line:
            raise ValueError(f"Unsupported frontmatter at {role_path}:{line_number}")
        key, raw_value = line.split(":", 1)
        key = key.strip()
        if key not in ALLOWED_METADATA:
            raise ValueError(f"Unsupported role metadata {key!r} at {role_path}:{line_number}")
        if key in metadata:
            raise ValueError(f"Duplicate role metadata {key!r} at {role_path}:{line_number}")
        if key == "tools" and not raw_value.strip():
            tools, index = _parse_tool_list(lines, index + 1, closing, role_path)
            metadata[key] = ", ".join(tools)
            continue
        value = _parse_scalar(raw_value.strip(), role_path, line_number)
        metadata[key] = value
        index += 1

    for key in ("name", "description"):
        if not isinstance(metadata.get(key), str) or not metadata[key].strip():
            raise ValueError(f"Role card requires non-empty scalar {key!r}: {role_path}")
    name = metadata["name"]
    if not ROLE_NAME.fullmatch(name):
        raise ValueError(f"Role name contains unsupported characters: {name!r}")
    if "effort" in metadata:
        effort = metadata["effort"]
        if not isinstance(effort, str) or effort not in SUPPORTED_EFFORTS:
            raise ValueError(f"Unsupported role effort {effort!r}: {role_path}")
    if "maxTurns" in metadata:
        turns = metadata["maxTurns"]
        if not isinstance(turns, int) or turns < 1:
            raise ValueError(f"Role maxTurns must be a positive integer: {role_path}")
    for key in ("model", "tools", "permissionMode"):
        if key in metadata and (not isinstance(metadata[key], str) or not metadata[key].strip()):
            raise ValueError(f"Role metadata {key!r} must be a non-empty scalar: {role_path}")
    metadata["instructions"] = "\n".join(lines[closing + 1 :]).lstrip("\n")
    metadata["path"] = str(role_path.resolve())
    metadata["source_sha256"] = _sha256(source_bytes)
    return metadata


def collect_agents(
    core_root: Path,
    companion_root: Path | None = None,
    extra_roots: dict[str, Path] | None = None,
) -> dict[str, str]:
    """Build native Codex TOML for role cards found in the source checkouts."""
    core_path = Path(core_root)
    if core_path.is_symlink() or not core_path.is_dir():
        raise ValueError(f"Core plugin root must be a directory: {core_path}")
    runtime_source = core_path / "codex" / "runtime.md"
    if runtime_source.is_symlink():
        raise ValueError(f"Codex runtime guidance must not be a symlink: {runtime_source}")
    try:
        runtime_metadata = runtime_source.stat()
    except OSError as exc:
        raise ValueError(f"Codex runtime guidance is unavailable: {runtime_source}") from exc
    if not stat.S_ISREG(runtime_metadata.st_mode):
        raise ValueError(f"Codex runtime guidance must be a regular file: {runtime_source}")
    try:
        runtime_bytes = runtime_source.read_bytes()
    except OSError as exc:
        raise ValueError(f"Codex runtime guidance is unreadable: {runtime_source}") from exc
    runtime_path = runtime_source.resolve()
    runtime_hash = _sha256(runtime_bytes)
    roles = _role_files(core_path, "adze_bonch")
    if not roles:
        raise ValueError(f"Core role inventory is missing or empty: {core_path / 'agents'}")
    if companion_root is not None:
        companion_path = Path(companion_root)
        if companion_path.is_symlink() or not companion_path.is_dir():
            raise ValueError(f"Companion plugin root must be a directory: {companion_path}")
        companion_roles = _role_files(companion_path, "prove_it")
        if not companion_roles:
            raise ValueError(f"Companion role inventory is missing or empty: {companion_path / 'agents'}")
        _merge_roles(roles, companion_roles)
    if extra_roots is not None:
        if not isinstance(extra_roots, dict):
            raise ValueError("Extra role roots must be a prefix-to-path mapping")
        for prefix, root in extra_roots.items():
            _validate_role_prefix(prefix, allow_reserved=False)
            if not isinstance(root, (str, os.PathLike)):
                raise ValueError(f"Role root for prefix {prefix!r} must be a path")
            extra_path = Path(root)
            if extra_path.is_symlink() or not extra_path.is_dir():
                raise ValueError(f"Explicit role root for prefix {prefix!r} must be a directory: {extra_path}")
            extra_roles = _role_files(extra_path, prefix)
            if not extra_roles:
                raise ValueError(f"Explicit role inventory for prefix {prefix!r} is missing or empty: {extra_path / 'agents'}")
            _merge_roles(roles, extra_roles)

    agents: dict[str, str] = {}
    for native_name, role_path in sorted(roles.items()):
        role = read_role(role_path)
        source_name = str(role["name"])
        if source_name.replace("-", "_") != role_path.stem.replace("-", "_"):
            raise ValueError(f"Role name does not match its filename: {role_path}")
        effort = str(role.get("effort", "medium"))
        agents[native_name] = _render_agent(native_name, role, runtime_path, effort, runtime_hash)
    return agents


def install_agents(
    codex_home: Path,
    agents: dict[str, str],
    *,
    dry_run: bool = False,
) -> dict[str, object]:
    """Install the requested inventory after checking every ownership boundary."""
    home = Path(codex_home).expanduser().absolute()
    _validate_inventory(agents)
    if not agents:
        raise ValueError("Refusing to install an empty inventory; use uninstall to remove owned agents")
    with _directory_lock(home.parent):
        plan = _installation_plan(home, agents)
        if dry_run:
            return {"ok": True, "dry_run": True, "agents": sorted(agents), "remove": plan["remove"]}
        agent_dir = home / "agents"
        _mkdir_checked(agent_dir)
        for name, content in agents.items():
            _atomic_write(agent_dir / f"{name}.toml", content.encode("utf-8"))
        for name in plan["remove"]:
            (agent_dir / f"{name}.toml").unlink()
        receipt = _make_receipt(agents)
        _atomic_write(home / RECEIPT_NAME, _json_bytes(receipt))
    return {"ok": True, "dry_run": False, "agents": sorted(agents), "remove": plan["remove"]}


def check_agents(codex_home: Path, agents: dict[str, str]) -> dict[str, object]:
    """Compare installed files and ownership receipt with the requested inventory."""
    home = Path(codex_home).expanduser().absolute()
    _validate_inventory(agents)
    issues: list[str] = []
    _assert_path_chain(home, allow_missing=True)
    _assert_path_chain(home / "agents", allow_missing=True)
    receipt_path = home / RECEIPT_NAME
    _assert_path_chain(receipt_path, allow_missing=True)
    receipt = _read_receipt(receipt_path, required=False)
    if receipt is None:
        issues.append("ownership receipt is missing")
    else:
        expected_names = sorted(agents)
        owned_names = sorted(receipt["files"])
        if expected_names != owned_names:
            issues.append(f"inventory differs: expected {expected_names}, receipt has {owned_names}")
        for name, content in agents.items():
            target = home / "agents" / f"{name}.toml"
            _assert_path_chain(target, allow_missing=True)
            try:
                actual = target.read_bytes()
            except FileNotFoundError:
                issues.append(f"agent file is missing: {name}")
                continue
            actual_hash = _sha256(actual)
            if actual_hash != _sha256(content.encode("utf-8")):
                issues.append(f"agent file differs from source inventory: {name}")
            recorded = receipt["files"].get(name)
            if recorded != actual_hash:
                issues.append(f"agent file differs from ownership receipt: {name}")
    return {"ok": not issues, "issues": issues, "agents": sorted(agents)}


def uninstall_agents(codex_home: Path) -> dict[str, object]:
    """Remove only installed agent files whose contents still match the receipt."""
    home = Path(codex_home).expanduser().absolute()
    _assert_path_chain(home.parent, allow_missing=False)
    with _directory_lock(home.parent):
        _assert_path_chain(home, allow_missing=True)
        receipt_path = home / RECEIPT_NAME
        _assert_path_chain(receipt_path, allow_missing=True)
        receipt = _read_receipt(receipt_path, required=False)
        if receipt is None:
            return {"ok": True, "removed": []}
        agent_dir = home / "agents"
        _assert_path_chain(agent_dir, allow_missing=True)
        for name, expected_hash in receipt["files"].items():
            target = agent_dir / f"{name}.toml"
            _assert_path_chain(target, allow_missing=True)
            try:
                actual_hash = _sha256(target.read_bytes())
            except FileNotFoundError:
                continue
            if actual_hash != expected_hash:
                raise ValueError(f"Refusing to remove modified owned agent file: {target}")
        removed = []
        for name in receipt["files"]:
            target = agent_dir / f"{name}.toml"
            if target.exists():
                target.unlink()
                removed.append(name)
        receipt_path.unlink()
    return {"ok": True, "removed": removed}


def _parse_scalar(raw_value: str, path: Path, line_number: int) -> str | int:
    if not raw_value:
        raise ValueError(f"Empty frontmatter scalar at {path}:{line_number}")
    if raw_value.startswith('"'):
        try:
            value = json.loads(raw_value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid quoted scalar at {path}:{line_number}") from exc
        if not isinstance(value, str):
            raise ValueError(f"Frontmatter value must be a scalar at {path}:{line_number}")
        return value
    if raw_value.startswith("'"):
        if len(raw_value) < 2 or not raw_value.endswith("'"):
            raise ValueError(f"Invalid quoted scalar at {path}:{line_number}")
        return raw_value[1:-1].replace("''", "'")
    value = re.split(r"\s+#", raw_value, maxsplit=1)[0].strip()
    if not value or value in {"null", "~", "true", "false"}:
        raise ValueError(f"Frontmatter value must be a non-empty string at {path}:{line_number}")
    if re.fullmatch(r"[0-9]+", value):
        return int(value)
    return value


def _parse_tool_list(
    lines: list[str],
    start: int,
    closing: int,
    path: Path,
) -> tuple[list[str], int]:
    tools: list[str] = []
    index = start
    while index < closing:
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if not line.startswith((" ", "\t")):
            break
        match = re.fullmatch(r" {2,}-\s+(.+?)\s*", line)
        if match is None:
            if line.lstrip().startswith("#"):
                index += 1
                continue
            raise ValueError(f"Unsupported tools list at {path}:{index + 1}")
        tool = _parse_scalar(match.group(1), path, index + 1)
        if not isinstance(tool, str) or "," in tool:
            raise ValueError(f"Invalid tool name at {path}:{index + 1}")
        tools.append(tool)
        index += 1
    if not tools:
        raise ValueError(f"Tools list must contain at least one item at {path}:{start + 1}")
    return tools, index


def _role_files(root: Path, prefix: str) -> dict[str, Path]:
    agents_dir = root / "agents"
    if agents_dir.is_symlink():
        raise ValueError(f"Role source directory cannot be a symlink: {agents_dir}")
    if not agents_dir.exists():
        return {}
    if not agents_dir.is_dir():
        raise ValueError(f"Role source path must be a directory: {agents_dir}")
    roles: dict[str, Path] = {}
    for path in sorted(agents_dir.iterdir()):
        if path.suffix != ".md":
            continue
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Role card must be a regular file: {path}")
        if not ROLE_NAME.fullmatch(path.stem):
            raise ValueError(f"Role filename contains unsupported characters: {path.name}")
        native_name = f"{prefix}_{path.stem.replace('-', '_')}"
        if not NATIVE_NAME.fullmatch(native_name):
            raise ValueError(f"Unsafe native agent name: {native_name!r}")
        if native_name in roles:
            raise ValueError(f"Role filenames map to the same native agent name: {native_name}")
        roles[native_name] = path
    return roles


def _validate_role_prefix(prefix: str, *, allow_reserved: bool) -> None:
    if not isinstance(prefix, str) or not ROLE_PREFIX.fullmatch(prefix):
        raise ValueError(f"Unsafe role namespace prefix: {prefix!r}")
    if not allow_reserved and prefix in RESERVED_PREFIXES:
        raise ValueError(f"Role namespace prefix is reserved: {prefix}")


def _merge_roles(target: dict[str, Path], incoming: dict[str, Path]) -> None:
    duplicate_names = sorted(set(target) & set(incoming))
    if duplicate_names:
        raise ValueError(f"Duplicate native agent names across role roots: {', '.join(duplicate_names)}")
    target.update(incoming)


def _render_agent(
    name: str,
    role: dict[str, str | int],
    runtime_path: Path,
    effort: str,
    runtime_hash: str | None,
) -> str:
    card_path = str(role["path"])
    advisory = [
        "Read the canonical role card at this absolute path before acting:",
        card_path,
        "Then read the Codex runtime guidance at this absolute path:",
        str(runtime_path),
        "The canonical role card is the source for the role's scope and instructions.",
        "Translate Claude communication patterns to Codex; delegated reports return as final responses.",
        f"Source role SHA-256: {role['source_sha256']}.",
    ]
    if runtime_hash is not None:
        advisory.append(f"Codex runtime SHA-256: {runtime_hash}.")
    for key in ("maxTurns", "tools", "permissionMode"):
        if key in role:
            label = {"maxTurns": "maxTurns", "tools": "declared tools", "permissionMode": "declared permissionMode"}[key]
            advisory.append(f"Source {label}: {role[key]} (advisory; Codex does not enforce it here).")
    fields = {
        "name": name,
        "description": str(role["description"]),
        "developer_instructions": "\n".join(advisory),
        "model": "gpt-6-luna",
        "model_reasoning_effort": effort,
    }
    return "".join(f"{key} = {json.dumps(value, ensure_ascii=False)}\n" for key, value in fields.items())


def _validate_inventory(agents: dict[str, str]) -> None:
    if not isinstance(agents, dict):
        raise ValueError("Agent inventory must be a mapping")
    for name, content in agents.items():
        if not isinstance(name, str) or not NATIVE_NAME.fullmatch(name):
            raise ValueError(f"Unsafe native agent filename: {name!r}")
        if name in {".", ".."} or not isinstance(content, str):
            raise ValueError(f"Invalid agent configuration for {name!r}")


def _installation_plan(home: Path, agents: dict[str, str]) -> dict[str, list[str]]:
    _assert_path_chain(home, allow_missing=True)
    agent_dir = home / "agents"
    _assert_path_chain(agent_dir, allow_missing=True)
    receipt_path = home / RECEIPT_NAME
    _assert_path_chain(receipt_path, allow_missing=True)
    receipt = _read_receipt(receipt_path, required=False)
    previous = {} if receipt is None else receipt["files"]
    for name, content in agents.items():
        target = agent_dir / f"{name}.toml"
        _assert_path_chain(target, allow_missing=True)
        if target.exists():
            old_hash = previous.get(name)
            if old_hash is None:
                raise ValueError(f"Refusing to overwrite unmanaged agent file: {target}")
            if _sha256(target.read_bytes()) != old_hash:
                raise ValueError(f"Refusing to overwrite modified owned agent file: {target}")
    remove = sorted(set(previous) - set(agents))
    for name in remove:
        target = agent_dir / f"{name}.toml"
        _assert_path_chain(target, allow_missing=True)
        if target.exists() and _sha256(target.read_bytes()) != previous[name]:
            raise ValueError(f"Refusing to remove modified owned agent file: {target}")
    return {"remove": remove}


def _read_receipt(path: Path, *, required: bool) -> dict[str, object] | None:
    if not path.exists():
        if required:
            raise ValueError(f"Ownership receipt is missing: {path}")
        return None
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Ownership receipt must be a regular file: {path}")
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(f"Ownership receipt is invalid: {path}") from exc
    if not isinstance(receipt, dict) or receipt.get("version") != 1 or not isinstance(receipt.get("files"), dict):
        raise ValueError(f"Ownership receipt has an unsupported shape: {path}")
    files = receipt["files"]
    for name, digest in files.items():
        if not isinstance(name, str) or not NATIVE_NAME.fullmatch(name):
            raise ValueError(f"Ownership receipt contains an unsafe name: {name!r}")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError(f"Ownership receipt contains an invalid hash for {name!r}")
    return receipt


def _make_receipt(agents: dict[str, str]) -> dict[str, object]:
    return {"version": 1, "files": {name: _sha256(content.encode("utf-8")) for name, content in sorted(agents.items())}}


def _json_bytes(value: dict[str, object]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _assert_path_chain(path: Path, *, allow_missing: bool) -> None:
    absolute = Path(os.path.abspath(path))
    parts = absolute.parents[::-1] + (absolute,)
    for part in parts:
        try:
            metadata = part.lstat()
        except FileNotFoundError:
            if not allow_missing:
                raise ValueError(f"Required path does not exist: {part}")
            continue
        if stat.S_ISLNK(metadata.st_mode):
            raise ValueError(f"Symlinked path is not allowed: {part}")


def _mkdir_checked(path: Path) -> None:
    _assert_path_chain(path, allow_missing=True)
    path.mkdir(parents=True, exist_ok=True)
    if path.is_symlink() or not path.is_dir():
        raise ValueError(f"Directory path is unsafe: {path}")


def _atomic_write(path: Path, content: bytes) -> None:
    _assert_path_chain(path.parent, allow_missing=False)
    _assert_path_chain(path, allow_missing=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temp_path, 0o600)
        os.replace(temp_path, path)
    except OSError as exc:
        cleanup_error = None
        try:
            temp_path.unlink(missing_ok=True)
        except OSError as error:
            cleanup_error = error
        if cleanup_error is not None:
            raise OSError(f"Could not clean temporary file {temp_path}: {cleanup_error}") from cleanup_error
        raise OSError(f"Could not atomically write {path}: {exc}") from exc


@contextmanager
def _directory_lock(directory: Path) -> Iterator[None]:
    _assert_path_chain(directory, allow_missing=False)
    if not directory.is_dir():
        raise ValueError(f"Lock parent must be a directory: {directory}")
    descriptor = os.open(directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage native Codex agent configs for adze-bonch.")
    parser.add_argument("command", choices=("inventory", "install", "check", "uninstall"))
    parser.add_argument("--codex-home", type=Path, default=Path(os.environ.get("CODEX_HOME", "~/.codex")).expanduser())
    parser.add_argument("--companion-root", type=Path)
    parser.add_argument("--role-root", action="append", default=[], metavar="PREFIX=PATH")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def _parse_role_roots(specifications: list[str]) -> dict[str, Path]:
    roots: dict[str, Path] = {}
    for specification in specifications:
        if "=" not in specification:
            raise ValueError(f"Role root must use PREFIX=PATH syntax: {specification!r}")
        prefix, raw_path = specification.split("=", 1)
        _validate_role_prefix(prefix, allow_reserved=False)
        if prefix in roots:
            raise ValueError(f"Role root prefix was supplied more than once: {prefix}")
        if not raw_path:
            raise ValueError(f"Role root path is empty for prefix {prefix!r}")
        roots[prefix] = Path(raw_path)
    return roots


def main(argv: list[str] | None = None) -> int:
    """Run the adapter command line interface."""
    args = _parser().parse_args(argv)
    core_root = Path(__file__).resolve().parent.parent
    try:
        if args.command == "uninstall":
            result: object = uninstall_agents(args.codex_home)
        else:
            extra_roots = _parse_role_roots(args.role_root)
            inventory = collect_agents(core_root, args.companion_root, extra_roots)
            if args.command == "inventory":
                result = {"ok": True, "agents": sorted(inventory), "configs": inventory}
            elif args.command == "install":
                result = install_agents(args.codex_home, inventory, dry_run=args.dry_run)
            else:
                result = check_agents(args.codex_home, inventory)
        print(json.dumps(result, indent=2, sort_keys=True))
        if isinstance(result, dict) and result.get("ok") is False:
            return 1
        return 0
    except (OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
