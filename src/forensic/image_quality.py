"""Chequeos reproducibles de calidad de imagen.

IMPORTANTE: estos valores representan CALIDAD de la fotografia, no fraude.
Una imagen borrosa o de baja resolucion nunca debe etiquetarse como
sospechosa por ese motivo; a lo sumo, calidad insuficiente contribuye a la
decision INSUFFICIENT (ver src/fusion/rules.py, regla R03).
"""
from __future__ import annotations

from pathlib import Path

import cv2
import yaml
from PIL import Image, UnidentifiedImageError

from src.schemas.evidence import ImageQuality

CONFIG_PATH = Path(__file__).resolve().parents[2] / "configs" / "baseline.yaml"


def _load_image_quality_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg.get("image_quality", {})


def _laplacian_variance(image_path: Path) -> float | None:
    gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if gray is None:
        return None
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def assess_image_quality(image_path: str | Path) -> ImageQuality:
    """Evalua una imagen existente en disco. Lanza FileNotFoundError si el
    archivo no existe (la ausencia de imagen se maneja como 'image_missing'
    en la capa de features/rules, regla R02, no aqui)."""
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"No existe el archivo de imagen: {image_path}")

    file_size_bytes = image_path.stat().st_size

    try:
        with Image.open(image_path) as im:
            im.verify()
        with Image.open(image_path) as im:
            width, height = im.size
            file_format = im.format or image_path.suffix.lstrip(".").upper()
    except (UnidentifiedImageError, OSError, ValueError):
        return ImageQuality(
            width=0,
            height=0,
            aspect_ratio=0.0,
            file_size_bytes=file_size_bytes,
            file_format="unknown",
            laplacian_variance=None,
            is_corrupted=True,
        )

    aspect_ratio = width / height if height else 0.0
    laplacian_variance = _laplacian_variance(image_path)

    return ImageQuality(
        width=width,
        height=height,
        aspect_ratio=aspect_ratio,
        file_size_bytes=file_size_bytes,
        file_format=file_format,
        laplacian_variance=laplacian_variance,
        is_corrupted=False,
    )


def quality_status(quality: ImageQuality, cfg: dict | None = None) -> str:
    """Devuelve 'GOOD', 'LOW QUALITY' o 'INSUFFICIENT' segun thresholds de
    configs/baseline.yaml::image_quality. Nunca devuelve una etiqueta de
    fraude."""
    cfg = cfg or _load_image_quality_config()

    if quality.is_corrupted:
        return "INSUFFICIENT"

    if quality.width < cfg.get("min_width", 200) or quality.height < cfg.get("min_height", 200):
        return "INSUFFICIENT"

    if quality.laplacian_variance is not None:
        if quality.laplacian_variance < cfg.get("blur_variance_insufficient_threshold", 30.0):
            return "INSUFFICIENT"
        if quality.laplacian_variance < cfg.get("blur_variance_low_quality_threshold", 100.0):
            return "LOW QUALITY"

    return "GOOD"
