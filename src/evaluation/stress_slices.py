"""FASE 6: metricas separadas por stress slice (C0, C1, C2, C6-C9, ver
seccion 11 del brief y demo/ casos de fallo). C10 (OOD) se evalua aparte
porque no es una cuarta clase de decision."""
from __future__ import annotations

from collections import defaultdict
from typing import Sequence

import numpy as np

from src.evaluation.metrics import NOT_EVALUATED, compute_all_metrics

MIN_SAMPLES_FOR_SLICE = 2


def metrics_by_condition(
    conditions: Sequence[str],
    y_true: Sequence[str],
    y_pred: Sequence[str],
    y_prob: np.ndarray,
) -> dict:
    """Agrupa evaluacion por condicion C0-C9. C10 se excluye (ver
    `ood_stress_metrics`): OOD no entra en la evaluacion de 3 clases."""
    y_prob = np.asarray(y_prob)
    groups: dict[str, list[int]] = defaultdict(list)
    for i, c in enumerate(conditions):
        if c == "C10":
            continue
        groups[c].append(i)

    by_condition: dict[str, dict] = {}
    for condition, idx in groups.items():
        if len(idx) < MIN_SAMPLES_FOR_SLICE:
            by_condition[condition] = {"n_samples": len(idx), "status": NOT_EVALUATED}
            continue
        sub_true = [y_true[i] for i in idx]
        sub_pred = [y_pred[i] for i in idx]
        sub_prob = y_prob[idx]
        by_condition[condition] = compute_all_metrics(sub_true, sub_pred, sub_prob)
    return by_condition


def ood_stress_metrics(conditions: Sequence[str], ood_score: Sequence[float]) -> dict:
    """C10 es OOD, no una cuarta clase: se evalua como deteccion binaria
    (C10 vs resto) con un score de rareza/incertidumbre (mayor = mas
    atipico), p.ej. la U(x) de src/uncertainty."""
    from sklearn.metrics import roc_auc_score

    is_ood = np.array([c == "C10" for c in conditions], dtype=int)
    if is_ood.sum() == 0 or is_ood.sum() == len(is_ood):
        return {"auroc_ood": NOT_EVALUATED, "n_ood": int(is_ood.sum()), "n_total": int(len(is_ood))}
    try:
        auroc = float(roc_auc_score(is_ood, np.asarray(ood_score)))
    except ValueError:
        auroc = NOT_EVALUATED
    return {"auroc_ood": auroc, "n_ood": int(is_ood.sum()), "n_total": int(len(is_ood))}
