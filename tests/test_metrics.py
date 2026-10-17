"""Tests de FASE 6: metricas de evaluacion sobre fixtures sinteticas
pequenas (no dependen de las 807 imagenes reales)."""
import numpy as np
import pytest

from src.evaluation.metrics import (
    CLASS_ORDER,
    NOT_EVALUATED,
    auroc_ovr_macro,
    brier_score_multiclass,
    compute_all_metrics,
    confusion_matrix,
    expected_calibration_error,
    macro_f1,
    nll,
    pr_auc_suspicious,
    precision_recall_macro,
)

SUPPORTED, SUSPICIOUS, INSUFFICIENT = CLASS_ORDER


def _perfect_fixture():
    y_true = [SUPPORTED, SUSPICIOUS, INSUFFICIENT, SUPPORTED, SUSPICIOUS, INSUFFICIENT]
    y_pred = list(y_true)
    y_prob = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ])
    return y_true, y_pred, y_prob


def test_perfect_predictions_give_best_scores():
    y_true, y_pred, y_prob = _perfect_fixture()
    metrics = compute_all_metrics(y_true, y_pred, y_prob)
    assert metrics["macro_f1"] == pytest.approx(1.0)
    assert metrics["pr_auc_suspicious"] == pytest.approx(1.0)
    assert metrics["brier"] == pytest.approx(0.0, abs=1e-9)
    assert metrics["ece"] == pytest.approx(0.0, abs=1e-9)
    assert metrics["nll"] < 1e-6
    assert metrics["n_samples"] == 6


def test_too_few_samples_reports_not_evaluated():
    y_true = [SUPPORTED]
    y_pred = [SUPPORTED]
    y_prob = np.array([[1.0, 0.0, 0.0]])
    assert macro_f1(y_true, y_pred) == NOT_EVALUATED
    assert pr_auc_suspicious(y_true, y_prob) == NOT_EVALUATED
    assert brier_score_multiclass(y_true, y_prob) == NOT_EVALUATED
    assert nll(y_true, y_prob) == NOT_EVALUATED
    assert expected_calibration_error(y_true, y_prob) == NOT_EVALUATED
    assert confusion_matrix(y_true, y_pred) == NOT_EVALUATED
    pr = precision_recall_macro(y_true, y_pred)
    assert pr["precision"] == NOT_EVALUATED and pr["recall"] == NOT_EVALUATED


def test_single_class_present_pr_auc_and_auroc_not_evaluated():
    y_true = [SUPPORTED, SUPPORTED, SUPPORTED]
    y_prob = np.array([[0.9, 0.05, 0.05], [0.8, 0.1, 0.1], [0.7, 0.2, 0.1]])
    assert pr_auc_suspicious(y_true, y_prob) == NOT_EVALUATED
    assert auroc_ovr_macro(y_true, y_prob) == NOT_EVALUATED


def test_unknown_label_raises():
    with pytest.raises(ValueError):
        macro_f1(["NOT_A_LABEL", SUPPORTED], ["NOT_A_LABEL", SUPPORTED])


def test_wrong_predictions_give_worse_brier_than_perfect():
    y_true, _, y_prob_perfect = _perfect_fixture()
    y_prob_wrong = 1.0 - y_prob_perfect / 2  # desplaza masa lejos del label correcto
    y_prob_wrong = y_prob_wrong / y_prob_wrong.sum(axis=1, keepdims=True)
    brier_perfect = brier_score_multiclass(y_true, y_prob_perfect)
    brier_wrong = brier_score_multiclass(y_true, y_prob_wrong)
    assert brier_wrong > brier_perfect
