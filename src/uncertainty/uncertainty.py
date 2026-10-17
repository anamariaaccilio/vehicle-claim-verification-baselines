"""Incertidumbre epistemica via ensemble configurable (FASE 6 / tesis
seccion de incertidumbre).

U(x) = entropy(mean_probability sobre M miembros). M=1 es un smoke test:
la incertidumbre degenera a la entropia de una sola prediccion y no mide
desacuerdo real entre miembros del ensemble. M=5 es el objetivo de tesis
para resultados reales. No confundir uncertainty (este modulo) con
reliability/quality/coverage, que son campos distintos del contrato de
evidencia (src/schemas/evidence.py) y no deben derivarse unos de otros.
"""
from __future__ import annotations

import numpy as np


def mean_ensemble_probability(member_probabilities: np.ndarray) -> np.ndarray:
    """member_probabilities: shape (M, N, C). Devuelve shape (N, C)."""
    arr = np.asarray(member_probabilities, dtype=float)
    if arr.ndim != 3:
        raise ValueError("member_probabilities debe tener forma (M, N, C)")
    return arr.mean(axis=0)


def entropy(probabilities: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    """Entropia de Shannon en nats, por fila. probabilities: shape (N, C)."""
    p = np.clip(np.asarray(probabilities, dtype=float), eps, 1.0)
    return -np.sum(p * np.log(p), axis=-1)


def predictive_uncertainty(member_probabilities: np.ndarray) -> np.ndarray:
    """U(x) = entropy(mean probability). member_probabilities: shape
    (M, N, C) con M>=1. M=1 -> smoke (sin desacuerdo de ensemble real)."""
    mean_prob = mean_ensemble_probability(member_probabilities)
    return entropy(mean_prob)
