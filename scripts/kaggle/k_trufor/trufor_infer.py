# UAFEG — Kaggle GPU kernel: TruFor (Guillaro et al., CVPR 2023) inference-only over the 5 240
# unique benchmark-v3 images, native resolution. Weights: official GRIP-UNINA zip (non-profit
# research licence), SHA-256 verified; checkpoint loaded with weights_only=True + allow-listed
# numpy scalars. Every input image is SHA-256 verified against the frozen v3 index.
import subprocess, sys, json, hashlib, os, glob, tarfile, time, platform, zipfile, io
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "yacs"], check=True)
from pathlib import Path
import numpy as np, torch
from torch.nn import functional as F
from PIL import Image
W = Path("/kaggle/working"); T = Path("/kaggle/tmp"); T.mkdir(exist_ok=True)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def find(pattern):
    hits = sorted(glob.glob(f"/kaggle/input/**/{pattern}", recursive=True))
    if not hits: raise SystemExit(f"not found: {pattern}")
    return Path(hits[0])
index = json.loads(find("images_index.json").read_text())
sums = dict(l.split()[::-1] for l in find("trufor_SHA256SUMS").read_text().splitlines() if l.strip())
print(subprocess.run("find /kaggle/input -maxdepth 4 | head -60", shell=True, capture_output=True, text=True).stdout)
_t = glob.glob("/kaggle/input/**/trufor_lib.tar.gz", recursive=True)
if _t:
    with tarfile.open(_t[0]) as t: t.extractall(T)
else:
    import shutil; shutil.copytree(find("lib/config/trufor_ph3.yaml").parents[2], T / "TruFor_train_test")
# weights
wz = T / "TruFor_weights.zip"
subprocess.run(["curl", "-sSL", "-o", str(wz), "https://www.grip.unina.it/download/prog/TruFor/TruFor_weights.zip"], check=True)
assert sha(wz) == sums["TruFor_weights.zip"], "weights zip hash mismatch"
with zipfile.ZipFile(wz) as z: z.extractall(T)
WEIGHTS = next(T.rglob("trufor.pth.tar"))
assert sha(WEIGHTS) == sums["weights/trufor.pth.tar"], "checkpoint hash mismatch"
# images: HITL originals + variant tars
for tar in glob.glob("/kaggle/input/**/variants_*.tar", recursive=True):
    with tarfile.open(tar) as t: t.extractall(T / "variants")
VAR = {}
for base in ["/kaggle/input", str(T / "variants")]:
    for dp, _, fs in os.walk(base):
        for f in fs:
            stem = f.split(".")[0]
            if len(stem) == 64 and stem in index: VAR[stem] = Path(dp) / f
print("variant files found:", len(VAR))
HITL_ROOT = find("Car parts dataset/File1/img").parents[2]
def path_of(s, v):
    return HITL_ROOT / v["hitl_rel"] if v["hitl_rel"] else VAR.get(s, Path("/nonexistent"))
TD = T / "TruFor_train_test"; sys.path.insert(0, str(TD)); os.chdir(TD)
from lib.config import config
from lib.utils import get_model
config.defrost(); config.merge_from_file("lib/config/trufor_ph3.yaml"); config.merge_from_list(["TEST.MODEL_FILE", str(WEIGHTS)]); config.freeze()
scalar = (np._core if hasattr(np, "_core") else np.core).multiarray.scalar
safe = [(scalar, "numpy.core.multiarray.scalar"), scalar, np.dtype, type(np.dtype("float64")), type(np.dtype("float32"))]
with torch.serialization.safe_globals(safe):
    ck = torch.load(str(WEIGHTS), map_location="cpu", weights_only=True)
model = get_model(config); model.load_state_dict(ck["state_dict"]); model = model.cuda().eval()
maps = W / "forensic_maps"; maps.mkdir(exist_ok=True)
rows, bad, t0 = [], 0, time.time()
MAP_SIDE = 64
for i, (s, v) in enumerate(sorted(index.items())):
    p = path_of(s, v)
    if not p.exists() or sha(p) != s: bad += 1; continue
    with Image.open(p) as im:
        im = im.convert("RGB"); w, h = im.size
        rgb = np.asarray(im, dtype=np.float32)
    x = torch.from_numpy(rgb.transpose(2, 0, 1)).unsqueeze(0).cuda() / 256.0
    with torch.no_grad():
        pred, conf, det, _ = model(x, save_np=False)
    loc = F.softmax(pred, dim=1)[:, 1:2]; cf = torch.sigmoid(conf)
    side = (MAP_SIDE, max(1, round(MAP_SIDE * w / h)))
    ls = F.interpolate(loc, size=side, mode="area")[0, 0].cpu().numpy().astype(np.float16)
    cs = F.interpolate(cf, size=side, mode="area")[0, 0].cpu().numpy().astype(np.float16)
    np.savez_compressed(maps / f"{s}.npz", localization=ls, confidence=cs)
    lf, cff = loc[0, 0].float().cpu().numpy(), cf[0, 0].float().cpu().numpy()
    rows.append({"image_sha256": s, "score": float(torch.sigmoid(det).item()),
                 "loc_mean": float(lf.mean()), "loc_area_05": float((lf > 0.5).mean()),
                 "conf_mean": float(cff.mean()), "conf_in_loc": float(cff[lf > 0.5].mean()) if (lf > 0.5).any() else None,
                 "inference_size": [w, h]})
    if i % 250 == 0: print(i, len(index), round(time.time() - t0), flush=True)
out = W / "forensic.jsonl"
out.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
prov = {"specialist": "forensic", "method": "TruFor (Guillaro et al., CVPR 2023), pretrained trufor_ph3, inference only",
        "checkpoint_sha256": sha(WEIGHTS), "weights_zip_sha256": sha(wz), "resolution": "native (no resize)",
        "map_side": MAP_SIDE, "license": "GRIP-UNINA non-profit research licence", "n_rows": len(rows),
        "n_images_index": len(index), "sha_mismatch_skipped": bad, "output_sha256": sha(out), "seed": 0,
        "load": "torch.load(weights_only=True) with allow-listed numpy scalars",
        "wall_seconds": round(time.time() - t0, 1), "hardware": torch.cuda.get_device_name(0),
        "versions": {"python": platform.python_version(), "torch": torch.__version__, "numpy": np.__version__}}
(W / "forensic.provenance.json").write_text(json.dumps(prov, indent=2, sort_keys=True))
subprocess.run(["tar", "czf", str(W / "forensic_maps.tar.gz"), "-C", str(W), "forensic_maps"], check=True)
subprocess.run(["rm", "-rf", str(maps)], check=True)
print(json.dumps(prov)); print("DONE")
