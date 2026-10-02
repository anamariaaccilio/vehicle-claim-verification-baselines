"""FASE 3: conversion de manifest interno a formato YOLO-seg + fine-tuning
(Ultralytics) sobre las anotaciones HITL.

ESTADO ACTUAL (ver reporte de la iteracion): data/raw/hitl/ esta vacio, por
lo que este modulo NO se ha ejecutado contra datos reales todavia. La
funcion build_yolo_seg_dataset() esta probada con manifests sinteticos
(tests/test_damage_dataset.py) para validar la logica de conversion antes
de que llegue el dataset real.

base_model usa un checkpoint verificado contra los .yaml de arquitectura
que trae instalada la version de ultralytics de este entorno
(ultralytics/cfg/models/v8/yolov8-seg.yaml existe => 'yolov8n-seg.pt' es un
nombre de peso real soportado, no inventado).
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import yaml

from src.schemas.claim import SourceImage
from src.schemas.evidence import CANONICAL_DAMAGE_CLASSES

CONFIG_PATH = Path(__file__).resolve().parents[2] / "configs" / "baseline.yaml"


def _load_damage_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg.get("damage", {})


def _polygon_to_yolo_line(class_index: int, points: list[tuple[float, float]], img_w: int, img_h: int) -> str:
    coords: list[str] = []
    for x, y in points:
        coords.append(f"{min(max(x / img_w, 0.0), 1.0):.6f}")
        coords.append(f"{min(max(y / img_h, 0.0), 1.0):.6f}")
    return f"{class_index} " + " ".join(coords)


def build_yolo_seg_dataset(
    records: list[SourceImage],
    output_dir: str | Path,
    class_names: list[str] = CANONICAL_DAMAGE_CLASSES,
) -> Path:
    """Convierte un manifest interno (SourceImage con anotaciones
    poligonales) al layout que espera Ultralytics YOLO para segmentacion:

        <output_dir>/images/<split>/*.jpg
        <output_dir>/labels/<split>/*.txt   (una linea por instancia:
            "<class_idx> x1 y1 x2 y2 ... xn yn", coords normalizadas [0,1])
        <output_dir>/data.yaml

    Anotaciones sin poligono (solo bbox) se omiten: segmentacion requiere
    poligono. Registros sin split asignado (ver src/data/split.py) tambien
    se omiten. Ambos casos se reportan al final, nunca en silencio.
    """
    from PIL import Image

    output_dir = Path(output_dir)
    class_index = {name: i for i, name in enumerate(class_names)}

    skipped_no_polygon = 0
    skipped_no_split = 0
    written = 0

    for record in records:
        if record.split is None:
            skipped_no_split += 1
            continue

        split_name = record.split.value
        img_path = Path(record.path)

        with Image.open(img_path) as im:
            width, height = im.size

        lines: list[str] = []
        for ann in record.annotations:
            if ann.polygon is None:
                skipped_no_polygon += 1
                continue
            if ann.damage_class not in class_index:
                continue
            lines.append(
                _polygon_to_yolo_line(class_index[ann.damage_class], ann.polygon.points, width, height)
            )

        images_dir = output_dir / "images" / split_name
        labels_dir = output_dir / "labels" / split_name
        images_dir.mkdir(parents=True, exist_ok=True)
        labels_dir.mkdir(parents=True, exist_ok=True)

        dest_image = images_dir / img_path.name
        if not dest_image.exists():
            shutil.copy2(img_path, dest_image)

        label_path = labels_dir / (img_path.stem + ".txt")
        label_path.write_text("\n".join(lines), encoding="utf-8")
        written += 1

    data_yaml = {
        "path": str(output_dir.resolve()),
        "train": "images/train",
        "val": "images/validation",
        "test": "images/test",
        "names": {i: name for i, name in enumerate(class_names)},
    }
    data_yaml_path = output_dir / "data.yaml"
    with data_yaml_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data_yaml, f, allow_unicode=True, sort_keys=False)

    if skipped_no_polygon:
        print(
            f"[build_yolo_seg_dataset] aviso: {skipped_no_polygon} anotaciones "
            "sin poligono omitidas (segmentacion requiere poligono, no solo bbox)."
        )
    if skipped_no_split:
        print(
            f"[build_yolo_seg_dataset] aviso: {skipped_no_split} registros sin "
            "split asignado omitidos (correr src/data/split.py primero)."
        )
    print(f"[build_yolo_seg_dataset] {written} imagenes escritas en {output_dir}")

    return data_yaml_path


def train(
    data_yaml_path: str | Path,
    base_model: str = "yolov8n-seg.pt",
    epochs: int = 3,
    imgsz: int = 640,
    batch: int = 4,
    project: str = "artifacts/damage",
    name: str = "smoke_test",
    **kwargs,
):
    """Fine-tuning real con Ultralytics YOLO. NO se ejecuta automaticamente
    al importar este modulo: requiere invocacion explicita via CLI
    (`python -m src.damage.train ...`) una vez el dataset este disponible."""
    from ultralytics import YOLO

    model = YOLO(base_model)
    return model.train(
        data=str(data_yaml_path),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        project=project,
        name=name,
        **kwargs,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Fine-tuning del Damage Specialist (Ultralytics YOLO-seg) sobre el manifest HITL."
    )
    parser.add_argument("--manifest", required=True, help="Path al manifest.jsonl (ver src/data/manifest.py)")
    parser.add_argument("--dataset-dir", default="data/processed/yolo_seg", help="Donde escribir el dataset en formato YOLO")
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Entrenamiento corto (subconjunto de imagenes, pocas epochs) solo para validar el pipeline, NO para obtener buen desempeno",
    )
    args = parser.parse_args()

    from src.data.manifest import load_manifest

    records = load_manifest(args.manifest)
    if args.smoke_test:
        records = records[:20]

    cfg = _load_damage_config()
    data_yaml_path = build_yolo_seg_dataset(records, args.dataset_dir)

    epochs = cfg.get("epochs_smoke_test", 3) if args.smoke_test else cfg.get("epochs", 50)
    batch = cfg.get("batch_smoke_test", 4) if args.smoke_test else cfg.get("batch", 16)

    train(
        data_yaml_path,
        base_model=cfg.get("base_model", "yolov8n-seg.pt"),
        epochs=epochs,
        imgsz=cfg.get("imgsz", 640),
        batch=batch,
        name="smoke_test" if args.smoke_test else "full_train",
    )


if __name__ == "__main__":
    main()
