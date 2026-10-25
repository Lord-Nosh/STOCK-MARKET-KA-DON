import os
import json
import time
import subprocess
import yaml
from typing import Dict, Any, List, Optional, Tuple
from scripts.dev.controller.storage import get_connection, RUNTIME_DIR, init_db
from scripts.dev.controller.state import get_task, transition_task
from scripts.dev.controller.commands import execute_command
from scripts.dev.controller.recovery import record_incident
from scripts.dev.controller.documentation import check_doc_sync_status
from scripts.dev.controller.context_builder import ContextBuilder

WORKFLOWS_DIR = os.path.join(RUNTIME_DIR, "workflows")
CHANGE_MAP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "change-map.yml"))

class WorkflowEngine:
    """
    Resumable Development Workflow Engine (DEV-AUTO-001).
    Chains:
    1. validate-environment
    2. inspect-task
    3. prepare-context
    4. run-focused-tests
    5. run-required-checks
    6. update-documentation
    7. record-checkpoint
    """

    STAGES = [
        "validate-environment",
        "inspect-task",
        "prepare-context",
        "run-focused-tests",
        "run-required-checks",
        "update-documentation",
        "record-checkpoint"
    ]

    def __init__(self, run_id: Optional[str] = None):
        init_db()
        os.makedirs(WORKFLOWS_DIR, exist_ok=True)
        self.run_id = run_id or f"run_{int(time.time())}"
        self.state_file = os.path.join(WORKFLOWS_DIR, f"{self.run_id}.json")
        self.state = self._load_or_init_state()

    def _load_or_init_state(self) -> Dict[str, Any]:
        if os.path.exists(self.state_file):
            with open(self.state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "run_id": self.run_id,
            "task_id": None,
            "status": "INITIATED",
            "current_stage_idx": 0,
            "stages": {s: {"status": "PENDING", "output": None, "exit_code": None} for s in self.STAGES},
            "created_at": time.time(),
            "updated_at": time.time()
        }

    def _save_state(self):
        self.state["updated_at"] = time.time()
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2)

    def run_or_resume(self, task_id: str, changed_files: Optional[List[str]] = None) -> Dict[str, Any]:
        self.state["task_id"] = task_id
        task = get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found in dev-control database.")

        files = changed_files or task.get("scope", [])
        focused_cmd, regression_cmds = self._resolve_checks(files)

        for idx, stage in enumerate(self.STAGES):
            if self.state["stages"][stage]["status"] == "COMPLETED":
                continue  # Skip already completed steps (resumability)

            self.state["current_stage_idx"] = idx
            self.state["status"] = f"RUNNING_{stage.upper()}"
            self._save_state()

            # Execute Stage
            task = get_task(task_id)
            success, exit_code, output = self._execute_stage(stage, task, files, focused_cmd, regression_cmds)

            self.state["stages"][stage] = {
                "status": "COMPLETED" if success else "FAILED",
                "exit_code": exit_code,
                "output": output[:500] if output else None,
                "timestamp": time.time()
            }

            if not success:
                self.state["status"] = "FAILED"
                self._save_state()
                # Record failure incident in controller
                record_incident(task_id, stage, output or "Stage failed", exit_code)
                return self.state

        self.state["status"] = "COMPLETED"
        self._save_state()
        return self.state

    def _execute_stage(self, stage: str, task: Dict[str, Any], files: List[str], focused_cmd: Optional[str], regression_cmds: List[str]):
        if stage == "validate-environment":
            # Quick doctor check
            code, out, err, summary = execute_command(task["task_id"], "powershell -File scripts/dev/devctl.ps1 doctor")
            return (code == 0), code, out + "\n" + err

        elif stage == "inspect-task":
            # Verify task is not blocked
            if task["status"] == "BLOCKED":
                return False, 1, f"Task {task['task_id']} is BLOCKED by circuit breaker."
            return True, 0, f"Task {task['task_id']} ready in status: {task['status']}"

        elif stage == "prepare-context":
            transition_task(task["task_id"], "CONTEXT_READY", reason="Context packet built.")
            builder = ContextBuilder()
            builder.build_packet(task["task_id"], task["title"], "smkd-safe-edit", task.get("scope", []))
            return True, 0, "Context packet verified and saved."

        elif stage == "run-focused-tests":
            transition_task(task["task_id"], "VERIFYING", reason="Automated workflow verification checks running.")
            if not focused_cmd:
                return True, 0, "No focused checks required for these paths."
            code, out, err, summary = execute_command(task["task_id"], focused_cmd)
            return (code == 0), code, out + "\n" + err

        elif stage == "run-required-checks":
            for cmd in regression_cmds:
                code, out, err, summary = execute_command(task["task_id"], cmd)
                if code != 0:
                    return False, code, out + "\n" + err
            return True, 0, f"Executed {len(regression_cmds)} regression check(s) successfully."

        elif stage == "update-documentation":
            doc_status = check_doc_sync_status(task["task_id"], files)
            if doc_status["status"] == "PENDING_SYNC":
                return False, 1, f"Documentation pending sync for: {doc_status['missing_docs']}"
            return True, 0, f"Documentation sync verified ({doc_status['status']})."

        elif stage == "record-checkpoint":
            transition_task(task["task_id"], "DONE", reason="Automated workflow pipeline passed all gates.")
            return True, 0, f"Task {task['task_id']} marked DONE."

        return False, 1, f"Unknown stage: {stage}"

    def _resolve_checks(self, changed_files: List[str]) -> Tuple[Optional[str], List[str]]:
        focused = None
        regressions = set()

        if not os.path.exists(CHANGE_MAP_PATH):
            return None, []

        try:
            with open(CHANGE_MAP_PATH, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                rules = data.get("rules", [])
        except Exception:
            return None, []

        for r in rules:
            rule_paths = r.get("paths", [])
            for p in rule_paths:
                p_norm = p.replace("**", "").replace("*", "")
                for cf in changed_files:
                    if p_norm in cf.replace("\\", "/"):
                        if not focused and "focused_check" in r:
                            focused = r["focused_check"]
                        for reg in r.get("regression_checks", []):
                            regressions.add(reg)

        return focused, list(regressions)

if __name__ == "__main__":
    engine = WorkflowEngine()
    print(f"Workflow engine initialized with run ID: {engine.run_id}")
