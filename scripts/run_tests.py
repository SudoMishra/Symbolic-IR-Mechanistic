"""Tiny zero-dependency test runner for minimal environments.

The same tests are pytest-compatible; this script only exists so the offline
base environment can verify them before the optional dev dependency is installed.
"""

from __future__ import annotations

import importlib.util
import inspect
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "src"))
    failures = []
    total = 0
    for path in sorted((root / "tests").glob("test_*.py")):
        spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader
        spec.loader.exec_module(module)
        for name, function in inspect.getmembers(module, inspect.isfunction):
            if not name.startswith("test_"):
                continue
            total += 1
            try:
                if tuple(inspect.signature(function).parameters) == ("tmp_path",):
                    with tempfile.TemporaryDirectory() as directory:
                        function(Path(directory))
                else:
                    function()
                print(f"PASS {path.name}::{name}")
            except Exception as exc:
                failures.append((path.name, name, exc))
                print(f"FAIL {path.name}::{name}: {exc}")
    print(f"\n{total - len(failures)}/{total} tests passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
