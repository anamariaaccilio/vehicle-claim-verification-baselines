"""PASO 6: genera variantes de estres (JPEG recompression, resize,
gaussian blur) a partir de UNA imagen real, para el benchmark/demo.

Las variantes comparten source_image_id con la imagen original (nunca
cambian de split, ver src/data/split.py). Metadata de cada variante se
anexa a <output_dir>/metadata.jsonl.

NO implementa splice / copy-move / inpainting (eso viene despues, cuando
haya evidence substitution con dos source_image_id reales).

Uso:
    python scripts/create_demo_variants.py \\
        --source demo/cases/assets/case01_clean.jpg \\
        --source-image-id car_00001 \\
        --output-dir demo/cases/assets
"""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def jpeg_recompress(image: Image.Image, quality: int = 30) -> Image.Image:
    buf = io.BytesIO()
    image.convert("RGB").save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


def resize(image: Image.Image, scale: float = 0.5) -> Image.Image:
    w, h = image.size
    new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
    return image.convert("RGB").resize(new_size)


def gaussian_blur(image: Image.Image, kernel_size: int = 25) -> Image.Image:
    if kernel_size % 2 == 0:
        kernel_size += 1
    arr = np.array(image.convert("RGB"))
    blurred = cv2.GaussianBlur(arr, (kernel_size, kernel_size), 0)
    return Image.fromarray(blurred)


TRANSFORMS = {
    "jpeg_recompress": {"fn": jpeg_recompress, "params": {"quality": 30}},
    "resize": {"fn": resize, "params": {"scale": 0.5}},
    "gaussian_blur": {"fn": gaussian_blur, "params": {"kernel_size": 25}},
}


def generate_variants(source_path: Path, source_image_id: str, output_dir: Path) -> list[dict]:
    output_dir.mkdir(parents=True, exist_ok=True)
    original = Image.open(source_path)

    metadata_records = []
    for transform_name, spec in TRANSFORMS.items():
        variant = spec["fn"](original, **spec["params"])
        out_name = f"{source_path.stem}_{transform_name}.jpg"
        out_path = output_dir / out_name
        variant.convert("RGB").save(out_path)

        metadata_records.append(
            {
                "source_image_id": source_image_id,
                "transformation": transform_name,
                "parameters": spec["params"],
                "parent_image": str(source_path),
                "output_image": str(out_path),
            }
        )

    return metadata_records


def main():
    parser = argparse.ArgumentParser(
        description="Genera variantes de estres reproducibles (JPEG/resize/blur) a partir de una imagen real."
    )
    parser.add_argument("--source", required=True, help="Path a la imagen real de origen")
    parser.add_argument(
        "--source-image-id",
        required=True,
        help="source_image_id compartido por todas las variantes (nunca cambia de split)",
    )
    parser.add_argument("--output-dir", required=True, help="Carpeta donde escribir las variantes + metadata.jsonl")
    args = parser.parse_args()

    source_path = Path(args.source)
    if not source_path.exists():
        raise FileNotFoundError(f"No existe la imagen fuente: {source_path}")

    output_dir = Path(args.output_dir)
    records = generate_variants(source_path, args.source_image_id, output_dir)

    metadata_path = output_dir / "metadata.jsonl"
    with metadata_path.open("a", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False))
            f.write("\n")
            print(f"[create_demo_variants] {record['transformation']} -> {record['output_image']}")

    print(f"[create_demo_variants] metadata anexada en {metadata_path}")


if __name__ == "__main__":
    main()
