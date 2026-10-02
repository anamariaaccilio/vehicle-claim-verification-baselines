"""Tests de FASE 2: NarrativeExtractor con inferencia REAL (sin mocks),
segun feedback del usuario de preferir integracion real sobre mocks.
Estos tests son mas lentos (~1 min) porque cargan mDeBERTa-v3-base-mnli-xnli
y corren inferencia real; requieren el modelo ya descargado en el cache de
Hugging Face (ver README) o conexion a internet la primera vez.
"""
import math

import pytest

from src.narrative.nli_extractor import NarrativeExtractor, load_hypotheses
from src.schemas.evidence import CANONICAL_DAMAGE_CLASSES


@pytest.fixture(scope="module")
def extractor():
    return NarrativeExtractor()


def test_hypotheses_cover_all_canonical_classes():
    hyps = load_hypotheses()
    assert set(hyps.keys()) == set(CANONICAL_DAMAGE_CLASSES)
    assert all(isinstance(v, str) and v.strip() for v in hyps.values())


@pytest.mark.model
def test_extractor_raises_on_empty_text(extractor):
    with pytest.raises(ValueError):
        extractor.extract("")


@pytest.mark.model
def test_extractor_raises_on_whitespace_only_text(extractor):
    with pytest.raises(ValueError):
        extractor.extract("   \n\t  ")


@pytest.mark.model
def test_extractor_returns_valid_schema_for_real_narrative(extractor):
    result = extractor.extract("El auto tiene una abolladura.")

    assert set(result.raw_scores.keys()) == set(CANONICAL_DAMAGE_CLASSES)
    assert set(result.normalized_scores.keys()) == set(CANONICAL_DAMAGE_CLASSES)
    assert all(0.0 <= v <= 1.0 for v in result.raw_scores.values())
    assert math.isclose(sum(result.normalized_scores.values()), 1.0, abs_tol=1e-6)
    assert result.top_damage in CANONICAL_DAMAGE_CLASSES
    assert result.raw_scores[result.top_damage] == max(result.raw_scores.values())
    assert result.entropy >= 0.0
    assert result.inference_time_seconds > 0.0
    assert result.model_name == "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"
    assert result.device in ("cpu", "cuda")


@pytest.mark.model
def test_extractor_to_evidence_matches_result(extractor):
    result = extractor.extract("El vehiculo tiene rayones.")
    evidence = result.to_evidence()

    assert evidence.raw_scores == result.raw_scores
    assert evidence.normalized_scores == result.normalized_scores
    assert evidence.model_name == result.model_name
    assert evidence.device == result.device
