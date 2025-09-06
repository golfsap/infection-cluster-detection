import json
from pathlib import Path
from typing import Dict

RESULT_DIR = Path("data/results")
RESULT_DIR.mkdir(parents=True, exist_ok=True)

def save_clusters(clusters: Dict, name: str = "last_run.json") -> Path: 
    out = RESULT_DIR / name
    with out.open("w") as f:
        json.dump(clusters, f, indent=2)
    return out

def load_clusters(name: str = "last_run.json") -> Dict:
    path = RESULT_DIR / name
    if not path.exists():
        return {}
    with path.open() as f:
        return json.load(f)