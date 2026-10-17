# Guía técnica — Vehicle Claim Verification Baselines

**Estado científico: READY_FOR_MODELS = NO.** V2 permanece congelado; v3 es un
candidato reproducible de 9.275 reclamos / 807 fuentes aceptadas del conjunto HITL
completo de daño. Falta adjudicación humana y resolver la compatibilidad semántica
frecuente de C2. Pasar tests de ingeniería no equivale a validar las etiquetas.

Revisión local: [galería v2](../benchmark_v2_qa.html),
[galería v3 completa](../benchmark_v3_qa.html) y [muestra v3](../benchmark_v3_qa_sample.html).
Cada galería identifica el hash de sus registros; la exportación de revisión no
cambia labels. Los bytes de imágenes permanecen fuera de Git.

Auditorías: [escala HITL](../DATASET_SCALE_AUDIT.md), [C2 v2](../C2_SEMANTIC_AUDIT.md), [C2 v3](../C2_SEMANTIC_AUDIT_V3.md),
[C3](../C3_FORENSIC_AUDIT.md), [C4](../C4_INPAINT_AUDIT.md), [C5](../C5_COMBINED_AUDIT.md),
[C8](../C8_BENIGN_CONTROLS_AUDIT.md), [C9 v3](../C9_DEGRADATION_AUDIT_V3.md),
[C10](../C10_OOD_AUDIT.md), [narrativas](../NARRATIVE_SHORTCUT_AUDIT.md),
[duplicados](../NEAR_DUPLICATE_FULL_AUDIT.md), [unidad estadística](../STATISTICAL_EVALUATION_PROTOCOL.md).

## Reproducir la fase de QA y el candidato v3

```bash
env -u PYTHONPATH .venv/bin/python scripts/fetch_hitl_full.py
env -u PYTHONPATH .venv/bin/python scripts/build_benchmark_v3.py
env -u PYTHONPATH .venv/bin/python scripts/build_benchmark_v3.py --check --verify-images
env -u PYTHONPATH .venv/bin/python scripts/audit_benchmark_v2.py
env -u PYTHONPATH .venv/bin/python scripts/summarize_benchmark_qa.py
env -u PYTHONPATH .venv/bin/python scripts/audit_benchmark_v3_pixels.py
env -u PYTHONPATH OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/python -m pytest -q
```

La QA de v2 requiere también el piloto en su ruta histórica. En una instalación
nueva se reproduce con `scripts/fetch_hitl_pilot.py --receipt data/hitl_pilot_receipt.json
--output data/raw/hitl_pilot_v2` y `scripts/build_benchmark_v2.py` antes de la auditoría.
Los tests ordinarios y `--check` sin imágenes usan artefactos de texto; no descargan raw.

V3 usa la taxonomía/etiquetas canónicas de `configs/benchmark_conditions_v2.yaml`;
las operaciones adicionales están en `configs/benchmark_v3.yaml`: C8_JPEG,
C8_RESIZE (1.25×), C8_CROP (hasta5% de margen sin eliminar daño anotado).
Las 538 exclusiones C9 conservan el umbral<=1.0; no se fuerzan. C10 tiene129 casos,
solo test. Las narrativas emparejadas conservan el mismo target y estilo entre
control/contradicción; las variaciones neutrales no añaden hechos sobre el vehículo.
La revisión no cambia automáticamente labels C2.

Unidad de evaluación: fuente/grupo, no variante individual. C2 requiere considerar
además dependencia con donantes. Anotaciones, condiciones, labels, IDs, paths y
parámetros son metadatos de auditoría y no deben entrar como features de modelos.
Las anotaciones referenciadas describen la fuente original; C2 referencia también
las del donante, y C8 registra la transformación geométrica. No son outputs de especialistas.

UAFEG mantiene el snapshot v2 en su lock mientras v3 sigue pendiente de QA científica.
No se entrenaron modelos ni se implementaron P1/P2 en esta fase.

## Estado de sistemas y versiones anteriores

Fuente canónica del contrato experimental de la tesis «Grafos de evidencia multimodal conscientes de incertidumbre para la verificación robusta de reclamos de seguros vehiculares». Conserva el código original y establece el benchmark reproducible y sus métodos de referencia. Existe un benchmark reproducible de 226 reclamos experimentales sobre 24 imágenes reales, con cobertura operativa C0–C10. No es un dataset de reclamos de una aseguradora ni una validación científica final; no hay resultados de modelos.

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

`IMPLEMENTED` no significa entrenado/evaluado en un benchmark real. Ver [auditoría inicial](../MIGRATION_AUDIT.md).

El contrato vive en `src/schemas`: `ClaimRecord` es un alias compatible de `Claim`, `EvidencePacket` agrega las evidencias existentes (versión explícita 0.3.0, compatible con registros 0.2.0), `SourceImage` representa filas del manifest. `configs/labels.yaml` es la fuente de taxonomía/mapping; las constantes Python se cargan desde ella. `DecisionLabel` conserva su enum público y un test verifica igualdad con YAML. No hay segunda definición en UAFEG.

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

La fixture es sintética, no el benchmark. Las 24 imágenes locales originan 226 reclamos controlados versionados en `data/manifests/benchmark_v2/manifest.jsonl`; la versión v1 anterior sigue congelada. Ver [benchmark y reproducción vigente](../BENCHMARK_V2_PROTOCOL.md), [dataset audit](../DATASET_AUDIT.md) y [near-duplicates](../NEAR_DUPLICATE_AUDIT.md). Ver [protocolo](../EXPERIMENTAL_PROTOCOL.md) y [datos](../data/README.md).

Por defecto se omiten 5 tests de integración con modelos; se conservan y pueden ejecutarse con `--run-model-tests` usando exclusivamente pesos ya cacheados. `tests/conftest.py` fuerza Hugging Face offline. CI usa Python 3.11, dependencias CPU y fixtures pequeñas: no descarga modelos/datasets ni entrena redes. No se ha ejecutado GitHub Actions desde esta migración local.

Los raw datasets, pesos, `.env`, `.venv`, caches y artefactos de demo no se versionan. La `.venv` existente se preserva tras el rename; sus antiguos scripts de activación/shebang pueden apuntar al nombre anterior, por eso se usa el ejecutable Python directamente. Para un entorno nuevo, créalo siguiendo los comandos anteriores. No se modificó el Python del sistema.

## Benchmark de reclamos v1

**Real vehicle-damage imagery + controlled/synthetic claim scenarios**, a partir de HITL v2 (CC0 según autor). C0: control compatible; C1: contradicción; C2: sustitución; C3: copy-move/splice; C4: inpainting/eliminación; C5: contradicción + manipulación; C6/C7: narrativa/imagen ausentes; C8: transformaciones benignas; C9: calidad insuficiente; C10: familia de manipulación OOD. Tabla canónica y estados en [BENCHMARK_PROTOCOL.md](../BENCHMARK_PROTOCOL.md).

En la versión histórica v1: implementados C0/C1/C6/C7 y C9 con gate de calidad; C8 parcial (JPEG); C2–C5/C10 pendientes entonces. La versión v2 descrita abajo completa la cobertura operativa. C0/C8 son SUPPORTED, no fraude; C6/C7/C9 son INSUFFICIENT. Splits por grupos de duplicados/near-duplicates antes de variantes: 17/4/3 fuentes, 89/22/16 claims. Narrativas deterministas derivadas de anotaciones; no datos personales inventados.

```bash
env -u PYTHONPATH .venv/bin/python scripts/build_claim_benchmark.py
env -u PYTHONPATH .venv/bin/python scripts/build_claim_benchmark.py --check --verify-images
```

El test set v1 está congelado. No usar labels/clases anotadas/condiciones/provenance como features. La muestra y las plantillas limitan la validez científica; ver shortcuts y limitaciones en el protocolo. EvidencePackets contienen referencias/texto reales, con especialistas null.

## Benchmark completo C0–C10 (v0.2.0)

La versión histórica v2 está en `data/manifests/benchmark_v2/`; v0.1.0 se conserva
sin cambios en `benchmark_v1/`. Son imágenes reales de daño vehicular con
reclamos experimentales/sintéticos, no expedientes de una aseguradora.
La taxonomía canónica es la tabla autorizada por el usuario; el `.tex` no estuvo disponible.

El generador produce 226 reclamos a partir de 24 imágenes: 24 por condición
C0–C8, 7 C9 y 3 C10. C9 conserva su criterio fijo de insuficiencia; 17 intentos
que no lo cumplen se registran como exclusiones. C10 se reserva exclusivamente
para test. Los splits de fuentes de v1 se mantienen exactamente (17/4/3);
los reclamos se distribuyen 157/38/31 en train/validation/test.

| Condición | Operación implementada | Etiqueta esperada |
|---|---|---|
| C0 | Narrativa compatible, imagen original | SUPPORTED |
| C1 | Negación de un daño anotado | SUSPICIOUS |
| C2 | Sustitución por otra fuente/grupo del mismo split | SUSPICIOUS |
| C3 | Copy-move localizado 24×24 | SUSPICIOUS |
| C4 | Inpainting Telea de un polígono de daño | SUSPICIOUS |
| C5 | C3 + negación de daño original conservado | SUSPICIOUS |
| C6 | Narrativa ausente | INSUFFICIENT |
| C7 | Imagen ausente | INSUFFICIENT |
| C8 | JPEG95 benigno con PSNR ≥35 dB | SUPPORTED |
| C9 | Desenfoque con criterio fijo de insuficiencia | INSUFFICIENT |
| C10 | Inversión RGB localizada, familia reservada para test | OOD |

Las once condiciones tienen generador y registros reales. Esto no implica que
se hayan implementado todas las alternativas de cada condición: C3 usa copy-move,
no splice; C8 usa JPEG, no resize/crop. C4 verifica inpainting y localización,
no desaparición convincente del daño. C2 registra sustitución conocida, que
puede no ser identificable solo a partir de imagen y texto. C10 es OOD respecto
a las familias del split de entrenamiento del benchmark; no hay modelos entrenados.

```bash
env -u PYTHONPATH .venv/bin/python scripts/build_benchmark_v2.py
env -u PYTHONPATH .venv/bin/python scripts/build_benchmark_v2.py --check --verify-images
env -u PYTHONPATH .venv/bin/python scripts/check_splits.py --manifest data/manifests/benchmark_v2/manifest.jsonl --group-key source_image_id --split-key split
env -u PYTHONPATH HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/python -m pytest -q
```

`--check` sin `--verify-images` valida contratos/artefactos sin raw en CI.
La regeneración exige el piloto local ya adquirido y rechaza sobrescrituras
incompatibles. Las imágenes y máscaras derivadas permanecen ignoradas por Git.
El contrato 0.3.0 acepta los registros 0.2.0 existentes y permite OOD únicamente
en C10/test; `DecisionLabel` sigue teniendo tres clases.

Véase `BENCHMARK_V2_PROTOCOL.md` para límites científicos, trazabilidad y revisión.

## Demo visual de avance

Ejecutar `./run_demo.sh` y abrir http://127.0.0.1:8765/demo para explorar la demo local. Muestra artefactos reales del benchmark v3, auditorías, contratos y el grafo MVP sin entrenamiento ni predicciones. Ver [instrucciones](../demo/benchmark/README.md) y [reporte](../DEMO_BUILD_REPORT.md). READY_FOR_MODELS sigue siendo NO.
