#!/usr/bin/env python3
"""Fetch and verify the official MuSiQue v1.0 answerable development split."""

from __future__ import annotations

import argparse
import hashlib
import io
import urllib.request
import zipfile
from pathlib import Path


URL = "https://drive.usercontent.google.com/download?id=1tGdADlNjWFaHLeZZGShh2IRcpO6Lv24h&export=download&confirm=t"
ARCHIVE_SHA256 = "98f839bf2fd5319f5c688aed77901a6d5c30b3b9f9f691ab9a8ecafb045ee0cd"
MEMBER = "data/musique_ans_v1.0_dev.jsonl"


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def fetch(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / "musique_ans_v1.0_dev.jsonl"
    print("downloading official MuSiQue v1.0 archive (approximately 260 MiB)")
    with urllib.request.urlopen(URL) as response:
        archive = response.read()
    actual_hash = sha256(archive)
    if actual_hash != ARCHIVE_SHA256:
        raise RuntimeError(f"MuSiQue archive SHA-256 mismatch: {actual_hash}")
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        payload = bundle.read(MEMBER)
    target.write_bytes(payload)
    print(f"wrote {target} ({len(payload)} bytes; archive verified)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", type=Path, default=Path("data/musique"))
    args = parser.parse_args()
    fetch(args.destination)


if __name__ == "__main__":
    main()
