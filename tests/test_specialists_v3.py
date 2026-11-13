"""Specialist adapters for v3: assertion extraction, quality factors, validity criteria."""
import importlib.util
import json
from pathlib import Path

import numpy as np

from src.narrative.assertions import ONTOLOGY_FIELDS, build_assertion, entropy3, split_sentences
from src.schemas.evidence import CANONICAL_DAMAGE_CLASSES

ROOT = Path(__file__).resolve().parents[1]


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"scripts/{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def nli(target, triple):
    return {k: (triple if k == target else (0.02, 0.96, 0.02)) for k in CANONICAL_DAMAGE_CLASSES}


def test_assertion_polarity_uncertainty_and_coverage():
    a = build_assertion("El vehículo presenta abolladuras leves en la puerta.", nli("dent", (0.9, 0.05, 0.05)))
    assert a.damage_type == "dent" and a.polarity == "affirmed"
    assert a.part == "door" and a.severity == "minor" and a.circumstance is None
    assert a.coverage == 3 / 4 and a.missing_fields == ["circumstance"]
    assert 0 < a.u < 1 and abs(a.u - entropy3((0.9, 0.05, 0.05))) < 1e-12
    d = build_assertion("El vehículo está libre de rayones.", nli("scratch", (0.05, 0.05, 0.9)))
    assert d.polarity == "denied" and d.coverage == 1 / len(ONTOLOGY_FIELDS)


def test_non_damage_sentence_is_not_an_assertion():
    assert build_assertion("Se describe el estado visible.", nli("dent", (0.1, 0.8, 0.1))) is None
    assert split_sentences("Uno. Dos; tres!") == ["Uno.", "Dos;", "tres!"]


def test_quality_factors_are_bounded_and_ignore_mode():
    run = _load("run_specialists")
    rng = np.random.default_rng(0)
    rgb = rng.integers(0, 255, (120, 160, 3), dtype=np.uint8)
    q = run.quality_factors(rgb)
    assert all(0.0 <= q[k] <= 1.0 for k in ("resolution", "sharpness", "exposure", "q"))
    flat = run.quality_factors(np.full((120, 160, 3), 128, dtype=np.uint8))
    assert flat["sharpness"] == 0.0 and flat["q"] == 0.0


def test_validity_criteria_reproduce_and_freeze_is_official():
    bundle = ROOT / "data/manifests/benchmark_v3"
    freeze = json.loads((bundle / "freeze.json").read_text())
    assert freeze["READY_FOR_MODELS"] == "YES" and freeze["frozen_on"] == "2026-11-13"
    validity = json.loads((bundle / "validity_criteria.json").read_text())
    assert validity["summary"]["C2"] == {"AMBIGUOUS": 510, "VALID": 297}
    statuses = {r["status"] for r in validity["cases"]}
    assert statuses <= {"VALID", "AMBIGUOUS", "INVALID"}
    excluded = json.loads((bundle / "exclusions_criteria.json").read_text())
    assert {e["claim_id"] for e in excluded} == {r["claim_id"] for r in validity["cases"] if r["status"] == "INVALID"}


def test_c2_rule_on_synthetic_rows():
    mod = _load("apply_v3_validity_criteria")
    sources = {"a": {"source_image_id": "a", "damage_classes": ["dent"], "dhash128": "0" * 32},
               "b": {"source_image_id": "b", "damage_classes": ["dent"], "dhash128": "f" * 32},
               "c": {"source_image_id": "c", "damage_classes": ["scratch"], "dhash128": "f" * 32},
               "d": {"source_image_id": "d", "damage_classes": ["scratch"], "dhash128": "0" * 31 + "1"}}
    def c2(cid, donor):
        return {"claim_id": cid, "condition": "C2", "source_image_id": "a", "expected_label": "SUSPICIOUS",
                "metadata": {"asserted_damage_classes": ["dent"]},
                "transformation": {"donor_source_image_ids": [donor]}}
    rows = mod.classify([c2("x", "b"), c2("y", "c"), c2("z", "d")], sources, {"C3": [], "C4": [], "C5": []}, 6)
    assert {r["claim_id"]: r["status"] for r in rows} == {"x": "AMBIGUOUS", "y": "VALID", "z": "INVALID"}
