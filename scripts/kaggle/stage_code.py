"""Stage small code/label bundle for Kaggle kernels (no images)."""
import json, sys, tarfile, hashlib, os, shutil
from pathlib import Path
ROOT = Path("/home/ana/Documentos/tesis 2/vehicle-claim-verification-baselines")
sys.path.insert(0, str(ROOT))
OUT = Path(sys.argv[1])
from src.data.manifest import load_manifest
from src.damage.train import build_yolo_seg_dataset
import yaml
recs = load_manifest(ROOT / "data/processed/damage_specialist/source_manifest.jsonl")
print(len(recs), {s: sum(1 for r in recs if r.split and r.split.value == s) for s in ["train","validation","test"]})
tmp = OUT.parent / "yolo_tmp"
shutil.rmtree(tmp, ignore_errors=True)
os.chdir(ROOT)
build_yolo_seg_dataset(recs, tmp, link_images=True)
# labels + mapping label-stem -> raw rel path
mapping = {}
for split in ["train", "validation", "test"]:
    for img in (tmp / "images" / split).iterdir():
        target = os.path.realpath(img)
        mapping[f"{split}/{img.name}"] = os.path.relpath(target, ROOT / "data/raw/hitl_full_v2")
(tmp / "image_map.json").write_text(json.dumps(mapping, indent=0))
with tarfile.open(OUT / "yolo_labels.tar.gz", "w:gz") as t:
    t.add(tmp / "labels", "labels"); t.add(tmp / "image_map.json", "image_map.json"); t.add(tmp / "data.yaml", "data.yaml")
# image index
rows = [json.loads(l) for l in open(ROOT / "data/manifests/benchmark_v3/manifest.jsonl")]
idx = {}
for c in rows:
    if c.get("image_path"):
        sha = c["transformation"]["image_sha256"]
        p = c["image_path"]
        idx.setdefault(sha, {"ext": Path(p).suffix.lower(),
                             "hitl_rel": os.path.relpath(p, "data/raw/hitl_full_v2") if p.startswith("data/raw/hitl_full_v2") else None,
                             "group": "hitl" if p.startswith("data/raw") else ("v2" if "benchmark_v2" in p else "v13")})
(OUT / "images_index.json").write_text(json.dumps(idx, sort_keys=True))
with tarfile.open(OUT / "trufor_lib.tar.gz", "w:gz") as t:
    base = ROOT / "artifacts/forensic/trufor/TruFor-main/TruFor_train_test"
    t.add(base / "lib", "TruFor_train_test/lib")
(OUT / "trufor_SHA256SUMS").write_text((ROOT / "artifacts/forensic/trufor/weights/SHA256SUMS").read_text())
print("data.yaml:", (tmp / "data.yaml").read_text())
print({k: len(list((tmp / 'labels' / k).iterdir())) for k in ["train","validation","test"]})
