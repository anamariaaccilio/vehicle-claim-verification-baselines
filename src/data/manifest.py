"""Lectura/escritura del manifest interno (JSONL, UTF-8).

El manifest es la unica fuente de verdad sobre que imagenes existen, donde
estan y a que split pertenecen. Lo produce src/data/hitl_adapter.py +
src/data/split.py; lo consumen los especialistas de vision (FASE 3) y los
scripts de benchmark (seccion 11).
"""
from __future__ import annotations

import json
from pathlib import Path

from src.schemas.claim import SourceImage


def save_manifest(records: list[SourceImage], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(record.model_dump_json())
            f.write("\n")


def load_manifest(path: str | Path) -> list[SourceImage]:
    path = Path(path)
    records: list[SourceImage] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(SourceImage.model_validate(json.loads(line)))
    return records
