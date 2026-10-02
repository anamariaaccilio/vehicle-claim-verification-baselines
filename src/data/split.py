"""Split determinista train/validation/test por source_image_id.

Regla dura: ningun derivado de una imagen fuente (variante aumentada,
recorte, version JPEG-comprimida usada en el benchmark de estres, etc.)
puede caer en un split distinto al de su source_image_id. Por eso el split
se decide una unica vez por source_image_id (nunca por registro/derivado),
usando un hash estable seed+id -> no depende del orden de iteracion ni de
random.shuffle, y es 100% reproducible entre corridas.
"""
from __future__ import annotations

import hashlib
from collections import defaultdict

from src.schemas.claim import SourceImage, Split

DEFAULT_RATIOS: dict[Split, float] = {
    Split.TRAIN: 0.70,
    Split.VALIDATION: 0.15,
    Split.TEST: 0.15,
}


def _validate_ratios(ratios: dict[Split, float]) -> None:
    total = sum(ratios.values())
    if abs(total - 1.0) > 1e-6:
        raise ValueError(f"Las proporciones de split deben sumar 1.0, suman {total}")


def _bucket(source_image_id: str, seed: int) -> float:
    """Hash estable en [0, 1) para un source_image_id dado un seed."""
    digest = hashlib.sha256(f"{seed}:{source_image_id}".encode("utf-8")).hexdigest()
    # usar los primeros 8 hex chars (32 bits) como entero normalizado
    return int(digest[:8], 16) / 0xFFFFFFFF


def assign_splits(
    source_image_ids: list[str],
    seed: int = 42,
    ratios: dict[Split, float] | None = None,
) -> dict[str, Split]:
    """Asigna un split a cada source_image_id, de forma determinista."""
    ratios = ratios or DEFAULT_RATIOS
    _validate_ratios(ratios)

    train_cut = ratios[Split.TRAIN]
    val_cut = train_cut + ratios[Split.VALIDATION]

    assignment: dict[str, Split] = {}
    for source_image_id in sorted(set(source_image_ids)):
        bucket = _bucket(source_image_id, seed)
        if bucket < train_cut:
            assignment[source_image_id] = Split.TRAIN
        elif bucket < val_cut:
            assignment[source_image_id] = Split.VALIDATION
        else:
            assignment[source_image_id] = Split.TEST
    return assignment


def apply_split(
    records: list[SourceImage],
    seed: int = 42,
    ratios: dict[Split, float] | None = None,
) -> list[SourceImage]:
    """Devuelve una copia de records con el campo split asignado."""
    assignment = assign_splits(
        [r.source_image_id for r in records], seed=seed, ratios=ratios
    )
    return [
        r.model_copy(update={"split": assignment[r.source_image_id]})
        for r in records
    ]


class LeakageError(ValueError):
    pass


def check_no_leakage(records: list[SourceImage]) -> None:
    """Verifica que ningun source_image_id aparezca en mas de un split."""
    splits_by_id: dict[str, set[Split]] = defaultdict(set)
    for r in records:
        if not r.source_image_id or not r.source_image_id.strip() or r.split is None:
            raise LeakageError("source_image_id and split are required for leakage audit")
        splits_by_id[r.source_image_id].add(r.split)

    offenders = {sid: splits for sid, splits in splits_by_id.items() if len(splits) > 1}
    if offenders:
        raise LeakageError(
            f"source_image_id con leakage entre splits: {offenders}"
        )
