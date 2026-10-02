"""PASO 7: logging de cada analisis de la demo en
artifacts/demo_runs/<timestamp>.json.

Nunca guarda expected_label/expected_condition como si fuera parte del
input o del feature_values del modelo -- ver src/fusion/features.py, cuya
firma no acepta ningun argumento de ese tipo. case_id se guarda solo como
metadata de trazabilidad (que caso preparado origino esta corrida), no se
usa en ningun calculo.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.fusion.inference import AnalysisResult

ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "artifacts" / "demo_runs"


def _hash_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()[:16]


def log_run(
    narrative_text: str | None,
    image_path: str | Path | None,
    result: AnalysisResult,
    source_image_id: str | None = None,
    case_id: str | None = None,
) -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")

    image_hash = _hash_file(Path(image_path)) if image_path else None

    narrative_result = result.narrative_result
    visual_evidence = result.visual_evidence

    payload: dict[str, Any] = {
        "timestamp_utc": timestamp,
        "case_id": case_id,
        "narrative": narrative_text,
        "image_path": str(image_path) if image_path else None,
        "image_sha256_16": image_hash,
        "source_image_id": source_image_id,
        "narrative_output": narrative_result.to_evidence().model_dump() if narrative_result else None,
        "narrative_inference_time_seconds": (
            narrative_result.inference_time_seconds if narrative_result else None
        ),
        "visual_output": visual_evidence.model_dump() if visual_evidence else None,
        "image_quality": result.image_quality.model_dump() if result.image_quality else None,
        "feature_values": result.features.as_dict(),
        "triggered_rule": result.rule_trace.as_dict(),
        "prediction": result.rule_trace.decision.value,
        "model_versions": {
            "narrative_model": narrative_result.model_name if narrative_result else None,
            "narrative_model_revision": narrative_result.model_revision if narrative_result else None,
            "visual_model": visual_evidence.model_name if visual_evidence else None,
        },
    }

    out_path = ARTIFACTS_DIR / f"{timestamp}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return out_path
