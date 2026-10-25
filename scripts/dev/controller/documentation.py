import os
from typing import List, Set, Dict, Any

# Mapping of code paths to affected documentation
DOC_MAP = {
    "stock-signal-bot/backend/app/api": ["docs/contracts/scanner-api.md", "docs/contracts/market-data.md"],
    "stock-signal-bot/backend/app/departments/market_data": ["docs/contracts/market-data.md"],
    "fast-framework/packages/stock-bot-ui/src/components": ["docs/dev/ARCHITECTURE.md"],
    "scripts/dev": ["docs/dev/RUNBOOK.md", "docs/dev/QUALITY_GATES.md"],
    "AGENTS.md": ["docs/dev/RUNBOOK.md"]
}

def get_affected_docs(changed_files: List[str]) -> Set[str]:
    affected = set()
    for f in changed_files:
        norm = f.replace("\\", "/")
        for prefix, docs in DOC_MAP.items():
            if norm.startswith(prefix) or prefix in norm:
                affected.update(docs)
    return affected

def check_doc_sync_status(task_id: str, changed_files: List[str]) -> Dict[str, Any]:
    affected = get_affected_docs(changed_files)
    if not affected:
        return {"status": "NOT_REQUIRED", "affected_docs": []}
    
    # If docs are affected, verify they exist or were acknowledged
    missing = [d for d in affected if not os.path.exists(d)]
    return {
        "status": "SYNCED" if not missing else "PENDING_SYNC",
        "affected_docs": list(affected),
        "missing_docs": missing
    }
