---
name: adze-bonch-tackle
description: "Deliver an adze task through the full adze-bonch lifecycle: research, interactive plan, branch, TDD implementation, parallel review, executable repro verification, fix confirmation, regression-test promotion, and commit. Use when the user asks to tackle, implement, fix, or work an adze task end to end."
---

# adze-bonch tackle

Read [the Codex runtime](../../runtime.md), then read and follow the canonical
orchestrator at [commands/tackle.md](../../../commands/tackle.md). Load linked
references and role cards only as each stage needs them. The parent remains the
orchestrator and does not write implementation code or tests. Preserve the full
workflow, including required review, repro verification, confirm-fix, and
promote-or-decline stages. Do not push or open a pull request unless the user asks.
