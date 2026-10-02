"""Read verified HITL v2 ann/img exports, without merging image geometries.

Accept only damage taxonomy and simple polygon exteriors supported by the
existing contract. Unsupported geometry/holes fail explicitly, never silently
turn into negative damage labels. Source IDs preserve original filenames;
this does not prove independence of photographs of the same car/incident.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image

from src.schemas.claim import SourceImage
from src.schemas.evidence import HITL_TO_CANONICAL, BoundingBox, DamageAnnotation, Polygon


def parse_hitl_supervisely(dataset_dir: str | Path, *, relative_to: str | Path | None = None) -> list[SourceImage]:
    root = Path(dataset_dir).resolve()
    meta = json.loads((root / 'meta.json').read_text(encoding='utf-8'))
    classes = {item['title'] for item in meta['classes']}
    if classes != set(HITL_TO_CANONICAL):
        raise ValueError('Expected HITL damage taxonomy; do not select dataset by folder name alone')
    annotations = sorted(root.glob('*/ann/*.json'))
    if not annotations:
        raise ValueError('No annotation files found')
    records, seen = [], set()
    for path in annotations:
        image_name = path.name.removesuffix('.json')
        image_path = path.parent.parent / 'img' / image_name
        source_id = 'hitl:' + Path(image_name).stem
        if source_id in seen:
            raise ValueError(f'Ambiguous source ID: {source_id}; refusing to merge annotations')
        seen.add(source_id)
        doc = json.loads(path.read_text(encoding='utf-8'))
        with Image.open(image_path) as image:
            image.verify()
        with Image.open(image_path) as image:
            width, height = image.size
        if doc['size'] != {'width': width, 'height': height}:
            raise ValueError(f'Annotation/image dimensions differ: {image_name}')
        objects = []
        for obj in doc['objects']:
            label = obj['classTitle']
            if label not in HITL_TO_CANONICAL:
                raise ValueError(f'Unknown damage class: {label}')
            if obj['geometryType'] != 'polygon' or obj['points'].get('interior'):
                raise ValueError('Only simple polygon exteriors are supported; geometry was not discarded')
            points = obj['points']['exterior']
            if len(points) < 3 or any(len(point) != 2 for point in points):
                raise ValueError('Invalid polygon')
            if any(not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in point) for point in points):
                raise ValueError('Non-finite/non-numeric polygon coordinates')
            if any(not (0 <= x <= width and 0 <= y <= height) for x, y in points):
                raise ValueError(f'Polygon outside image: {image_name}')
            area2 = sum(points[i][0] * points[(i+1) % len(points)][1]
                        - points[(i+1) % len(points)][0] * points[i][1]
                        for i in range(len(points)))
            if area2 == 0:
                raise ValueError('Degenerate polygon')
            xs, ys = zip(*points)
            objects.append(DamageAnnotation(
                damage_class=HITL_TO_CANONICAL[label],
                polygon=Polygon(points=points),
                bbox=BoundingBox(x_min=min(xs), y_min=min(ys), x_max=max(xs), y_max=max(ys)),
            ))
        stored_path = image_path if relative_to is None else image_path.relative_to(Path(relative_to).resolve())
        records.append(SourceImage(source_image_id=source_id, path=stored_path.as_posix(), annotations=objects))
    return records
