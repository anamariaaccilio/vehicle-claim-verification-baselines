"""Bootstrap agrupado por source_image_id (FASE 6 / tesis seccion
estadistica). Nunca bootstrap por fila de claim: v3 tiene 9275 claims
provenientes de solo 807 source_image_id, por lo que remuestrear filas
subestima la varianza real. Esta funcion remuestrea GRUPOS completos
(todas las filas de un mismo source_image_id viajan juntas en cada resample).
"""
from __future__ import annotations

from typing import Callable, Sequence

import numpy as np


def grouped_bootstrap_ci(
    groups: Sequence[str],
    metric_fn: Callable[[np.ndarray], float],
    n_resamples: int = 2000,
    confidence: float = 0.95,
    seed: int = 42,
) -> dict:
    """metric_fn recibe un array de INDICES de fila (no de grupo) ya
    expandido para el resample y debe devolver un escalar."""
    groups = np.asarray(groups)
    unique_groups = np.unique(groups)
    n_groups = len(unique_groups)
    if n_groups < 2:
        return {"status": "NOT_EVALUATED", "reason": "menos de 2 grupos unicos (source_image_id)"}

    group_to_indices = {g: np.where(groups == g)[0] for g in unique_groups}
    rng = np.random.default_rng(seed)
    point_estimate = float(metric_fn(np.arange(len(groups))))

    estimates = np.empty(n_resamples, dtype=float)
    for i in range(n_resamples):
        sampled_groups = rng.choice(unique_groups, size=n_groups, replace=True)
        idx = np.concatenate([group_to_indices[g] for g in sampled_groups])
        estimates[i] = metric_fn(idx)

    alpha = 1.0 - confidence
    return {
        "point_estimate": point_estimate,
        "ci_low": float(np.quantile(estimates, alpha / 2)),
        "ci_high": float(np.quantile(estimates, 1 - alpha / 2)),
        "confidence": confidence,
        "n_resamples": n_resamples,
        "n_groups": int(n_groups),
    }


def paired_grouped_bootstrap_diff(
    groups: Sequence[str],
    metric_fn_a: Callable[[np.ndarray], float],
    metric_fn_b: Callable[[np.ndarray], float],
    n_resamples: int = 2000,
    confidence: float = 0.95,
    seed: int = 42,
) -> dict:
    """Comparacion emparejada A vs B (p.ej. B6 vs P1, P1 vs P2) sobre los
    MISMOS resamples de grupos para que la diferencia quede correctamente
    pareada. positivo => A > B. El p-valor es una aproximacion por
    permutacion del bootstrap (fraccion de resamples que cruzan 0),
    reportada solo para datos agrupados — nunca sobre filas de claim
    tratadas como independientes."""
    groups = np.asarray(groups)
    unique_groups = np.unique(groups)
    n_groups = len(unique_groups)
    if n_groups < 2:
        return {"status": "NOT_EVALUATED", "reason": "menos de 2 grupos unicos (source_image_id)"}

    group_to_indices = {g: np.where(groups == g)[0] for g in unique_groups}
    rng = np.random.default_rng(seed)
    all_idx = np.arange(len(groups))
    point_diff = float(metric_fn_a(all_idx) - metric_fn_b(all_idx))

    diffs = np.empty(n_resamples, dtype=float)
    for i in range(n_resamples):
        sampled_groups = rng.choice(unique_groups, size=n_groups, replace=True)
        idx = np.concatenate([group_to_indices[g] for g in sampled_groups])
        diffs[i] = metric_fn_a(idx) - metric_fn_b(idx)

    alpha = 1.0 - confidence
    p_value_two_sided = float(2 * min((diffs <= 0).mean(), (diffs >= 0).mean()))
    return {
        "point_diff": point_diff,
        "ci_low": float(np.quantile(diffs, alpha / 2)),
        "ci_high": float(np.quantile(diffs, 1 - alpha / 2)),
        "p_value_approx": min(p_value_two_sided, 1.0),
        "confidence": confidence,
        "n_resamples": n_resamples,
        "n_groups": int(n_groups),
    }


def holm_correction(p_values: Sequence[float]) -> list[float]:
    """Correccion de Holm-Bonferroni (step-down), confirmada contra el .tex
    real de la tesis (capitulo4.tex, "Diseno estadistico": "La correccion de
    Holm se aplica a las tres hipotesis confirmatorias [H1, H2, H3], con
    nivel global alpha=0.05"). Devuelve p-valores ajustados en el ORDEN
    ORIGINAL de entrada (no en el orden ordenado internamente).

    Procedimiento: ordenar p-valores ascendente; al i-esimo (1-indexado) de
    m comparaciones se le multiplica por (m-i+1); se aplica el maximo
    acumulado para garantizar monotonicidad; se recorta a 1.0.
    """
    m = len(p_values)
    if m == 0:
        return []
    order = sorted(range(m), key=lambda i: p_values[i])
    adjusted_sorted = []
    running_max = 0.0
    for rank, idx in enumerate(order):
        factor = m - rank
        value = min(1.0, p_values[idx] * factor)
        running_max = max(running_max, value)
        adjusted_sorted.append(running_max)
    adjusted = [0.0] * m
    for rank, idx in enumerate(order):
        adjusted[idx] = adjusted_sorted[rank]
    return adjusted


def bonferroni_correction(p_values: Sequence[float]) -> list[float]:
    """Correccion de Bonferroni (conservadora) para comparaciones multiples.

    El .tex real de la tesis especifica Holm (ver `holm_correction`), no
    Bonferroni, para H1/H2/H3. Esta funcion se conserva como alternativa
    mas conservadora y de uso general (p.ej. comparaciones exploratorias
    fuera de H1-H3), no como el metodo confirmado por la tesis.
    """
    m = len(p_values)
    return [min(1.0, p * m) for p in p_values]
