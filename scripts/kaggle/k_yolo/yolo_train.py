# UAFEG — Kaggle GPU kernel: fine-tune YOLOv8n-seg on HITL v3 (train; val for early stopping),
# evaluate mask/box mAP on val and test (test never used for training/selection), and
# external box-mAP on CarDD test (CC BY-NC 4.0 mirror, boxes only).
import subprocess, sys, json, hashlib, os, glob, tarfile, shutil, time, platform
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "ultralytics==8.4.155"], check=True)
from pathlib import Path
W = Path("/kaggle/working"); W.mkdir(exist_ok=True)
LOG = {"started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def find(pattern):
    hits = sorted(glob.glob(f"/kaggle/input/**/{pattern}", recursive=True))
    if not hits: raise SystemExit(f"not found: {pattern}")
    return Path(hits[0])
print(subprocess.run("find /kaggle/input -maxdepth 4 | head -60", shell=True, capture_output=True, text=True).stdout)
index = json.loads(find("images_index.json").read_text())
hitl_probe = find("Car parts dataset/File1/img")
HITL_ROOT = hitl_probe.parents[2]
print("HITL root", HITL_ROOT)
Y = W / "yolo"; Y.mkdir(exist_ok=True)
tars = glob.glob("/kaggle/input/**/yolo_labels.tar.gz", recursive=True)
if tars:
    with tarfile.open(tars[0]) as t: t.extractall(Y)
else:  # Kaggle auto-extracted the archive
    src = find("image_map.json").parent
    shutil.copytree(src / "labels", Y / "labels"); shutil.copy(src / "image_map.json", Y / "image_map.json")
imap = json.loads((Y / "image_map.json").read_text())
by_rel = {v["hitl_rel"]: k for k, v in index.items() if v["hitl_rel"]}
bad = 0
for key, rel in imap.items():
    split, name = key.split("/", 1)
    src = HITL_ROOT / rel
    if sha(src) != by_rel[rel]: bad += 1
    d = Y / "images" / split; d.mkdir(parents=True, exist_ok=True)
    os.symlink(src, d / name)
LOG["hitl_images"] = len(imap); LOG["hitl_sha_mismatch"] = bad
assert bad == 0, f"{bad} HITL images differ from frozen v3 hashes"
names = {0: "dent", 1: "crack", 2: "scratch", 3: "flaking", 4: "broken_part", 5: "paint_chip", 6: "missing_part", 7: "corrosion"}
import yaml
(Y / "data.yaml").write_text(yaml.safe_dump({"path": str(Y), "train": "images/train", "val": "images/validation",
                                             "test": "images/test", "names": names}))
from ultralytics import YOLO
import torch, ultralytics
LOG["versions"] = {"python": platform.python_version(), "torch": torch.__version__, "ultralytics": ultralytics.__version__,
                   "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}
CFG = dict(epochs=100, imgsz=640, batch=16, patience=20, seed=0, deterministic=True, workers=2,
           optimizer="auto", pretrained=True)
LOG["train_config"] = CFG
model = YOLO("yolov8n-seg.pt")
LOG["base_weights_sha256"] = sha("yolov8n-seg.pt")
model.train(data=str(Y / "data.yaml"), project=str(W / "runs"), name="hitl_v3_n_seg", exist_ok=True, device=0, **CFG)
best = W / "runs/hitl_v3_n_seg/weights/best.pt"
shutil.copy(best, W / "best.pt")
LOG["best_sha256"] = sha(W / "best.pt")
m = YOLO(str(W / "best.pt"))
res = {}
for split in ["val", "test"]:
    r = m.val(data=str(Y / "data.yaml"), split=split, imgsz=640, batch=16, device=0, plots=False,
              project=str(W / "runs"), name=f"eval_{split}", exist_ok=True)
    res[split] = {"mask_map50": float(r.seg.map50), "mask_map50_95": float(r.seg.map),
                  "box_map50": float(r.box.map50), "box_map50_95": float(r.box.map),
                  "per_class_mask_map50_95": {names[int(c)]: float(v) for c, v in zip(r.ap_class_index, r.seg.maps[r.ap_class_index])},
                  "n_images": len(list((Y / "images" / ("validation" if split == "val" else "test")).iterdir()))}
    print(split, res[split])
LOG["hitl_eval"] = res
json.dump(LOG, open(W / "yolo_record.json", "w"), indent=1)

# ---------------- external: CarDD test (boxes only) ----------------
ext = {"status": "NOT_RUN"}
try:
    import numpy as np
    from ultralytics.utils.metrics import ap_per_class, box_iou
    cands = [Path(p) for p in glob.glob("/kaggle/input/**/test/images", recursive=True) if "cardd" in p.lower()]
    img_dir = cands[0]; lab_dir = img_dir.parent / "labels"
    yamls = [Path(p) for p in glob.glob(str(img_dir.parents[1]) + "/**/*.yaml", recursive=True)]
    cardd_names = yaml.safe_load(yamls[0].read_text())["names"] if yamls else None
    print("CarDD names", cardd_names, "dir", img_dir)
    if isinstance(cardd_names, dict): cardd_names = [cardd_names[k] for k in sorted(cardd_names)]
    # pre-registered mapping (docs/decisiones_cierre.md) CarDD -> HITL ontology
    MAP = {"dent": 0, "scratch": 2, "crack": 1, "glass shatter": 4, "lamp broken": 4, "tire flat": None}
    cmap = {i: MAP.get(str(n).lower().replace("_", " ")) for i, n in enumerate(cardd_names)}
    imgs = sorted(p for p in img_dir.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
    h = hashlib.sha256()
    for p in imgs: h.update(sha(p).encode())
    iouv = torch.linspace(0.5, 0.95, 10)
    stats = {"mapped": [], "agnostic": []}
    for p in imgs:
        r = m.predict(str(p), conf=0.001, iou=0.7, imgsz=640, max_det=300, verbose=False, device=0)[0]
        H, Wd = r.orig_shape
        gt = []
        lp = lab_dir / (p.stem + ".txt")
        if lp.exists():
            for line in lp.read_text().split("\n"):
                v = line.split()
                if len(v) < 5: continue
                c, x, y, w, hh = int(v[0]), *map(float, v[1:5])
                gt.append([c, (x - w / 2) * Wd, (y - hh / 2) * H, (x + w / 2) * Wd, (y + hh / 2) * H])
        pb = r.boxes.xyxy.cpu(); pc = r.boxes.cls.cpu(); pconf = r.boxes.conf.cpu()
        for mode in ["mapped", "agnostic"]:
            g = [(cmap[c] if mode == "mapped" else 0, *b) for c, *b in gt if (cmap[c] is not None or mode == "agnostic")]
            gcls = torch.tensor([x[0] for x in g], dtype=torch.float32); gbox = torch.tensor([x[1:] for x in g], dtype=torch.float32).reshape(-1, 4)
            pcls = pc.clone() if mode == "mapped" else torch.zeros_like(pc)
            correct = torch.zeros(len(pb), 10, dtype=torch.bool)
            if len(g) and len(pb):
                iou = box_iou(gbox, pb)
                same = gcls[:, None] == pcls[None, :]
                iou = iou * same
                for ti, t in enumerate(iouv):
                    mt = torch.nonzero(iou >= t)
                    if mt.shape[0]:
                        mt = torch.cat([mt, iou[mt[:, 0], mt[:, 1]][:, None]], 1).numpy()
                        mt = mt[mt[:, 2].argsort()[::-1]]
                        mt = mt[np.unique(mt[:, 1], return_index=True)[1]]
                        mt = mt[np.unique(mt[:, 0], return_index=True)[1]]
                        correct[mt[:, 1].astype(int), ti] = True
            stats[mode].append((correct.numpy(), pconf.numpy(), pcls.numpy(), gcls.numpy()))
    ext = {"status": "MEASURED", "dataset": "gabrielfcarvalho/cardd-with-yolo-annotations-images-labels (test split)",
           "license": "CC BY-NC 4.0 (declared on Kaggle)", "n_images": len(imgs), "images_sha256_of_sha256s": h.hexdigest(),
           "cardd_names": cardd_names, "class_map_to_hitl": {str(cardd_names[k]): (names[v] if v is not None else None) for k, v in cmap.items()},
           "label_type": "bounding boxes only (mask mAP not computable)"}
    for mode in ["mapped", "agnostic"]:
        tp, conf, pcl, tcl = [np.concatenate(x, 0) for x in zip(*stats[mode])]
        out = ap_per_class(tp, conf, pcl, tcl)
        ap = out[5]  # (nc, 10)
        ext[f"box_map50_{mode}"] = float(ap[:, 0].mean()); ext[f"box_map50_95_{mode}"] = float(ap.mean())
        ext[f"n_gt_{mode}"] = int(len(tcl))
    print(ext)
except Exception as e:  # recorded, never filled in
    import traceback; traceback.print_exc()
    ext = {"status": f"NOT_RUN: {type(e).__name__}: {e}"}
LOG["external_cardd"] = ext
LOG["finished"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
json.dump(LOG, open(W / "yolo_record.json", "w"), indent=1)
shutil.rmtree(W / "yolo", ignore_errors=True)
print("DONE")
