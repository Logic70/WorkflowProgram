#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = ROOT / ".claude" / "scripts"


def run_json(*args: str, expect: int = 0) -> dict:
    completed = subprocess.run(
        [sys.executable, *args, "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != expect:
        raise AssertionError(
            f"expected exit {expect}, got {completed.returncode}\nstdout={completed.stdout}\nstderr={completed.stderr}"
        )
    payload = json.loads(completed.stdout)
    if not isinstance(payload, dict):
        raise AssertionError("expected JSON object")
    return payload


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def seed_canonical_run(run_root: Path, *, missing_acceptance_ref: bool = False, complex_node: bool = False) -> None:
    run_root.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "tests" / "spec-fixtures" / "valid-minimal.yaml", run_root / "workflow-spec.yaml")
    if complex_node:
        spec = yaml.safe_load((run_root / "workflow-spec.yaml").read_text(encoding="utf-8"))
        spec["workflow_graph"]["nodes"][1]["complexity"] = "complex"
        (run_root / "workflow-spec.yaml").write_text(yaml.safe_dump(spec, allow_unicode=True, sort_keys=False), encoding="utf-8")
    stages = run_root / "outputs" / "stages"
    write_text(
        stages / "target-requirements.yaml",
        "requirements:\n  - id: REQ-001\n    statement: demo\n",
    )
    write_text(stages / "target-context-findings.yaml", "findings:\n  - id: CTX-001\n    requirement_refs: [REQ-001]\n")
    write_text(stages / "target-design-overview.md", "# Target Design Overview\n\nREQ-001 intake implement.\n")
    write_text(stages / "target-design-detail.md", "# Target Design Detail\n\nREQ-001 intake implement.\n")
    write_text(stages / "target-implementation-plan.md", "# Target Implementation Plan\n")
    write_text(
        stages / "target-acceptance-tests.yaml",
        yaml.safe_dump(
            {
                "tests": [
                    {
                        "id": "AT-001",
                        "requirement_ids": [] if missing_acceptance_ref else ["REQ-001"],
                        "expected_evidence": ["state.json"],
                    }
                ]
            },
            allow_unicode=True,
            sort_keys=False,
        ),
    )
    write_json(
        stages / "target-traceability-matrix.json",
        {
            "schema_version": 1,
            "requirements": [
                {
                    "requirement_id": "REQ-001",
                    "workflow_graph_nodes": ["intake", "implement"],
                    "acceptance_tests": ["AT-001"],
                    "runtime_evidence": ["state.json"],
                }
            ],
        },
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="target-design-governance-") as temp_dir:
        temp = Path(temp_dir)
        good = temp / "good"
        seed_canonical_run(good)
        assert run_json(str(SCRIPT_ROOT / "validate-target-design-governance.py"), "--run-root", str(good))["status"] == "PASS"

        bad_acceptance = temp / "bad-acceptance"
        seed_canonical_run(bad_acceptance, missing_acceptance_ref=True)
        failed = run_json(str(SCRIPT_ROOT / "validate-target-design-governance.py"), "--run-root", str(bad_acceptance), expect=1)
        assert failed["status"] == "FAIL"
        assert any("acceptance tests missing" in error for error in failed["errors"])

        complex_missing = temp / "complex-missing"
        seed_canonical_run(complex_missing, complex_node=True)
        failed = run_json(str(SCRIPT_ROOT / "validate-target-design-governance.py"), "--run-root", str(complex_missing), expect=1)
        assert any("complex nodes missing" in error for error in failed["errors"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
