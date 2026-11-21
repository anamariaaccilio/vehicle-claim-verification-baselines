# UAFEG — Kaggle GPU kernel: visual specialist inference (POST HOC: fine-tuned yolo11m-seg, output of
# kernel uafeg-yolo-train-11m) over the 5 240 unique benchmark-v3 images. Same per-detection fields
# as scripts/run_specialists.py::run_visual (Repo A). Images SHA-256 verified.
import subprocess, sys, json, hashlib, os, glob, tarfile, time, platform, math, base64
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "ultralytics==8.4.155"], check=True)
from pathlib import Path
import numpy as np, cv2, torch
from PIL import Image
W = Path("/kaggle/working"); T = Path("/kaggle/tmp"); T.mkdir(exist_ok=True)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def find(pattern):
    hits = sorted(glob.glob(f"/kaggle/input/**/{pattern}", recursive=True))
    if not hits: raise SystemExit(f"not found: {pattern}")
    return Path(hits[0])
index = json.loads(find("images_index.json").read_text())
best = find("best.pt"); record = json.loads(find("yolo_record.json").read_text())
assert sha(best) == record["best_sha256"], "best.pt hash differs from training record"
for tar in glob.glob("/kaggle/input/**/variants_*.tar", recursive=True):
    with tarfile.open(tar) as t: t.extractall(T / "variants")
VAR = {}
for base in ["/kaggle/input", str(T / "variants")]:
    for dp, _, fs in os.walk(base):
        for f in fs:
            stem = f.split(".")[0]
            if len(stem) == 64 and stem in index: VAR[stem] = Path(dp) / f
HITL_ROOT = find("Car parts dataset/File1/img").parents[2]
def path_of(s, v): return HITL_ROOT / v["hitl_rel"] if v["hitl_rel"] else VAR.get(s, Path("/nonexistent"))
def quality_factors(rgb):
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY); h, w = gray.shape
    resolution = min(1.0, math.sqrt(w * h) / math.sqrt(640 * 480))
    lap = float(cv2.Laplacian(gray, cv2.CV_64F).var()); sharpness = min(1.0, lap / 100.0)
    mean = float(gray.mean()) / 255.0; clipped = float(((gray <= 5) | (gray >= 250)).mean())
    exposure = max(0.0, 1.0 - 2.0 * abs(mean - 0.5)) * (1.0 - clipped)
    return {"resolution": resolution, "sharpness": sharpness, "exposure": exposure,
            "laplacian_variance": lap, "q": resolution * sharpness * exposure}
def encode_mask(m): return base64.b64encode(np.packbits(m.astype(np.uint8), axis=None).tobytes()).decode()
from ultralytics import YOLO
import ultralytics
model = YOLO(str(best)); names = model.names
CONF, IMGSZ, MAXDET = 0.25, 640, 10
rows, bad, t0 = [], 0, time.time()
for i, (s, v) in enumerate(sorted(index.items())):
    p = path_of(s, v)
    if not p.exists() or sha(p) != s: bad += 1; continue
    with Image.open(p) as im: rgb = np.asarray(im.convert("RGB"))
    bgr = np.ascontiguousarray(rgb[:, :, ::-1])
    r = model.predict(bgr, conf=CONF, imgsz=IMGSZ, verbose=False, max_det=MAXDET, device=0)[0]
    h, w = rgb.shape[:2]; dets = []
    if r.boxes is not None:
        masks = r.masks.data.cpu().numpy() if r.masks is not None else None
        for k in range(len(r.boxes)):
            x1, y1, x2, y2 = [float(t) for t in r.boxes.xyxy[k].tolist()]
            conf = float(r.boxes.conf[k])
            xi1, yi1, xi2, yi2 = int(max(0, x1)), int(max(0, y1)), int(min(w, x2)), int(min(h, y2))
            region = rgb[yi1:max(yi1 + 1, yi2), xi1:max(xi1 + 1, xi2)]
            rq = quality_factors(region) if region.size and min(region.shape[:2]) >= 3 else None
            if rq is not None:
                rq["resolution"] = min(1.0, math.sqrt(region.shape[0] * region.shape[1]) / 64.0)
                rq["q"] = rq["resolution"] * rq["sharpness"] * rq["exposure"]
            ms = None
            if masks is not None:
                m = cv2.resize(masks[k].astype(np.uint8), (64, 48), interpolation=cv2.INTER_NEAREST); ms = encode_mask(m > 0)
            dets.append({"damage_class": names[int(r.boxes.cls[k])], "confidence": conf,
                         "bbox_norm": [x1 / w, y1 / h, x2 / w, y2 / h],
                         "area_fraction": max(0.0, (x2 - x1) * (y2 - y1)) / (w * h),
                         "region_quality": rq, "mask_64x48": ms})
    rows.append({"image_sha256": s, "width": w, "height": h, "detections": dets})
    if i % 500 == 0: print(i, len(index), round(time.time() - t0), flush=True)
out = W / "visual.jsonl"
out.write_text("".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in rows))
prov = {"specialist": "visual", "model": "yolo11m-seg fine-tuned on HITL v3 train (val for early stopping), Kaggle GPU, POST HOC (Parte 1.2)",
        "checkpoint_sha256": sha(best), "train_record": record, "conf_threshold": CONF, "imgsz": IMGSZ, "max_det": MAXDET,
        "n_rows": len(rows), "n_images_index": len(index), "sha_mismatch_skipped": bad, "output_sha256": sha(out), "seed": 0,
        "wall_seconds": round(time.time() - t0, 1),
        "versions": {"python": platform.python_version(), "torch": torch.__version__, "numpy": np.__version__,
                     "ultralytics": ultralytics.__version__}}
(W / "visual.provenance.json").write_text(json.dumps(prov, indent=2, sort_keys=True))
print(json.dumps({k: prov[k] for k in ("n_rows", "sha_mismatch_skipped", "output_sha256")})); print("DONE")
