"""Run the evidence specialists over benchmark v3 and cache their raw outputs.

    python scripts/run_specialists.py narrative   # NLI per assertion, keyed by sha256(text)
    python scripts/run_specialists.py quality     # q factors + s (origin/EXIF), keyed by image sha256
    python scripts/run_specialists.py visual      # YOLO-seg detections (+ region q), keyed by image sha256
    python scripts/run_specialists.py forensic    # TruFor score + maps, keyed by image sha256

Outputs: artifacts/specialists/<name>.jsonl (+ maps under artifacts/specialists/forensic_maps/)
and artifacts/specialists/<name>.provenance.json (model, checkpoint hash, seed,
library versions, output sha256). Every specialist sees ONLY the narrative text or
the image bytes: labels, condition, claim_id and paths never reach it (paths are
used to open the file and are not stored in the output).

Images are always converted to RGB before any measurement: in v3 the RGBA/RGB mode
and the PNG/JPEG format are generation fingerprints (originals RGBA PNG or JPEG,
edited variants RGB PNG), so neither mode, format nor file size is ever emitted.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

MANIFEST = ROOT / "data/manifests/benchmark_v3/manifest.jsonl"
OUT = ROOT / "artifacts/specialists"
SEED = 0


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def claims() -> list[dict]:
    return [json.loads(line) for line in MANIFEST.read_text().splitlines()]


def unique_images() -> dict[str, str]:
    """image sha256 -> path (path only used to open the file)."""
    images = {}
    for c in claims():
        if c.get("image_path"):
            images.setdefault(c["transformation"]["image_sha256"], c["image_path"])
    return dict(sorted(images.items()))


def write_outputs(name: str, rows: list[dict], provenance: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}.jsonl"
    path.write_text("".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in rows))
    import torch
    provenance.update({
        "specialist": name, "seed": SEED, "n_rows": len(rows), "output_sha256": sha256_file(path),
        "manifest_sha256": sha256_file(MANIFEST),
        "git_commit": subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip(),
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "torch": torch.__version__},
    })
    (OUT / f"{name}.provenance.json").write_text(json.dumps(provenance, indent=2, sort_keys=True))
    print(json.dumps({k: provenance[k] for k in ("specialist", "n_rows", "output_sha256")}))


def load_rgb(path: str) -> np.ndarray:
    from PIL import Image
    with Image.open(ROOT / path) as im:
        return np.asarray(im.convert("RGB"))


# ----------------------------------------------------------------- quality (q, s)
def quality_factors(rgb: np.ndarray) -> dict:
    """q = resolución efectiva x nitidez x exposición, cada factor en [0, 1]."""
    import cv2
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    h, w = gray.shape
    resolution = min(1.0, math.sqrt(w * h) / math.sqrt(640 * 480))
    lap = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    sharpness = min(1.0, lap / 100.0)
    mean = float(gray.mean()) / 255.0
    clipped = float(((gray <= 5) | (gray >= 250)).mean())
    exposure = max(0.0, 1.0 - 2.0 * abs(mean - 0.5)) * (1.0 - clipped)
    return {"resolution": resolution, "sharpness": sharpness, "exposure": exposure,
            "laplacian_variance": lap, "q": resolution * sharpness * exposure}


def run_quality(_args) -> None:
    from PIL import Image
    rows = []
    for image_sha, path in unique_images().items():
        rgb = load_rgb(path)
        with Image.open(ROOT / path) as im:
            exif = im.getexif()
        row = {"image_sha256": image_sha, "width": int(rgb.shape[1]), "height": int(rgb.shape[0]),
               **quality_factors(rgb)}
        # s (origen/EXIF): v3 has no EXIF in any image, so s is not observable.
        row["s"] = None if len(exif) == 0 else 1.0
        row["s_status"] = "NOT_OBSERVABLE_NO_EXIF" if len(exif) == 0 else "EXIF_PRESENT"
        rows.append(row)
    write_outputs("quality", rows, {"method": "resolution x Laplacian sharpness x exposure on RGB; s from EXIF",
                                    "normalization": "resolution/sqrt(640*480), laplacian/100, |mean-0.5|"})


# ----------------------------------------------------------------- narrative
def run_narrative(args) -> None:
    from src.narrative.assertions import SentenceNLI
    nli = SentenceNLI(threads=args.threads)
    texts = sorted({c["narrative_text"] for c in claims() if c.get("narrative_text")})
    rows = []
    started = time.time()
    for i, text in enumerate(texts):
        rows.append({"text_sha256": sha256_bytes(text.encode()),
                     "assertions": [a.as_dict() for a in nli.extract(text)]})
        if i % 100 == 0:
            print(f"{i}/{len(texts)} {time.time() - started:.0f}s", flush=True)
    write_outputs("narrative", rows, {"model": nli.model_name, "model_revision": nli.revision,
                                      "method": "sentence-level NLI vs 8 damage hypotheses (configs/labels.yaml)",
                                      "wall_seconds": round(time.time() - started, 1)})


# ----------------------------------------------------------------- visual
def encode_mask(mask: np.ndarray) -> str:
    return base64.b64encode(np.packbits(mask.astype(np.uint8), axis=None).tobytes()).decode()


def run_visual(args) -> None:
    import torch
    from ultralytics import YOLO
    import cv2
    torch.set_num_threads(args.threads)
    weights = ROOT / "artifacts/damage/weights/best.pt"
    model = YOLO(str(weights))
    names = model.names
    rows = []
    started = time.time()
    images = unique_images()
    for i, (image_sha, path) in enumerate(images.items()):
        rgb = load_rgb(path)
        bgr = np.ascontiguousarray(rgb[:, :, ::-1])
        result = model.predict(bgr, conf=args.conf, imgsz=args.imgsz, verbose=False, max_det=args.max_det)[0]
        h, w = rgb.shape[:2]
        dets = []
        if result.boxes is not None:
            masks = result.masks.data.numpy() if result.masks is not None else None
            for k in range(len(result.boxes)):
                x1, y1, x2, y2 = [float(v) for v in result.boxes.xyxy[k].tolist()]
                conf = float(result.boxes.conf[k])
                xi1, yi1, xi2, yi2 = int(max(0, x1)), int(max(0, y1)), int(min(w, x2)), int(min(h, y2))
                region = rgb[yi1:max(yi1 + 1, yi2), xi1:max(xi1 + 1, xi2)]
                rq = quality_factors(region) if region.size and min(region.shape[:2]) >= 3 else None
                if rq is not None:  # region resolution relative to a 64x64 patch
                    rq["resolution"] = min(1.0, math.sqrt(region.shape[0] * region.shape[1]) / 64.0)
                    rq["q"] = rq["resolution"] * rq["sharpness"] * rq["exposure"]
                mask_small = None
                if masks is not None:
                    m = cv2.resize(masks[k].astype(np.uint8), (64, 48), interpolation=cv2.INTER_NEAREST)
                    mask_small = encode_mask(m > 0)
                dets.append({"damage_class": names[int(result.boxes.cls[k])], "confidence": conf,
                             "bbox_norm": [x1 / w, y1 / h, x2 / w, y2 / h],
                             "area_fraction": max(0.0, (x2 - x1) * (y2 - y1)) / (w * h),
                             "region_quality": rq, "mask_64x48": mask_small})
        rows.append({"image_sha256": image_sha, "width": w, "height": h, "detections": dets})
        if i % 200 == 0:
            print(f"{i}/{len(images)} {time.time() - started:.0f}s", flush=True)
    record = json.loads((ROOT / "artifacts/damage/weights/run_record.json").read_text())
    write_outputs("visual", rows, {"model": "yolov8n-seg fine-tuned on HITL train (val for early stopping)",
                                   "checkpoint_sha256": sha256_file(weights), "train_record": record,
                                   "conf_threshold": args.conf, "imgsz": args.imgsz, "max_det": args.max_det,
                                   "wall_seconds": round(time.time() - started, 1)})


# ----------------------------------------------------------------- forensic
def run_forensic(args) -> None:
    from src.forensic.trufor_adapter import METHOD, WEIGHTS, TruForSpecialist
    specialist = TruForSpecialist(max_side=args.max_side, threads=args.threads)
    if not specialist.is_available:
        raise SystemExit("TruFor not available: forensic stays null (see src/forensic/trufor_adapter.py)")
    maps_dir = OUT / "forensic_maps"
    maps_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    started = time.time()
    images = unique_images()
    for i, (image_sha, path) in enumerate(images.items()):
        out = specialist.predict(ROOT / path)
        np.savez_compressed(maps_dir / f"{image_sha}.npz", localization=out["localization"], confidence=out["confidence"])
        loc, conf = out["localization"].astype(np.float32), out["confidence"].astype(np.float32)
        rows.append({"image_sha256": image_sha, "score": out["score"],
                     "loc_mean": float(loc.mean()), "loc_area_05": float((loc > 0.5).mean()),
                     "conf_mean": float(conf.mean()), "conf_in_loc": float(conf[loc > 0.5].mean()) if (loc > 0.5).any() else None,
                     "inference_size": out["inference_size"]})
        if i % 100 == 0:
            print(f"{i}/{len(images)} {time.time() - started:.0f}s", flush=True)
    write_outputs("forensic", rows, {"method": METHOD, "checkpoint_sha256": sha256_file(WEIGHTS),
                                     "max_side": args.max_side, "license": "GRIP-UNINA non-profit research licence",
                                     "wall_seconds": round(time.time() - started, 1)})


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("specialist", choices=["narrative", "quality", "visual", "forensic"])
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--imgsz", type=int, default=512)
    ap.add_argument("--max-det", type=int, default=10)
    ap.add_argument("--max-side", type=int, default=512)
    args = ap.parse_args()
    {"narrative": run_narrative, "quality": run_quality, "visual": run_visual, "forensic": run_forensic}[args.specialist](args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
