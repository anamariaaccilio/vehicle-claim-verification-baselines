"""FASE 2: NarrativeExtractor basado en NLI (mDeBERTa-v3-base-mnli-xnli).

Enfoque: NLI de hipotesis independientes (no zero-shot-classification con
una sola plantilla). Para cada clase canonica de danio se evalua el par
(premise=narrativa del reclamo, hypothesis=oracion fija en
configs/labels.yaml::nli_hypotheses) y se toma la probabilidad de
'entailment' del modelo como score crudo para esa clase. Esto permite
multi-label real (un reclamo puede mencionar mas de un tipo de danio) sin
forzar a que las clases compitan entre si como ocurriria con un unico
softmax sobre labels de una plantilla compartida.

No es un LLM generativo: es clasificacion NLI discriminativa.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass
from pathlib import Path

import torch
import yaml
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from src.schemas.evidence import CANONICAL_DAMAGE_CLASSES, NarrativeEvidence

DEFAULT_MODEL_NAME = "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"
LABELS_CONFIG_PATH = Path(__file__).resolve().parents[2] / "configs" / "labels.yaml"


def load_hypotheses(path: Path = LABELS_CONFIG_PATH) -> dict[str, str]:
    with Path(path).open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    hypotheses = cfg["nli_hypotheses"]
    missing = set(CANONICAL_DAMAGE_CLASSES) - set(hypotheses)
    if missing:
        raise ValueError(f"Faltan hipotesis NLI para las clases: {missing}")
    return hypotheses


@dataclass
class NarrativeResult:
    raw_scores: dict[str, float]
    normalized_scores: dict[str, float]
    top_damage: str
    top_confidence: float
    entropy: float
    model_name: str
    model_revision: str | None
    device: str
    inference_time_seconds: float

    def to_evidence(self) -> NarrativeEvidence:
        return NarrativeEvidence(
            raw_scores=self.raw_scores,
            normalized_scores=self.normalized_scores,
            model_name=self.model_name,
            model_revision=self.model_revision,
            device=self.device,
        )


class NarrativeExtractor:
    """Envuelve mDeBERTa-v3-base-mnli-xnli para scoring multi-label de
    danio vehicular a partir de narrativa libre en espanol."""

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        hypotheses: dict[str, str] | None = None,
        device: str | None = None,
    ):
        self.model_name = model_name
        self.hypotheses = hypotheses or load_hypotheses()
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()

        self.model_revision = getattr(self.model.config, "_commit_hash", None)

        label2id = {k.lower(): v for k, v in self.model.config.label2id.items()}
        if "entailment" not in label2id:
            raise ValueError(
                f"El modelo '{model_name}' no expone una etiqueta 'entailment' "
                f"en config.label2id ({self.model.config.label2id})"
            )
        self._entailment_index = label2id["entailment"]

    @torch.inference_mode()
    def extract(self, narrative_text: str) -> NarrativeResult:
        if narrative_text is None or not narrative_text.strip():
            raise ValueError(
                "narrative_text vacio: NarrativeExtractor requiere texto no "
                "vacio. La ausencia de narrativa se maneja como 'text_missing' "
                "en la capa de features/rules (regla R01), no aqui."
            )

        start = time.perf_counter()

        raw_scores: dict[str, float] = {}
        for damage_class in CANONICAL_DAMAGE_CLASSES:
            hypothesis = self.hypotheses[damage_class]
            inputs = self.tokenizer(
                narrative_text,
                hypothesis,
                return_tensors="pt",
                truncation=True,
            ).to(self.device)
            logits = self.model(**inputs).logits[0]
            probs = torch.softmax(logits, dim=-1)
            raw_scores[damage_class] = float(probs[self._entailment_index])

        inference_time = time.perf_counter() - start

        total = sum(raw_scores.values())
        if total > 0:
            normalized_scores = {k: v / total for k, v in raw_scores.items()}
        else:
            normalized_scores = {k: 0.0 for k in raw_scores}

        top_damage = max(raw_scores, key=raw_scores.get)
        top_confidence = raw_scores[top_damage]

        entropy = -sum(p * math.log(p) for p in normalized_scores.values() if p > 0)

        return NarrativeResult(
            raw_scores=raw_scores,
            normalized_scores=normalized_scores,
            top_damage=top_damage,
            top_confidence=top_confidence,
            entropy=entropy,
            model_name=self.model_name,
            model_revision=self.model_revision,
            device=self.device,
            inference_time_seconds=inference_time,
        )
