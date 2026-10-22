"""Test native Codex agent conversion and installation."""

import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import tomllib
from unittest.mock import patch

from adapter import (
    check_agents,
    collect_agents,
    install_agents,
    main,
    read_role,
    uninstall_agents,
)


class AdapterTests(unittest.TestCase):
    """Verify role conversion and safe installation behavior."""

    def setUp(self) -> None:
        """Create isolated role sources and a Codex home."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.core = self.root / "core"
        self.companion = self.root / "companion"
        self.home = self.root / "codex"
        self.core.mkdir()
        self.companion.mkdir()
        runtime = self.core / "codex" / "runtime.md"
        runtime.parent.mkdir()
        runtime.write_text("Runtime guidance for adapter tests.\n", encoding="utf-8")

    def tearDown(self) -> None:
        """Remove the temporary fixture tree."""
        self.temp_dir.cleanup()

    def write_role(
        self,
        root: Path,
        filename: str,
        *,
        name: str,
        effort: str = "high",
        max_turns: int = 12,
        tools: str = "Read, Write",
    ) -> Path:
        """Write a small role definition and return its path."""
        path = root / "agents" / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "---\n"
            f"name: {name}\n"
            f"description: Description for {name}\n"
            "model: sonnet\n"
            f"effort: {effort}\n"
            f"maxTurns: {max_turns}\n"
            f"tools: {tools}\n"
            "---\n\n"
            f"# {name}\n\nRole instructions for {name}.\n",
            encoding="utf-8",
        )
        return path

    def test_should_read_role_metadata_and_instructions(self) -> None:
        role_path = self.write_role(self.core, "tester.md", name="tester")

        role = read_role(role_path)

        self.assertEqual(role["name"], "tester")
        self.assertEqual(role["description"], "Description for tester")
        self.assertEqual(role["effort"], "high")
        self.assertEqual(role["maxTurns"], 12)
        self.assertEqual(role["tools"], "Read, Write")

    def test_should_normalize_yaml_tools_list_and_preserve_xhigh_effort(self) -> None:
        """Keep canonical list-form tools and effort values in the parsed role."""
        role_path = self.core / "agents" / "implementer.md"
        role_path.parent.mkdir()
        role_path.write_text(
            "---\n"
            "name: implementer\n"
            "description: Implements approved changes\n"
            "model: sonnet\n"
            "effort: xhigh\n"
            "maxTurns: 200\n"
            "tools:\n"
            "  - Read\n"
            "  - Write\n"
            "  - Edit\n"
            "---\n\n"
            "Canonical implementer instructions.\n",
            encoding="utf-8",
        )

        role = read_role(role_path)

        self.assertEqual(role["tools"], "Read, Write, Edit")
        self.assertEqual(role["effort"], "xhigh")

    def test_should_retain_xhigh_effort_in_native_agent_config(self) -> None:
        """Preserve source effort when converting canonical roles to TOML."""
        self.write_role(self.core, "implementer.md", name="implementer", effort="xhigh")

        agent = tomllib.loads(collect_agents(self.core)["adze_bonch_implementer"])

        self.assertEqual(agent["model_reasoning_effort"], "xhigh")

    def test_should_collect_roles_from_explicit_extra_roots(self) -> None:
        """Add explicitly configured role inventories without implicit sources."""
        self.write_role(self.core, "writer.md", name="writer")
        self.write_role(self.companion, "reviewer.md", name="reviewer")
        personal = self.root / "personal"
        simplifier = self.root / "simplifier"
        self.write_role(personal, "implementer.md", name="implementer")
        self.write_role(simplifier, "code-simplifier.md", name="code-simplifier")
        extra_roots = {"personal": personal, "simplifier": simplifier}

        default_agents = collect_agents(self.core, self.companion)
        agents = collect_agents(self.core, self.companion, extra_roots)

        self.assertEqual(
            set(default_agents),
            {"adze_bonch_writer", "prove_it_reviewer"},
        )
        self.assertEqual(
            set(agents),
            {
                "adze_bonch_writer",
                "prove_it_reviewer",
                "personal_implementer",
                "simplifier_code_simplifier",
            },
        )

    def test_should_fail_closed_for_missing_explicit_extra_role_root(self) -> None:
        """Do not silently omit a configured role inventory."""
        self.write_role(self.core, "writer.md", name="writer")

        with self.assertRaises((ValueError, RuntimeError, OSError)):
            collect_agents(self.core, extra_roots={"personal": self.root / "missing-personal"})

    def test_should_fail_closed_for_empty_explicit_extra_role_root(self) -> None:
        """Do not treat an empty configured role inventory as a valid source."""
        self.write_role(self.core, "writer.md", name="writer")
        empty_personal = self.root / "personal"
        (empty_personal / "agents").mkdir(parents=True)

        with self.assertRaises((ValueError, RuntimeError, OSError)):
            collect_agents(self.core, extra_roots={"personal": empty_personal})

    def test_should_parse_repeatable_cli_role_roots(self) -> None:
        """Pass each explicit root prefix and path into collection."""
        personal = self.root / "personal"
        simplifier = self.root / "simplifier"
        (personal / "agents").mkdir(parents=True)
        (simplifier / "agents").mkdir(parents=True)
        expected_roots = {"personal": personal, "simplifier": simplifier}
        stdout = StringIO()

        with patch("adapter.collect_agents", return_value={}) as collect_agents_mock, redirect_stdout(stdout):
            status = main(
                [
                    "inventory",
                    "--role-root",
                    f"personal={personal}",
                    "--role-root",
                    f"simplifier={simplifier}",
                ]
            )

        self.assertEqual(status, 0)
        self.assertIn(expected_roots, collect_agents_mock.call_args.args + tuple(collect_agents_mock.call_args.kwargs.values()))

    def test_should_uninstall_without_collecting_role_sources(self) -> None:
        """Remove a valid receipt and agent after runtime guidance disappears."""
        install_agents(self.home, {"adze_bonch_tester": 'name = "tester"\n'})
        receipt = self.home / ".adze-bonch-agents.json"
        owned_agent = self.home / "agents" / "adze_bonch_tester.toml"
        runtime = self.core / "codex" / "runtime.md"
        runtime.unlink()
        adapter_source = self.core / "codex" / "adapter.py"
        stdout, stderr = StringIO(), StringIO()

        with (
            patch("adapter.__file__", str(adapter_source)),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            status = main(["uninstall", "--codex-home", str(self.home)])

        self.assertEqual(status, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertIn('"ok": true', stdout.getvalue())
        self.assertFalse(receipt.exists())
        self.assertFalse(owned_agent.exists())

    def test_should_reject_role_missing_required_metadata(self) -> None:
        role_path = self.core / "agents" / "broken.md"
        role_path.parent.mkdir()
        role_path.write_text("---\nname: broken\n---\nInstructions\n", encoding="utf-8")

        with self.assertRaises((ValueError, RuntimeError, OSError)):
            read_role(role_path)

    def test_should_collect_native_toml_for_core_and_companion_roles(self) -> None:
        self.write_role(self.core, "task-runner.md", name="task-runner", effort="low", max_turns=4)
        self.write_role(self.companion, "edge-checker.md", name="edge-checker", effort="high", max_turns=31)

        agents = collect_agents(self.core, self.companion)

        self.assertEqual(set(agents), {"adze_bonch_task_runner", "prove_it_edge_checker"})
        core_agent = tomllib.loads(agents["adze_bonch_task_runner"])
        companion_agent = tomllib.loads(agents["prove_it_edge_checker"])
        self.assertEqual(core_agent["name"], "adze_bonch_task_runner")
        self.assertEqual(core_agent["model"], "gpt-6-luna")
        self.assertEqual(core_agent["model_reasoning_effort"], "low")
        self.assertEqual(companion_agent["model_reasoning_effort"], "high")
        self.assertIn(str((self.core / "agents" / "task-runner.md").resolve()), core_agent["developer_instructions"])
        self.assertIn("maxTurns: 4", core_agent["developer_instructions"])
        self.assertIn("Read, Write", core_agent["developer_instructions"])
        self.assertNotIn("max_turns", core_agent)
        self.assertNotIn("sandbox", core_agent)
        self.assertNotIn("tools", core_agent)

    def test_should_use_default_medium_effort_when_role_omits_effort(self) -> None:
        role_path = self.write_role(self.core, "plain.md", name="plain")
        role_path.write_text(
            role_path.read_text(encoding="utf-8").replace("effort: high\n", ""),
            encoding="utf-8",
        )

        agent = tomllib.loads(collect_agents(self.core)["adze_bonch_plain"])

        self.assertEqual(agent["model_reasoning_effort"], "medium")

    def test_should_reject_missing_runtime_guidance_with_its_path(self) -> None:
        self.write_role(self.core, "writer.md", name="writer")
        runtime = self.core / "codex" / "runtime.md"
        runtime.unlink()

        with self.assertRaisesRegex((ValueError, RuntimeError, OSError), "runtime\\.md"):
            collect_agents(self.core)

    def test_should_reject_runtime_guidance_path_that_is_a_directory(self) -> None:
        self.write_role(self.core, "writer.md", name="writer")
        runtime = self.core / "codex" / "runtime.md"
        runtime.unlink()
        runtime.mkdir()

        with self.assertRaisesRegex((ValueError, RuntimeError, OSError), "runtime\\.md"):
            collect_agents(self.core)

    def test_should_reject_symlinked_runtime_guidance(self) -> None:
        self.write_role(self.core, "writer.md", name="writer")
        runtime = self.core / "codex" / "runtime.md"
        runtime.unlink()
        outside_runtime = self.root / "outside-runtime.md"
        outside_runtime.write_text("External runtime guidance.\n", encoding="utf-8")
        runtime.symlink_to(outside_runtime)

        with self.assertRaises((ValueError, RuntimeError, OSError)):
            collect_agents(self.core)

    def test_should_regenerate_config_and_report_drift_after_role_body_changes(self) -> None:
        role_path = self.write_role(self.core, "writer.md", name="writer")
        initial = collect_agents(self.core)
        install_agents(self.home, initial)
        role_path.write_text(
            role_path.read_text(encoding="utf-8").replace(
                "Role instructions for writer.", "Updated role instructions for writer."
            ),
            encoding="utf-8",
        )

        regenerated = collect_agents(self.core)
        check = check_agents(self.home, regenerated)

        self.assertNotEqual(initial["adze_bonch_writer"], regenerated["adze_bonch_writer"])
        self.assertFalse(check["ok"])

    def test_should_fail_closed_when_core_role_directory_is_missing(self) -> None:
        self.write_role(self.core, "writer.md", name="writer")
        install_agents(self.home, collect_agents(self.core))
        missing_core = self.root / "missing-core"

        with self.assertRaises((ValueError, RuntimeError, OSError)):
            collect_agents(missing_core)

        self.assertTrue((self.home / "agents" / "adze_bonch_writer.toml").is_file())

    def test_should_fail_closed_when_core_role_directory_is_empty(self) -> None:
        self.write_role(self.core, "writer.md", name="writer")
        install_agents(self.home, collect_agents(self.core))
        (self.core / "agents" / "writer.md").unlink()

        with self.assertRaises((ValueError, RuntimeError, OSError)):
            collect_agents(self.core)

        self.assertTrue((self.home / "agents" / "adze_bonch_writer.toml").is_file())

    def test_should_fail_closed_when_explicit_companion_role_directory_is_missing(self) -> None:
        self.write_role(self.core, "writer.md", name="writer")
        install_agents(self.home, collect_agents(self.core))
        missing_companion = self.root / "missing-companion"

        with self.assertRaises((ValueError, RuntimeError, OSError)):
            collect_agents(self.core, missing_companion)

        self.assertTrue((self.home / "agents" / "adze_bonch_writer.toml").is_file())

    def test_should_fail_closed_when_explicit_companion_role_directory_is_empty(self) -> None:
        self.write_role(self.core, "writer.md", name="writer")
        install_agents(self.home, collect_agents(self.core))
        (self.companion / "agents").mkdir()

        with self.assertRaises((ValueError, RuntimeError, OSError)):
            collect_agents(self.core, self.companion)

        self.assertTrue((self.home / "agents" / "adze_bonch_writer.toml").is_file())

    def test_should_refuse_empty_install_inventory_instead_of_pruning(self) -> None:
        install_agents(self.home, {"adze_bonch_writer": 'name = "writer"\n'})

        with self.assertRaises((ValueError, RuntimeError, OSError)):
            install_agents(self.home, {})

        self.assertTrue((self.home / "agents" / "adze_bonch_writer.toml").is_file())

    def test_should_install_idempotently_and_check_installed_agents(self) -> None:
        self.write_role(self.core, "writer.md", name="writer")
        agents = collect_agents(self.core)

        first = install_agents(self.home, agents)
        second = install_agents(self.home, agents)
        check = check_agents(self.home, agents)

        self.assertTrue(first["ok"])
        self.assertTrue(second["ok"])
        self.assertTrue(check["ok"])
        self.assertEqual(
            (self.home / "agents" / "adze_bonch_writer.toml").read_text(encoding="utf-8"),
            agents["adze_bonch_writer"],
        )
        self.assertTrue((self.home / ".adze-bonch-agents.json").is_file())

    def test_should_leave_files_untouched_during_dry_run(self) -> None:
        agents = {"adze_bonch_writer": 'name = "adze_bonch_writer"\n'}

        result = install_agents(self.home, agents, dry_run=True)

        self.assertTrue(result["ok"])
        self.assertTrue(result["dry_run"])
        self.assertFalse((self.home / "agents").exists())
        self.assertFalse((self.home / ".adze-bonch-agents.json").exists())

    def test_should_refuse_unmanaged_collision(self) -> None:
        target = self.home / "agents"
        target.mkdir(parents=True)
        existing = target / "adze_bonch_writer.toml"
        existing.write_text('name = "someone_else"\n', encoding="utf-8")

        with self.assertRaises((ValueError, RuntimeError, OSError)):
            install_agents(self.home, {"adze_bonch_writer": 'name = "ours"\n'})

    def test_should_refuse_install_over_modified_owned_file(self) -> None:
        agents = {"adze_bonch_writer": 'name = "ours"\n'}
        install_agents(self.home, agents)
        target = self.home / "agents" / "adze_bonch_writer.toml"
        target.write_text('name = "edited"\n', encoding="utf-8")

        with self.assertRaises((ValueError, RuntimeError, OSError)):
            install_agents(self.home, agents)

    def test_should_refuse_modified_owned_file(self) -> None:
        agents = {"adze_bonch_writer": 'name = "ours"\n'}
        install_agents(self.home, agents)
        target = self.home / "agents" / "adze_bonch_writer.toml"
        target.write_text('name = "edited"\n', encoding="utf-8")

        with self.assertRaises((ValueError, RuntimeError, OSError)):
            uninstall_agents(self.home)

    def test_should_refuse_symlinked_agents_directory(self) -> None:
        self.home.mkdir()
        external = self.root / "external"
        external.mkdir()
        (self.home / "agents").symlink_to(external, target_is_directory=True)

        with self.assertRaises((ValueError, RuntimeError, OSError)):
            install_agents(self.home, {"adze_bonch_writer": 'name = "ours"\n'})

    def test_should_refuse_symlinked_target_file(self) -> None:
        install_agents(self.home, {"adze_bonch_writer": 'name = "writer"\n'})
        target = self.home / "agents" / "adze_bonch_writer.toml"
        target.unlink()
        external = self.root / "external.toml"
        external.write_text('name = "external"\n', encoding="utf-8")
        target.symlink_to(external)

        with self.assertRaises((ValueError, RuntimeError, OSError)):
            install_agents(self.home, {"adze_bonch_writer": 'name = "writer"\n'})

        self.assertEqual(external.read_text(encoding="utf-8"), 'name = "external"\n')

    def test_should_refuse_dangling_symlinked_target_file(self) -> None:
        target = self.home / "agents" / "adze_bonch_writer.toml"
        target.parent.mkdir(parents=True)
        target.symlink_to(self.root / "missing.toml")

        with self.assertRaises((ValueError, RuntimeError, OSError)):
            install_agents(self.home, {"adze_bonch_writer": 'name = "writer"\n'})

    def test_should_refuse_symlinked_receipt(self) -> None:
        install_agents(self.home, {"adze_bonch_writer": 'name = "writer"\n'})
        receipt = self.home / ".adze-bonch-agents.json"
        receipt.unlink()
        external = self.root / "external-receipt.json"
        external.write_text("{}\n", encoding="utf-8")
        receipt.symlink_to(external)

        with self.assertRaises((ValueError, RuntimeError, OSError)):
            uninstall_agents(self.home)

        self.assertEqual(external.read_text(encoding="utf-8"), "{}\n")

    def test_should_preflight_collisions_before_creating_any_agent(self) -> None:
        agents_dir = self.home / "agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "adze_bonch_collision.toml").write_text("unmanaged\n", encoding="utf-8")

        with self.assertRaises((ValueError, RuntimeError, OSError)):
            install_agents(
                self.home,
                {
                    "adze_bonch_new": 'name = "new"\n',
                    "adze_bonch_collision": 'name = "collision"\n',
                },
            )

        self.assertFalse((agents_dir / "adze_bonch_new.toml").exists())
        self.assertFalse((self.home / ".adze-bonch-agents.json").exists())

    def test_should_detect_added_inventory_drift(self) -> None:
        installed = {"adze_bonch_writer": 'name = "writer"\n'}
        install_agents(self.home, installed)

        check = check_agents(
            self.home,
            {
                "adze_bonch_writer": 'name = "writer"\n',
                "adze_bonch_reviewer": 'name = "reviewer"\n',
            },
        )

        self.assertFalse(check["ok"])

    def test_should_detect_removed_inventory_drift(self) -> None:
        install_agents(
            self.home,
            {
                "adze_bonch_writer": 'name = "writer"\n',
                "adze_bonch_reviewer": 'name = "reviewer"\n',
            },
        )

        check = check_agents(self.home, {"adze_bonch_writer": 'name = "writer"\n'})

        self.assertFalse(check["ok"])

    def test_should_uninstall_owned_agents_and_receipt(self) -> None:
        install_agents(self.home, {"adze_bonch_writer": 'name = "writer"\n'})

        result = uninstall_agents(self.home)

        self.assertTrue(result["ok"])
        self.assertFalse((self.home / "agents" / "adze_bonch_writer.toml").exists())
        self.assertFalse((self.home / ".adze-bonch-agents.json").exists())

    def test_should_preserve_unrelated_files_during_uninstall(self) -> None:
        install_agents(self.home, {"adze_bonch_writer": 'name = "writer"\n'})
        unrelated = self.home / "agents" / "personal.toml"
        unrelated.write_text('name = "personal"\n', encoding="utf-8")

        uninstall_agents(self.home)

        self.assertEqual(unrelated.read_text(encoding="utf-8"), 'name = "personal"\n')


if __name__ == "__main__":
    unittest.main()
