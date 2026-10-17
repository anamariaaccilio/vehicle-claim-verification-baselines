"""Abstencion por umbral de incertidumbre (tau_U) y/o confianza (tau_c)
(FASE 6 / tesis seccion de abstencion). tau_U y tau_c se ajustan SOLO con
validation, nunca con test. No se crea una cuarta clase ABSTAIN: la salida
por muestra es siempre (prediction, abstained: bool), conservando la
prediccion original incluso cuando se abstiene.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class AbstentionThresholds:
    tau_u: float | None = None  # abstiene si uncertainty > tau_u
    tau_c: float | None = None  # abstiene si confidence < tau_c

    def decide(self, uncertainty: np.ndarray, confidence: np.ndarray) -> np.ndarray:
        n = len(np.asarray(uncertainty))
        abstain = np.zeros(n, dtype=bool)
        if self.tau_u is not None:
            abstain |= np.asarray(uncertainty) > self.tau_u
        if self.tau_c is not None:
            abstain |= np.asarray(confidence) < self.tau_c
        return abstain


def fit_thresholds_on_validation(
    val_uncertainty: np.ndarray,
    val_confidence: np.ndarray,
    target_coverage: float,
) -> AbstentionThresholds:
    """Elige tau_u/tau_c sobre validation para retener aproximadamente
    target_coverage de las muestras (las de menor incertidumbre / mayor
    confianza). NUNCA debe ajustarse sobre test."""
    val_uncertainty = np.asarray(val_uncertainty, dtype=float)
    val_confidence = np.asarray(val_confidence, dtype=float)
    n = len(val_uncertainty)
    if n == 0:
        return AbstentionThresholds()
    if not 0.0 < target_coverage <= 1.0:
        raise ValueError("target_coverage debe estar en (0, 1]")

    order = np.argsort(val_uncertainty)
    n_keep = max(1, int(np.ceil(target_coverage * n)))
    kept_idx = order[:n_keep]
    tau_u = float(val_uncertainty[kept_idx].max())
    tau_c = float(val_confidence[kept_idx].min())
    return AbstentionThresholds(tau_u=tau_u, tau_c=tau_c)


def risk_coverage_curve(uncertainty: np.ndarray, correct: np.ndarray) -> dict:
    """Ordena por incertidumbre ascendente y calcula riesgo acumulado vs
    cobertura. Devuelve coverage[], risk[] y AURC (area bajo la curva;
    menor es mejor)."""
    uncertainty = np.asarray(uncertainty, dtype=float)
    correct = np.asarray(correct, dtype=bool)
    n = len(uncertainty)
    if n == 0:
        return {"coverage": np.array([]), "risk": np.array([]), "aurc": "NOT_EVALUATED"}

    order = np.argsort(uncertainty)
    sorted_correct = correct[order]
    errors = (~sorted_correct).astype(float)
    cumulative_error = np.cumsum(errors)
    coverage = np.arange(1, n + 1) / n
    risk = cumulative_error / np.arange(1, n + 1)
    aurc = float(np.trapezoid(risk, coverage))
    return {"coverage": coverage, "risk": risk, "aurc": aurc}


def apply_abstention(
    predictions,
    uncertainty: np.ndarray,
    confidence: np.ndarray,
    thresholds: AbstentionThresholds,
) -> list[dict]:
    """Salida por muestra: {'prediction': ..., 'abstained': bool}. No agrega
    una clase ABSTAIN; la prediccion original siempre se conserva."""
    abstain = thresholds.decide(uncertainty, confidence)
    return [
        {"prediction": pred, "abstained": bool(ab)}
        for pred, ab in zip(predictions, abstain)
    ]
