import os
import time
import unittest
import tempfile
from scripts.dev.controller.storage import init_db, get_connection
from scripts.dev.controller.state import create_task, get_task
from scripts.dev.controller.workflow import WorkflowEngine

class TestWorkflowEngine(unittest.TestCase):
    def setUp(self):
        init_db()
        conn = get_connection()
        with conn:
            conn.execute("DELETE FROM incidents")
            conn.execute("DELETE FROM task_events")
            conn.execute("DELETE FROM tasks")
        conn.close()

    def test_workflow_execution_and_resumability(self):
        task_id = "WF-TEST-001"
        create_task(task_id, "Test Workflow Pipeline", ["docs/dev/START_HERE.md"], ["Docs verified"])

        # Clean up workflows dir
        wf_dir = os.path.join(tempfile.gettempdir(), "test_wf")
        run_id = f"test_run_{int(time.time() * 1000)}"
        engine = WorkflowEngine(run_id=run_id)

        # Run pipeline
        res = engine.run_or_resume(task_id)
        self.assertEqual(res["status"], "COMPLETED")
        self.assertEqual(res["stages"]["validate-environment"]["status"], "COMPLETED")
        self.assertEqual(res["stages"]["record-checkpoint"]["status"], "COMPLETED")

        # Verify task is now marked DONE in controller
        task = get_task(task_id)
        self.assertEqual(task["status"], "DONE")

        # Re-running the same run_id resumes idempotently without re-executing completed stages
        engine_resume = WorkflowEngine(run_id=run_id)
        res_resume = engine_resume.run_or_resume(task_id)
        self.assertEqual(res_resume["status"], "COMPLETED")

if __name__ == "__main__":
    unittest.main()
