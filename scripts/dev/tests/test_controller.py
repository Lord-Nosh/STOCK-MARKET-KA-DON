import os
import unittest
import tempfile
import sqlite3
from scripts.dev.controller.storage import init_db, get_connection, DB_PATH
from scripts.dev.controller.state import create_task, get_task, transition_task
from scripts.dev.controller.recovery import record_incident
from scripts.dev.controller.documentation import check_doc_sync_status

class TestDevelopmentController(unittest.TestCase):
    def setUp(self):
        init_db()
        conn = get_connection()
        with conn:
            conn.execute("DELETE FROM incidents")
            conn.execute("DELETE FROM task_events")
            conn.execute("DELETE FROM tasks")
        conn.close()

    def test_task_lifecycle_transitions(self):
        task_id = "CTRL-TEST-001"
        task = create_task(task_id, "Test Lifecycle", ["file_a.py"], ["All tests pass"])
        self.assertEqual(task["status"], "READY")

        # READY -> IN_PROGRESS
        t_prog = transition_task(task_id, "IN_PROGRESS", reason="Started")
        self.assertEqual(t_prog["status"], "IN_PROGRESS")

        # IN_PROGRESS -> VERIFYING
        t_ver = transition_task(task_id, "VERIFYING", reason="Checking")
        self.assertEqual(t_ver["status"], "VERIFYING")

        # VERIFYING -> DONE
        t_done = transition_task(task_id, "DONE", reason="Verified")
        self.assertEqual(t_done["status"], "DONE")

    def test_illegal_state_transition_rejected(self):
        task_id = "CTRL-TEST-002"
        create_task(task_id, "Test Illegal Transition", [], [])
        with self.assertRaises(ValueError):
            # Cannot jump directly from READY to DONE without VERIFYING
            transition_task(task_id, "DONE")

    def test_circuit_breaker_on_repeated_failure(self):
        task_id = "CTRL-TEST-003"
        create_task(task_id, "Test Circuit Breaker", [], [])
        transition_task(task_id, "IN_PROGRESS")

        inc1 = record_incident(task_id, "pnpm run build", "SyntaxError in manifest", 1)
        self.assertFalse(inc1["is_blocked"])
        self.assertEqual(inc1["attempt_count"], 1)

        # Same failure 2nd time triggers circuit breaker and BLOCKS task
        inc2 = record_incident(task_id, "pnpm run build", "SyntaxError in manifest", 1)
        self.assertTrue(inc2["is_blocked"])
        self.assertEqual(inc2["attempt_count"], 2)

        task = get_task(task_id)
        self.assertEqual(task["status"], "BLOCKED")

    def test_doc_sync_mapping(self):
        res_no_doc = check_doc_sync_status("CTRL-TEST-004", ["styles/main.css"])
        self.assertEqual(res_no_doc["status"], "NOT_REQUIRED")

        res_api_doc = check_doc_sync_status("CTRL-TEST-004", ["stock-signal-bot/backend/app/api/routes.py"])
        self.assertIn("docs/contracts/scanner-api.md", res_api_doc["affected_docs"])

if __name__ == "__main__":
    unittest.main()
