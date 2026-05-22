from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / ".claude" / "scripts" / "target-workflow-runner.py"
VALIDATOR = ROOT / ".claude" / "scripts" / "validate-target-runtime-state.py"
SPEC = ROOT / "tests" / "spec-fixtures" / "valid-minimal.yaml"


def write_target_fixture(tmp_path: Path, *, include_owner: bool = True) -> Path:
    target = tmp_path / "target"
    target.mkdir()
    if include_owner:
        skill = target / ".claude" / "skills" / "example" / "SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("---\nname: example-skill\n---\n", encoding="utf-8")
    return target


def test_target_managed_runtime_passes(tmp_path: Path) -> None:
    target = write_target_fixture(tmp_path)
    run_root = tmp_path / "run"
    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "run",
            "--spec",
            str(SPEC),
            "--run-root",
            str(run_root),
            "--target-root",
            str(target),
            "--entry-skill",
            "example",
            "--runtime-provider",
            "fixture_host",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["status"] == "PASS"
    assert (run_root / "target-state.json").exists()
    assert (run_root / "target-events.jsonl").exists()
    assert (run_root / "artifact-provenance.json").exists()

    validation = subprocess.run(
        [sys.executable, str(VALIDATOR), "--state", str(run_root / "target-state.json"), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert validation.returncode == 0, validation.stderr or validation.stdout
    assert json.loads(validation.stdout)["status"] == "PASS"


def test_target_managed_runtime_missing_owner_fails(tmp_path: Path) -> None:
    target = write_target_fixture(tmp_path, include_owner=False)
    run_root = tmp_path / "run"
    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "run",
            "--spec",
            str(SPEC),
            "--run-root",
            str(run_root),
            "--target-root",
            str(target),
            "--entry-skill",
            "example",
            "--runtime-provider",
            "fixture_host",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 1
    payload = json.loads(completed.stdout)
    assert payload["status"] == "FAIL"
    assert "owner not found" in payload["failure_reason"]


def test_target_runtime_policy_requires_capability(tmp_path: Path) -> None:
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    spec["generated_runtime_contract"]["runtime_capabilities"] = ["state_transitions", "run_state_validation"]
    invalid = tmp_path / "invalid.yaml"
    invalid.write_text(yaml.safe_dump(spec, allow_unicode=True, sort_keys=False), encoding="utf-8")
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / ".claude" / "scripts" / "validate-workflow-spec.py"),
            "--spec",
            str(invalid),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 1
    payload = json.loads(completed.stdout)
    assert any("target_managed_runtime" in item for item in payload["errors"])


def test_target_managed_runtime_exception_writes_failure_evidence(tmp_path: Path) -> None:
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    spec.pop("workflow_graph", None)
    invalid = tmp_path / "missing-graph.yaml"
    invalid.write_text(yaml.safe_dump(spec, allow_unicode=True, sort_keys=False), encoding="utf-8")
    target = write_target_fixture(tmp_path)
    run_root = tmp_path / "run"
    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "run",
            "--spec",
            str(invalid),
            "--run-root",
            str(run_root),
            "--target-root",
            str(target),
            "--entry-skill",
            "example",
            "--runtime-provider",
            "fixture_host",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 1
    payload = json.loads(completed.stdout)
    assert payload["status"] == "FAIL"
    assert (run_root / "target-state.json").exists()
    assert (run_root / "target-events.jsonl").exists()
    assert (run_root / "outputs" / "stages" / "target-runtime-summary.json").exists()

    validation = subprocess.run(
        [sys.executable, str(VALIDATOR), "--state", str(run_root / "target-state.json"), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert validation.returncode == 1
    validation_payload = json.loads(validation.stdout)
    assert validation_payload["status"] == "FAIL"
