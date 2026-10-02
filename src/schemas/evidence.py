"""Esquemas de evidencia: taxonomia de danio y outputs de cada especialista
(narrativa, visual, calidad de imagen, forense).

Estos esquemas son el contrato de datos entre los modulos de FASE 2-8.
No implementan logica de fusion ni de grafos: son solo estructuras.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator

# Canonical taxonomy is read from the existing repository configuration.
# Local development uses an editable installation of this repository.
from pathlib import Path
import yaml

LABELS_CONFIG_PATH = Path(__file__).resolve().parents[2] / "configs" / "labels.yaml"
with LABELS_CONFIG_PATH.open(encoding="utf-8") as _stream:
    _labels = yaml.safe_load(_stream)
CANONICAL_DAMAGE_CLASSES: tuple[str, ...] = tuple(_labels["canonical_classes"])
HITL_TO_CANONICAL: dict[str, str] = dict(_labels["hitl_to_canonical"])


class DecisionLabel(str, Enum):
    SUPPORTED = "SUPPORTED"
    SUSPICIOUS = "SUSPICIOUS"
    INSUFFICIENT = "INSUFFICIENT"


class BoundingBox(BaseModel):
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    @field_validator("x_max")
    @classmethod
    def _x_order(cls, v: float, info) -> float:
        x_min = info.data.get("x_min")
        if x_min is not None and v < x_min:
            raise ValueError("x_max debe ser >= x_min")
        return v

    @field_validator("y_max")
    @classmethod
    def _y_order(cls, v: float, info) -> float:
        y_min = info.data.get("y_min")
        if y_min is not None and v < y_min:
            raise ValueError("y_max debe ser >= y_min")
        return v


class Polygon(BaseModel):
    """Lista de puntos (x, y) en coordenadas de pixel, tal como se exportan
    en las anotaciones poligonales del dataset HITL."""

    points: list[tuple[float, float]] = Field(min_length=3)


class DamageAnnotation(BaseModel):
    """Una anotacion (ground-truth o prediccion) de danio sobre una imagen."""

    damage_class: str
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    bbox: Optional[BoundingBox] = None
    polygon: Optional[Polygon] = None

    @field_validator("damage_class")
    @classmethod
    def _must_be_canonical(cls, v: str) -> str:
        if v not in CANONICAL_DAMAGE_CLASSES:
            raise ValueError(
                f"damage_class '{v}' no pertenece a la taxonomia canonica "
                f"{CANONICAL_DAMAGE_CLASSES}"
            )
        return v


class ImageQuality(BaseModel):
    """Metricas de calidad de imagen. Representan CALIDAD, no fraude."""

    width: int
    height: int
    aspect_ratio: float
    file_size_bytes: int
    file_format: str
    laplacian_variance: Optional[float] = None
    is_corrupted: bool = False


class ForensicResult(BaseModel):
    """Resultado del especialista forense. Si el modelo (p. ej. TruFor) no
    esta disponible, available=False y el resto de campos deben ser None.
    Nunca se debe simular un resultado cuando available=False.
    """

    available: bool
    method: Optional[str] = None
    score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    reliability: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    is_diagnostic_heuristic: bool = False


class NarrativeEvidence(BaseModel):
    """Salida del NarrativeExtractor (NLI) sobre el texto del reclamo."""

    raw_scores: dict[str, float]
    normalized_scores: dict[str, float]
    model_name: str
    model_revision: Optional[str] = None
    device: str


class VisualEvidence(BaseModel):
    """Salida del detector/segmentador de danio sobre una imagen."""

    detections: list[DamageAnnotation]
    model_name: str
    image_width: int
    image_height: int
