#!/usr/bin/env python3
"""
校验 workflow-lowlevel.md 是否仍然是 workflow-spec.yaml 的确定性派生物。
"""

from __future__ import annotations

import argparse
import difflib
import importlib.util
import json
from pathlib import Path
from typing import Any, Dict, List


def load_generator_module() -> Any:
    script_path = Path(__file__).resolve().with_name("generate-workflow-lowlevel.py")
    spec = importlib.util.spec_from_file_location("generate_workflow_lowlevel", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load generator module from {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def short_diff(expected: str, actual: str) -> List[str]:
    diff = list(
        difflib.unified_diff(
            expected.splitlines(),
            actual.splitlines(),
            fromfile="expected",
            tofile="actual",
            lineterm="",
            n=2,
        )
    )
    return diff[:12]


def validate_lowlevel(spec_path: Path, lowlevel_path: Path) -> Dict[str, object]:
    errors: List[str] = []
    warnings: List[str] = []
    if not spec_path.exists():
        return {
            "status": "FAIL",
            "errors": [f"workflow spec not found: {spec_path}"],
            "warnings": warnings,
            "spec": str(spec_path),
            "lowlevel": str(lowlevel_path),
        }
    if not lowlevel_path.exists():
        return {
            "status": "FAIL",
            "errors": [f"workflow lowlevel not found: {lowlevel_path}"],
            "warnings": warnings,
            "spec": str(spec_path),
            "lowlevel": str(lowlevel_path),
        }

    try:
        generator = load_generator_module()
        workflow_spec = generator.load_spec(spec_path)
        missing_top_keys = generator.ensure_spec_shape(workflow_spec)
        if missing_top_keys:
            errors.append(f"workflow-spec.yaml is missing required top keys: {', '.join(missing_top_keys)}")
        spec_sha256 = generator.sha256_file(spec_path)
        expected = generator.render_lowlevel(workflow_spec, spec_sha256, generated_at="<normalized>")
        expected = generator.normalize_lowlevel_content(expected)
        actual = generator.normalize_lowlevel_content(lowlevel_path.read_text(encoding="utf-8"))
        if actual != expected:
            errors.append("workflow-lowlevel.md does not match deterministic render from workflow-spec.yaml")
            warnings.extend(short_diff(expected, actual))
    except Exception as exc:
        errors.append(str(exc))

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
        "spec": str(spec_path),
        "lowlevel": str(lowlevel_path),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate workflow-lowlevel.md against workflow-spec.yaml")
    parser.add_argument("--spec", required=True, help="Path to workflow-spec.yaml")
    parser.add_argument("--lowlevel", required=True, help="Path to workflow-lowlevel.md")
    parser.add_argument("--json", action="store_true", help="Print JSON payload")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = validate_lowlevel(Path(args.spec).resolve(), Path(args.lowlevel).resolve())
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"[{payload['status']}] {payload['lowlevel']}")
        for item in payload["errors"]:
            print(f"- ERROR: {item}")
        for item in payload["warnings"]:
            print(f"- WARN: {item}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
