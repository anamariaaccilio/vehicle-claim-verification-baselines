"""Tests de FASE 4: chequeos de calidad de imagen (reales, con imagenes
sinteticas generadas en el momento; sin mocks de cv2/PIL)."""
import numpy as np
import pytest
from PIL import Image

from src.forensic.image_quality import assess_image_quality, quality_status


def _save_checkerboard(path, size=(300, 300)):
    # patron de alta frecuencia -> Laplaciano alto -> imagen "nitida"
    # size sigue la convencion de PIL: (width, height)
    width, height = size
    arr = np.indices((height, width)).sum(axis=0) % 2 * 255
    Image.fromarray(arr.astype("uint8")).save(path)


def _save_flat_image(path, size=(300, 300), color=128):
    # imagen totalmente plana -> Laplaciano ~0 -> "borrosa"/sin detalle
    Image.new("L", size, color=color).save(path)


def test_assess_image_quality_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        assess_image_quality(tmp_path / "no_existe.jpg")


def test_assess_image_quality_corrupted_file(tmp_path):
    bad_path = tmp_path / "corrupto.jpg"
    bad_path.write_bytes(b"esto no es una imagen valida")

    quality = assess_image_quality(bad_path)
    assert quality.is_corrupted is True
    assert quality_status(quality) == "INSUFFICIENT"


def test_assess_image_quality_reports_resolution_and_format(tmp_path):
    path = tmp_path / "sharp.png"
    _save_checkerboard(path, size=(320, 240))

    quality = assess_image_quality(path)
    assert quality.is_corrupted is False
    assert quality.width == 320
    assert quality.height == 240
    assert quality.aspect_ratio == pytest.approx(320 / 240)
    assert quality.file_format == "PNG"
    assert quality.file_size_bytes > 0


def test_blur_detection_distinguishes_sharp_from_flat_image(tmp_path):
    sharp_path = tmp_path / "sharp.png"
    flat_path = tmp_path / "flat.png"
    _save_checkerboard(sharp_path)
    _save_flat_image(flat_path)

    sharp_quality = assess_image_quality(sharp_path)
    flat_quality = assess_image_quality(flat_path)

    assert sharp_quality.laplacian_variance > flat_quality.laplacian_variance
    assert flat_quality.laplacian_variance < 5.0  # practicamente sin bordes


def test_quality_status_good_for_sharp_high_res_image(tmp_path):
    path = tmp_path / "sharp.png"
    _save_checkerboard(path, size=(400, 400))
    quality = assess_image_quality(path)
    assert quality_status(quality) == "GOOD"


def test_quality_status_insufficient_for_flat_low_detail_image(tmp_path):
    path = tmp_path / "flat.png"
    _save_flat_image(path, size=(400, 400))
    quality = assess_image_quality(path)
    assert quality_status(quality) == "INSUFFICIENT"


def test_quality_status_insufficient_for_tiny_image(tmp_path):
    path = tmp_path / "tiny.png"
    _save_checkerboard(path, size=(20, 20))
    quality = assess_image_quality(path)
    assert quality_status(quality) == "INSUFFICIENT"


def test_assess_image_quality_handles_utf8_path(tmp_path):
    path = tmp_path / "imagen_dañada_ñoño.png"
    _save_checkerboard(path)
    quality = assess_image_quality(path)
    assert quality.is_corrupted is False
