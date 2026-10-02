# Contrato experimental y límites del milestone

## Fuentes canónicas

| Elemento | Fuente | Estado |
|---|---|---|
| ClaimRecord | src/schemas/claim.py::ClaimRecord (alias de Claim) | Compatible con API previa |
| EvidencePacket | src/schemas/packet.py | Nuevo contrato 0.1.0, evidencias opcionales tipadas |
| Labels y mapping | configs/labels.yaml; DecisionLabel verificado por test | Disponible |
| Manifest | src/data/manifest.py; SourceImage | IO JSONL y piloto real de imágenes disponibles; benchmark de reclamos NOT AVAILABLE YET |
| Splits | src/data/split.py; configs/baseline.yaml | Hash seed 42; 0.70/0.15/0.15; splits piloto persistidos, benchmark aún sin fijar |
| Predicción B0 | src/fusion/rules.py::RuleTrace / as_dict | Decisión y traza; no probabilidad calibrada |
| Esquema común de probabilidades | No existe | NOT AVAILABLE YET |
| C0–C10 | No hay especificación/generador completo | NOT AVAILABLE YET; no asignar significados nuevos por inferencia |
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

No se pueden comparar científicamente sistemas hasta completar estos artefactos. El lock del MVP usa null para manifest/splits ausentes y no convierte una fixture en benchmark real. La versión de schema 0.1.0 se introduce en esta migración; no se infiere de la versión de distribución.

## Evidencia de reproducibilidad

El tag pre-two-repo-split-2026-10-02 contiene el código anterior sin alteraciones. Las pruebas iniciales completas dieron 64 passed en Python 3.11.9 con NLI ya cacheado. El snapshot externo conserva hashes originales, índice y patches. `requirements-ci.txt` fija las dependencias directas de tests observadas; no es un lock completo de todas las dependencias transitivas. Una validación en entorno CI limpio sigue pendiente hasta ejecutar Actions.

## Avance de ingestión 2026-10-02

Se añadió un piloto real de HITL v2, documentado en docs/DATASET_DISCOVERY.md.
El manifest de 24 imágenes y sus splits sirven para verificar ingestión y
auditoría; no reemplazan el manifest/labels/packets del benchmark de reclamos
que sigue NOT AVAILABLE YET. El lector real valida el formato ann/img; el
adapter COCO previo no se usó.
