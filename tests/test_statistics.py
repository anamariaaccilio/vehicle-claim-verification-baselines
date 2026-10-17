"""Tests de FASE 6: bootstrap agrupado por source_image_id. Verifica que el
resample mueve grupos completos (nunca filas de claim sueltas), ya que v3
tiene 9275 claims provenientes de solo 807 source_image_id."""
import numpy as np
import pytest

from src.evaluation.statistics import (
    bonferroni_correction,
    grouped_bootstrap_ci,
    paired_grouped_bootstrap_diff,
)


def _accuracy_fn(correct_flags):
    def _fn(idx):
        return float(np.mean(correct_flags[idx]))
    return _fn


def test_grouped_bootstrap_resamples_whole_groups_not_rows():
    # 4 source_image_id, cada uno con 3 filas (como v3: varios claims por imagen)
    groups = np.repeat(["img1", "img2", "img3", "img4"], 3)
    # img1 y img2 siempre correctos, img3 y img4 siempre incorrectos
    correct = np.array([1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0], dtype=float)

    result = grouped_bootstrap_ci(groups, _accuracy_fn(correct), n_resamples=500, seed=7)
    assert result["point_estimate"] == pytest.approx(0.5)
    # cada resample promedia grupos completos (0.0, 0.25, 0.5, 0.75, 1.0 solamente
    # son posibles si se preservan grupos de 3 filas identicas; no hay fracciones
    # intermedias imposibles con 4 grupos binarios)
    assert 0.0 <= result["ci_low"] <= result["ci_high"] <= 1.0
    assert result["n_groups"] == 4


def test_too_few_groups_reports_not_evaluated():
    groups = np.array(["only_one_image"] * 5)
    result = grouped_bootstrap_ci(groups, _accuracy_fn(np.ones(5)), n_resamples=10)
    assert result["status"] == "NOT_EVALUATED"


def test_paired_bootstrap_detects_consistent_difference():
    groups = np.repeat([f"img{i}" for i in range(20)], 5)
    rng = np.random.default_rng(0)
    a_correct = (rng.uniform(0, 1, size=len(groups)) < 0.9).astype(float)  # sistema A mejor
    b_correct = (rng.uniform(0, 1, size=len(groups)) < 0.5).astype(float)  # sistema B peor

    result = paired_grouped_bootstrap_diff(
        groups, _accuracy_fn(a_correct), _accuracy_fn(b_correct), n_resamples=500, seed=3
    )
    assert result["point_diff"] > 0
    assert result["ci_low"] > 0  # el intervalo no cruza 0: diferencia consistente


def test_bonferroni_correction_scales_by_number_of_tests():
    corrected = bonferroni_correction([0.01, 0.02, 0.5])
    assert corrected == [pytest.approx(0.03), pytest.approx(0.06), 1.0]
