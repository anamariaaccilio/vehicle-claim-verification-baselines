"""Tests de FASE 1: manifest JSONL (UTF-8, roundtrip, dimension estable)."""
from src.data.manifest import load_manifest, save_manifest
from src.schemas.claim import SourceImage, Split
from src.schemas.evidence import DamageAnnotation, Polygon


def test_manifest_roundtrip_preserves_data(tmp_path):
    records = [
        SourceImage(
            source_image_id="car_00001",
            path="data/raw/hitl/car_00001.jpg",
            split=Split.TRAIN,
            annotations=[
                DamageAnnotation(
                    damage_class="dent",
                    confidence=0.87,
                    polygon=Polygon(points=[(1.0, 2.0), (3.0, 4.0), (5.0, 1.0)]),
                )
            ],
        ),
    ]

    out_path = tmp_path / "manifest.jsonl"
    save_manifest(records, out_path)
    loaded = load_manifest(out_path)

    assert loaded == records


def test_manifest_handles_utf8_paths_and_narratives(tmp_path):
    # Nombres de archivo con caracteres no-ASCII (acentos, enie) comunes en
    # datasets/rutas en espanol.
    records = [
        SourceImage(
            source_image_id="camion_dañado_01",
            path="data/raw/hitl/camión_dañado_01.jpg",
        ),
    ]

    out_path = tmp_path / "manifest_utf8.jsonl"
    save_manifest(records, out_path)

    raw_bytes = out_path.read_bytes()
    raw_bytes.decode("utf-8")  # no debe lanzar UnicodeDecodeError

    loaded = load_manifest(out_path)
    assert loaded[0].source_image_id == "camion_dañado_01"
    assert loaded[0].path == "data/raw/hitl/camión_dañado_01.jpg"


def test_manifest_records_have_stable_field_set(tmp_path):
    records = [
        SourceImage(source_image_id="car_00001", path="a.jpg"),
        SourceImage(source_image_id="car_00002", path="b.jpg", annotations=[
            DamageAnnotation(damage_class="scratch")
        ]),
    ]
    out_path = tmp_path / "manifest.jsonl"
    save_manifest(records, out_path)
    loaded = load_manifest(out_path)

    keys_0 = set(loaded[0].model_dump().keys())
    keys_1 = set(loaded[1].model_dump().keys())
    assert keys_0 == keys_1
