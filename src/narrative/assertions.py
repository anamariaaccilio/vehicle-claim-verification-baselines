"""Especialista narrativo por afirmación (tesis, sec. especialistas).

Convierte el relato en afirmaciones estructuradas (parte afectada, tipo de daño,
severidad, circunstancia) con un modelo NLI preentrenado (mDeBERTa-v3 xnli, solo
inferencia; no se entrena ningún modelo de lenguaje). Por afirmación entrega:

  p  = (p_entail, p_neutral, p_contradiction) de la hipótesis de su tipo de daño
  u  = H(p) / log 3            (incertidumbre del extractor, en [0, 1])
  c  = campos de la ontología llenados / 4   (cobertura)
  missing_fields = campos de la ontología sin llenar

Segmentación: una afirmación por oración. Una oración cuya relevancia máxima
(p_entail + p_contradiction sobre las 8 hipótesis de daño) es < ``RELEVANCE_MIN``
no habla de un daño (p. ej. "Se describe el estado visible.") y no se convierte
en afirmación. Parte, severidad y circunstancia se extraen con un léxico fijo de
la ontología (abajo), nunca desde metadatos del reclamo.

Nada aquí lee expected_label, condition, claim_id ni rutas: solo el texto.
"""
from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass, field

from src.schemas.evidence import CANONICAL_DAMAGE_CLASSES

RELEVANCE_MIN = 0.5
ONTOLOGY_FIELDS = ("part", "damage_type", "severity", "circumstance")

PART_LEXICON = {
    "bumper": ["parachoques", "paragolpes", "defensa", "bumper"],
    "door": ["puerta"],
    "hood": ["capo", "cofre"],
    "fender": ["guardabarros", "salpicadera", "aleta"],
    "headlight": ["faro", "foco", "luz delantera"],
    "taillight": ["piloto", "luz trasera", "stop"],
    "mirror": ["espejo", "retrovisor"],
    "windshield": ["parabrisas", "luna"],
    "trunk": ["maletero", "baul", "cajuela", "portalon"],
    "roof": ["techo"],
    "wheel": ["rueda", "llanta", "neumatico", "rin"],
    "grille": ["parrilla", "rejilla"],
    "quarter_panel": ["panel lateral", "costado", "lateral"],
}
SEVERITY_LEXICON = {
    "minor": ["leve", "leves", "pequeno", "pequenos", "pequena", "pequenas", "superficial", "superficiales",
              "ligero", "ligeros", "ligera", "ligeras", "menor", "menores"],
    "moderate": ["moderado", "moderados", "moderada", "moderadas", "considerable", "considerables", "notable"],
    "severe": ["grave", "graves", "severo", "severos", "severa", "severas", "fuerte", "fuertes", "profundo",
               "profundos", "profunda", "profundas", "importante", "importantes", "total"],
}
CIRCUMSTANCE_LEXICON = {
    "collision": ["choque", "colision", "impacto", "golpe", "chocaron", "choco"],
    "parking": ["estacionado", "estacionamiento", "aparcado", "parqueado"],
    "vandalism": ["vandalismo", "vandalos", "rayaron"],
    "weather": ["granizo", "tormenta", "inundacion", "arbol"],
    "theft": ["robo", "robaron", "hurto"],
}


def _fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def _lexicon_match(folded: str, lexicon: dict[str, list[str]]) -> str | None:
    for value, words in lexicon.items():
        for word in words:
            if re.search(rf"\b{re.escape(word)}\b", folded):
                return value
    return None


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?;])\s+", text.strip()) if s.strip()]


@dataclass
class Assertion:
    text: str
    damage_type: str
    polarity: str                      # "affirmed" | "denied" | "undetermined"
    p: tuple[float, float, float]      # entail, neutral, contradiction (hypothesis of damage_type)
    u: float
    coverage: float
    part: str | None = None
    severity: str | None = None
    circumstance: str | None = None
    missing_fields: list[str] = field(default_factory=list)
    class_nli: dict[str, tuple[float, float, float]] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {"text": self.text, "damage_type": self.damage_type, "polarity": self.polarity,
                "p": list(self.p), "u": self.u, "coverage": self.coverage, "part": self.part,
                "severity": self.severity, "circumstance": self.circumstance,
                "missing_fields": self.missing_fields,
                "class_nli": {k: list(v) for k, v in self.class_nli.items()}}


def entropy3(p: tuple[float, float, float]) -> float:
    return -sum(x * math.log(x) for x in p if x > 0) / math.log(3)


def build_assertion(sentence: str, class_nli: dict[str, tuple[float, float, float]]) -> Assertion | None:
    """class_nli[k] = (entail, neutral, contradiction) of hypothesis k given the sentence."""
    relevance = {k: v[0] + v[2] for k, v in class_nli.items()}
    damage_type = max(CANONICAL_DAMAGE_CLASSES, key=lambda k: relevance[k])
    if relevance[damage_type] < RELEVANCE_MIN:
        return None
    p = class_nli[damage_type]
    polarity = "affirmed" if p[0] > max(p[1], p[2]) else "denied" if p[2] > max(p[0], p[1]) else "undetermined"
    folded = _fold(sentence)
    part = _lexicon_match(folded, PART_LEXICON)
    severity = _lexicon_match(folded, SEVERITY_LEXICON)
    circumstance = _lexicon_match(folded, CIRCUMSTANCE_LEXICON)
    filled = {"part": part, "damage_type": damage_type, "severity": severity, "circumstance": circumstance}
    missing = [f for f in ONTOLOGY_FIELDS if filled[f] is None]
    return Assertion(text=sentence, damage_type=damage_type, polarity=polarity, p=tuple(p),
                     u=entropy3(tuple(p)), coverage=(4 - len(missing)) / 4, part=part,
                     severity=severity, circumstance=circumstance, missing_fields=missing,
                     class_nli=dict(class_nli))


class SentenceNLI:
    """mDeBERTa NLI, batched over the 8 damage hypotheses, with a sentence cache."""

    def __init__(self, model_name: str = "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli", threads: int | None = None):
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        from src.narrative.nli_extractor import load_hypotheses
        if threads:
            torch.set_num_threads(threads)
        self.torch = torch
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name).eval()
        self.revision = getattr(self.model.config, "_commit_hash", None)
        ids = {k.lower(): v for k, v in self.model.config.label2id.items()}
        self.order = [ids["entailment"], ids["neutral"], ids["contradiction"]]
        self.hypotheses = load_hypotheses()
        self.cache: dict[str, dict[str, tuple[float, float, float]]] = {}

    def __call__(self, sentence: str) -> dict[str, tuple[float, float, float]]:
        if sentence not in self.cache:
            classes = list(CANONICAL_DAMAGE_CLASSES)
            batch = self.tokenizer([sentence] * len(classes), [self.hypotheses[k] for k in classes],
                                   return_tensors="pt", padding=True, truncation=True)
            with self.torch.inference_mode():
                probs = self.torch.softmax(self.model(**batch).logits, dim=-1)[:, self.order]
            self.cache[sentence] = {k: tuple(round(float(x), 6) for x in probs[i]) for i, k in enumerate(classes)}
        return self.cache[sentence]

    def extract(self, text: str | None) -> list[Assertion]:
        if not text or not text.strip():
            return []
        out = []
        for sentence in split_sentences(text):
            assertion = build_assertion(sentence, self(sentence))
            if assertion is not None:
                out.append(assertion)
        return out
