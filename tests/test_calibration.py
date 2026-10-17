"""Tests de FASE 6: temperature scaling (fit solo sobre validation, nunca
sobre test) con logits sinteticos pequenos."""
import numpy as np

from src.calibration.calibrate import TemperatureScaler, raw_and_calibrated_probabilities


def _overconfident_logits(n=60, seed=0):
    """Logits extremadamente seguros pero correctos solo ~55% de las veces:
    el caso clasico que temperature scaling debe corregir con T>1 (si el
    modelo fuera igual de seguro y casi siempre correcto, T~1 ya seria
    optimo y no habria nada que corregir)."""
    rng = np.random.default_rng(seed)
    true_labels = rng.integers(0, 3, size=n)
    is_correct = rng.uniform(0, 1, size=n) < 0.55
    predicted_labels = true_labels.copy()
    for i in np.where(~is_correct)[0]:
        choices = [c for c in range(3) if c != true_labels[i]]
        predicted_labels[i] = rng.choice(choices)
    logits = np.full((n, 3), -5.0)
    logits[np.arange(n), predicted_labels] = 5.0
    noise = rng.normal(scale=0.3, size=logits.shape)
    return logits + noise, true_labels


def test_temperature_scaling_reduces_extreme_overconfidence():
    val_logits, val_labels = _overconfident_logits(seed=1)
    eval_logits, eval_labels = _overconfident_logits(seed=2)

    scaler = TemperatureScaler().fit(val_logits, val_labels)
    assert scaler.temperature > 1.0  # logits extremos -> T>1 los suaviza

    raw_probs = np.exp(eval_logits) / np.exp(eval_logits).sum(axis=1, keepdims=True)
    calibrated = scaler.calibrate_probabilities(eval_logits)

    raw_confidence = raw_probs.max(axis=1).mean()
    calibrated_confidence = calibrated.max(axis=1).mean()
    assert calibrated_confidence < raw_confidence


def test_raw_and_calibrated_probabilities_are_both_preserved():
    val_logits, val_labels = _overconfident_logits(seed=3)
    eval_logits, _ = _overconfident_logits(seed=4)

    result = raw_and_calibrated_probabilities(val_logits, val_labels, eval_logits)
    assert "raw_probabilities" in result and "calibrated_probabilities" in result
    assert not np.allclose(result["raw_probabilities"], result["calibrated_probabilities"])
    assert np.allclose(result["raw_probabilities"].sum(axis=1), 1.0)
    assert np.allclose(result["calibrated_probabilities"].sum(axis=1), 1.0)
    assert result["temperature"] > 0
