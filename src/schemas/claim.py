"""Esquemas de nivel 'claim' (reclamo) y de imagen fuente del dataset.

Un SourceImage representa una imagen unica del dataset (identificada por
source_image_id). Un Claim representa una instancia de verificacion
(narrativa + imagen) tal como la vera el pipeline de fusion o la demo.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from src.schemas.evidence import DamageAnnotation, DecisionLabel


class Split(str, Enum):
    TRAIN = "train"
    VALIDATION = "validation"
    TEST = "test"


class SourceImage(BaseModel):
    """Una imagen del dataset HITL, ya normalizada al manifest interno."""

    source_image_id: str
    path: str
    split: Optional[Split] = None
    annotations: list[DamageAnnotation] = Field(default_factory=list)
    damage_classes: list[str] = Field(default_factory=list)

    def model_post_init(self, __context) -> None:
        # damage_classes se deriva de annotations si no se provee explicitamente.
        if not self.damage_classes and self.annotations:
            seen: list[str] = []
            for ann in self.annotations:
                if ann.damage_class not in seen:
                    seen.append(ann.damage_class)
            self.damage_classes = seen


class Claim(BaseModel):
    """Instancia de verificacion: narrativa + imagen (ambas opcionales para
    poder representar casos de evidencia faltante, ver benchmark seccion 11).
    """

    claim_id: str
    narrative_text: Optional[str] = None
    image_path: Optional[str] = None
    source_image_id: Optional[str] = None
    expected_label: Optional[DecisionLabel] = None
    metadata: dict = Field(default_factory=dict)


# Public contract name; preserves compatibility with existing Claim users.
ClaimRecord = Claim
