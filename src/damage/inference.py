"""FASE 3: inferencia del Damage Specialist (segmentacion Ultralytics).

ESTADO ACTUAL: no existe ningun checkpoint fine-tuneado (no hay dataset
todavia, ver data/README.md). DamageSpecialist.is_available siempre
devuelve False en este repositorio hasta que:
  1. el dataset HITL se coloque en data/raw/hitl/,
  2. se genere el manifest (src/data/hitl_adapter.py + split.py),
  3. se corra src/damage/train.py,
  4. el checkpoint resultante quede en configs/baseline.yaml::damage.weights_path.

predict() NUNCA fabrica una deteccion: si is_available es False, lanza
FileNotFoundError explicito en vez de simular un resultado.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from src.schemas.evidence import BoundingBox, DamageAnnotation, Polygon, VisualEvidence

CONFIG_PATH = Path(__file__).resolve().parents[2] / "configs" / "baseline.yaml"


def _load_damage_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg.get("damage", {})


class DamageSpecialist:
    """Envuelve un checkpoint Ultralytics YOLO-seg fine-tuneado sobre HITL."""

    def __init__(self, weights_path: str | Path | None = None, conf_threshold: float | None = None):
        cfg = _load_damage_config()
        self.weights_path = Path(weights_path or cfg.get("weights_path", "artifacts/damage/weights/best.pt"))
        self.conf_threshold = conf_threshold if conf_threshold is not None else cfg.get("conf_threshold", 0.25)
        self._model = None

    @property
    def is_available(self) -> bool:
        return self.weights_path.exists()

    def _load_model(self):
        if self._model is None:
            from ultralytics import YOLO

            self._model = YOLO(str(self.weights_path))
        return self._model

    def predict(self, image_path: str | Path) -> VisualEvidence:
        if not self.is_available:
            raise FileNotFoundError(
                f"No hay un checkpoint de Damage Specialist en '{self.weights_path}'. "
                "El modelo NO esta disponible todavia (falta dataset/entrenamiento; "
                "ver data/README.md y src/damage/train.py). No se fabrica ninguna deteccion."
            )

        model = self._load_model()
        results = model.predict(str(image_path), conf=self.conf_threshold, verbose=False)
        result = results[0]

        names = result.names
        img_h, img_w = result.orig_shape
        boxes = result.boxes
        masks = result.masks

        detections: list[DamageAnnotation] = []
        if boxes is not None:
            for i in range(len(boxes)):
                class_id = int(boxes.cls[i])
                class_name = names[class_id]
                confidence = float(boxes.conf[i])
                xyxy = boxes.xyxy[i].tolist()
                bbox = BoundingBox(x_min=xyxy[0], y_min=xyxy[1], x_max=xyxy[2], y_max=xyxy[3])

                polygon = None
                if masks is not None:
                    poly_xy = masks.xy[i]
                    if len(poly_xy) >= 3:
                        polygon = Polygon(points=[(float(x), float(y)) for x, y in poly_xy])

                detections.append(
                    DamageAnnotation(
                        damage_class=class_name,
                        confidence=confidence,
                        bbox=bbox,
                        polygon=polygon,
                    )
                )

        return VisualEvidence(
            detections=detections,
            model_name=str(self.weights_path),
            image_width=img_w,
            image_height=img_h,
        )
