"""FASE 4: orquestacion end-to-end del Rule Baseline B0 (Narrative +
Damage + Image Quality -> features -> rules). NO incluye late fusion /
LogisticRegression (eso es FASE 5, no implementado todavia).

Este es el punto unico que reutilizan demo/app.py y los tests, para no
duplicar la logica de orquestacion.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.damage.inference import DamageSpecialist
from src.forensic.image_quality import assess_image_quality
from src.fusion.features import FeatureVector, build_feature_vector
from src.fusion.rules import RuleTrace, evaluate
from src.narrative.nli_extractor import NarrativeExtractor, NarrativeResult
from src.schemas.evidence import ImageQuality, VisualEvidence


@dataclass
class AnalysisResult:
    narrative_result: NarrativeResult | None
    visual_evidence: VisualEvidence | None
    image_quality: ImageQuality | None
    features: FeatureVector
    rule_trace: RuleTrace


def analyze(
    narrative_text: str | None,
    image_path: str | Path | None,
    narrative_extractor: NarrativeExtractor,
    damage_specialist: DamageSpecialist,
) -> AnalysisResult:
    """Corre el pipeline completo para una instancia (Claim). No usa ningun
    label/expected_condition/metadata de perturbacion como input."""
    narrative_result: NarrativeResult | None = None
    if narrative_text is not None and narrative_text.strip():
        narrative_result = narrative_extractor.extract(narrative_text)

    image_quality: ImageQuality | None = None
    visual_evidence: VisualEvidence | None = None
    visual_model_available = damage_specialist.is_available

    if image_path is not None:
        image_quality = assess_image_quality(image_path)
        if visual_model_available and not image_quality.is_corrupted:
            visual_evidence = damage_specialist.predict(image_path)

    features = build_feature_vector(
        narrative_result=narrative_result,
        visual_evidence=visual_evidence,
        image_quality=image_quality,
        visual_model_available=visual_model_available,
    )
    rule_trace = evaluate(features)

    return AnalysisResult(
        narrative_result=narrative_result,
        visual_evidence=visual_evidence,
        image_quality=image_quality,
        features=features,
        rule_trace=rule_trace,
    )
