# Vehicle Claim Verification Baselines

Fuente canónica del contrato experimental de la tesis «Grafos de evidencia multimodal conscientes de incertidumbre para la verificación robusta de reclamos de seguros vehiculares». Conserva el código original y establece el benchmark reproducible y sus métodos de referencia. El benchmark completo todavía no está generado; no hay resultados científicos reportados.

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

El contrato vive en `src/schemas`: `ClaimRecord` es un alias compatible de `Claim`, `EvidencePacket` agrega las evidencias existentes (versión nueva explícita 0.1.0), `SourceImage` representa filas del manifest. `configs/labels.yaml` es la fuente de taxonomía/mapping; las constantes Python se cargan desde ella. `DecisionLabel` conserva su enum público y un test verifica igualdad con YAML. No hay segunda definición en UAFEG.

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

La fixture es sintética, no el benchmark. `data/manifests` solo contiene `.gitkeep`: el audit de dataset real está pendiente. Ver [protocolo](EXPERIMENTAL_PROTOCOL.md) y [datos](data/README.md).

Por defecto se omiten 5 tests de integración con modelos; se conservan y pueden ejecutarse con `--run-model-tests` usando exclusivamente pesos ya cacheados. `tests/conftest.py` fuerza Hugging Face offline. CI usa Python 3.11, dependencias CPU y fixtures pequeñas: no descarga modelos/datasets ni entrena redes. No se ha ejecutado GitHub Actions desde esta migración local.

Los raw datasets, pesos, `.env`, `.venv`, caches y artefactos de demo no se versionan. La `.venv` existente se preserva tras el rename; sus antiguos scripts de activación/shebang pueden apuntar al nombre anterior, por eso se usa el ejecutable Python directamente. Para un entorno nuevo, créalo siguiendo los comandos anteriores. No se modificó el Python del sistema.
