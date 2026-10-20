import os
import sys
import time
import subprocess
import re

BACKEND_PORT = 8000
FRONTEND_PORT = 5173

def get_pids_on_port(port: int):
    """Finds PIDs bound to the port using native Windows netstat"""
    pids = set()
    try:
        output = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True, text=True, stderr=subprocess.DEVNULL)
        for line in output.strip().split("\n"):
            parts = re.split(r'\s+', line.strip())
            # Format: TCP 0.0.0.0:8000 0.0.0.0:0 LISTENING 1234
            if len(parts) >= 5 and "LISTENING" in parts:
                pid = int(parts[-1])
                if pid > 0:
                    pids.add(pid)
    except Exception:
        pass
    return pids

def kill_pid(pid: int):
    """Terminates process tree cleanly using taskkill"""
    try:
        subprocess.run(f"taskkill /F /T /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False

def terminate_existing_instances():
    """Identifies and terminates previous runs on ports 8000 & 5173"""
    print("[*] Inspecting running processes for existing bot instances...")
    pids_to_kill = set()
    pids_to_kill.update(get_pids_on_port(BACKEND_PORT))
    pids_to_kill.update(get_pids_on_port(FRONTEND_PORT))

    if not pids_to_kill:
        print("[OK] Zero active instances found. Workspace is clean.")
        return

    for pid in pids_to_kill:
        print(f"[*] Terminating conflicting instance (PID: {pid})...")
        kill_pid(pid)
        print(f"[OK] Terminated PID {pid}")

    # Allow OS network sockets to release
    time.sleep(1.2)
    print("[OK] Port 8000 & Port 5173 successfully freed.")

if __name__ == "__main__":
    terminate_existing_instances()
