"""Build real EvidencePackets for benchmark v3 from the cached specialist outputs.

    python scripts/build_evidence_packets.py reliability   # r per specialist, measured on validation only
    python scripts/build_evidence_packets.py packets       # artifacts/packets/v3/{split}.jsonl + checksums

Each packet carries e = (z, p, u, r, q, c, l, s) per evidence element, with full
provenance (model, checkpoint hash, seed, image/text hash). Deterministic: claims
sorted by claim_id, JSON with sorted keys, no timestamps inside the packets.

Reliability r (versioned in data/specialists/reliability_v3.json):
  narrative  per predicted damage type: P(type in asserted classes AND polarity
             correct) on VALIDATION claims, Laplace-smoothed (k+1)/(n+2).
             Expected polarity: denied for the narrative-contradiction
             conditions (C1, C5), affirmed otherwise. This uses the condition
             of validation claims only to compute an aggregate table; it never
             enters a packet as a per-claim feature.
  visual     per predicted class: precision at IoU>=0.5 against the HITL
             polygons' bounding boxes on the VALIDATION source images (original
             photos only), Laplace-smoothed.
  forensic   null while TruFor is NOT_RUN.
INVALID claims (exclusions_criteria.json) are dropped here; AMBIGUOUS ones are kept
and listed in artifacts/packets/v3/ambiguous_claim_ids.json for the sensitivity
analysis (the flag is never written into a packet).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.schemas.claim import ClaimRecord  # noqa: E402
from src.schemas.evidence import (  # noqa: E402
    CANONICAL_DAMAGE_CLASSES, DamageAnnotation, ForensicResult, ImageQuality, NarrativeAssertion,
    NarrativeEvidence, VisualEvidence, BoundingBox,
)
from src.schemas.packet import EvidencePacket  # noqa: E402

BUNDLE = ROOT / "data/manifests/benchmark_v3"
SPEC = ROOT / "artifacts/specialists"
OUT = ROOT / "artifacts/packets/v3"
RELIABILITY = ROOT / "data/specialists/reliability_v3.json"
DENIAL_CONDITIONS = {"C1", "C5"}
FORENSIC_STATUS = ("NOT_RUN: TruFor adapter implemented (src/forensic/trufor_adapter.py) and weights "
                   "downloaded, but executing the downloaded third-party code/pickle checkpoint was not "
                   "authorized in this session; forensic stays null")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def claims() -> list[dict]:
    return load_jsonl(BUNDLE / "manifest.jsonl")


def iou(a, b) -> float:
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def binary_entropy(p: float) -> float:
    p = min(max(p, 1e-9), 1 - 1e-9)
    return -(p * math.log(p) + (1 - p) * math.log(1 - p)) / math.log(2)


def smoothed(k: int, n: int) -> float:
    return (k + 1) / (n + 2)


def main_assertion(assertions: list[dict]) -> dict | None:
    if not assertions:
        return None
    return max(assertions, key=lambda a: a["p"][0] + a["p"][2])


def compute_reliability() -> dict:
    narrative = {r["text_sha256"]: r for r in load_jsonl(SPEC / "narrative.jsonl")}
    visual = {r["image_sha256"]: r for r in load_jsonl(SPEC / "visual.jsonl")} if (SPEC / "visual.jsonl").exists() else {}
    val = [c for c in claims() if c["split"] == "validation"]
    hits, totals = defaultdict(int), defaultdict(int)
    for c in val:
        if not c.get("narrative_text"):
            continue
        row = narrative[hashlib.sha256(c["narrative_text"].encode()).hexdigest()]
        a = main_assertion(row["assertions"])
        if a is None:
            continue
        expected = "denied" if c["condition"] in DENIAL_CONDITIONS else "affirmed"
        asserted = set(c["metadata"].get("asserted_damage_classes", []))
        totals[a["damage_type"]] += 1
        hits[a["damage_type"]] += int(a["damage_type"] in asserted and a["polarity"] == expected)
    narrative_r = {k: smoothed(hits[k], totals[k]) for k in CANONICAL_DAMAGE_CLASSES}

    visual_r, vis_counts = None, None
    if visual:
        sources = {json.loads(l)["source_image_id"]: json.loads(l)
                   for l in (ROOT / "data/processed/damage_specialist/source_manifest.jsonl").read_text().splitlines()}
        tp, n = defaultdict(int), defaultdict(int)
        for c in val:
            if c["condition"] != "C0":
                continue  # original photo of each validation source, exactly once
            src = sources[c["source_image_id"]]
            from PIL import Image
            with Image.open(ROOT / src["path"]) as im:
                w, h = im.size
            gts = [(a["damage_class"], [a["bbox"]["x_min"] / w, a["bbox"]["y_min"] / h,
                                        a["bbox"]["x_max"] / w, a["bbox"]["y_max"] / h])
                   for a in src["annotations"] if a.get("bbox")]
            used = set()
            for d in sorted(visual[c["transformation"]["image_sha256"]]["detections"], key=lambda d: -d["confidence"]):
                n[d["damage_class"]] += 1
                best, best_j = 0.0, None
                for j, (cls, box) in enumerate(gts):
                    if cls == d["damage_class"] and j not in used:
                        v = iou(d["bbox_norm"], box)
                        if v > best:
                            best, best_j = v, j
                if best >= 0.5:
                    used.add(best_j)
                    tp[d["damage_class"]] += 1
        visual_r = {k: smoothed(tp[k], n[k]) for k in CANONICAL_DAMAGE_CLASSES}
        vis_counts = {k: {"tp": tp[k], "n": n[k]} for k in CANONICAL_DAMAGE_CLASSES}
    out = {
        "measured_on": "validation split only", "smoothing": "Laplace (k+1)/(n+2)",
        "narrative": {"r": narrative_r, "counts": {k: {"hits": hits[k], "n": totals[k]} for k in CANONICAL_DAMAGE_CLASSES},
                      "input_sha256": sha256_file(SPEC / "narrative.jsonl")},
        "visual": {"r": visual_r, "counts": vis_counts, "criterion": "precision at IoU>=0.5 vs GT bbox",
                   "input_sha256": sha256_file(SPEC / "visual.jsonl") if visual else None,
                   "status": "MEASURED" if visual else "NOT_AVAILABLE"},
        "forensic": {"r": None, "status": FORENSIC_STATUS},
    }
    RELIABILITY.parent.mkdir(parents=True, exist_ok=True)
    RELIABILITY.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"narrative_r": narrative_r, "visual_r": visual_r}, indent=1))
    return out


def build_packets() -> None:
    rel = json.loads(RELIABILITY.read_text())
    narrative = {r["text_sha256"]: r for r in load_jsonl(SPEC / "narrative.jsonl")}
    quality = {r["image_sha256"]: r for r in load_jsonl(SPEC / "quality.jsonl")}
    visual_path = SPEC / "visual.jsonl"
    visual = {r["image_sha256"]: r for r in load_jsonl(visual_path)} if visual_path.exists() else None
    excluded = {e["claim_id"] for e in json.loads((BUNDLE / "exclusions_criteria.json").read_text())}
    validity = json.loads((BUNDLE / "validity_criteria.json").read_text())
    ambiguous = sorted(r["claim_id"] for r in validity["cases"] if r["status"] == "AMBIGUOUS")
    provenance_common = {
        "narrative": json.loads((SPEC / "narrative.provenance.json").read_text()),
        "quality": json.loads((SPEC / "quality.provenance.json").read_text()),
        "visual": json.loads((SPEC / "visual.provenance.json").read_text()) if visual else {"status": "NOT_AVAILABLE"},
        "forensic": {"status": FORENSIC_STATUS},
        "reliability_sha256": sha256_file(RELIABILITY),
    }
    for p in provenance_common.values():
        if isinstance(p, dict):
            p.pop("versions", None)
    OUT.mkdir(parents=True, exist_ok=True)
    by_split = defaultdict(list)
    for c in sorted(claims(), key=lambda c: c["claim_id"]):
        if c["claim_id"] in excluded:
            continue
        record = ClaimRecord.model_validate(c)
        prov = {"seed": 0, "text_sha256": None, "image_sha256": None}
        narrative_ev = None
        if c.get("narrative_text"):
            text_sha = hashlib.sha256(c["narrative_text"].encode()).hexdigest()
            prov["text_sha256"] = text_sha
            assertions = narrative[text_sha]["assertions"]
            raw = {k: max([a["class_nli"][k][0] for a in assertions] or [0.0]) for k in CANONICAL_DAMAGE_CLASSES}
            total = sum(raw.values())
            narrative_ev = NarrativeEvidence(
                raw_scores=raw, normalized_scores={k: (v / total if total else 0.0) for k, v in raw.items()},
                model_name=provenance_common["narrative"]["model"],
                model_revision=provenance_common["narrative"].get("model_revision"), device="cpu",
                assertions=[NarrativeAssertion(**a, reliability=rel["narrative"]["r"][a["damage_type"]])
                            for a in assertions])
        visual_ev = quality_ev = None
        forensic_ev = None
        if c.get("image_path"):
            image_sha = c["transformation"]["image_sha256"]
            prov["image_sha256"] = image_sha
            q = quality[image_sha]
            quality_ev = ImageQuality(
                width=q["width"], height=q["height"], aspect_ratio=q["width"] / q["height"],
                file_size_bytes=(ROOT / c["image_path"]).stat().st_size,
                file_format=(ROOT / c["image_path"]).suffix.lstrip(".").upper(),
                laplacian_variance=q["laplacian_variance"], is_corrupted=False,
                quality_q=q["q"], quality_factors={k: q[k] for k in ("resolution", "sharpness", "exposure")},
                source_s=q["s"], source_s_status=q["s_status"])
            if visual is not None:
                v = visual[image_sha]
                dets = []
                for d in v["detections"]:
                    rq = d["region_quality"]
                    x1, y1, x2, y2 = d["bbox_norm"]
                    dets.append(DamageAnnotation(
                        damage_class=d["damage_class"], confidence=d["confidence"],
                        bbox=BoundingBox(x_min=x1 * v["width"], y_min=y1 * v["height"],
                                         x_max=x2 * v["width"], y_max=y2 * v["height"]),
                        bbox_norm=tuple(d["bbox_norm"]), area_fraction=min(1.0, d["area_fraction"]),
                        uncertainty=binary_entropy(d["confidence"]),
                        reliability=rel["visual"]["r"][d["damage_class"]],
                        region_quality=(rq["q"] if rq else None),
                        region_quality_factors=({k: rq[k] for k in ("resolution", "sharpness", "exposure")} if rq else None),
                        coverage=1.0, mask_64x48=d["mask_64x48"]))
                visual_ev = VisualEvidence(detections=dets, model_name="yolov8n-seg-hitl-v3",
                                           image_width=v["width"], image_height=v["height"])
            forensic_ev = ForensicResult(available=False, status=FORENSIC_STATUS)
        packet = EvidencePacket(claim=record, narrative=narrative_ev, visual=visual_ev,
                                image_quality=quality_ev, forensic=forensic_ev, provenance=prov)
        by_split[c["split"]].append(packet.model_dump_json())
    checksums = {}
    for split, lines in sorted(by_split.items()):
        path = OUT / f"{split}.jsonl"
        path.write_text("".join(json.dumps(json.loads(l), sort_keys=True, ensure_ascii=False) + "\n" for l in lines))
        checksums[f"{split}.jsonl"] = {"sha256": sha256_file(path), "n_packets": len(lines)}
    (OUT / "ambiguous_claim_ids.json").write_text(json.dumps(ambiguous, indent=0) + "\n")
    manifest = {"benchmark_version": "0.3.0", "freeze_sha256": sha256_file(BUNDLE / "freeze.json"),
                "excluded_invalid": len(excluded), "ambiguous_flagged": len(ambiguous),
                "files": checksums, "specialists": provenance_common,
                "ambiguous_claim_ids_sha256": sha256_file(OUT / "ambiguous_claim_ids.json")}
    (OUT / "packets_manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    print(json.dumps(checksums, indent=1))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("step", choices=["reliability", "packets"])
    args = ap.parse_args()
    compute_reliability() if args.step == "reliability" else build_packets()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
