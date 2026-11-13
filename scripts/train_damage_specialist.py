"""Fine-tune the visual damage specialist (YOLO-seg) on HITL train/validation.

Reduced CPU scale (decided 2026-11-13, FASE 1): yolov8n-seg, imgsz 512,
<=20 epochs, patience 5, seed 0. The test split is NEVER materialized: only
train and validation images are linked into the YOLO dataset, so the
specialist cannot see a test source. Writes a run record with config, seed,
commit, input/output hashes and library versions next to best.pt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.damage.train import build_yolo_seg_dataset  # noqa: E402
from src.data.manifest import load_manifest  # noqa: E402

MANIFEST = ROOT / "data/processed/damage_specialist/source_manifest.jsonl"
DATASET = ROOT / "data/processed/damage_specialist/yolo_seg_trainval"
OUT = ROOT / "artifacts/damage"


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--imgsz", type=int, default=512)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--patience", type=int, default=5)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--base-model", default="yolov8n-seg.pt")
    ap.add_argument("--name", default="hitl_v3_n_seg")
    args = ap.parse_args()

    records = [r.model_copy(update={"path": str((ROOT / r.path).resolve())}) for r in load_manifest(MANIFEST)]
    if DATASET.exists():
        shutil.rmtree(DATASET)
    data_yaml = build_yolo_seg_dataset(records, DATASET, link_images=True, splits=("train", "validation"))
    assert not (DATASET / "images/test").exists(), "test split must never be materialized"

    from ultralytics import YOLO
    import torch
    import ultralytics

    started = time.time()
    base = OUT / args.base_model  # base weights cached under artifacts/, never in git
    model = YOLO(str(base) if base.exists() else args.base_model)
    model.train(data=str(data_yaml), epochs=args.epochs, imgsz=args.imgsz, batch=args.batch,
                patience=args.patience, seed=args.seed, deterministic=True, device="cpu",
                workers=2, project=str(OUT / "runs"), name=args.name, exist_ok=True,
                plots=False, verbose=False)
    run_dir = OUT / "runs" / args.name
    best = run_dir / "weights/best.pt"
    (OUT / "weights").mkdir(parents=True, exist_ok=True)
    shutil.copy2(best, OUT / "weights/best.pt")
    commit = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    record = {
        "component": "damage_specialist", "status": "TRAINED_REDUCED_SCALE",
        "config": vars(args), "seed": args.seed, "git_commit": commit,
        "splits_used": ["train", "validation"], "test_split_used": False,
        "inputs_sha256": {"source_manifest": sha256(MANIFEST), "data_yaml": sha256(data_yaml),
                          "splits_json": sha256(ROOT / "data/manifests/benchmark_v3/splits.json")},
        "outputs_sha256": {"best.pt": sha256(OUT / "weights/best.pt")},
        "versions": {"python": platform.python_version(), "torch": torch.__version__,
                     "ultralytics": ultralytics.__version__},
        "wall_seconds": round(time.time() - started, 1),
        "validation_metrics_csv": str((run_dir / "results.csv").relative_to(ROOT)),
    }
    (OUT / "weights/run_record.json").write_text(json.dumps(record, indent=2))
    print(json.dumps(record, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
