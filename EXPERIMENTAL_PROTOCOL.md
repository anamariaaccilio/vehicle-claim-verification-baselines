# Contrato experimental y límites del milestone

## Fuentes canónicas

| Elemento | Fuente | Estado |
|---|---|---|
| ClaimRecord | src/schemas/claim.py::ClaimRecord (alias de Claim) | Compatible con API previa |
| EvidencePacket | src/schemas/packet.py | Contrato 0.2.0 con ClaimRecord/provenance extendidos y evidencias opcionales tipadas |
| Labels y mapping | configs/labels.yaml; DecisionLabel verificado por test | Disponible |
| Manifest | src/data/manifest.py; SourceImage | IO de fuentes + manifest real de 127 reclamos controlados en data/manifests/benchmark_v1 |
| Splits | src/data/split.py; configs/baseline.yaml | Grupos exactos/dHash antes de hash seed 42; splits v1 congelados |
| Predicción B0 | src/fusion/rules.py::RuleTrace / as_dict | Decisión y traza; no probabilidad calibrada |
| Esquema común de probabilidades | No existe | NOT AVAILABLE YET |
| C0–C10 | configs/benchmark_conditions.yaml, tabla autorizada por usuaria | Generación parcial; ver BENCHMARK_PROTOCOL.md |
| Narrativas | configs/labels.yaml::nli_hypotheses; demo/cases/cases.yaml | Hipótesis y casos demo, no benchmark etiquetado |
| Métricas | src/evaluation/metrics.py, stress_slices.py | STUB, sin resultados |
| Calibration | src/calibration/calibrate.py | STUB |

`None` en EvidencePacket significa evidencia ausente. Detecciones vacías con VisualEvidence presente indican ejecución sin detecciones. ForensicResult(available=False) no constituye evidencia forense disponible. El packet conserva claim/ground truth para trazabilidad; labels, metadata de condición e identificadores NO deben convertirse en features de modelo. UAFEG MVP excluye estos campos de los atributos del grafo.

## Protocolo previo a cualquier experimento científico

1. Validar el adapter HITL contra la exportación real. Riesgo preexistente: fusiona anotaciones de variantes bajo el primer path; confirmar correspondencia geométrica antes de usarlo científicamente.
2. Crear/versionar de forma controlada el manifest y los splits, sin imágenes raw; guardar SHA256. La exclusión actual de data/manifests es conservadora y requiere decidir explícitamente qué manifest publicar.
3. Auditar `source_image_id`, y `claim_id` cuando esté presente. El schema Claim tiene claim_id; no existen incident_id/vehicle_id/policy_id en el contrato actual. La fixture nueva incluye claim_id sintético para probar su auditoría. Auditar duplicados visuales y shortcuts de narrativa/condición antes de experimentar.
4. Fijar las condiciones C0–C10 y el generador; los casos de demo y variantes JPEG/blur no equivalen al benchmark completo.
5. Congelar EvidencePackets (mismos extractores, revisiones, preprocessing) y su hash. Mantener labels fuera de features.
6. Entrenar solo en train; selección, thresholds y calibración solo en validation. Abrir test únicamente para evaluación final, igual para B0–B8/P1/P2/ablations.
7. Implementar evaluación compartida: macro-F1, precision/recall, matriz de confusión; PR-AUC/AUROC de SUSPICIOUS cuando haya soporte; Brier/NLL/ECE solo para probabilidades válidas. Declarar binning y casos indefinidos antes de comparar. Selective prediction requiere curva riesgo/cobertura con umbral fijado en validation. Estas métricas aún NO están implementadas.

Existe un primer benchmark de reclamos controlados versionado; no equivale a completar C0–C10 ni a validar científicamente UAFEG. Schema 0.2.0 explícito. El lock registra artefactos reales del benchmark, distintos del antiguo manifest de fuentes del piloto.

## Evidencia de reproducibilidad

El tag pre-two-repo-split-2026-10-02 contiene el código anterior sin alteraciones. Las pruebas iniciales completas dieron 64 passed en Python 3.11.9 con NLI ya cacheado. El snapshot externo conserva hashes originales, índice y patches. `requirements-ci.txt` fija las dependencias directas de tests observadas; no es un lock completo de todas las dependencias transitivas. Una validación en entorno CI limpio sigue pendiente hasta ejecutar Actions.

## Avance de ingestión 2026-10-02

Se añadió un piloto real de HITL v2, documentado en docs/DATASET_DISCOVERY.md.
El manifest de 24 imágenes y sus splits sirven para verificar ingestión y
auditoría; no reemplazan el manifest/labels/packets del benchmark de reclamos
que sigue NOT AVAILABLE YET. El lector real valida el formato ann/img; el
adapter COCO previo no se usó.

## Estado actual de benchmark

La nota de ingestión anterior describe el milestone previo. Ahora existe v1 de reclamos controlados con manifest/splits/packets reales, schema 0.2.0, generador y auditoría. Ver BENCHMARK_PROTOCOL.md para protocolo vigente, tabla canónica C0–C10, campos de ClaimRecord, reproducción y límites científicos. El schema probabilístico y las métricas de modelos permanecen pendientes; esta fase no entrenó sistemas.
