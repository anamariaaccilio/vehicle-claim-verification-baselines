"""FASE 6: PR-AUC (SUSPICIOUS), macro-F1, precision, recall, AUROC, Brier,
NLL, ECE, matriz de confusion. Nunca inventar resultados; si no hay
suficientes muestras, reportar 'NOT_EVALUATED'."""
from __future__ import annotations

from typing import Sequence

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix as sk_confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)

from src.schemas.evidence import DecisionLabel

CLASS_ORDER: tuple[str, ...] = (
    DecisionLabel.SUPPORTED.value,
    DecisionLabel.SUSPICIOUS.value,
    DecisionLabel.INSUFFICIENT.value,
)
MIN_SAMPLES_FOR_METRIC = 2
NOT_EVALUATED = "NOT_EVALUATED"


def _encode_labels(y_true: Sequence[str]) -> np.ndarray:
    index = {label: i for i, label in enumerate(CLASS_ORDER)}
    unknown = sorted(set(y_true) - set(index))
    if unknown:
        raise ValueError(f"Etiquetas fuera de CLASS_ORDER: {unknown}")
    return np.array([index[label] for label in y_true], dtype=int)


def _one_hot(y_idx: np.ndarray, n_classes: int) -> np.ndarray:
    out = np.zeros((len(y_idx), n_classes), dtype=float)
    out[np.arange(len(y_idx)), y_idx] = 1.0
    return out


def pr_auc_suspicious(y_true: Sequence[str], y_prob: np.ndarray) -> float | str:
    """Average precision para SUSPICIOUS (positiva) vs el resto."""
    if len(y_true) < MIN_SAMPLES_FOR_METRIC:
        return NOT_EVALUATED
    y_idx = _encode_labels(y_true)
    pos = CLASS_ORDER.index(DecisionLabel.SUSPICIOUS.value)
    y_binary = (y_idx == pos).astype(int)
    if y_binary.sum() == 0 or y_binary.sum() == len(y_binary):
        return NOT_EVALUATED
    return float(average_precision_score(y_binary, np.asarray(y_prob)[:, pos]))


def macro_f1(y_true: Sequence[str], y_pred: Sequence[str]) -> float | str:
    if len(y_true) < MIN_SAMPLES_FOR_METRIC:
        return NOT_EVALUATED
    _encode_labels(y_true)
    _encode_labels(y_pred)
    return float(
        f1_score(y_true, y_pred, labels=list(CLASS_ORDER), average="macro", zero_division=0)
    )


def precision_recall_macro(y_true: Sequence[str], y_pred: Sequence[str]) -> dict:
    if len(y_true) < MIN_SAMPLES_FOR_METRIC:
        return {"precision": NOT_EVALUATED, "recall": NOT_EVALUATED}
    _encode_labels(y_true)
    _encode_labels(y_pred)
    return {
        "precision": float(
            precision_score(y_true, y_pred, labels=list(CLASS_ORDER), average="macro", zero_division=0)
        ),
        "recall": float(
            recall_score(y_true, y_pred, labels=list(CLASS_ORDER), average="macro", zero_division=0)
        ),
    }


def auroc_ovr_macro(y_true: Sequence[str], y_prob: np.ndarray) -> float | str:
    if len(y_true) < MIN_SAMPLES_FOR_METRIC:
        return NOT_EVALUATED
    y_idx = _encode_labels(y_true)
    if len(set(y_idx)) < 2:
        return NOT_EVALUATED
    try:
        return float(
            roc_auc_score(
                y_idx,
                np.asarray(y_prob),
                multi_class="ovr",
                average="macro",
                labels=list(range(len(CLASS_ORDER))),
            )
        )
    except ValueError:
        return NOT_EVALUATED


def brier_score_multiclass(y_true: Sequence[str], y_prob: np.ndarray) -> float | str:
    """Brier multiclase (promedio de ||p - onehot||^2 por muestra)."""
    if len(y_true) < MIN_SAMPLES_FOR_METRIC:
        return NOT_EVALUATED
    y_idx = _encode_labels(y_true)
    y_onehot = _one_hot(y_idx, len(CLASS_ORDER))
    y_prob = np.asarray(y_prob, dtype=float)
    return float(np.mean(np.sum((y_prob - y_onehot) ** 2, axis=1)))


def nll(y_true: Sequence[str], y_prob: np.ndarray) -> float | str:
    if len(y_true) < MIN_SAMPLES_FOR_METRIC:
        return NOT_EVALUATED
    y_idx = _encode_labels(y_true)
    try:
        return float(log_loss(y_idx, np.asarray(y_prob), labels=list(range(len(CLASS_ORDER)))))
    except ValueError:
        return NOT_EVALUATED


def expected_calibration_error(y_true: Sequence[str], y_prob: np.ndarray, n_bins: int = 10) -> float | str:
    """ECE estandar: bins por confianza top-1, |acc-conf| ponderado por tamanio de bin."""
    if len(y_true) < MIN_SAMPLES_FOR_METRIC:
        return NOT_EVALUATED
    y_idx = _encode_labels(y_true)
    y_prob = np.asarray(y_prob, dtype=float)
    confidences = y_prob.max(axis=1)
    predictions = y_prob.argmax(axis=1)
    correct = (predictions == y_idx).astype(float)

    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n = len(y_idx)
    for lo, hi in zip(bin_edges[:-1], bin_edges[1:]):
        if hi == bin_edges[-1]:
            mask = (confidences >= lo) & (confidences <= hi)
        else:
            mask = (confidences >= lo) & (confidences < hi)
        if not mask.any():
            continue
        bin_acc = correct[mask].mean()
        bin_conf = confidences[mask].mean()
        ece += (mask.sum() / n) * abs(bin_acc - bin_conf)
    return float(ece)


def confusion_matrix(y_true: Sequence[str], y_pred: Sequence[str]):
    if len(y_true) < MIN_SAMPLES_FOR_METRIC:
        return NOT_EVALUATED
    _encode_labels(y_true)
    _encode_labels(y_pred)
    return sk_confusion_matrix(y_true, y_pred, labels=list(CLASS_ORDER))


def compute_all_metrics(y_true: Sequence[str], y_pred: Sequence[str], y_prob: np.ndarray) -> dict:
    """Agrega todas las metricas de FASE 6. y_prob debe seguir CLASS_ORDER."""
    return {
        "pr_auc_suspicious": pr_auc_suspicious(y_true, y_prob),
        "macro_f1": macro_f1(y_true, y_pred),
        **precision_recall_macro(y_true, y_pred),
        "auroc_ovr_macro": auroc_ovr_macro(y_true, y_prob),
        "brier": brier_score_multiclass(y_true, y_prob),
        "nll": nll(y_true, y_prob),
        "ece": expected_calibration_error(y_true, y_prob),
        "n_samples": len(y_true),
    }
