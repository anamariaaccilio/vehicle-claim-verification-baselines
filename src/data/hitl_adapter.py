"""Adapter para el dataset 'Car Parts and Car Damages Dataset' (Humans in
the Loop).

SUPUESTOS (a verificar cuando el usuario coloque el dataset real en
data/raw/hitl/, ver data/README.md):

  - El dataset se distribuye en formato de exportacion estilo COCO
    (categories / images / annotations con 'segmentation' poligonal),
    que es el formato mas comun para este dataset via Roboflow.
  - Puede venir como un unico archivo `_annotations.coco.json` en la raiz
    de data/raw/hitl/, o repartido en subcarpetas (p. ej. train/valid/test
    de Roboflow, cada una con su propio _annotations.coco.json). Si viene
    repartido, este adapter IGNORA el split original de Roboflow: el
    split real del baseline se recalcula desde cero en src/data/split.py
    por source_image_id, para garantizar ausencia de leakage.
  - Las exportaciones de Roboflow frecuentemente generan copias
    aumentadas del mismo archivo original con un sufijo tipo
    '<nombre>_jpg.rf.<hash>.jpg'. Se usa ese patron para agrupar
    derivados bajo el mismo source_image_id (el nombre antes de
    '.rf.<hash>'); si el patron no aparece, se usa el stem del archivo.

Si al integrar el dataset real esta estructura no coincide, ajustar
_iter_coco_files() y _derive_source_image_id() -- el resto del pipeline
(manifest, split, tests) no depende del formato de origen.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from src.schemas.claim import SourceImage
from src.schemas.evidence import (
    HITL_TO_CANONICAL,
    BoundingBox,
    DamageAnnotation,
    Polygon,
)

_RF_SUFFIX_RE = re.compile(r"^(?P<stem>.+?)(?:_jpg|_png|_jpeg)?\.rf\.[0-9a-fA-F]+$")


def _derive_source_image_id(file_name: str) -> str:
    """Agrupa variantes aumentadas de Roboflow bajo un mismo id de imagen
    fuente. Ver docstring del modulo."""
    stem = Path(file_name).stem
    match = _RF_SUFFIX_RE.match(stem)
    if match:
        return match.group("stem")
    return stem


def _iter_coco_files(raw_dir: Path):
    """Encuentra todos los archivos de anotaciones COCO bajo raw_dir."""
    yield from sorted(raw_dir.rglob("*.json"))


def _coco_bbox_to_bbox(coco_bbox: list[float]) -> BoundingBox:
    x, y, w, h = coco_bbox
    return BoundingBox(x_min=x, y_min=y, x_max=x + w, y_max=y + h)


def _coco_segmentation_to_polygon(segmentation) -> Polygon | None:
    if not segmentation:
        return None
    # COCO polygon segmentation: lista de listas planas [x1,y1,x2,y2,...]
    if isinstance(segmentation, list) and segmentation and isinstance(segmentation[0], list):
        flat = segmentation[0]
        points = [(flat[i], flat[i + 1]) for i in range(0, len(flat) - 1, 2)]
        if len(points) >= 3:
            return Polygon(points=points)
    return None


def parse_hitl_dataset(
    raw_dir: str | Path,
    unmapped_class_policy: str = "skip",
) -> list[SourceImage]:
    """Parsea uno o mas exports COCO del dataset HITL bajo raw_dir y
    devuelve una lista de SourceImage SIN split asignado (ver
    src/data/split.py::apply_split para eso).

    unmapped_class_policy: 'skip' (default) ignora categorias COCO que no
    esten en HITL_TO_CANONICAL; 'error' lanza ValueError.
    """
    raw_dir = Path(raw_dir)
    coco_files = list(_iter_coco_files(raw_dir))
    if not coco_files:
        raise FileNotFoundError(
            f"No se encontraron archivos de anotaciones (*.json) bajo {raw_dir}. "
            "Ver data/README.md para instrucciones de descarga y ubicacion."
        )

    images_by_source_id: dict[str, SourceImage] = {}

    for coco_path in coco_files:
        with coco_path.open("r", encoding="utf-8") as f:
            coco = json.load(f)

        categories = {c["id"]: c["name"] for c in coco.get("categories", [])}
        images = {img["id"]: img for img in coco.get("images", [])}
        anns_by_image: dict[int, list[dict]] = {}
        for ann in coco.get("annotations", []):
            anns_by_image.setdefault(ann["image_id"], []).append(ann)

        image_dir = coco_path.parent

        for image_id, image_meta in images.items():
            file_name = image_meta["file_name"]
            source_image_id = _derive_source_image_id(file_name)
            image_path = str((image_dir / file_name).resolve())

            annotations: list[DamageAnnotation] = []
            for ann in anns_by_image.get(image_id, []):
                category_name = categories.get(ann["category_id"])
                canonical = HITL_TO_CANONICAL.get(category_name)
                if canonical is None:
                    if unmapped_class_policy == "error":
                        raise ValueError(
                            f"Categoria COCO '{category_name}' sin mapping en "
                            "HITL_TO_CANONICAL (configs/labels.yaml)"
                        )
                    continue

                annotations.append(
                    DamageAnnotation(
                        damage_class=canonical,
                        bbox=_coco_bbox_to_bbox(ann["bbox"]) if ann.get("bbox") else None,
                        polygon=_coco_segmentation_to_polygon(ann.get("segmentation")),
                    )
                )

            if source_image_id in images_by_source_id:
                # Ya vista otra variante/derivado de la misma imagen fuente:
                # se fusionan anotaciones, se mantiene el primer path visto.
                existing = images_by_source_id[source_image_id]
                existing.annotations.extend(annotations)
            else:
                images_by_source_id[source_image_id] = SourceImage(
                    source_image_id=source_image_id,
                    path=image_path,
                    annotations=annotations,
                )

    return list(images_by_source_id.values())
