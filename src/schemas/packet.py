"""Canonical packet introduced for the migration MVP, not a model output claim.

None means unavailable evidence. Empty visual detections mean an available
specialist with no detections. Ground truth stays in ClaimRecord and must not
be used as graph/model features.
"""
from pydantic import BaseModel, ConfigDict
from src.schemas.claim import ClaimRecord, SchemaVersion, CLAIM_SCHEMA_VERSION
from src.schemas.evidence import (
    NarrativeEvidence, VisualEvidence, ImageQuality, ForensicResult,
)

SCHEMA_VERSION = CLAIM_SCHEMA_VERSION  # Explicitly extended claim/provenance contract.


class EvidencePacket(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: SchemaVersion = SCHEMA_VERSION
    claim: ClaimRecord
    narrative: NarrativeEvidence | None = None
    visual: VisualEvidence | None = None
    image_quality: ImageQuality | None = None
    forensic: ForensicResult | None = None
