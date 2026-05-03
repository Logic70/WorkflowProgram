#!/usr/bin/env python3
# AUTO-GENERATED FROM .claude/ - DO NOT EDIT DIRECTLY
"""
校验目标工作流持久化的 deterministic runtime 资产是否与 workflow-spec.yaml 一致。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from lib.host_team_utils import (
    agent_team_contract_from_spec,
    agent_team_enabled,
    capability_discovery_from_spec,
    host_global_adapter,
    host_capabilities_from_spec,
    runtime_capabilities_from_contract,
)
from lib.yaml_utils import load_yaml_mapping


REQUIRED_GENERATED_RUNTIME_KEYS = {
    "runtime_root",
    "design_spec_path",
    "entry_script",
    "runner_script",
    "state_validator_script",
    "runtime_manifest",
    "run_root_dir",
    "mode",
    "runtime_capabilities",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate target-side generated runtime assets")
    parser.add_argument("--spec", required=True, help="Path to persistent workflow-spec.yaml")
    parser.add_argument("--target-root", required=True, help="Target workflow root")
    parser.add_argument("--json", action="store_true", help="Print JSON payload")
    return parser.parse_args()


def validate_generated_runtime(spec_path: Path, target_root: Path) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []

    if not spec_path.exists():
        return {
            "status": "FAIL",
            "errors": [f"workflow spec not found: {spec_path}"],
            "warnings": warnings,
            "spec": str(spec_path),
            "target_root": str(target_root),
        }
    if not target_root.exists():
        return {
            "status": "FAIL",
            "errors": [f"target root not found: {target_root}"],
            "warnings": warnings,
            "spec": str(spec_path),
            "target_root": str(target_root),
        }

    try:
        spec = load_yaml_mapping(spec_path)
        contract = spec.get("generated_runtime_contract")
        if not isinstance(contract, dict):
            errors.append("generated_runtime_contract must be a mapping/object")
            contract = {}

        missing_keys = sorted(REQUIRED_GENERATED_RUNTIME_KEYS - set(contract.keys()))
        if missing_keys:
            errors.append(f"generated_runtime_contract missing required keys: {', '.join(missing_keys)}")

        normalized = {key: str(contract.get(key, "")).strip() for key in REQUIRED_GENERATED_RUNTIME_KEYS if key != "runtime_capabilities"}
        expected_runtime_capabilities = runtime_capabilities_from_contract(contract)
        capability_discovery = capability_discovery_from_spec(spec)
        declared_host_capabilities = host_capabilities_from_spec(spec)
        host_global_adapter_declared = any(
            str(item.get("bootstrap", {}).get("scope", "")).strip() == "host_global" and bool(host_global_adapter(item))
            for item in declared_host_capabilities
            if isinstance(item, dict) and isinstance(item.get("bootstrap"), dict)
        )
        declared_agent_team = agent_team_contract_from_spec(spec)
        main_entry = (
            str(spec.get("test_contract", {}).get("entry", {}).get("main_entry", "")).strip()
            if isinstance(spec.get("test_contract", {}), dict)
            else ""
        )

        entry_path = target_root / normalized.get("entry_script", "")
        runner_path = target_root / normalized.get("runner_script", "")
        validator_path = target_root / normalized.get("state_validator_script", "")
        manifest_path = target_root / normalized.get("runtime_manifest", "")
        design_spec_target = target_root / normalized.get("design_spec_path", "")

        for label, path in (
            ("entry_script", entry_path),
            ("runner_script", runner_path),
            ("state_validator_script", validator_path),
            ("runtime_manifest", manifest_path),
        ):
            if not str(path):
                continue
            if not path.exists():
                errors.append(f"{label} is missing: {path}")

        if design_spec_target and design_spec_target != spec_path:
            errors.append(
                "generated_runtime_contract.design_spec_path does not point back to the validated persistent workflow-spec.yaml"
            )

        manifest_payload: Dict[str, Any] = {}
        if manifest_path.exists():
            try:
                manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(f"runtime manifest is not valid JSON: {exc}")

        if manifest_payload:
            expected_pairs = {
                "runtime_root": normalized.get("runtime_root", ""),
                "design_spec_path": normalized.get("design_spec_path", ""),
                "entry_script": normalized.get("entry_script", ""),
                "runner_script": normalized.get("runner_script", ""),
                "state_validator_script": normalized.get("state_validator_script", ""),
                "runtime_manifest": normalized.get("runtime_manifest", ""),
                "run_root_dir": normalized.get("run_root_dir", ""),
                "runtime_mode": normalized.get("mode", ""),
                "runtime_capabilities": expected_runtime_capabilities,
                "default_entry_skill": main_entry,
                "capability_discovery_enabled": bool(capability_discovery.get("enabled", False)),
                "capability_discovery_domains": capability_discovery.get("domains", []) if isinstance(capability_discovery.get("domains", []), list) else [],
                "host_capabilities_declared": bool(declared_host_capabilities),
                "host_global_adapter_declared": host_global_adapter_declared,
                "agent_team_enabled": agent_team_enabled(declared_agent_team),
            }
            for key, expected in expected_pairs.items():
                observed_value = manifest_payload.get(key)
                if isinstance(expected, list):
                    observed = [str(item).strip() for item in observed_value] if isinstance(observed_value, list) else []
                    if observed != expected:
                        errors.append(f"runtime manifest field '{key}' mismatch: expected '{expected}', got '{observed}'")
                    continue
                if isinstance(expected, bool):
                    observed = observed_value if isinstance(observed_value, bool) else None
                    if observed is not expected:
                        errors.append(f"runtime manifest field '{key}' mismatch: expected '{expected}', got '{observed}'")
                    continue
                observed = str(observed_value).strip() if observed_value is not None else ""
                if observed != str(expected).strip():
                    errors.append(f"runtime manifest field '{key}' mismatch: expected '{expected}', got '{observed}'")

        if entry_path.exists():
            entry_text = entry_path.read_text(encoding="utf-8")
            for needle in (
                f"DEFAULT_ENTRY_SKILL = {main_entry!r}",
                f"DESIGN_SPEC_REL = {normalized.get('design_spec_path', '')!r}",
                f"RUNNER_SCRIPT_REL = {normalized.get('runner_script', '')!r}",
                f"STATE_VALIDATOR_SCRIPT_REL = {normalized.get('state_validator_script', '')!r}",
                "workflowprogram-python",
            ):
                if needle not in entry_text:
                    errors.append(f"entry wrapper is missing expected marker: {needle}")
            if capability_discovery.get("enabled") is True and "DISCOVER_HOST_SCRIPT = \"discover-host-capabilities.py\"" not in entry_text:
                errors.append("entry wrapper is missing discover-host-capabilities.py integration marker")
            if declared_host_capabilities and "PROBE_HOST_SCRIPT = \"probe-host-capabilities.py\"" not in entry_text:
                errors.append("entry wrapper is missing probe-host-capabilities.py integration marker")
            if declared_host_capabilities and "ENVIRONMENT_REMEDIATION_SCRIPT = \"generate-environment-remediation.py\"" not in entry_text:
                errors.append("entry wrapper is missing generate-environment-remediation.py integration marker")
            if agent_team_enabled(declared_agent_team) and "TEAM_ORCHESTRATION_ENABLED = True" not in entry_text:
                errors.append("entry wrapper is missing TEAM_ORCHESTRATION_ENABLED marker")

        if runner_path.exists():
            runner_text = runner_path.read_text(encoding="utf-8")
            for needle in ("workflow-runner.py", "--entry-skill", "--intent", "workflowprogram-python"):
                if needle not in runner_text:
                    errors.append(f"runner wrapper is missing expected marker: {needle}")

        if validator_path.exists():
            validator_text = validator_path.read_text(encoding="utf-8")
            for needle in ("validate-run-state.py", "workflowprogram-python"):
                if needle not in validator_text:
                    errors.append(f"state validator wrapper is missing expected marker: {needle}")
    except Exception as exc:
        errors.append(str(exc))

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
        "spec": str(spec_path),
        "target_root": str(target_root),
    }


def main() -> int:
    args = parse_args()
    payload = validate_generated_runtime(Path(args.spec).resolve(), Path(args.target_root).resolve())
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"[{payload['status']}] {payload['target_root']}")
        for item in payload["errors"]:
            print(f"- ERROR: {item}")
        for item in payload["warnings"]:
            print(f"- WARN: {item}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
