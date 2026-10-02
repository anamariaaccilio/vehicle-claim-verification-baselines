"""Tests de FASE 1: schemas, taxonomia canonica y mapping HITL.

Los tests de: narrativa vacia, imagen ausente/corrupta, modelo forense
deshabilitado, rule engine y semantic mismatch se agregan en sus fases
correspondientes (2, 4, 8), cuando esos modulos dejen de ser stubs.
"""
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from src.schemas.claim import Claim, Split, SourceImage
from src.schemas.evidence import (
    CANONICAL_DAMAGE_CLASSES,
    HITL_TO_CANONICAL,
    DamageAnnotation,
    DecisionLabel,
)

CONFIG_DIR = Path(__file__).resolve().parents[1] / "configs"


def test_labels_yaml_matches_canonical_classes_constant():
    with (CONFIG_DIR / "labels.yaml").open("r", encoding="utf-8") as f:
        labels_cfg = yaml.safe_load(f)

    assert set(labels_cfg["canonical_classes"]) == set(CANONICAL_DAMAGE_CLASSES)
    assert len(labels_cfg["canonical_classes"]) == 8


def test_labels_yaml_hitl_mapping_matches_constant():
    with (CONFIG_DIR / "labels.yaml").open("r", encoding="utf-8") as f:
        labels_cfg = yaml.safe_load(f)

    assert labels_cfg["hitl_to_canonical"] == HITL_TO_CANONICAL


def test_hitl_mapping_targets_are_all_canonical():
    for canonical in HITL_TO_CANONICAL.values():
        assert canonical in CANONICAL_DAMAGE_CLASSES


def test_damage_annotation_accepts_canonical_class():
    ann = DamageAnnotation(damage_class="dent", confidence=0.9)
    assert ann.damage_class == "dent"


def test_damage_annotation_rejects_non_canonical_class():
    with pytest.raises(ValidationError):
        DamageAnnotation(damage_class="Dent")  # debe ser 'dent' (canonico), no el raw HITL


def test_damage_annotation_confidence_bounds():
    with pytest.raises(ValidationError):
        DamageAnnotation(damage_class="dent", confidence=1.5)


def test_source_image_derives_damage_classes_from_annotations():
    img = SourceImage(
        source_image_id="car_0001",
        path="data/raw/hitl/car_0001.jpg",
        annotations=[
            DamageAnnotation(damage_class="dent"),
            DamageAnnotation(damage_class="scratch"),
            DamageAnnotation(damage_class="dent"),
        ],
    )
    assert img.damage_classes == ["dent", "scratch"]


def test_source_image_split_optional_until_assigned():
    img = SourceImage(source_image_id="car_0002", path="x.jpg")
    assert img.split is None


def test_claim_allows_missing_narrative_text():
    claim = Claim(claim_id="c1", narrative_text=None, image_path="x.jpg")
    assert claim.narrative_text is None


def test_claim_allows_missing_image():
    claim = Claim(claim_id="c2", narrative_text="Mi vehiculo presenta una abolladura.", image_path=None)
    assert claim.image_path is None


def test_claim_expected_label_is_decision_enum():
    claim = Claim(claim_id="c3", expected_label=DecisionLabel.SUSPICIOUS)
    assert claim.expected_label == DecisionLabel.SUSPICIOUS


def test_split_enum_values():
    assert {s.value for s in Split} == {"train", "validation", "test"}
