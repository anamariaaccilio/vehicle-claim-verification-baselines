# Vehicle Claim Verification Baselines

Fuente canónica del contrato experimental de la tesis «Grafos de evidencia multimodal conscientes de incertidumbre para la verificación robusta de reclamos de seguros vehiculares». Conserva el código original y establece el benchmark reproducible y sus métodos de referencia. Existe un primer benchmark reproducible de 127 reclamos experimentales sobre 24 imágenes reales. No es un dataset de reclamos de una aseguradora ni el benchmark C0–C10 completo; no hay resultados científicos de modelos.

| SYSTEM | DESCRIPTION | STATUS |
|---|---|---|
| B0 | Rules: features, reglas R01–R05 y pipeline ejecutables; umbrales sin calibrar | IMPLEMENTED |
| B1 | Text/NLI only: extractor NLI real; falta decisión text-only y evaluación | PARTIAL |
| B2 | Visual damage only: preparación YOLO, train/inference; sin checkpoint ni evaluación | PARTIAL |
| B3 | Forensic only: TruFor/base contienen solo docstrings; calidad de imagen no es forense | STUB |
| B4 | Concatenation + MLP: features existentes; MLP ausente y train_classifier es stub | PARTIAL |
| B5 | Calibrated late fusion | NOT IMPLEMENTED |
| B6 | DeepSets | NOT IMPLEMENTED |
| B7 | Discounted Belief Fusion | NOT IMPLEMENTED |
| B8 | Frozen multimodal LLM; condicionado a viabilidad y reproducibilidad | NOT IMPLEMENTED |

`IMPLEMENTED` no significa entrenado/evaluado en un benchmark real. Ver [auditoría inicial](MIGRATION_AUDIT.md).

El contrato vive en `src/schemas`: `ClaimRecord` es un alias compatible de `Claim`, `EvidencePacket` agrega las evidencias existentes (versión explícita 0.2.0), `SourceImage` representa filas del manifest. `configs/labels.yaml` es la fuente de taxonomía/mapping; las constantes Python se cargan desde ella. `DecisionLabel` conserva su enum público y un test verifica igualdad con YAML. No hay segunda definición en UAFEG.

El repositorio hermano `uafeg` consume este contrato por instalación editable y fija commit/hashes en `benchmark.lock.json`. Aquí no se implementan P1/P2, gates, modelos de grafos ni Claims Analyst Agent. Para B6 vs P1, P1 vs P2 y ablations se usarán idénticos manifest, splits, EvidencePackets, labels, métricas y test set.

Los splits se asignan por hash de `seed=42` + `source_image_id` (`src/data/split.py`). Todas las variantes de una fuente quedan en un solo split. `validation` es el nombre canónico (no `val`). El auditor rechaza IDs/splits ausentes y comprueba también claim/incident/vehicle/policy IDs solo cuando aparecen realmente.

```bash
python3.11 -m venv .venv
# En el entorno existente basta usar .venv/bin/python; no requiere activación.
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install --no-deps -e .
env -u PYTHONPATH OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 .venv/bin/python -m pytest -q
env -u PYTHONPATH .venv/bin/python scripts/check_splits.py --manifest tests/fixtures/split_manifest.jsonl --group-key source_image_id --split-key split
```

La fixture es sintética, no el benchmark. Las 24 imágenes locales originan 127 reclamos controlados versionados en `data/manifests/benchmark_v1/manifest.jsonl`. Ver [benchmark y reproducción](BENCHMARK_PROTOCOL.md), [dataset audit](DATASET_AUDIT.md) y [near-duplicates](NEAR_DUPLICATE_AUDIT.md). Ver [protocolo](EXPERIMENTAL_PROTOCOL.md) y [datos](data/README.md).

Por defecto se omiten 5 tests de integración con modelos; se conservan y pueden ejecutarse con `--run-model-tests` usando exclusivamente pesos ya cacheados. `tests/conftest.py` fuerza Hugging Face offline. CI usa Python 3.11, dependencias CPU y fixtures pequeñas: no descarga modelos/datasets ni entrena redes. No se ha ejecutado GitHub Actions desde esta migración local.

Los raw datasets, pesos, `.env`, `.venv`, caches y artefactos de demo no se versionan. La `.venv` existente se preserva tras el rename; sus antiguos scripts de activación/shebang pueden apuntar al nombre anterior, por eso se usa el ejecutable Python directamente. Para un entorno nuevo, créalo siguiendo los comandos anteriores. No se modificó el Python del sistema.

## Benchmark de reclamos v1

**Real vehicle-damage imagery + controlled/synthetic claim scenarios**, a partir de HITL v2 (CC0 según autor). C0: control compatible; C1: contradicción; C2: sustitución; C3: copy-move/splice; C4: inpainting/eliminación; C5: contradicción + manipulación; C6/C7: narrativa/imagen ausentes; C8: transformaciones benignas; C9: calidad insuficiente; C10: familia de manipulación OOD. Tabla canónica y estados en [BENCHMARK_PROTOCOL.md](BENCHMARK_PROTOCOL.md).

Implementados C0/C1/C6/C7 y C9 con gate de calidad; C8 parcial (JPEG). C2–C5/C10 pendientes. C0/C8 son SUPPORTED, no fraude; C6/C7/C9 son INSUFFICIENT. Splits por grupos de duplicados/near-duplicates antes de variantes: 17/4/3 fuentes, 89/22/16 claims. Narrativas deterministas derivadas de anotaciones; no datos personales inventados.

```bash
env -u PYTHONPATH .venv/bin/python scripts/build_claim_benchmark.py
env -u PYTHONPATH .venv/bin/python scripts/build_claim_benchmark.py --check --verify-images
```

El test set v1 está congelado. No usar labels/clases anotadas/condiciones/provenance como features. La muestra y las plantillas limitan la validez científica; ver shortcuts y limitaciones en el protocolo. EvidencePackets contienen referencias/texto reales, con especialistas null.
