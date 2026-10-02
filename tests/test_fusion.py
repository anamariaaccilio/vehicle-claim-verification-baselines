"""Tests de FASE 4: features (semantic mismatch) y Rule Baseline B0."""
import inspect

import pytest

from src.fusion.features import (
    FeatureVector,
    build_feature_vector,
    jensen_shannon_distance,
    normalize,
    visual_scores_from_evidence,
)
from src.fusion.rules import RuleTrace, evaluate, load_rules_config
from src.narrative.nli_extractor import NarrativeResult
from src.schemas.evidence import (
    CANONICAL_DAMAGE_CLASSES,
    BoundingBox,
    DamageAnnotation,
    DecisionLabel,
    ImageQuality,
    VisualEvidence,
)


def _narrative_result(top_damage="dent", scores=None) -> NarrativeResult:
    scores = scores or {c: (0.9 if c == top_damage else 0.01) for c in CANONICAL_DAMAGE_CLASSES}
    total = sum(scores.values())
    normalized = {k: v / total for k, v in scores.items()}
    return NarrativeResult(
        raw_scores=scores,
        normalized_scores=normalized,
        top_damage=top_damage,
        top_confidence=scores[top_damage],
        entropy=0.0,
        model_name="test-model",
        model_revision=None,
        device="cpu",
        inference_time_seconds=0.01,
    )


def _visual_evidence(damage_class="dent", confidence=0.9) -> VisualEvidence:
    return VisualEvidence(
        detections=[
            DamageAnnotation(
                damage_class=damage_class,
                confidence=confidence,
                bbox=BoundingBox(x_min=0, y_min=0, x_max=10, y_max=10),
            )
        ],
        model_name="test-yolo",
        image_width=100,
        image_height=100,
    )


def _good_quality() -> ImageQuality:
    return ImageQuality(
        width=400,
        height=400,
        aspect_ratio=1.0,
        file_size_bytes=1000,
        file_format="PNG",
        laplacian_variance=500.0,
        is_corrupted=False,
    )


# ---------------------------------------------------------------------------
# semantic mismatch (Jensen-Shannon distance)
# ---------------------------------------------------------------------------

def test_jensen_shannon_distance_is_zero_for_identical_distributions():
    p = {c: 1 / len(CANONICAL_DAMAGE_CLASSES) for c in CANONICAL_DAMAGE_CLASSES}
    assert jensen_shannon_distance(p, p) == pytest.approx(0.0, abs=1e-9)


def test_jensen_shannon_distance_is_near_one_for_disjoint_distributions():
    p = {c: 0.0 for c in CANONICAL_DAMAGE_CLASSES}
    p["dent"] = 1.0
    q = {c: 0.0 for c in CANONICAL_DAMAGE_CLASSES}
    q["corrosion"] = 1.0
    assert jensen_shannon_distance(p, q) == pytest.approx(1.0, abs=1e-6)


def test_jensen_shannon_distance_is_symmetric():
    p = {"dent": 0.7, "crack": 0.3, **{c: 0.0 for c in CANONICAL_DAMAGE_CLASSES if c not in ("dent", "crack")}}
    q = {"dent": 0.2, "corrosion": 0.8, **{c: 0.0 for c in CANONICAL_DAMAGE_CLASSES if c not in ("dent", "corrosion")}}
    assert jensen_shannon_distance(p, q) == pytest.approx(jensen_shannon_distance(q, p))


def test_visual_scores_takes_max_confidence_per_class():
    evidence = VisualEvidence(
        detections=[
            DamageAnnotation(damage_class="dent", confidence=0.4),
            DamageAnnotation(damage_class="dent", confidence=0.8),
            DamageAnnotation(damage_class="scratch", confidence=0.5),
        ],
        model_name="m",
        image_width=10,
        image_height=10,
    )
    scores = visual_scores_from_evidence(evidence)
    assert scores["dent"] == 0.8
    assert scores["scratch"] == 0.5
    assert scores["crack"] == 0.0


# ---------------------------------------------------------------------------
# build_feature_vector
# ---------------------------------------------------------------------------

def test_feature_vector_flags_missing_text():
    fv = build_feature_vector(None, None, None, visual_model_available=False)
    assert fv.text_missing is True
    assert fv.image_missing is True


def test_feature_vector_agreement_high_when_same_top_damage():
    narrative = _narrative_result(top_damage="dent")
    visual = _visual_evidence(damage_class="dent", confidence=0.95)
    quality = _good_quality()

    fv = build_feature_vector(narrative, visual, quality, visual_model_available=True)

    assert fv.visual_available is True
    assert fv.semantic_mismatch is not None
    assert fv.semantic_mismatch < 0.3  # distribuciones concentradas en la misma clase


def test_feature_vector_mismatch_high_when_different_top_damage():
    narrative = _narrative_result(top_damage="dent")
    visual = _visual_evidence(damage_class="corrosion", confidence=0.95)
    quality = _good_quality()

    fv = build_feature_vector(narrative, visual, quality, visual_model_available=True)

    assert fv.semantic_mismatch > 0.5


def test_feature_vector_visual_unavailable_when_model_not_available():
    narrative = _narrative_result()
    quality = _good_quality()
    fv = build_feature_vector(narrative, None, quality, visual_model_available=False)
    assert fv.visual_available is False
    assert fv.semantic_mismatch is None


def test_feature_vector_stable_dimensionality():
    empty = build_feature_vector(None, None, None, visual_model_available=False)
    full = build_feature_vector(_narrative_result(), _visual_evidence(), _good_quality(), True)
    assert set(empty.as_dict().keys()) == set(full.as_dict().keys())


def test_feature_vector_signature_never_takes_a_label_argument():
    # Verificacion estructural: build_feature_vector no debe aceptar
    # expected_label / label real / case_id / perturbation metadata.
    params = set(inspect.signature(build_feature_vector).parameters)
    forbidden = {"label", "expected_label", "expected_condition", "case_id", "perturbation"}
    assert params.isdisjoint(forbidden)


# ---------------------------------------------------------------------------
# rule engine
# ---------------------------------------------------------------------------

def _fv(**overrides) -> FeatureVector:
    base = dict(
        text_missing=False,
        image_missing=False,
        visual_available=True,
        text_top_damage="dent",
        text_top_confidence=0.9,
        visual_top_damage="dent",
        visual_top_confidence=0.9,
        semantic_mismatch=0.1,
        semantic_agreement=0.9,
        blur_score=500.0,
        image_quality_status="GOOD",
    )
    base.update(overrides)
    return FeatureVector(**base)


def test_r01_text_missing_triggers_insufficient():
    trace = evaluate(_fv(text_missing=True))
    assert trace.rule_id == "R01"
    assert trace.decision == DecisionLabel.INSUFFICIENT


def test_r02_image_missing_triggers_insufficient():
    trace = evaluate(_fv(image_missing=True))
    assert trace.rule_id == "R02"
    assert trace.decision == DecisionLabel.INSUFFICIENT


def test_r03_low_image_quality_triggers_insufficient():
    trace = evaluate(_fv(image_quality_status="INSUFFICIENT"))
    assert trace.rule_id == "R03"
    assert trace.decision == DecisionLabel.INSUFFICIENT


def test_r06_visual_model_unavailable_triggers_insufficient():
    trace = evaluate(_fv(visual_available=False, semantic_mismatch=None))
    assert trace.rule_id == "R06"
    assert trace.decision == DecisionLabel.INSUFFICIENT


def test_r04_high_mismatch_triggers_suspicious():
    cfg = load_rules_config()
    threshold = cfg["semantic_mismatch_threshold"]
    trace = evaluate(_fv(semantic_mismatch=threshold + 0.1))
    assert trace.rule_id == "R04"
    assert trace.decision == DecisionLabel.SUSPICIOUS
    assert trace.threshold == threshold


def test_r05_compatible_evidence_triggers_supported():
    cfg = load_rules_config()
    threshold = cfg["semantic_mismatch_threshold"]
    trace = evaluate(_fv(semantic_mismatch=max(threshold - 0.1, 0.0)))
    assert trace.rule_id == "R05"
    assert trace.decision == DecisionLabel.SUPPORTED


def test_rule_thresholds_come_from_yaml_not_hardcoded():
    cfg = load_rules_config()
    custom_cfg = {"semantic_mismatch_threshold": 0.01}
    trace = evaluate(_fv(semantic_mismatch=0.05), rules_cfg=custom_cfg)
    assert trace.rule_id == "R04"  # con threshold muy bajo, 0.05 ya es "mismatch"
    assert trace.threshold == 0.01
    assert custom_cfg["semantic_mismatch_threshold"] != cfg.get("semantic_mismatch_threshold")


def test_rule_trace_signature_never_takes_a_label_argument():
    params = set(inspect.signature(evaluate).parameters)
    forbidden = {"label", "expected_label", "expected_condition", "case_id", "perturbation"}
    assert params.isdisjoint(forbidden)


def test_rule_trace_serializes_decision_as_string():
    trace = evaluate(_fv())
    d = trace.as_dict()
    assert isinstance(d["decision"], str)
    assert d["decision"] in {"SUPPORTED", "SUSPICIOUS", "INSUFFICIENT"}
