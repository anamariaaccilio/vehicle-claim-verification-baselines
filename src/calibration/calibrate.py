"""FASE 6: calibracion de probabilidades sobre validation (temperature
scaling, Guo et al. 2017). Reporta Brier score, NLL y ECE. Nunca calibrar
con test. Conserva siempre raw_probabilities junto a calibrated_probabilities
(nunca se sobrescribe la serie raw)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
import torch.nn.functional as F


@dataclass
class TemperatureScaler:
    """T se ajusta SOLO sobre validation; nunca sobre test. logits debe
    seguir el orden de clases de src.evaluation.metrics.CLASS_ORDER."""

    temperature: float = 1.0

    def fit(
        self,
        val_logits: np.ndarray,
        val_labels_idx: np.ndarray,
        max_iter: int = 200,
        lr: float = 0.01,
    ) -> "TemperatureScaler":
        logits = torch.tensor(np.asarray(val_logits), dtype=torch.float64)
        labels = torch.tensor(np.asarray(val_labels_idx), dtype=torch.long)
        log_t = torch.zeros(1, dtype=torch.float64, requires_grad=True)
        optimizer = torch.optim.LBFGS([log_t], lr=lr, max_iter=max_iter)

        def closure():
            optimizer.zero_grad()
            t = torch.exp(log_t)
            loss = F.cross_entropy(logits / t, labels)
            loss.backward()
            return loss

        optimizer.step(closure)
        self.temperature = float(torch.exp(log_t).item())
        return self

    def calibrate_probabilities(self, logits: np.ndarray) -> np.ndarray:
        scaled = torch.tensor(np.asarray(logits), dtype=torch.float64) / self.temperature
        return torch.softmax(scaled, dim=-1).numpy()


def raw_and_calibrated_probabilities(
    val_logits: np.ndarray,
    val_labels_idx: np.ndarray,
    eval_logits: np.ndarray,
) -> dict:
    """Ajusta T en validation y devuelve raw + calibrated para eval_logits.
    null/None nunca se sustituye por 0 ni viceversa: esta funcion opera
    solo sobre logits ya presentes."""
    scaler = TemperatureScaler().fit(np.asarray(val_logits), np.asarray(val_labels_idx))
    raw = torch.softmax(torch.tensor(np.asarray(eval_logits), dtype=torch.float64), dim=-1).numpy()
    calibrated = scaler.calibrate_probabilities(eval_logits)
    return {
        "temperature": scaler.temperature,
        "raw_probabilities": raw,
        "calibrated_probabilities": calibrated,
    }
