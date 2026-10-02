"""Tests de FASE 3.

data/raw/hitl/ esta vacio en este repositorio (dataset no descargado
todavia), asi que estos tests NO entrenan ni corren inferencia real de
segmentacion. Validan:
  1. la conversion manifest -> formato YOLO-seg con un manifest sintetico
     (prueba la logica de build_yolo_seg_dataset sin necesitar el dataset real);
  2. que DamageSpecialist.is_available sea False de forma honesta cuando no
     hay checkpoint, y que predict() no fabrique resultados.
"""
from pathlib import Path

import pytest
import yaml
from PIL import Image

from src.damage.inference import DamageSpecialist
from src.damage.train import build_yolo_seg_dataset
from src.schemas.claim import SourceImage, Split
from src.schemas.evidence import DamageAnnotation, Polygon


def _make_synthetic_image(path: Path, size=(64, 48)):
    Image.new("RGB", size, color=(120, 120, 120)).save(path)


def test_build_yolo_seg_dataset_from_synthetic_manifest(tmp_path):
    img_dir = tmp_path / "raw_images"
    img_dir.mkdir()
    img1 = img_dir / "car_00001.jpg"
    img2 = img_dir / "car_00002.jpg"
    _make_synthetic_image(img1, size=(100, 50))
    _make_synthetic_image(img2, size=(80, 80))

    records = [
        SourceImage(
            source_image_id="car_00001",
            path=str(img1),
            split=Split.TRAIN,
            annotations=[
                DamageAnnotation(
                    damage_class="dent",
                    polygon=Polygon(points=[(10, 10), (50, 10), (50, 30), (10, 30)]),
                ),
                DamageAnnotation(damage_class="scratch"),  # sin poligono -> se omite
            ],
        ),
        SourceImage(
            source_image_id="car_00002",
            path=str(img2),
            split=Split.VALIDATION,
            annotations=[
                DamageAnnotation(
                    damage_class="crack",
                    polygon=Polygon(points=[(0, 0), (20, 0), (20, 20)]),
                )
            ],
        ),
        SourceImage(source_image_id="car_00003", path="unused.jpg"),  # sin split -> se omite
    ]

    out_dir = tmp_path / "yolo_seg"
    data_yaml_path = build_yolo_seg_dataset(records, out_dir)

    assert data_yaml_path.exists()
    data_cfg = yaml.safe_load(data_yaml_path.read_text(encoding="utf-8"))
    assert data_cfg["names"][0] == "dent"
    assert (out_dir / "images" / "train" / "car_00001.jpg").exists()
    assert (out_dir / "images" / "validation" / "car_00002.jpg").exists()
    assert not (out_dir / "images" / "test").exists() or not list((out_dir / "images" / "test").iterdir())

    train_label = (out_dir / "labels" / "train" / "car_00001.txt").read_text(encoding="utf-8")
    lines = [l for l in train_label.splitlines() if l.strip()]
    assert len(lines) == 1  # solo la anotacion con poligono
    class_idx, *coords = lines[0].split()
    assert class_idx == str(list(data_cfg["names"].values()).index("dent"))
    assert all(0.0 <= float(c) <= 1.0 for c in coords)

    val_label = (out_dir / "labels" / "validation" / "car_00002.txt").read_text(encoding="utf-8")
    assert val_label.strip() != ""


def test_damage_specialist_reports_unavailable_when_no_checkpoint(tmp_path):
    fake_weights = tmp_path / "does_not_exist.pt"
    specialist = DamageSpecialist(weights_path=fake_weights)

    assert specialist.is_available is False

    with pytest.raises(FileNotFoundError):
        specialist.predict("some_image.jpg")


def test_damage_specialist_default_weights_currently_absent():
    # Refleja el estado REAL de este repositorio: sin dataset, sin
    # checkpoint entrenado. Si este test empieza a fallar, es porque ya se
    # entreno un modelo real -- en ese caso hay que actualizar el test, no
    # el codigo.
    specialist = DamageSpecialist()
    assert specialist.is_available is False
