"""Muestra determinista para revisión humana de C0-C10 del candidato v3.

No aprueba el benchmark ni adjudica etiquetas. Selecciona una cobertura
variada por condición (y por clasificación C2 / subtipo C8) más los casos que
las auditorías automáticas ya marcaron como atípicos (p. ej. área modificada
grande en C4). Reutiliza qa_v3_pixels.json y c2_audit ya calculados: no
recomputa sobre imágenes ni cambia los artefactos congelados. La salida es
exclusivamente informativa/HTML; no escribe en data/manifests/benchmark_v3.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.benchmark_qa import build_audit_index, c2_audit, gallery  # noqa: E402

SALT = "review-sample-v3-2026-10-23"
PER_CONDITION = 4
PER_C2_CLASS = 4
PER_C8_SUBTYPE = 2
C4_NOT_SMALL_EXTRA = 3


def rank(claim_id: str) -> str:
    return hashlib.sha256((SALT + claim_id).encode("utf-8")).hexdigest()


def main() -> int:
    bundle = ROOT / "data/manifests/benchmark_v3"
    claims = [json.loads(line) for line in (bundle / "manifest.jsonl").read_text().splitlines()]
    audit = json.loads((bundle / "dataset_audit.json").read_text())
    sources = {s["source_image_id"]: s for s in audit["sources"]}
    claim_by_id = {c["claim_id"]: c for c in claims}
    pixel_rows = json.loads((ROOT / "qa_v3_pixels.json").read_text())
    c2_rows = c2_audit(claims, sources)
    audit_index = build_audit_index(c2_rows, pixel_rows)

    selected: dict[str, dict] = {}
    notes: list[str] = []

    def add(claim: dict, why: str) -> None:
        selected[claim["claim_id"]] = claim
        notes.append(f"{claim['claim_id']} ({claim['condition']}): {why}")

    # 1. C2: cobertura de ambas clasificaciones heurísticas (compatible / contradicción).
    by_class: dict[str, list[str]] = defaultdict(list)
    for row in c2_rows:
        by_class[row["classification"]].append(row["claim_id"])
    for classification, ids in sorted(by_class.items()):
        for claim_id in sorted(ids, key=rank)[:PER_C2_CLASS]:
            add(claim_by_id[claim_id], f"C2 cobertura determinista de '{classification}'")

    # 2. C3/C4/C5: muestra base determinista por condición.
    for condition in ("C3", "C4", "C5"):
        group = [c for c in claims if c["condition"] == condition]
        for claim in sorted(group, key=lambda c: rank(c["claim_id"]))[:PER_CONDITION]:
            add(claim, f"{condition} cobertura determinista base")

    # 3. Casos que las auditorías automáticas ya marcaron como atípicos.
    large_area = [r["claim_id"] for rows in pixel_rows.values() for r in rows if r.get("large_area_flag")]
    for claim_id in large_area:
        add(claim_by_id[claim_id], "alerta automática: large_area_flag=True (área modificada >20%)")
    boundary_artifacts = [r["claim_id"] for r in pixel_rows["C4"] if r.get("possible_boundary_artifact_flag")]
    for claim_id in boundary_artifacts:
        add(claim_by_id[claim_id], "alerta automática: possible_boundary_artifact_flag=True")
    too_similar = [row["claim_id"] for row in c2_rows if row.get("too_similar_flag")]
    for claim_id in too_similar:
        add(claim_by_id[claim_id], "alerta automática: too_similar_flag=True (donante casi idéntico por dHash)")
    c4_not_small = [r["claim_id"] for r in pixel_rows["C4"] if not r.get("small_area_flag") and r["claim_id"] not in selected]
    for claim_id in sorted(c4_not_small, key=rank)[:C4_NOT_SMALL_EXTRA]:
        add(claim_by_id[claim_id], "C4 fuera del rango 'área pequeña' (>0.5%), para contraste")

    # 4. Resto de condiciones sin heurística dedicada.
    for condition in ("C0", "C1", "C6", "C7", "C10"):
        group = [c for c in claims if c["condition"] == condition]
        for claim in sorted(group, key=lambda c: rank(c["claim_id"]))[:PER_CONDITION]:
            add(claim, f"{condition} cobertura determinista base")

    # 5. C8: un ejemplo por subtipo real (JPEG/resize/crop).
    c8 = [c for c in claims if c["condition"] == "C8"]
    for subtype in ("C8_JPEG", "C8_RESIZE", "C8_CROP"):
        group = [c for c in c8 if c["transformation"]["parameters"]["subtype"] == subtype]
        for claim in sorted(group, key=lambda c: rank(c["claim_id"]))[:PER_C8_SUBTYPE]:
            add(claim, f"C8 cobertura determinista de subtipo {subtype}")

    # 6. C9 aceptados (los excluidos no generan ClaimRecord, no hay nada que mostrar de ellos aquí).
    c9 = [c for c in claims if c["condition"] == "C9"]
    for claim in sorted(c9, key=lambda c: rank(c["claim_id"]))[:PER_CONDITION]:
        add(claim, "C9 cobertura determinista base (aceptados; los excluidos no generan claim)")

    ordered = sorted(selected.values(), key=lambda c: (int(c["condition"][1:]), c["claim_id"]))

    intro = (
        "<section style='background:#fff3cd;border:1px solid #e0c36a;border-radius:8px;"
        "padding:14px;margin:0 0 20px'><strong>Cómo se construyó esta muestra (determinista, "
        f"salt='{SALT}'):</strong><ul>"
        f"<li>C2: hasta {PER_C2_CLASS} casos por clasificación heurística (compatible/contradicción), "
        "ordenados por sha256(salt+claim_id).</li>"
        f"<li>C3/C4/C5: hasta {PER_CONDITION} casos base por condición, mismo criterio de orden.</li>"
        "<li>Más TODOS los casos que la auditoría automática ya marcó como atípicos: "
        f"{len(large_area)} con área modificada &gt;20%, {len(boundary_artifacts)} con posible artefacto "
        f"de borde en C4, {len(too_similar)} con donante casi idéntico en C2 (dHash&le;6).</li>"
        f"<li>C8: hasta {PER_C8_SUBTYPE} casos por subtipo real (JPEG/resize/crop).</li>"
        "<li>C0/C1/C6/C7/C9/C10: cobertura base determinista, sin heurística adicional porque no "
        "tienen auditoría de manipulación de píxeles.</li>"
        f"<li>Total: {len(ordered)} de {len(claims)} reclamos del candidato v3 "
        f"({100*len(ordered)/len(claims):.1f}%).</li></ul>"
        "<p><strong>Qué permite concluir y qué no:</strong> permite a un revisor humano formarse una "
        "opinión informada sobre la validez de cada condición y decidir criterios junto con la "
        "asesora, usando ejemplos variados y los casos más atípicos detectados automáticamente. "
        "No es una muestra probabilística ni un estimador de la tasa de error del benchmark completo; "
        "aprobar estos casos no aprueba el resto de v3, y los casos no incluidos siguen sin revisión "
        "humana.</p></section>"
    )

    gallery(ROOT, ordered, sources, ROOT / "benchmark_v3_review_sample.html", audit_index=audit_index, extra_intro=intro)

    print(json.dumps({
        "total_claims_v3": len(claims),
        "sample_size": len(ordered),
        "by_condition": dict(sorted(((c, sum(1 for x in ordered if x["condition"] == c)) for c in {x["condition"] for x in ordered}))),
        "flagged_included": {
            "large_area_flag": len(large_area),
            "possible_boundary_artifact_flag": len(boundary_artifacts),
            "too_similar_flag_c2": len(too_similar),
        },
        "output": "benchmark_v3_review_sample.html",
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
