# UAFEG — B8: frozen open multimodal LLM (Qwen2-VL-2B-Instruct, Apache-2.0), zero-shot, Kaggle GPU.
# For each validation/test claim (no label, no condition is ever given), the model sees the photo
# (if any) and the narrative (if any) and we read the next-token logits of the options A/B/C.
# Output: log-scores per claim; calibration (T*) and abstention happen locally on validation.
import subprocess, sys, json, hashlib, os, glob, tarfile, time, platform
from pathlib import Path
import numpy as np, torch
from PIL import Image
W = Path("/kaggle/working"); T = Path("/kaggle/tmp"); T.mkdir(exist_ok=True)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def find(pattern):
    hits = sorted(glob.glob(f"/kaggle/input/**/{pattern}", recursive=True))
    if not hits: raise SystemExit(f"not found: {pattern}")
    return Path(hits[0])
index = json.loads(find("images_index.json").read_text())
claims = [json.loads(l) for l in find("claims_val_test_nolabel.jsonl").read_text().splitlines()]
for tar in glob.glob("/kaggle/input/**/variants_*.tar", recursive=True):
    with tarfile.open(tar) as t: t.extractall(T / "variants")
VAR = {}
for base in ["/kaggle/input", str(T / "variants")]:
    for dp, _, fs in os.walk(base):
        for f in fs:
            stem = f.split(".")[0]
            if len(stem) == 64 and stem in index: VAR[stem] = Path(dp) / f
HITL_ROOT = find("Car parts dataset/File1/img").parents[2]
def path_of(s):
    v = index[s]; return HITL_ROOT / v["hitl_rel"] if v["hitl_rel"] else VAR[s]
from transformers import AutoProcessor, Qwen2VLForConditionalGeneration
import transformers
MODEL = "Qwen/Qwen2-VL-2B-Instruct"
model = Qwen2VLForConditionalGeneration.from_pretrained(MODEL, torch_dtype=torch.float16, device_map="cuda").eval()
proc = AutoProcessor.from_pretrained(MODEL, min_pixels=256 * 28 * 28, max_pixels=640 * 28 * 28)
revision = getattr(model.config, "_commit_hash", None)
PROMPT = ("Eres un verificador de reclamos de seguros vehiculares. Se te da la foto del vehículo (si existe) y el "
          "relato del asegurado (si existe). Clasifica el reclamo:\n"
          "A) SUPPORTED: la foto es auténtica y muestra lo que afirma el relato.\n"
          "B) SUSPICIOUS: la foto parece manipulada o el relato contradice la foto.\n"
          "C) INSUFFICIENT: falta la foto o el relato, o la evidencia no permite decidir.\n"
          "Relato: {text}\nResponde solo con la letra A, B o C.")
opt_ids = [proc.tokenizer.encode(x, add_special_tokens=False)[0] for x in ("A", "B", "C")]
rows, t0 = [], time.time()
for i, c in enumerate(claims):
    text = c["narrative_text"] if c["narrative_text"] else "(no hay relato)"
    content = []
    img = None
    if c["image_sha256"]:
        p = path_of(c["image_sha256"]); assert sha(p) == c["image_sha256"]
        img = Image.open(p).convert("RGB"); content.append({"type": "image"})
    else:
        text += "\n(No se adjuntó ninguna foto.)"
    content.append({"type": "text", "text": PROMPT.format(text=text)})
    msgs = [{"role": "user", "content": content}]
    chat = proc.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    inputs = proc(text=[chat], images=[img] if img is not None else None, return_tensors="pt").to("cuda")
    with torch.no_grad():
        logits = model(**inputs).logits[0, -1].float()
    lp = torch.log_softmax(logits, -1)[opt_ids].cpu().numpy()
    rows.append({"claim_id": c["claim_id"], "logscores_ABC": lp.tolist()})
    if i % 200 == 0: print(i, len(claims), round(time.time() - t0), flush=True)
out = W / "b8_scores.jsonl"; out.write_text("".join(json.dumps(r) + "\n" for r in rows))
prov = {"system": "B8", "model": MODEL, "model_revision": revision, "license": "Apache-2.0", "dtype": "float16",
        "prompt": PROMPT, "options": {"A": "SUPPORTED", "B": "SUSPICIOUS", "C": "INSUFFICIENT"},
        "n_rows": len(rows), "output_sha256": sha(out), "wall_seconds": round(time.time() - t0, 1),
        "versions": {"python": platform.python_version(), "torch": torch.__version__, "transformers": transformers.__version__}}
(W / "b8.provenance.json").write_text(json.dumps(prov, indent=2)); print("DONE", prov["n_rows"])
