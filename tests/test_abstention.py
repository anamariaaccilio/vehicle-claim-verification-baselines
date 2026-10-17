"""Tests de FASE 6: abstencion por umbral (tau_U sobre incertidumbre, tau_c
sobre cobertura de evidencia c_bar(x), ambos ajustados solo en validation,
eq:abstencion de la tesis), risk-coverage curve y AURC. No se crea una
cuarta clase ABSTAIN."""
import numpy as np
import pytest

from src.abstention.abstention import (
    AbstentionThresholds,
    apply_abstention,
    fit_thresholds_on_validation,
    risk_coverage_curve,
)


def test_fit_thresholds_keeps_approximately_target_coverage():
    rng = np.random.default_rng(0)
    val_uncertainty = rng.uniform(0, 1, size=100)
    val_evidence_coverage = 1 - val_uncertainty
    thresholds = fit_thresholds_on_validation(val_uncertainty, val_evidence_coverage, target_coverage=0.8)

    abstain = thresholds.decide(val_uncertainty, val_evidence_coverage)
    coverage = 1 - abstain.mean()
    assert coverage == pytest.approx(0.8, abs=0.02)


def test_decide_never_adds_a_fourth_class_only_boolean_flag():
    thresholds = AbstentionThresholds(tau_u=0.5)
    predictions = ["SUPPORTED", "SUSPICIOUS", "INSUFFICIENT"]
    uncertainty = np.array([0.1, 0.9, 0.4])
    evidence_coverage = np.array([0.9, 0.1, 0.6])
    output = apply_abstention(predictions, uncertainty, evidence_coverage, thresholds)
    assert [o["prediction"] for o in output] == predictions  # predicciones nunca se reemplazan
    assert [o["abstained"] for o in output] == [False, True, False]


def test_low_evidence_coverage_triggers_abstention_even_with_low_uncertainty():
    # eq:abstencion es un OR: c_bar(x) < tau_c debe poder disparar abstencion
    # por si solo, aunque la incertidumbre este por debajo de tau_u.
    thresholds = AbstentionThresholds(tau_u=0.9, tau_c=0.5)
    uncertainty = np.array([0.1])
    evidence_coverage = np.array([0.2])  # expediente con poca evidencia observada
    output = apply_abstention(["SUPPORTED"], uncertainty, evidence_coverage, thresholds)
    assert output[0]["abstained"] is True


def test_risk_coverage_curve_monotonic_coverage_and_valid_aurc():
    rng = np.random.default_rng(1)
    n = 200
    uncertainty = rng.uniform(0, 1, size=n)
    # las muestras de menor incertidumbre son correctas con mas frecuencia
    correct = rng.uniform(0, 1, size=n) > uncertainty
    curve = risk_coverage_curve(uncertainty, correct)
    assert np.all(np.diff(curve["coverage"]) > 0)
    assert 0.0 <= curve["aurc"] <= 1.0


def test_perfect_ranking_gives_lower_aurc_than_random_ranking():
    n = 100
    correct = np.array([True] * 70 + [False] * 30)
    # ranking perfecto: errores todos al final (mayor incertidumbre)
    perfect_uncertainty = np.concatenate([np.linspace(0, 0.5, 70), np.linspace(0.51, 1.0, 30)])
    rng = np.random.default_rng(2)
    random_uncertainty = rng.permutation(perfect_uncertainty)

    perfect_curve = risk_coverage_curve(perfect_uncertainty, correct)
    random_curve = risk_coverage_curve(random_uncertainty, correct)
    assert perfect_curve["aurc"] < random_curve["aurc"]


def test_target_coverage_out_of_range_raises():
    with pytest.raises(ValueError):
        fit_thresholds_on_validation(np.array([0.1]), np.array([0.9]), target_coverage=1.5)
