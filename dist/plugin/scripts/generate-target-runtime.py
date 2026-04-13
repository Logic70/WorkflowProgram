#!/usr/bin/env python3
# AUTO-GENERATED FROM .claude/ - DO NOT EDIT DIRECTLY
"""
根据 workflow-spec.yaml 为目标工作流生成确定性的 target-side runtime 资产。

这些资产本身不直接替代 WorkflowProgram 的共享脚本，
而是把“固定主链 + 固定控制面”的机制显式下沉到目标项目：

- `.workflowprogram/runtime/workflow-entry.py`
- `.workflowprogram/runtime/workflow-runner.py`
- `.workflowprogram/runtime/validate-run-state.py`
- `.workflowprogram/runtime/runtime-manifest.json`
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from lib.io_utils import iso_now, write_json
from lib.yaml_utils import load_yaml_mapping


REQUIRED_TOP_KEYS = [
    "meta",
    "stages",
    "intent_flows",
    "agent_refs",
    "skills",
    "registry",
    "constraints",
    "resource_limits",
    "runtime_contract",
    "generated_runtime_contract",
    "test_contract",
]

REQUIRED_GENERATED_RUNTIME_KEYS = {
    "runtime_root",
    "design_spec_path",
    "entry_script",
    "runner_script",
    "state_validator_script",
    "runtime_manifest",
    "run_root_dir",
    "mode",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate target-side workflow runtime assets from workflow-spec.yaml")
    parser.add_argument("--spec", default="workflow-spec.yaml", help="Path to workflow-spec.yaml")
    parser.add_argument("--out-root", required=True, help="Directory where generated runtime assets will be written")
    parser.add_argument("--json", action="store_true", help="Print JSON payload")
    return parser.parse_args()


def ensure_spec_shape(spec: Dict[str, Any]) -> List[str]:
    missing = [key for key in REQUIRED_TOP_KEYS if key not in spec]
    stages = spec.get("stages")
    if stages is None or not isinstance(stages, list):
        raise ValueError("workflow-spec.yaml field 'stages' must be a list")
    return missing


def require_runtime_contract(spec: Dict[str, Any]) -> Dict[str, str]:
    contract = spec.get("generated_runtime_contract")
    if not isinstance(contract, dict):
        raise ValueError("generated_runtime_contract must be a mapping/object")
    missing = sorted(REQUIRED_GENERATED_RUNTIME_KEYS - set(contract.keys()))
    if missing:
        raise ValueError(f"generated_runtime_contract missing required keys: {', '.join(missing)}")
    normalized: Dict[str, str] = {}
    for key in REQUIRED_GENERATED_RUNTIME_KEYS:
        value = str(contract.get(key, "")).strip()
        if not value:
            raise ValueError(f"generated_runtime_contract.{key} must not be empty")
        normalized[key] = value
    return normalized


def default_entry_skill(spec: Dict[str, Any]) -> str:
    test_contract = spec.get("test_contract", {})
    if not isinstance(test_contract, dict):
        return "workflow"
    entry = test_contract.get("entry", {})
    if not isinstance(entry, dict):
        return "workflow"
    value = str(entry.get("main_entry", "")).strip()
    return value or "workflow"


def render_entry_wrapper(contract: Dict[str, str], main_entry: str) -> str:
    return f"""#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


DEFAULT_ENTRY_SKILL = {main_entry!r}
DEFAULT_INTENT = "develop"
DESIGN_SPEC_REL = {contract["design_spec_path"]!r}
RUN_ROOT_DIR_REL = {contract["run_root_dir"]!r}
RUNNER_SCRIPT_REL = {contract["runner_script"]!r}
STATE_VALIDATOR_SCRIPT_REL = {contract["state_validator_script"]!r}


def utc_run_id() -> str:
    return datetime.now(timezone.utc).strftime("generated-runtime-%Y%m%dT%H%M%SZ")


def script_root() -> Path:
    return Path(__file__).resolve().parent


def resolve_target_root(explicit: str) -> Path:
    if explicit:
        return Path(explicit).resolve()
    return script_root().parents[1]


def resolve_plugin_root(explicit: str) -> Path:
    if explicit:
        return Path(explicit).resolve()
    env_value = os.environ.get("CLAUDE_PLUGIN_ROOT", "").strip()
    if env_value:
        return Path(env_value).resolve()
    raise RuntimeError("target runtime requires --plugin-root or CLAUDE_PLUGIN_ROOT")


def parse_json_output(text: str) -> Dict[str, Any]:
    text = text.strip()
    if not text:
        return {{}}
    try:
        payload = json.loads(text)
        return payload if isinstance(payload, dict) else {{}}
    except json.JSONDecodeError:
        pass
    lines = [line for line in text.splitlines() if line.strip()]
    for idx in range(len(lines)):
        candidate = "\\n".join(lines[idx:])
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    return {{}}


def run_command(cmd: List[str]) -> Tuple[int, Dict[str, Any], str]:
    completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
    text = completed.stdout.strip() or completed.stderr.strip()
    return completed.returncode, parse_json_output(text), text


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8", newline="\\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run generated workflow deterministic entry wrapper")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Run generated workflow control plane")
    run.add_argument("--target-root", default="", help="Target workflow root; defaults from this script location")
    run.add_argument("--run-root", default="", help="Explicit RUN_ROOT; defaults to target/.workflowprogram/runs/<id>")
    run.add_argument("--plugin-root", default="", help="Plugin root containing shared WorkflowProgram scripts")
    run.add_argument("--request", default="", help="Original request text")
    run.add_argument("--intent", default=DEFAULT_INTENT, help="Logical intent for this invocation")
    run.add_argument("--entry-skill", default=DEFAULT_ENTRY_SKILL, help="Entry name for this generated workflow")
    run.add_argument("--runtime-provider", default="", help="Runtime host provider override")
    run.add_argument("--provider-command", default="", help="Provider command for command_adapter")
    run.add_argument("--claude-bin", default="claude", help="Claude binary for claude_cli")
    run.add_argument("--auto-approve", action="store_true", help="Resolve approval gate automatically")
    run.add_argument("--approval-status", default="", choices=["approved"], help="Resolve approval gate as manually approved")
    run.add_argument("--json", action="store_true", help="Print JSON summary")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    target_root = resolve_target_root(args.target_root)
    plugin_root = resolve_plugin_root(args.plugin_root)
    spec_path = target_root / DESIGN_SPEC_REL
    run_root = Path(args.run_root).resolve() if args.run_root else (target_root / RUN_ROOT_DIR_REL / utc_run_id()).resolve()
    run_root.mkdir(parents=True, exist_ok=True)

    validate_cmd = [
        sys.executable,
        str(plugin_root / "scripts" / "validate-workflow-spec.py"),
        "--spec",
        str(spec_path),
        "--json",
    ]
    validate_code, validate_payload, validate_text = run_command(validate_cmd)
    if validate_code != 0 or validate_payload.get("status") != "PASS":
        payload = {{
            "status": "FAIL",
            "error": validate_text or "generated workflow spec validation failed",
            "run_root": str(run_root),
            "target_root": str(target_root),
            "spec": str(spec_path),
        }}
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(payload["error"])
        return 1

    runner_cmd = [
        sys.executable,
        str(target_root / RUNNER_SCRIPT_REL),
        "run",
        "--spec",
        str(spec_path),
        "--run-root",
        str(run_root),
        "--target-root",
        str(target_root),
        "--plugin-root",
        str(plugin_root),
        "--request",
        args.request,
        "--intent",
        args.intent,
        "--entry-skill",
        args.entry_skill,
        "--runtime-provider",
        args.runtime_provider,
        "--provider-command",
        args.provider_command,
        "--claude-bin",
        args.claude_bin,
        "--json",
    ]
    if args.auto_approve:
        runner_cmd.append("--auto-approve")
    if args.approval_status:
        runner_cmd.extend(["--approval-status", args.approval_status])
    runner_code, runner_payload, runner_text = run_command(runner_cmd)
    if runner_code not in {{0, 2, 3}} or not runner_payload:
        payload = {{
            "status": "FAIL",
            "error": runner_text or "generated workflow runner failed",
            "run_root": str(run_root),
            "target_root": str(target_root),
            "spec": str(spec_path),
        }}
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(payload["error"])
        return 1

    validator_cmd = [
        sys.executable,
        str(target_root / STATE_VALIDATOR_SCRIPT_REL),
        "--state",
        str(run_root / "state.json"),
        "--plugin-root",
        str(plugin_root),
        "--json",
    ]
    state_code, state_payload, state_text = run_command(validator_cmd)
    if state_code != 0 or state_payload.get("status") != "PASS":
        payload = {{
            "status": "FAIL",
            "error": state_text or "generated workflow state validation failed",
            "run_root": str(run_root),
            "target_root": str(target_root),
            "spec": str(spec_path),
            "runner": runner_payload,
        }}
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(payload["error"])
        return 1

    summary = {{
        "status": str(runner_payload.get("status", "PASS")).strip() or "PASS",
        "generated_runtime": True,
        "target_root": str(target_root),
        "run_root": str(run_root),
        "spec": str(spec_path),
        "entry_skill": args.entry_skill,
        "intent": args.intent,
        "runner": runner_payload,
        "state_validation": state_payload,
    }}
    write_json(run_root / "outputs" / "stages" / "entry-orchestration-summary.json", summary)
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"[{{summary['status']}}] generated workflow runtime completed: {{run_root}}")
    return 0 if summary["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
"""


def render_runner_wrapper() -> str:
    return """#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


def resolve_plugin_root(explicit: str) -> Path:
    if explicit:
        return Path(explicit).resolve()
    env_value = os.environ.get("CLAUDE_PLUGIN_ROOT", "").strip()
    if env_value:
        return Path(env_value).resolve()
    raise RuntimeError("generated workflow runner requires --plugin-root or CLAUDE_PLUGIN_ROOT")


def parse_json_output(text: str) -> Dict[str, Any]:
    text = text.strip()
    if not text:
        return {}
    try:
        payload = json.loads(text)
        return payload if isinstance(payload, dict) else {}
    except json.JSONDecodeError:
        pass
    lines = [line for line in text.splitlines() if line.strip()]
    for idx in range(len(lines)):
        candidate = "\\n".join(lines[idx:])
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    return {}


def run_command(cmd: List[str]) -> Tuple[int, Dict[str, Any], str]:
    completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
    text = completed.stdout.strip() or completed.stderr.strip()
    return completed.returncode, parse_json_output(text), text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generated workflow runner wrapper")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Run generated workflow control plane")
    run.add_argument("--spec", required=True)
    run.add_argument("--run-root", required=True)
    run.add_argument("--target-root", required=True)
    run.add_argument("--plugin-root", default="")
    run.add_argument("--request", default="")
    run.add_argument("--intent", required=True)
    run.add_argument("--entry-skill", required=True)
    run.add_argument("--runtime-provider", default="")
    run.add_argument("--provider-command", default="")
    run.add_argument("--claude-bin", default="claude")
    run.add_argument("--auto-approve", action="store_true")
    run.add_argument("--approval-status", default="", choices=["approved"])
    run.add_argument("--json", action="store_true")

    status = sub.add_parser("status", help="Read generated workflow runner status")
    status.add_argument("--run-root", required=True)
    status.add_argument("--plugin-root", default="")
    status.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plugin_root = resolve_plugin_root(getattr(args, "plugin_root", ""))
    cmd = [
        sys.executable,
        str(plugin_root / "scripts" / "workflow-runner.py"),
        args.command,
    ]
    if args.command == "run":
        cmd.extend(
            [
                "--spec",
                str(Path(args.spec).resolve()),
                "--run-root",
                str(Path(args.run_root).resolve()),
                "--target-root",
                str(Path(args.target_root).resolve()),
                "--plugin-root",
                str(plugin_root),
                "--request",
                args.request,
                "--intent",
                args.intent,
                "--entry-skill",
                args.entry_skill,
                "--runtime-provider",
                args.runtime_provider,
                "--provider-command",
                args.provider_command,
                "--claude-bin",
                args.claude_bin,
                "--json",
            ]
        )
        if args.auto_approve:
            cmd.append("--auto-approve")
        if args.approval_status:
            cmd.extend(["--approval-status", args.approval_status])
    else:
        cmd.extend(["--run-root", str(Path(args.run_root).resolve()), "--json"])
    code, payload, text = run_command(cmd)
    if args.json:
        print(json.dumps(payload or {"status": "FAIL", "error": text or "runner wrapper failed"}, ensure_ascii=False, indent=2))
    else:
        print(text or json.dumps(payload, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
"""


def render_state_validator_wrapper() -> str:
    return """#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


def resolve_plugin_root(explicit: str) -> Path:
    if explicit:
        return Path(explicit).resolve()
    env_value = os.environ.get("CLAUDE_PLUGIN_ROOT", "").strip()
    if env_value:
        return Path(env_value).resolve()
    raise RuntimeError("generated workflow state validator requires --plugin-root or CLAUDE_PLUGIN_ROOT")


def parse_json_output(text: str) -> Dict[str, Any]:
    text = text.strip()
    if not text:
        return {}
    try:
        payload = json.loads(text)
        return payload if isinstance(payload, dict) else {}
    except json.JSONDecodeError:
        pass
    lines = [line for line in text.splitlines() if line.strip()]
    for idx in range(len(lines)):
        candidate = "\\n".join(lines[idx:])
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    return {}


def run_command(cmd: List[str]) -> Tuple[int, Dict[str, Any], str]:
    completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
    text = completed.stdout.strip() or completed.stderr.strip()
    return completed.returncode, parse_json_output(text), text


def main() -> int:
    parser = argparse.ArgumentParser(description="Generated workflow state validator wrapper")
    parser.add_argument("--state", required=True)
    parser.add_argument("--plugin-root", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    plugin_root = resolve_plugin_root(args.plugin_root)
    cmd = [
        sys.executable,
        str(plugin_root / "scripts" / "validate-run-state.py"),
        "--state",
        str(Path(args.state).resolve()),
        "--json",
    ]
    code, payload, text = run_command(cmd)
    if args.json:
        print(json.dumps(payload or {"status": "FAIL", "error": text or "state validator wrapper failed"}, ensure_ascii=False, indent=2))
    else:
        print(text or json.dumps(payload, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
"""


def manifest_payload(contract: Dict[str, str], main_entry: str) -> Dict[str, Any]:
    return {
        "manifest_version": 1,
        "generated_at": iso_now(),
        "runtime_mode": contract["mode"],
        "runtime_root": contract["runtime_root"],
        "design_spec_path": contract["design_spec_path"],
        "entry_script": contract["entry_script"],
        "runner_script": contract["runner_script"],
        "state_validator_script": contract["state_validator_script"],
        "runtime_manifest": contract["runtime_manifest"],
        "run_root_dir": contract["run_root_dir"],
        "default_intent": "develop",
        "default_entry_skill": main_entry,
        "shared_plugin_dependency": True,
        "shared_scripts": [
            "validate-workflow-spec.py",
            "workflow-runner.py",
            "validate-run-state.py",
        ],
    }


def main() -> int:
    args = parse_args()
    spec_path = Path(args.spec).resolve()
    out_root = Path(args.out_root).resolve()
    payload: Dict[str, Any] = {
        "status": "PASS",
        "spec": str(spec_path),
        "out_root": str(out_root),
        "files": {},
        "missing_top_keys": [],
    }
    try:
        spec = load_yaml_mapping(spec_path)
        payload["missing_top_keys"] = ensure_spec_shape(spec)
        contract = require_runtime_contract(spec)
        main_entry = default_entry_skill(spec)

        entry_path = out_root / Path(contract["entry_script"]).name
        runner_path = out_root / Path(contract["runner_script"]).name
        validator_path = out_root / Path(contract["state_validator_script"]).name
        manifest_path = out_root / Path(contract["runtime_manifest"]).name

        out_root.mkdir(parents=True, exist_ok=True)
        entry_path.write_text(render_entry_wrapper(contract, main_entry), encoding="utf-8", newline="\n")
        runner_path.write_text(render_runner_wrapper(), encoding="utf-8", newline="\n")
        validator_path.write_text(render_state_validator_wrapper(), encoding="utf-8", newline="\n")
        write_json(manifest_path, manifest_payload(contract, main_entry))

        payload["files"] = {
            "entry_script": str(entry_path),
            "runner_script": str(runner_path),
            "state_validator_script": str(validator_path),
            "runtime_manifest": str(manifest_path),
        }
    except Exception as exc:
        payload["status"] = "FAIL"
        payload["error"] = str(exc)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"Error: {exc}")
        return 1

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Generated target runtime assets under {out_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
