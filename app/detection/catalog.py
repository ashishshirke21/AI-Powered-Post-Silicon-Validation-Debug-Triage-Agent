from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from app.models.schemas import Severity, Signature

_DEFAULT_CATALOG = Path(__file__).resolve().parents[2] / "data" / "signatures.yaml"


@lru_cache
def load_signatures(path: str | None = None) -> tuple[Signature, ...]:
    catalog_path = Path(path) if path else _DEFAULT_CATALOG
    raw = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or []
    signatures = [
        Signature(
            id=entry["id"],
            name=entry["name"],
            category=entry["category"],
            pattern=entry["pattern"],
            severity=Severity(entry["severity"]),
            description=entry.get("description", ""),
        )
        for entry in raw
    ]
    return tuple(signatures)
