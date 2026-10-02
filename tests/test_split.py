"""Tests de FASE 1: split determinista y ausencia de leakage por source_image_id."""
from src.data.split import (
    DEFAULT_RATIOS,
    LeakageError,
    apply_split,
    assign_splits,
    check_no_leakage,
)
from src.schemas.claim import SourceImage, Split


def _ids(n: int) -> list[str]:
    return [f"car_{i:05d}" for i in range(n)]


def test_assign_splits_is_deterministic_across_calls():
    ids = _ids(200)
    a = assign_splits(ids, seed=42)
    b = assign_splits(ids, seed=42)
    assert a == b


def test_assign_splits_is_deterministic_regardless_of_input_order():
    ids = _ids(200)
    shuffled = list(reversed(ids))
    a = assign_splits(ids, seed=42)
    b = assign_splits(shuffled, seed=42)
    assert a == b


def test_assign_splits_changes_with_seed():
    ids = _ids(200)
    a = assign_splits(ids, seed=42)
    b = assign_splits(ids, seed=7)
    assert a != b


def test_assign_splits_respects_ratios_approximately():
    ids = _ids(5000)
    assignment = assign_splits(ids, seed=42)
    counts = {s: 0 for s in Split}
    for split in assignment.values():
        counts[split] += 1

    total = len(ids)
    for split, ratio in DEFAULT_RATIOS.items():
        observed = counts[split] / total
        assert abs(observed - ratio) < 0.03  # tolerancia estadistica


def test_no_derived_variant_crosses_split_boundary():
    # Simula variantes derivadas de la misma imagen fuente (p. ej. benchmark
    # C8 JPEG-comprimido o C9 con blur) que deben permanecer en el mismo split.
    records = [
        SourceImage(source_image_id="car_00001", path="car_00001.jpg"),
        SourceImage(source_image_id="car_00001", path="car_00001_jpeg_q30.jpg"),
        SourceImage(source_image_id="car_00001", path="car_00001_blur.jpg"),
        SourceImage(source_image_id="car_00002", path="car_00002.jpg"),
    ]
    split_records = apply_split(records, seed=42)
    check_no_leakage(split_records)  # no debe lanzar

    splits_for_car1 = {r.split for r in split_records if r.source_image_id == "car_00001"}
    assert len(splits_for_car1) == 1


def test_check_no_leakage_detects_conflicting_splits():
    records = [
        SourceImage(source_image_id="car_00001", path="a.jpg", split=Split.TRAIN),
        SourceImage(source_image_id="car_00001", path="b.jpg", split=Split.TEST),
    ]
    try:
        check_no_leakage(records)
        assert False, "se esperaba LeakageError"
    except LeakageError:
        pass
