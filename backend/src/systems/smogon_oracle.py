import json
import os
import subprocess
from typing import Any, Dict, Optional


BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class SmogonDamageOracle:
    def __init__(self, backend_dir: str = BACKEND_DIR):
        self.backend_dir = backend_dir

    def is_available(self) -> bool:
        return os.path.exists(os.path.join(self.backend_dir, "node_modules", "@smogon", "calc"))

    def calculate(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.is_available():
            return None

        proc = subprocess.run(
            ["npm", "--prefix", self.backend_dir, "run", "smogon:damage", "--silent"],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            timeout=5,
            check=False,
        )
        if proc.returncode != 0:
            return {
                "error": proc.stderr.strip() or proc.stdout.strip() or "Smogon damage oracle failed",
                "returncode": proc.returncode,
            }
        return json.loads(proc.stdout)


smogon_damage_oracle = SmogonDamageOracle()
