# Revisión documental para simplificación de la demo

Alcance: Markdown, HTML, PDF y TXT del proyecto en ambos repositorios, incluidos archivos locales. Se excluyen dependencias de `.venv`, metadatos Git y caches. Los guiones/PDF de la carpeta padre están fuera de estos repositorios y permanecen intactos.

A = científico/técnico, conservar. B = presentación auxiliar: eliminar si no tiene dependencia funcional o científica; una referencia editorial no obliga a conservarla. C = ambiguo o generado por herramientas, no borrar.

| Repositorio / archivo | Clase | Decisión |
|---|---|---|
| vehicle-claim-verification-baselines/requirements.txt | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: === FASE 1: repo, schemas, dataset manifest, tests ===. |
| vehicle-claim-verification-baselines/C9_DEGRADATION_AUDIT.md | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: C9 — criterio original preservado. |
| vehicle-claim-verification-baselines/BENCHMARK_V2_PROTOCOL.md | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: Benchmark v0.2.0: cobertura operativa completa C0–C10. |
| vehicle-claim-verification-baselines/DATASET_AUDIT.md | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: DATASET AUDIT — HITL local, 2026-10-02. |
| vehicle-claim-verification-baselines/STATISTICAL_EVALUATION_PROTOCOL.md | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: Unidad estadística y evaluación futura. |
| vehicle-claim-verification-baselines/C10_OOD_AUDIT.md | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: C10 — OOD procedimental. |
| vehicle-claim-verification-baselines/benchmark_v3_qa_sample.html | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: Benchmark — QA humana local. |
| vehicle-claim-verification-baselines/BENCHMARK_PROTOCOL.md | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: Benchmark v1: reclamos controlados sobre imágenes reales. |
| vehicle-claim-verification-baselines/NEAR_DUPLICATE_FULL_AUDIT.md | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: Full-source duplicate / near-duplicate audit. |
| vehicle-claim-verification-baselines/C2_SEMANTIC_AUDIT.md | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: C2 semantic audit — v2. |
| vehicle-claim-verification-baselines/benchmark_v2_qa.html | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: Benchmark — QA humana local. |
| vehicle-claim-verification-baselines/DEMO_BUILD_REPORT.md | C | Mezcla presentación y evidencia de validación; conservar por trazabilidad. Contenido: DEMO BUILD REPORT. |
| vehicle-claim-verification-baselines/NEAR_DUPLICATE_AUDIT.md | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: NEAR DUPLICATE AUDIT — benchmark v1. |
| vehicle-claim-verification-baselines/NARRATIVE_SHORTCUT_AUDIT.md | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: Narrative shortcut audit — v2 original. |
| vehicle-claim-verification-baselines/C9_DEGRADATION_AUDIT_V3.md | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: C9 — v3, mismo criterio. |
| vehicle-claim-verification-baselines/DATASET_SCALE_AUDIT.md | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: HITL full-source scale audit. |
| vehicle-claim-verification-baselines/NARRATIVE_SHORTCUT_AUDIT_V3.md | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: Narrative shortcut audit — v3 candidate. |
| vehicle-claim-verification-baselines/C4_INPAINT_AUDIT.md | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: C4 audit — v2. |
| vehicle-claim-verification-baselines/C2_SEMANTIC_AUDIT_V3.md | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: C2 semantic audit — v3 candidate. |
| vehicle-claim-verification-baselines/C4_INPAINT_AUDIT_V3.md | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: C4 pixel audit — v3. |
| vehicle-claim-verification-baselines/EXPERIMENTAL_PROTOCOL.md | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: Contrato experimental y límites del milestone. |
| vehicle-claim-verification-baselines/requirements-ci.txt | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: Lightweight test surface; torch CPU installed separately by CI.. |
| vehicle-claim-verification-baselines/C8_BENIGN_CONTROLS_AUDIT.md | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: C8 benign controls — v3 candidate. |
| vehicle-claim-verification-baselines/C5_COMBINED_AUDIT.md | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: C5 audit — v2. |
| vehicle-claim-verification-baselines/benchmark_v3_qa.html | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: Benchmark — QA humana local. |
| vehicle-claim-verification-baselines/MIGRATION_AUDIT.md | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: Migration audit — estado previo a modificaciones de código. |
| vehicle-claim-verification-baselines/C5_COMBINED_AUDIT_V3.md | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: C5 pixel audit — v3. |
| vehicle-claim-verification-baselines/README.md | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: UAFEG. |
| vehicle-claim-verification-baselines/C3_FORENSIC_AUDIT_V3.md | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: C3 pixel audit — v3. |
| vehicle-claim-verification-baselines/C3_FORENSIC_AUDIT.md | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: C3 audit — v2. |
| vehicle-claim-verification-baselines/uafeg_baseline.egg-info/dependency_links.txt | C | Metadatos de instalación; preservados, no documentación descartable.  |
| vehicle-claim-verification-baselines/uafeg_baseline.egg-info/SOURCES.txt | C | Metadatos de instalación; preservados, no documentación descartable.  |
| vehicle-claim-verification-baselines/uafeg_baseline.egg-info/top_level.txt | C | Metadatos de instalación; preservados, no documentación descartable.  |
| vehicle-claim-verification-baselines/data/README.md | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: Datos. |
| vehicle-claim-verification-baselines/vehicle_claim_verification_baselines.egg-info/dependency_links.txt | C | Metadatos de instalación; preservados, no documentación descartable.  |
| vehicle-claim-verification-baselines/vehicle_claim_verification_baselines.egg-info/SOURCES.txt | C | Metadatos de instalación; preservados, no documentación descartable.  |
| vehicle-claim-verification-baselines/vehicle_claim_verification_baselines.egg-info/requires.txt | C | Metadatos de instalación; preservados, no documentación descartable.  |
| vehicle-claim-verification-baselines/vehicle_claim_verification_baselines.egg-info/top_level.txt | C | Metadatos de instalación; preservados, no documentación descartable.  |
| vehicle-claim-verification-baselines/docs/DATASET_DISCOVERY.md | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: Fuentes de datos y piloto de integración — 2026-10-02. |
| vehicle-claim-verification-baselines/demo/benchmark/index.html | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: UAFEG · Benchmark Demo. |
| vehicle-claim-verification-baselines/demo/benchmark/README.md | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: UAFEG Benchmark Demo. |
| vehicle-claim-verification-baselines/demo/screenshots/README.md | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: Capturas de la demo. |
| uafeg/requirements.txt | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: Run from this repository; install the canonical sibling explicitly.. |
| uafeg/README.md | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: UAFEG. |
| uafeg/src/uafeg.egg-info/dependency_links.txt | C | Metadatos de instalación; preservados, no documentación descartable.  |
| uafeg/src/uafeg.egg-info/SOURCES.txt | C | Metadatos de instalación; preservados, no documentación descartable.  |
| uafeg/src/uafeg.egg-info/requires.txt | C | Metadatos de instalación; preservados, no documentación descartable.  |
| uafeg/src/uafeg.egg-info/top_level.txt | C | Metadatos de instalación; preservados, no documentación descartable.  |
| uafeg/configs/ablations/README.md | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: Ablations previstas. |
| uafeg/experiments/README.md | A | Documentación técnica, auditoría, recurso de interfaz o requisito de ejecución; conservar. Contenido: Próximo experimento, pendiente de autorización. |

## Reorganización sin pérdida

`README.md` se simplificó. Su contenido técnico anterior queda en `docs/TECHNICAL_GUIDE.md`, con enlaces relativos corregidos. Se conservan la historia, comandos y referencias de reproducción. El reporte final de QA de la carpeta padre tampoco se modifica.

No se encontraron archivos GUION_PRESENTACION* o GUION_COMPLETO* dentro de los repositorios. No se borran archivos externos ni documentos solo por antigüedad.
