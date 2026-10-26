#!/usr/bin/env python3
"""Download the revision-pinned public LongProc ToM dataset and prompt."""

from __future__ import annotations

import argparse
import hashlib
import urllib.request
from pathlib import Path


REVISION = "673ec4c230876e941d674116d66d28783c186b15"
BASE_URL = f"https://raw.githubusercontent.com/princeton-pli/LongProc/{REVISION}/data/tom_tracking"
FILES = {
    "tom_tracking_2k.json": "c7a03d3b71ad6b6a6eec45a7dc86cf911d8786541bce4884f4b6a4308bcf6e76",
    "prompts.yaml": "1a15f592f722eea0e2e8622de960ea38ee4b594d09a58ecd91704f34db56908b",
}


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def fetch(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for filename, expected_hash in FILES.items():
        target = destination / filename
        if target.exists() and sha256(target.read_bytes()) == expected_hash:
            print(f"verified {target}")
            continue
        with urllib.request.urlopen(f"{BASE_URL}/{filename}") as response:
            payload = response.read()
        actual_hash = sha256(payload)
        if actual_hash != expected_hash:
            raise RuntimeError(f"SHA-256 mismatch for {filename}: {actual_hash}")
        target.write_bytes(payload)
        print(f"downloaded {target}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", type=Path, default=Path("data/longproc/tom_tracking"))
    args = parser.parse_args()
    fetch(args.destination)


if __name__ == "__main__":
    main()
