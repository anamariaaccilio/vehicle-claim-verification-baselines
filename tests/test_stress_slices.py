"""Tests de FASE 6: metricas por condicion C0-C9 y evaluacion OOD separada
de C10 (nunca como cuarta clase de decision)."""
import numpy as np

from src.evaluation.metrics import CLASS_ORDER, NOT_EVALUATED
from src.evaluation.stress_slices import metrics_by_condition, ood_stress_metrics

SUPPORTED, SUSPICIOUS, INSUFFICIENT = CLASS_ORDER


def test_metrics_by_condition_splits_and_skips_c10():
    # cada slice cubre las 3 clases para que macro-F1 perfecto sea alcanzable
    # (macro-F1 promedia sobre CLASS_ORDER completo, no solo clases presentes,
    # para que las metricas sean comparables entre condiciones).
    conditions = ["C0", "C0", "C0", "C1", "C1", "C1", "C10", "C10"]
    y_true = [SUPPORTED, SUSPICIOUS, INSUFFICIENT, SUPPORTED, SUSPICIOUS, INSUFFICIENT, SUPPORTED, SUPPORTED]
    y_pred = [SUPPORTED, SUSPICIOUS, INSUFFICIENT, SUPPORTED, SUSPICIOUS, INSUFFICIENT, SUPPORTED, SUPPORTED]
    y_prob = np.array([
        [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0],
        [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0],
        [1.0, 0.0, 0.0], [1.0, 0.0, 0.0],
    ])

    result = metrics_by_condition(conditions, y_true, y_pred, y_prob)
    assert "C10" not in result
    assert result["C0"]["n_samples"] == 3
    assert result["C1"]["macro_f1"] == 1.0


def test_metrics_by_condition_small_slice_not_evaluated():
    conditions = ["C5"]
    result = metrics_by_condition(conditions, [SUPPORTED], [SUPPORTED], np.array([[1.0, 0.0, 0.0]]))
    assert result["C5"]["status"] == NOT_EVALUATED


def test_ood_stress_metrics_detects_separation():
    conditions = ["C0", "C0", "C0", "C10", "C10", "C10"]
    ood_score = [0.1, 0.2, 0.15, 0.9, 0.95, 0.85]
    result = ood_stress_metrics(conditions, ood_score)
    assert result["n_ood"] == 3
    assert result["n_total"] == 6
    assert result["auroc_ood"] == 1.0


def test_ood_stress_metrics_no_ood_present():
    conditions = ["C0", "C0"]
    result = ood_stress_metrics(conditions, [0.1, 0.2])
    assert result["auroc_ood"] == NOT_EVALUATED
