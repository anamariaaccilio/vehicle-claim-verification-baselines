"""Deterministic lightweight duplicate grouping; no learned representations."""
from __future__ import annotations

import hashlib
from itertools import combinations
from pathlib import Path
from PIL import Image


def image_fingerprints(path: str | Path) -> dict:
    path = Path(path)
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        rgb = image.convert('RGB')
        width, height = rgb.size
        horizontal = list(rgb.convert('L').resize((9, 8), Image.Resampling.LANCZOS).tobytes())
        vertical = list(rgb.convert('L').resize((8, 9), Image.Resampling.LANCZOS).tobytes())
        bits = [horizontal[y*9+x] > horizontal[y*9+x+1] for y in range(8) for x in range(8)]
        bits += [vertical[y*8+x] > vertical[(y+1)*8+x] for y in range(8) for x in range(8)]
        digest = 0
        for bit in bits:
            digest = (digest << 1) | int(bit)
        pixel_sha = hashlib.sha256(str(rgb.size).encode() + b'\0' + rgb.tobytes()).hexdigest()
    return {'width': width, 'height': height,
            'file_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'pixel_sha256': pixel_sha, 'dhash128': f'{digest:032x}'}


def group_sources(sources: list[dict], threshold: int = 6) -> dict:
    if not isinstance(threshold, int) or not 0 <= threshold <= 128:
        raise ValueError('dHash threshold must be an integer in [0,128]')
    ids = sorted(source['source_image_id'] for source in sources)
    if len(ids) != len(set(ids)) or not ids:
        raise ValueError('Sources must have unique IDs and must not be empty')
    parent = {source_id: source_id for source_id in ids}

    def find(source_id):
        while parent[source_id] != source_id:
            parent[source_id] = parent[parent[source_id]]
            source_id = parent[source_id]
        return source_id

    pairs = []
    for a, b in combinations(sorted(sources, key=lambda row: row['source_image_id']), 2):
        distance = (int(a['dhash128'], 16) ^ int(b['dhash128'], 16)).bit_count()
        kinds = []
        if a['file_sha256'] == b['file_sha256']:
            kinds.append('file_exact')
        if a['pixel_sha256'] == b['pixel_sha256']:
            kinds.append('pixel_exact')
        if distance <= threshold:
            kinds.append('near_duplicate_candidate')
        if kinds:
            first, second = a['source_image_id'], b['source_image_id']
            root_a, root_b = find(first), find(second)
            parent[max(root_a, root_b)] = min(root_a, root_b)
            pairs.append({'source_a': first, 'source_b': second, 'hamming_distance': distance,
                          'reasons': kinds, 'decision': 'GROUP_TOGETHER_NO_DELETION'})
    groups = {}
    for source_id in ids:
        groups.setdefault(find(source_id), []).append(source_id)
    return {'method': '128-bit dHash: 64 horizontal + 64 vertical grayscale gradients; Pillow LANCZOS',
            'threshold': threshold, 'pairs': pairs, 'groups': groups,
            'source_to_group': {source_id: group for group, members in groups.items() for source_id in members}}
