"""Prepara datos para el especialista visual (YOLO-seg) sin entrenar ni
descargar pesos. Dos problemas reales que corrige respecto al estado previo:

1. El manifest interno (ver src/data/manifest.py) decia estar producido por
   src/data/hitl_adapter.py, que asume una exportacion COCO. La exportacion
   real de HITL v2 es estilo Supervisely (ver docs/DATASET_DISCOVERY.md); el
   lector correcto y ya usado por el benchmark de reclamos es
   src/data/hitl_supervisely.py. Este script usa ese lector, no el adapter COCO.

2. src/data/split.py::apply_split() asigna split hasheando directamente
   source_image_id. El benchmark de reclamos (claim_benchmark.frozen_splits)
   agrupa primero por near-duplicate (group_id) y recien ahi hashea; para v3
   hoy group_id==source_image_id para las 807 fuentes aceptadas (0 grupos con
   >1 miembro, verificado abajo), asi que ambos metodos coinciden hoy, pero
   coinciden por construccion de los datos actuales, no por diseno del
   codigo: si una futura revision agrupa fuentes casi-duplicadas, apply_split
   divergiria en silencio del split del benchmark de reclamos y el
   especialista visual podria entrenar con fuentes que el benchmark reserva
   para test. Por eso este script NUNCA llama apply_split/assign_splits:
   reusa literalmente splits.json['sources'] (la asignacion congelada que ya
   consume el benchmark), y verifica explicitamente la invariante de grupo.

Salida: SIEMPRE en data/processed/damage_specialist/ (nuevo, fuera de
data/manifests/benchmark_v3/). No modifica ningun artefacto congelado.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import yaml  # noqa: E402

from src.data.hitl_supervisely import parse_hitl_supervisely  # noqa: E402
from src.data.manifest import save_manifest  # noqa: E402
from src.damage.train import build_yolo_seg_dataset  # noqa: E402
from src.schemas.claim import Split  # noqa: E402

OUTPUT_DIR = ROOT / "data/processed/damage_specialist"
VERIFY_SUBSET_PER_SPLIT = 4  # pequeno a proposito: ver restriccion de espacio en disco abajo


def main() -> int:
    config = yaml.safe_load((ROOT / "configs/benchmark_v3.yaml").read_text())
    dataset_dir = ROOT / config["dataset_dir"]
    bundle = ROOT / "data/manifests/benchmark_v3"
    splits = json.loads((bundle / "splits.json").read_text())
    audit = json.loads((bundle / "dataset_audit.json").read_text())
    accepted_sources = {s["source_image_id"]: s for s in audit["sources"]}

    # Invariante de grupo: todo miembro del mismo group_id debe compartir split.
    # Siempre deberia cumplirse por construccion de splits.json; se verifica
    # explicitamente para no asumirlo en silencio si splits.json cambiara.
    by_group: dict[str, set[str]] = {}
    for source_id, row in splits["sources"].items():
        by_group.setdefault(row["group_id"], set()).add(row["split"])
    inconsistent_groups = {g: s for g, s in by_group.items() if len(s) > 1}
    if inconsistent_groups:
        raise ValueError(f"splits.json tiene grupos con mas de un split (leakage): {inconsistent_groups}")

    multi_member_groups = sum(1 for g, members in
                               __import__("collections").Counter(row["group_id"] for row in splits["sources"].values()).items()
                               if members > 1)

    missing_split = sorted(set(accepted_sources) - set(splits["sources"]))
    if missing_split:
        raise ValueError(f"{len(missing_split)} fuentes aceptadas no tienen split congelado asignado: {missing_split[:5]}...")

    records = []
    for source_id, source_row in sorted(accepted_sources.items()):
        annotation_path = ROOT / source_row["annotation_reference"]
        parsed = parse_hitl_supervisely(dataset_dir, relative_to=ROOT, annotation_paths=[annotation_path])
        record = parsed[0]
        assert record.source_image_id == source_id, f"source_image_id mismatch: {record.source_image_id} != {source_id}"
        official_split = Split(splits["sources"][source_id]["split"])
        records.append(record.model_copy(update={"split": official_split}))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = OUTPUT_DIR / "source_manifest.jsonl"
    save_manifest(records, manifest_path)

    counts = {split.value: sum(1 for r in records if r.split == split) for split in Split}
    total_annotations = sum(len(r.annotations) for r in records)
    with_polygon = sum(1 for r in records for a in r.annotations if a.polygon is not None)

    # Verificacion end-to-end real (polígono -> YOLO-seg) sobre un subconjunto
    # pequeno y deterministico, NO sobre las 807 fuentes: data/raw/hitl_full_v2
    # pesa ~534MB y build_yolo_seg_dataset copia bytes de imagen; el disco de
    # este equipo tiene ~1.7GB libres (98% usado). Copiar las 807 imagenes es
    # viable en espacio pero arriesgado en una maquina casi llena sin que el
    # usuario lo decida explicitamente. Documentado como pendiente, no como
    # fallo del script.
    by_split: dict[Split, list] = {split: [] for split in Split}
    for record in records:
        by_split[record.split].append(record)
    verify_subset = []
    for split in Split:
        verify_subset.extend(sorted(by_split[split], key=lambda r: r.source_image_id)[:VERIFY_SUBSET_PER_SPLIT])

    verify_dir = OUTPUT_DIR / "yolo_seg_verify"
    if verify_dir.exists():
        shutil.rmtree(verify_dir)
    data_yaml_path = build_yolo_seg_dataset(verify_subset, verify_dir)

    report = {
        "accepted_sources": len(accepted_sources),
        "sources_with_frozen_split": len(records),
        "groups_total": len(by_group),
        "groups_with_more_than_one_member": multi_member_groups,
        "claims_per_split_matches_damage_specialist_split": counts,
        "total_polygon_annotations": with_polygon,
        "total_annotations_including_bbox_only": total_annotations,
        "source_manifest": str(manifest_path.relative_to(ROOT)),
        "yolo_seg_verification_subset": {
            "n_sources": len(verify_subset),
            "data_yaml": str(data_yaml_path.relative_to(ROOT)),
        },
        "full_yolo_seg_materialization": (
            "PENDIENTE: requiere copiar ~534MB de imagenes "
            "(data/raw/hitl_full_v2 completo); este equipo tiene ~1.7GB libres (98% de disco usado). "
            "No se ejecuto automaticamente. Para generarlo cuando haya espacio: "
            "cambiar VERIFY_SUBSET_PER_SPLIT o llamar build_yolo_seg_dataset(records, "
            "'data/processed/damage_specialist/yolo_seg_full') con el manifest completo de arriba."
        ),
        "next_step_for_training": (
            "Entrenar YOLO-seg real es trabajo de computo largo y descarga el peso base "
            "yolov8n-seg.pt (pesos de Ultralytics, no repositorio local): no se ejecuta aqui. "
            "Una vez materializado el YOLO-seg completo: "
            "python -m src.damage.train --manifest data/processed/damage_specialist/source_manifest.jsonl "
            "--dataset-dir data/processed/damage_specialist/yolo_seg_full --smoke-test (consultar antes de "
            "una corrida completa)."
        ),
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
