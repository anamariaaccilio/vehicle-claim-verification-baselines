"""FASE 4.5: demo Streamlit del baseline (Narrative + Damage + Image
Quality + Rule Baseline B0). Sin late fusion, sin calibracion, sin TruFor,
sin Evidence Graph/GATv2/agentes/RL -- ver README.md.

Correr con:
    streamlit run demo/app.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from demo.cases_loader import load_cases  # noqa: E402
from demo.run_logger import log_run  # noqa: E402
from src.damage.inference import DamageSpecialist  # noqa: E402
from src.fusion.inference import analyze  # noqa: E402
from src.fusion.rules import load_rules_config  # noqa: E402
from src.narrative.nli_extractor import NarrativeExtractor  # noqa: E402
from src.schemas.evidence import CANONICAL_DAMAGE_CLASSES  # noqa: E402

st.set_page_config(page_title="Baseline actual - verificacion de reclamos", layout="wide")


@st.cache_resource(show_spinner="Cargando NarrativeExtractor (mDeBERTa-v3-base-mnli-xnli)...")
def get_narrative_extractor() -> NarrativeExtractor:
    return NarrativeExtractor()


@st.cache_resource(show_spinner=False)
def get_damage_specialist() -> DamageSpecialist:
    return DamageSpecialist()


def _pct(x: float | None) -> str:
    return "N/A" if x is None else f"{x * 100:.1f}%"


st.title("BASELINE ACTUAL - VERIFICACION DE RECLAMOS")
st.info(
    "Esta aplicacion implementa un baseline convencional basado en modelos "
    "existentes y reglas explicitas. No contiene la contribucion Evidence "
    "Graph/UAFEG-GATv2."
)

# ---------------------------------------------------------------------------
# Sidebar: casos preparados
# ---------------------------------------------------------------------------
st.sidebar.header("Casos preparados")
cases = load_cases()
case_labels = {"(ninguno - entrada manual)": None}
for c in cases:
    availability = "✅" if c.is_runnable else "⛔ falta imagen real"
    case_labels[f"{c.case_id} - {c.title} [{availability}]"] = c

selected_label = st.sidebar.radio("Cargar un caso preparado:", list(case_labels.keys()))
selected_case = case_labels[selected_label]

if selected_case is not None:
    st.sidebar.markdown(f"**Esperado:** `{selected_case.expected_condition}`")
    st.sidebar.caption(selected_case.notes)
    if not selected_case.is_runnable:
        st.sidebar.warning(
            "Este caso requiere una imagen real del dataset HITL que todavia "
            "no esta colocada en demo/cases/assets/. Ver data/README.md."
        )

# ---------------------------------------------------------------------------
# INPUT
# ---------------------------------------------------------------------------
st.header("INPUT")
col_a, col_b = st.columns(2)

default_narrative = selected_case.narrative_text if selected_case else ""
with col_a:
    narrative_text = st.text_area(
        "Narrativa:", value=default_narrative or "", height=120, key="narrative_input"
    )

with col_b:
    uploaded_file = st.file_uploader("Imagen:", type=["jpg", "jpeg", "png"])

analyze_clicked = st.button("ANALIZAR", type="primary")

if analyze_clicked:
    # --- resolver imagen de entrada (upload manual > caso preparado > ninguna) ---
    image_path: Path | None = None
    tmp_file = None
    if uploaded_file is not None:
        tmp_file = tempfile.NamedTemporaryFile(
            delete=False, suffix=Path(uploaded_file.name).suffix or ".jpg"
        )
        tmp_file.write(uploaded_file.getvalue())
        tmp_file.flush()
        image_path = Path(tmp_file.name)
    elif selected_case is not None and selected_case.absolute_image_path is not None:
        if selected_case.absolute_image_path.exists():
            image_path = selected_case.absolute_image_path

    narrative_for_pipeline = narrative_text if narrative_text.strip() else None

    with st.spinner("Corriendo Narrative Specialist + Damage Specialist + Rule Baseline B0..."):
        narrative_extractor = get_narrative_extractor()
        damage_specialist = get_damage_specialist()
        result = analyze(
            narrative_text=narrative_for_pipeline,
            image_path=image_path,
            narrative_extractor=narrative_extractor,
            damage_specialist=damage_specialist,
        )
        log_path = log_run(
            narrative_text=narrative_for_pipeline,
            image_path=image_path,
            result=result,
            case_id=selected_case.case_id if selected_case else None,
        )

    st.divider()

    # -----------------------------------------------------------------
    # 1. NARRATIVE SPECIALIST
    # -----------------------------------------------------------------
    st.header("1. NARRATIVE SPECIALIST")
    nr = result.narrative_result
    if nr is None:
        st.warning("Narrativa ausente: no se corrio el Narrative Specialist.")
    else:
        st.markdown(f"**Modelo:** `{nr.model_name}` (revision `{nr.model_revision or 'N/A'}`, device `{nr.device}`)")
        rows = sorted(nr.raw_scores.items(), key=lambda kv: -kv[1])
        st.table({"Clase de danio": [k for k, _ in rows], "Score (entailment NLI)": [_pct(v) for _, v in rows]})
        col1, col2, col3 = st.columns(3)
        col1.metric("Top", nr.top_damage)
        col2.metric("Confidence", _pct(nr.top_confidence))
        col3.metric("Entropy", f"{nr.entropy:.3f}")
        st.caption(f"Tiempo de inferencia: {nr.inference_time_seconds:.2f}s")

    st.divider()

    # -----------------------------------------------------------------
    # 2. VISUAL DAMAGE SPECIALIST
    # -----------------------------------------------------------------
    st.header("2. VISUAL DAMAGE SPECIALIST")
    if image_path is not None:
        st.image(str(image_path), caption="Imagen analizada", width=350)

    if image_path is None:
        st.warning("No se proveyo imagen.")
    elif not damage_specialist.is_available:
        st.error(
            "DAMAGE MODEL NOT AVAILABLE\n\n"
            "No hay un checkpoint entrenado (falta el dataset HITL en "
            "data/raw/hitl/ y el fine-tuning de src/damage/train.py). "
            "No se genera ninguna deteccion simulada."
        )
    elif result.visual_evidence is None:
        st.warning("No se pudo correr el Damage Specialist sobre esta imagen (ver calidad de imagen abajo).")
    elif not result.visual_evidence.detections:
        st.info("El Damage Specialist corrio pero no detecto danio en la imagen.")
    else:
        ve = result.visual_evidence
        st.markdown(f"**Modelo:** `{ve.model_name}`")
        for det in ve.detections:
            st.write(f"- **{det.damage_class}** — confidence: {_pct(det.confidence)}")

    st.divider()

    # -----------------------------------------------------------------
    # 3. IMAGE QUALITY
    # -----------------------------------------------------------------
    st.header("3. IMAGE QUALITY")
    iq = result.image_quality
    if iq is None:
        st.warning("No aplica: no se proveyo imagen.")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Resolution", f"{iq.width}x{iq.height}")
        col2.metric("Blur (Laplacian var.)", f"{iq.laplacian_variance:.1f}" if iq.laplacian_variance is not None else "N/A")
        col3.metric("Status", result.features.image_quality_status or "N/A")
        st.caption(
            f"aspect_ratio={iq.aspect_ratio:.3f} · formato={iq.file_format} · "
            f"tamaño={iq.file_size_bytes} bytes · corrupta={iq.is_corrupted}"
        )

    st.divider()

    # -----------------------------------------------------------------
    # 4. CONSISTENCIA TEXTO <-> IMAGEN
    # -----------------------------------------------------------------
    st.header("4. CONSISTENCIA TEXTO <-> IMAGEN")
    fv = result.features
    if nr is None:
        st.warning("No aplica: no hay narrativa.")
    elif not fv.visual_available:
        st.warning("No aplica: no hay evidencia visual disponible para comparar (ver seccion 2).")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Narrative top:** {fv.text_top_damage} — {_pct(fv.text_top_confidence)}")
        with col2:
            st.write(f"**Visual top:** {fv.visual_top_damage or '(sin deteccion)'} — {_pct(fv.visual_top_confidence)}")
        st.metric("Semantic agreement", f"{fv.semantic_agreement:.3f}" if fv.semantic_agreement is not None else "N/A")
        st.metric("Semantic mismatch", f"{fv.semantic_mismatch:.3f}" if fv.semantic_mismatch is not None else "N/A")

    st.caption(
        "Formula: distancia de Jensen-Shannon (log base 2, rango [0,1]) entre la "
        "distribucion narrativa normalizada y la distribucion visual normalizada "
        "sobre las 8 clases canonicas. IMPORTANTE: esto es comparacion de "
        "features (dos vectores de probabilidad). NO es un grafo de evidencia."
    )

    st.divider()

    # -----------------------------------------------------------------
    # 5. BASELINE B0
    # -----------------------------------------------------------------
    st.header("5. BASELINE B0")
    rt = result.rule_trace
    decision_color = {"SUPPORTED": "green", "SUSPICIOUS": "orange", "INSUFFICIENT": "gray"}[rt.decision.value]
    st.markdown(f"## Prediction: :{decision_color}[{rt.decision.value}]")

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Triggered rule:** `{rt.rule_id}`")
        st.write(f"**Reason:** {rt.description}")
    with col2:
        st.write(f"**Threshold:** {rt.threshold}")
        st.write(f"**Observed:** {rt.observed_value}")

    if selected_case is not None:
        match = "✅ coincide" if rt.decision.value == selected_case.expected_condition else "⚠️ NO coincide"
        st.caption(f"Condicion esperada del caso preparado: `{selected_case.expected_condition}` ({match})")

    st.caption(f"Corrida registrada en: `{log_path}`")

    st.divider()

    # -----------------------------------------------------------------
    # 6. LIMITACION DEL BASELINE
    # -----------------------------------------------------------------
    st.header("6. LIMITACION DEL BASELINE")
    st.warning(
        "El baseline compara outputs de modalidades mediante variables y "
        "reglas. No representa explicitamente relaciones de evidencia, "
        "procedencia ni propagacion de incertidumbre."
    )

    if tmp_file is not None:
        tmp_file.close()

else:
    st.caption(
        "Clases canonicas de danio: " + ", ".join(CANONICAL_DAMAGE_CLASSES)
    )
    st.caption(
        f"Umbral de mismatch actual (configs/baseline.yaml): "
        f"{load_rules_config().get('semantic_mismatch_threshold')}"
    )
