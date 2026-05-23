from __future__ import annotations

import json
import hashlib
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / ".claude" / "scripts" / "target-workflow-runner.py"
VALIDATOR = ROOT / ".claude" / "scripts" / "validate-target-runtime-state.py"
FINALIZER = ROOT / ".claude" / "scripts" / "target-runtime-finalizer.py"
SPEC = ROOT / "tests" / "spec-fixtures" / "valid-minimal.yaml"


def write_target_fixture(tmp_path: Path, *, include_owner: bool = True) -> Path:
    target = tmp_path / "target"
    target.mkdir()
    if include_owner:
        skill = target / ".claude" / "skills" / "example" / "SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("---\nname: example-skill\n---\n", encoding="utf-8")
    return target


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manual_evidence(
    run_root: Path,
    node_id: str,
    *,
    input_refs: list[str],
    output_refs: list[str],
    outputs: list[str],
    provider: str = "current_agent",
    operator: str = "deepseek-current-session",
) -> None:
    evidence_dir = run_root / "outputs" / "stages" / "executor-evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "provider": provider,
        "node_id": node_id,
        "status": "PASS",
        "operator": operator,
        "started_at": "2026-05-24T00:00:00Z",
        "completed_at": "2026-05-24T00:00:01Z",
        "input_refs": input_refs,
        "output_refs": output_refs,
        "outputs": [
            {"path": rel, "sha256": sha256_file(run_root / rel)}
            for rel in outputs
        ],
    }
    (evidence_dir / f"{node_id}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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
    assert (run_root / "outputs" / "target-workflow" / "implementation-summary.md").exists()
    assert not (target / "outputs" / "target-workflow" / "implementation-summary.md").exists()

    validation = subprocess.run(
        [sys.executable, str(VALIDATOR), "--state", str(run_root / "target-state.json"), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert validation.returncode == 0, validation.stderr or validation.stdout
    assert json.loads(validation.stdout)["status"] == "PASS"


def test_unsupported_executor_provider_fails_without_publish(tmp_path: Path) -> None:
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
            "claude_cli",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 1
    payload = json.loads(completed.stdout)
    assert payload["status"] == "FAIL"
    assert payload["failure_kind"] == "environment"
    assert "unsupported executor provider" in payload["failure_reason"]
    assert not (target / "outputs" / "target-workflow").exists()


def test_default_current_agent_provider_requires_evidence(tmp_path: Path) -> None:
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
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 1
    payload = json.loads(completed.stdout)
    assert payload["status"] == "FAIL"
    assert "executor evidence missing" in payload["failure_reason"]
    assert not (target / "outputs" / "target-workflow").exists()


def test_current_agent_evidence_requires_finalizer_before_pass(tmp_path: Path) -> None:
    target = write_target_fixture(tmp_path)
    run_root = tmp_path / "run"
    (run_root / "outputs" / "target-workflow").mkdir(parents=True)
    intake = run_root / "outputs" / "target-workflow" / "intake-summary.md"
    implementation = run_root / "outputs" / "target-workflow" / "implementation-summary.md"
    intake.write_text("# Intake\n", encoding="utf-8")
    implementation.write_text("# Implementation\n", encoding="utf-8")
    write_manual_evidence(
        run_root,
        "intake",
        input_refs=["$ARGUMENTS"],
        output_refs=["outputs/target-workflow/intake-summary.md"],
        outputs=["outputs/target-workflow/intake-summary.md"],
    )
    write_manual_evidence(
        run_root,
        "implement",
        input_refs=["outputs/target-workflow/intake-summary.md"],
        output_refs=["outputs/target-workflow/implementation-summary.md"],
        outputs=["outputs/target-workflow/implementation-summary.md"],
    )

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
            "current_agent",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 2, completed.stderr or completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["status"] == "BLOCKED"
    state = json.loads((run_root / "target-state.json").read_text(encoding="utf-8"))
    assert state["status"] == "BLOCKED"
    assert state["manual_finalizer_required"] is True

    validation = subprocess.run(
        [sys.executable, str(VALIDATOR), "--state", str(run_root / "target-state.json"), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert validation.returncode == 0, validation.stderr or validation.stdout

    finalized = subprocess.run(
        [
            sys.executable,
            str(FINALIZER),
            "--spec",
            str(SPEC),
            "--run-root",
            str(run_root),
            "--target-root",
            str(target),
            "--state",
            str(run_root / "target-state.json"),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert finalized.returncode == 0, finalized.stderr or finalized.stdout
    final_state = json.loads((run_root / "target-state.json").read_text(encoding="utf-8"))
    assert final_state["status"] == "PASS"
    assert final_state["finalizer_status"] == "PASS"
    assert (target / "outputs" / "target-workflow" / "implementation-summary.md").exists()


def test_target_runtime_finalizer_publishes_current_run_outputs(tmp_path: Path) -> None:
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

    finalized = subprocess.run(
        [
            sys.executable,
            str(FINALIZER),
            "--spec",
            str(SPEC),
            "--run-root",
            str(run_root),
            "--target-root",
            str(target),
            "--state",
            str(run_root / "target-state.json"),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert finalized.returncode == 0, finalized.stderr or finalized.stdout
    payload = json.loads(finalized.stdout)
    assert payload["status"] == "PASS"
    assert (target / "outputs" / "target-workflow" / "implementation-summary.md").exists()
    manifest = json.loads((target / "outputs" / "target-workflow" / "run-manifest.json").read_text(encoding="utf-8"))
    latest = json.loads((target / "outputs" / "target-workflow" / ".workflowprogram-latest.json").read_text(encoding="utf-8"))
    assert manifest["run_id"] == run_root.name
    assert latest["run_id"] == run_root.name
    assert json.loads((run_root / "target-state.json").read_text(encoding="utf-8"))["finalizer_status"] == "PASS"


def test_target_runtime_finalizer_blocks_report_mismatch(tmp_path: Path) -> None:
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
    summary_path = run_root / "outputs" / "stages" / "target-runtime-summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["status"] = "FAIL"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    finalized = subprocess.run(
        [
            sys.executable,
            str(FINALIZER),
            "--spec",
            str(SPEC),
            "--run-root",
            str(run_root),
            "--target-root",
            str(target),
            "--state",
            str(run_root / "target-state.json"),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert finalized.returncode == 1
    payload = json.loads(finalized.stdout)
    assert payload["status"] == "FAIL"
    state = json.loads((run_root / "target-state.json").read_text(encoding="utf-8"))
    assert state["status"] == "FAIL"
    assert state["finalizer_status"] == "FAIL"
    assert not (target / "outputs" / "target-workflow" / "run-manifest.json").exists()


def test_target_runtime_finalizer_blocks_doctor_contract_failure(tmp_path: Path) -> None:
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    spec["target_publish_policy"]["required_reports"].append(
        {
            "path": "outputs/stages/doctor.json",
            "status_field": "status",
            "pass_values": ["PASS"],
        }
    )
    spec_path = tmp_path / "doctor-required.yaml"
    spec_path.write_text(yaml.safe_dump(spec, allow_unicode=True, sort_keys=False), encoding="utf-8")
    target = write_target_fixture(tmp_path)
    run_root = tmp_path / "run"
    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "run",
            "--spec",
            str(spec_path),
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
    doctor_path = run_root / "outputs" / "stages" / "doctor.json"
    doctor_path.write_text(json.dumps({"status": "FAIL"}, indent=2) + "\n", encoding="utf-8")

    finalized = subprocess.run(
        [
            sys.executable,
            str(FINALIZER),
            "--spec",
            str(spec_path),
            "--run-root",
            str(run_root),
            "--target-root",
            str(target),
            "--state",
            str(run_root / "target-state.json"),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert finalized.returncode == 1
    payload = json.loads(finalized.stdout)
    assert payload["status"] == "FAIL"
    state = json.loads((run_root / "target-state.json").read_text(encoding="utf-8"))
    assert state["status"] == "FAIL"
    assert state["finalizer_status"] == "FAIL"
    assert not (target / "outputs" / "target-workflow" / "run-manifest.json").exists()


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


def test_target_publish_policy_requires_capability(tmp_path: Path) -> None:
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    spec["generated_runtime_contract"]["runtime_capabilities"] = [
        item
        for item in spec["generated_runtime_contract"]["runtime_capabilities"]
        if item != "target_atomic_publish"
    ]
    invalid = tmp_path / "invalid-publish.yaml"
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
    assert any("target_atomic_publish" in item for item in payload["errors"])


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
