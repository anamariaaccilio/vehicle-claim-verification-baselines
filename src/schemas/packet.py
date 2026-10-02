"""Canonical packet introduced for the migration MVP, not a model output claim.

None means unavailable evidence. Empty visual detections mean an available
specialist with no detections. Ground truth stays in ClaimRecord and must not
be used as graph/model features.
"""
from typing import Literal
from pydantic import BaseModel, ConfigDict
from src.schemas.claim import ClaimRecord
from src.schemas.evidence import (
    NarrativeEvidence, VisualEvidence, ImageQuality, ForensicResult,
)

SCHEMA_VERSION = "0.1.0"  # First explicit packet contract version, introduced here.


class EvidencePacket(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["0.1.0"] = SCHEMA_VERSION
    claim: ClaimRecord
    narrative: NarrativeEvidence | None = None
    visual: VisualEvidence | None = None
    image_quality: ImageQuality | None = None
    forensic: ForensicResult | None = None
