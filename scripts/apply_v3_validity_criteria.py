"""Apply the advisor-approved C2-C5 validity criteria to benchmark v3 and freeze it.

Decision (2026-11-13, aprobado por la asesora): the VALIDO / AMBIGUO / INVALIDO
table of the workspace README is applied automatically wherever the criterion
is measurable. Realism is NOT measurable automatically and is never inferred:
``human_realism_review`` stays ``NOT PERFORMED`` and is reported as a limitation.

Operationalization (only measured signals, never labels or model outputs):

C2 (substitution)
  INVALID   dhash_distance(source, donor) <= near_duplicate_hamming_threshold (6),
            donor == source, or donor metadata missing.
  AMBIGUOUS every asserted class is also annotated in the donor
            (asserted subset of donor classes): not identifiable from text+image.
  VALID     at least one asserted class is absent from the donor annotations
            (observable contradiction).
C3 / C5 (copy-move [+ narrative denial])
  INVALID   any integrity check of qa_v3_pixels.json is False.
  AMBIGUOUS mean absolute RGB change inside the mask < 5.0 (edit imperceptible,
            transformation not clearly fulfilled) or large_area_flag.
  VALID     otherwise.
C4 (inpainting)
  INVALID   any integrity check is False.
  AMBIGUOUS possible_boundary_artifact_flag, large_area_flag, or mean absolute RGB
            change inside the mask < 5.0 (damage removal barely changed pixels).
  VALID     otherwise. ``damage_removal_verified`` is False by construction
            (it means "not human-verified"), so it is not used as a criterion.

Outputs (written next to the frozen generator artifacts, which stay untouched so
that ``build_benchmark_v3.py --check`` still regenerates them byte for byte):
  validity_criteria.json   per-claim status + reasons for C2-C5
  exclusions_criteria.json INVALID claims with their reason (excluded by the loader)
  freeze.json              READY_FOR_MODELS = YES, date, approval, hashes
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import yaml  # noqa: E402

from src.data.benchmark_qa import c2_audit  # noqa: E402

BUNDLE = ROOT / "data/manifests/benchmark_v3"
RGB_CHANGE_MIN = 5.0
INTEGRITY_KEYS = {
    "C3": ["dimensions_match", "mask_nonempty", "mask_sha_matches", "reproducible", "source_copy_matches",
           "source_and_destination_in_bounds", "original_damage_preserved", "valid_source_and_donor"],
    "C4": ["dimensions_match", "mask_nonempty", "mask_sha_matches", "reproducible", "mask_matches_annotation"],
    "C5": ["dimensions_match", "mask_nonempty", "mask_sha_matches", "reproducible", "source_copy_matches",
           "source_and_destination_in_bounds", "original_damage_preserved", "valid_source_and_donor",
           "narrative_denial_matches", "semantic_contradiction_annotation_supported",
           "visual_manipulation_verified"],
}
DECISION_DATE = "2026-11-13"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=1) + "\n"


def classify(claims: list[dict], sources: dict, pixels: dict, threshold: int) -> list[dict]:
    rows = []
    for row in c2_audit(claims, sources):
        donor = row["donor_source_image_id"]
        if donor == row["source_image_id"] or donor not in sources:
            status, reason = "INVALID", "donor missing or equal to source (metadata mal derivada)"
        elif row["dhash_distance"] <= threshold:
            status, reason = "INVALID", f"donor near-identical: dhash_distance={row['dhash_distance']}<={threshold}"
        elif set(row["asserted_classes"]) <= set(row["donor_classes"]):
            status, reason = "AMBIGUOUS", "asserted classes all present in donor: not identifiable from text+image"
        else:
            status, reason = "VALID", f"asserted classes absent from donor: {row['unconfirmed_classes']}"
        rows.append({"claim_id": row["claim_id"], "condition": "C2", "source_image_id": row["source_image_id"],
                     "status": status, "reason": reason,
                     "measurements": {"dhash_distance": row["dhash_distance"],
                                      "asserted_classes": row["asserted_classes"],
                                      "donor_classes": row["donor_classes"]}})
    for condition in ("C3", "C4", "C5"):
        for row in pixels[condition]:
            failed = [k for k in INTEGRITY_KEYS[condition] if row.get(k) is not True]
            change = row["mean_absolute_rgb_change_in_mask"]
            flags = []
            if change < RGB_CHANGE_MIN:
                flags.append(f"mean_abs_rgb_change_in_mask={change:.2f}<{RGB_CHANGE_MIN}")
            if row.get("large_area_flag"):
                flags.append("large_area_flag")
            if condition == "C4" and row.get("possible_boundary_artifact_flag"):
                flags.append("possible_boundary_artifact_flag")
            if failed:
                status, reason = "INVALID", "integrity check failed: " + ",".join(failed)
            elif flags:
                status, reason = "AMBIGUOUS", "; ".join(flags)
            else:
                status, reason = "VALID", "integrity OK; edit measurable (realism not human-reviewed)"
            rows.append({"claim_id": row["claim_id"], "condition": condition,
                         "source_image_id": row["source_image_id"], "status": status, "reason": reason,
                         "measurements": {"mean_absolute_rgb_change_in_mask": change,
                                          "changed_percent": row["changed_percent"],
                                          "human_realism_review": row["human_realism_review"]}})
    return sorted(rows, key=lambda r: (r["condition"], r["claim_id"]))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="recompute and compare, write nothing")
    args = ap.parse_args()
    config = yaml.safe_load((ROOT / "configs/benchmark_v3.yaml").read_text())
    claims = [json.loads(line) for line in (BUNDLE / "manifest.jsonl").read_text().splitlines()]
    audit = json.loads((BUNDLE / "dataset_audit.json").read_text())
    sources = {s["source_image_id"]: s for s in audit["sources"]}
    pixels = json.loads((ROOT / "data/qa/qa_v3_pixels.json").read_text())
    rows = classify(claims, sources, pixels, config["near_duplicate_hamming_threshold"])
    exclusions = [{"claim_id": r["claim_id"], "condition": r["condition"], "source_image_id": r["source_image_id"],
                   "reason": r["reason"], "criterion": "advisor-approved C2-C5 validity table"}
                  for r in rows if r["status"] == "INVALID"]
    summary = {c: dict(Counter(r["status"] for r in rows if r["condition"] == c)) for c in ("C2", "C3", "C4", "C5")}
    validity = {"decision_date": DECISION_DATE, "approved_by": "asesora (aprobado por la asesora)",
                "rules": __doc__, "rgb_change_min": RGB_CHANGE_MIN,
                "near_duplicate_hamming_threshold": config["near_duplicate_hamming_threshold"],
                "summary": summary, "cases": rows}
    texts = {"validity_criteria.json": canonical(validity), "exclusions_criteria.json": canonical(exclusions)}
    if args.check:
        for name, text in texts.items():
            if (BUNDLE / name).read_text() != text:
                raise SystemExit(f"FAIL: {name} differs from recomputation")
        print("PASS: validity criteria reproduce")
        return 0
    for name, text in texts.items():
        (BUNDLE / name).write_text(text)
    freeze = {
        "benchmark_version": "0.3.0", "READY_FOR_MODELS": "YES", "official": True,
        "frozen_on": DECISION_DATE, "approved_by": "asesora (aprobado por la asesora)",
        "historical_versions": {"0.2.0": "historical, kept reproducible, no longer official"},
        "validity_summary": summary, "n_excluded_invalid": len(exclusions),
        "n_ambiguous_flagged": sum(r["status"] == "AMBIGUOUS" for r in rows),
        "limitations": [
            "QA del diseno del benchmark miro tambien test: test no es completamente ciego.",
            "Realismo de C3/C4/C5 no revisado por humanos (human_realism_review = NOT PERFORMED).",
            "AMBIGUOUS se conservan y se marcan para analisis de sensibilidad (con y sin ellos).",
        ],
        "artifacts_sha256": {name: sha256(BUNDLE / name) for name in
                             ["manifest.jsonl", "splits.json", "metadata.json", "exclusions.json",
                              "validity_criteria.json", "exclusions_criteria.json"]},
    }
    (BUNDLE / "freeze.json").write_text(canonical(freeze))
    print(json.dumps({"summary": summary, "excluded": len(exclusions)}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
