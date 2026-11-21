import json, sys, tarfile, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
group, out = sys.argv[1], Path(sys.argv[2])
rows = [json.loads(l) for l in open(ROOT / "data/manifests/benchmark_v3/manifest.jsonl")]
seen = {}
for c in rows:
    p = c.get("image_path")
    if not p or p.startswith("data/raw"): continue
    g = "v2" if "benchmark_v2" in p else "v13"
    if g == group: seen.setdefault(c["transformation"]["image_sha256"], p)
out.mkdir(parents=True, exist_ok=True)
with tarfile.open(out / f"variants_{group}.tar", "w") as t:
    for sha, p in sorted(seen.items()):
        t.add(ROOT / p, sha + Path(p).suffix.lower())
print(group, len(seen))
