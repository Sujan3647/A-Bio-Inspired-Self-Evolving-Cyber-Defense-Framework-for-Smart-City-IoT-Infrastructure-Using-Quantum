




"""
ImmunoGrid — Root pytest conftest
Adds all module roots to sys.path so every test file can import
project modules without manual sys.path hacks.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent

# Module roots that need to be on the path
_paths = [
    ROOT,                      # top-level (blockchain/, crypto_layer/, etc.)
    ROOT / "backend",          # backend imports (routers, models, services, …)
    ROOT / "iot_simulator",    # iot_simulator internal imports
]

for p in _paths:
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)
