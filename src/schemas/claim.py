"""Esquemas de nivel 'claim' (reclamo) y de imagen fuente del dataset.

Un SourceImage representa una imagen unica del dataset (identificada por
source_image_id). Un Claim representa una instancia de verificacion
(narrativa + imagen) tal como la vera el pipeline de fusion o la demo.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.schemas.evidence import DamageAnnotation, DecisionLabel, CANONICAL_DAMAGE_CLASSES


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


CLAIM_SCHEMA_VERSION = "0.2.0"
SchemaVersion = Literal["0.2.0"]
Condition = Literal["C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10"]


class ClaimProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")
    synthetic_claim: Literal[True] = True
    dataset: str = Field(min_length=1)
    dataset_version: int
    source_group_id: str = Field(min_length=1)
    source_image_path: str = Field(min_length=1)
    source_image_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    annotation_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    generator_version: str
    seed: int
    narrative_template_id: str


class ClaimTransformation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation: str = Field(min_length=1)
    parameters: dict = Field(default_factory=dict)
    seed: int
    image_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    donor_source_image_ids: list[str] = Field(default_factory=list)


class Claim(BaseModel):
    """Instancia de verificacion: narrativa + imagen (ambas opcionales para
    poder representar casos de evidencia faltante, ver benchmark seccion 11).
    """

    claim_id: str = Field(min_length=1)
    schema_version: SchemaVersion = CLAIM_SCHEMA_VERSION
    narrative_text: Optional[str] = None
    image_path: Optional[str] = None
    source_image_id: Optional[str] = None
    expected_label: Optional[DecisionLabel] = None
    metadata: dict = Field(default_factory=dict)
    split: Optional[Split] = None
    condition: Optional[Condition] = None
    annotation_reference: Optional[str] = None
    annotated_damage_classes: list[str] = Field(default_factory=list)
    parent_claim_id: Optional[str] = None
    provenance: Optional[ClaimProvenance] = None
    transformation: Optional[ClaimTransformation] = None

    @field_validator("annotated_damage_classes")
    @classmethod
    def valid_damage_classes(cls, values):
        if any(value not in CANONICAL_DAMAGE_CLASSES for value in values) or len(values) != len(set(values)):
            raise ValueError("Expected unique canonical damage classes")
        return values

    @model_validator(mode="after")
    def complete_benchmark_record(self):
        # Legacy minimal Claim instances remain valid. Conditional records must
        # have traceability; benchmark-level semantics are checked by the auditor.
        if self.condition is not None:
            if not all([self.source_image_id, self.split, self.expected_label,
                        self.annotation_reference, self.provenance, self.transformation]):
                raise ValueError("Benchmark claims require source, split, label and complete provenance")
            if self.transformation.seed != self.provenance.seed:
                raise ValueError("Transformation and provenance seeds differ")
            if self.condition == "C0" and self.parent_claim_id is not None:
                raise ValueError("C0 has no parent claim")
            if self.condition != "C0" and not self.parent_claim_id:
                raise ValueError("Variant must reference parent C0 claim")
        return self


# Public contract name; preserves compatibility with existing Claim users.
ClaimRecord = Claim
