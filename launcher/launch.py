import os
import sys
import subprocess
import time
from instance_manager import terminate_existing_instances

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(ROOT_DIR, "stock-signal-bot", "backend")
FRONTEND_DIR = os.path.join(ROOT_DIR, "fast-framework", "packages", "stock-bot-ui")

def launch_application():
    print("=======================================================")
    print("   INDIAN STOCK SIGNAL ENGINE - SINGLE INSTANCE LAUNCHER")
    print("=======================================================")
    
    # 1. Terminate all stale instances
    terminate_existing_instances()
    
    # 2. Start Python FastAPI Backend
    print("[*] Starting backend service on http://127.0.0.1:8000 ...")
    backend_cmd = "python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
    subprocess.Popen(f'start cmd /k "title Stock Signal Backend && cd /d "{BACKEND_DIR}" && {backend_cmd}"', shell=True)
    
    # 3. Start Zuari Reactive Frontend
    print("[*] Starting Zuari UI frontend on http://localhost:5173 ...")
    frontend_cmd = "pnpm dev"
    subprocess.Popen(f'start cmd /k "title Stock Signal UI && cd /d "{FRONTEND_DIR}" && {frontend_cmd}"', shell=True)
    
    time.sleep(2)
    print("\n[OK] Fresh instance initiated successfully!")
    print("     - Web Dashboard: http://localhost:5173")
    print("     - Backend Docs:  http://127.0.0.1:8000/docs")
    print("=======================================================")

if __name__ == "__main__":
    launch_application()
