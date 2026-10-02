"""FASE 4: Rule Baseline B0 -- motor de reglas deterministico (SIN grafos,
SIN ML). Thresholds leidos de configs/baseline.yaml::rules /
configs/baseline.yaml::image_quality; nunca hardcodeados en este archivo.

Las reglas se evaluan en orden de prioridad fijo; la PRIMERA que se cumple
determina la decision final y queda registrada en un RuleTrace (rule_id,
description, observed_value, threshold, decision), para poder explicar
exactamente por que se tomo cada decision.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from src.fusion.features import FeatureVector
from src.schemas.evidence import DecisionLabel

CONFIG_PATH = Path(__file__).resolve().parents[2] / "configs" / "baseline.yaml"


def load_rules_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg.get("rules", {})


@dataclass
class RuleTrace:
    rule_id: str
    description: str
    observed_value: Any
    threshold: Any
    decision: DecisionLabel

    def as_dict(self) -> dict:
        d = dict(self.__dict__)
        d["decision"] = self.decision.value
        return d


def evaluate(features: FeatureVector, rules_cfg: dict | None = None) -> RuleTrace:
    rules_cfg = rules_cfg or load_rules_config()
    mismatch_threshold = rules_cfg.get("semantic_mismatch_threshold", 0.45)

    if features.text_missing:
        return RuleTrace(
            rule_id="R01",
            description="Narrativa del reclamo ausente: no se puede verificar contra la evidencia visual.",
            observed_value=True,
            threshold=None,
            decision=DecisionLabel.INSUFFICIENT,
        )

    if features.image_missing:
        return RuleTrace(
            rule_id="R02",
            description="Fotografia del reclamo ausente: no se puede verificar la narrativa.",
            observed_value=True,
            threshold=None,
            decision=DecisionLabel.INSUFFICIENT,
        )

    if features.image_quality_status == "INSUFFICIENT":
        return RuleTrace(
            rule_id="R03",
            description="Calidad de imagen insuficiente (corrupta, demasiado pequeña o demasiado borrosa) para evaluar evidencia visual.",
            observed_value=features.image_quality_status,
            threshold="INSUFFICIENT",
            decision=DecisionLabel.INSUFFICIENT,
        )

    if not features.visual_available:
        return RuleTrace(
            rule_id="R06",
            description=(
                "Damage Specialist (vision) no disponible: no hay checkpoint "
                "entrenado, por lo que no se puede corroborar visualmente la narrativa."
            ),
            observed_value=features.visual_available,
            threshold=None,
            decision=DecisionLabel.INSUFFICIENT,
        )

    if features.semantic_mismatch is not None and features.semantic_mismatch > mismatch_threshold:
        return RuleTrace(
            rule_id="R04",
            description="Discrepancia entre narrativa y evidencia visual por encima del umbral configurado.",
            observed_value=round(features.semantic_mismatch, 4),
            threshold=mismatch_threshold,
            decision=DecisionLabel.SUSPICIOUS,
        )

    return RuleTrace(
        rule_id="R05",
        description="Evidencia narrativa y visual compatible y suficiente.",
        observed_value=round(features.semantic_mismatch, 4) if features.semantic_mismatch is not None else None,
        threshold=mismatch_threshold,
        decision=DecisionLabel.SUPPORTED,
    )
