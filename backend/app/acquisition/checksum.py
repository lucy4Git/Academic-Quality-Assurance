"""SHA-256 checksum utilities."""
import hashlib
from pathlib import Path


def compute_sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def compute_sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
