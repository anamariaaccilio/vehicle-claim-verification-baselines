"""Tests de FASE 6: incertidumbre U(x) = entropy(mean probability) sobre
ensembles sinteticos pequenos. Nunca confundir con reliability/quality/
coverage (campos distintos del contrato de evidencia)."""
import numpy as np
import pytest

from src.uncertainty.uncertainty import (
    entropy,
    mean_ensemble_probability,
    predictive_uncertainty,
)


def test_entropy_zero_for_one_hot_distribution():
    probs = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    assert entropy(probs) == pytest.approx([0.0, 0.0], abs=1e-9)


def test_entropy_maximal_for_uniform_distribution():
    probs = np.array([[1 / 3, 1 / 3, 1 / 3]])
    assert entropy(probs)[0] == pytest.approx(np.log(3), abs=1e-6)


def test_mean_ensemble_probability_shape_and_values():
    members = np.array([
        [[0.9, 0.1, 0.0], [0.1, 0.8, 0.1]],
        [[0.7, 0.3, 0.0], [0.3, 0.6, 0.1]],
    ])  # shape (M=2, N=2, C=3)
    mean = mean_ensemble_probability(members)
    assert mean.shape == (2, 3)
    assert mean[0] == pytest.approx([0.8, 0.2, 0.0])


def test_disagreeing_ensemble_has_higher_uncertainty_than_agreeing():
    agreeing = np.array([
        [[0.9, 0.05, 0.05]],
        [[0.9, 0.05, 0.05]],
    ])
    disagreeing = np.array([
        [[0.9, 0.05, 0.05]],
        [[0.05, 0.9, 0.05]],
    ])
    u_agree = predictive_uncertainty(agreeing)
    u_disagree = predictive_uncertainty(disagreeing)
    assert u_disagree[0] > u_agree[0]


def test_m_equals_one_is_smoke_only_no_ensemble_disagreement_possible():
    single_member = np.array([[[0.6, 0.3, 0.1]]])  # M=1
    u = predictive_uncertainty(single_member)
    assert u.shape == (1,)
    assert u[0] == pytest.approx(entropy(np.array([[0.6, 0.3, 0.1]]))[0])


def test_rejects_wrong_input_shape():
    with pytest.raises(ValueError):
        mean_ensemble_probability(np.array([0.5, 0.5]))
