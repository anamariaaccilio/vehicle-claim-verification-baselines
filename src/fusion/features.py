"""FASE 4: construccion del feature vector plano para el Rule Baseline B0.

Metrica de semantic mismatch: distancia de Jensen-Shannon (log base 2,
implementada sin dependencias externas) entre la distribucion normalizada
de danio narrativo (NarrativeResult.normalized_scores) y una distribucion
analoga derivada de las detecciones visuales (maxima confianza por clase,
normalizada). Se eligio JS y no KL porque JS es simetrica, acotada en
[0, 1] y esta bien definida incluso cuando una clase tiene probabilidad 0
en una de las dos distribuciones -- algo esperable aqui, ya que ni la
narrativa ni la vision van a mencionar/detectar las 8 clases a la vez.

IMPORTANTE: este modulo NUNCA recibe ni usa expected_label, label real, ID
de caso ni metadata de perturbacion para calcular ningun feature. Solo
consume las salidas de los especialistas (narrativa, visual, calidad de
imagen).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from src.forensic.image_quality import quality_status
from src.narrative.nli_extractor import NarrativeResult
from src.schemas.evidence import CANONICAL_DAMAGE_CLASSES, ImageQuality, VisualEvidence


def visual_scores_from_evidence(evidence: VisualEvidence) -> dict[str, float]:
    """Un score por clase canonica = maxima confianza observada entre las
    detecciones de esa clase (0.0 si no hubo ninguna)."""
    scores = {c: 0.0 for c in CANONICAL_DAMAGE_CLASSES}
    for det in evidence.detections:
        if det.confidence is not None:
            scores[det.damage_class] = max(scores[det.damage_class], det.confidence)
    return scores


def normalize(scores: dict[str, float]) -> dict[str, float]:
    total = sum(scores.values())
    if total <= 0:
        return {k: 0.0 for k in scores}
    return {k: v / total for k, v in scores.items()}


def jensen_shannon_distance(p: dict[str, float], q: dict[str, float]) -> float:
    """Distancia JS (raiz de la divergencia JS, log base 2) entre dos
    distribuciones sobre CANONICAL_DAMAGE_CLASSES. Rango [0, 1]:
    0 = distribuciones identicas, 1 = soportes disjuntos."""
    keys = CANONICAL_DAMAGE_CLASSES
    p_vec = [p.get(k, 0.0) for k in keys]
    q_vec = [q.get(k, 0.0) for k in keys]
    m_vec = [(pi + qi) / 2 for pi, qi in zip(p_vec, q_vec)]

    def _kl(a_vec: list[float], b_vec: list[float]) -> float:
        total = 0.0
        for a, b in zip(a_vec, b_vec):
            if a > 0 and b > 0:
                total += a * math.log2(a / b)
        return total

    js_divergence = 0.5 * _kl(p_vec, m_vec) + 0.5 * _kl(q_vec, m_vec)
    js_divergence = max(js_divergence, 0.0)  # proteger contra ruido de punto flotante
    return math.sqrt(js_divergence)


@dataclass
class FeatureVector:
    text_missing: bool
    image_missing: bool
    visual_available: bool

    text_top_damage: str | None
    text_top_confidence: float | None

    visual_top_damage: str | None
    visual_top_confidence: float | None

    semantic_mismatch: float | None
    semantic_agreement: float | None

    blur_score: float | None
    image_quality_status: str | None

    def as_dict(self) -> dict:
        return dict(self.__dict__)


def build_feature_vector(
    narrative_result: NarrativeResult | None,
    visual_evidence: VisualEvidence | None,
    image_quality: ImageQuality | None,
    visual_model_available: bool,
) -> FeatureVector:
    """narrative_result es None si no hay narrativa (texto vacio/ausente).
    image_quality es None si no hay imagen. visual_evidence es None si no
    hay imagen O si el Damage Specialist no esta disponible."""
    text_missing = narrative_result is None
    image_missing = image_quality is None

    visual_available = (
        not image_missing and visual_model_available and visual_evidence is not None
    )

    text_top_damage = narrative_result.top_damage if narrative_result else None
    text_top_confidence = narrative_result.top_confidence if narrative_result else None

    visual_top_damage = None
    visual_top_confidence = None
    semantic_mismatch = None
    semantic_agreement = None

    if visual_available and visual_evidence is not None:
        visual_scores = visual_scores_from_evidence(visual_evidence)
        if any(v > 0 for v in visual_scores.values()):
            visual_top_damage = max(visual_scores, key=visual_scores.get)
            visual_top_confidence = visual_scores[visual_top_damage]

        if not text_missing:
            visual_dist = normalize(visual_scores)
            semantic_mismatch = jensen_shannon_distance(
                narrative_result.normalized_scores, visual_dist
            )
            semantic_agreement = 1.0 - semantic_mismatch

    blur_score = image_quality.laplacian_variance if image_quality else None
    quality_label = quality_status(image_quality) if image_quality else None

    return FeatureVector(
        text_missing=text_missing,
        image_missing=image_missing,
        visual_available=visual_available,
        text_top_damage=text_top_damage,
        text_top_confidence=text_top_confidence,
        visual_top_damage=visual_top_damage,
        visual_top_confidence=visual_top_confidence,
        semantic_mismatch=semantic_mismatch,
        semantic_agreement=semantic_agreement,
        blur_score=blur_score,
        image_quality_status=quality_label,
    )
