# Migration audit — estado previo a modificaciones de código

Fecha: 2026-10-02. Fuente: inspección local; PDF solo referencia, no autorización independiente.

## Git inicial

Ruta: `/home/ana/Documentos/tesis 2/uafeg-baseline`.
Branch `master`, sin commits (git log falla: does not have any commits yet), sin remotos.
Working tree con archivos A/AM y untracked. No existe historial que etiquetar aún.
Estado, índice y diffs originales conservados fuera de ambos repos en `.migration-snapshot-2026-10-02`.
No se modificó código para esta auditoría.

## Hallazgos reales

- Claim existe en src/schemas/claim.py; ClaimRecord y EvidencePacket NO existen.
- Evidencias tipadas, DecisionLabel, SourceImage y Split existen.
- Manifest JSONL implementado; data/manifests contiene solo .gitkeep. No dataset real ni splits persistidos.
- Split hash seed+source_image_id y test de variantes/leakage existentes. Omite splits None: mejorar fail-closed.
- claim_id existe en Claim y casos demo; incident_id/vehicle_id/policy_id no encontrados como campos.
- Taxonomía duplicada entre constantes Python y YAML, tests verifican igualdad; centralizar sin romper API.
- B0 IMPLEMENTED: reglas R01-R05 + feature vector + pipeline; sin evaluación científica.
- B1 PARTIAL: extractor NLI real; falta baseline text-only de decisión/evaluación.
- B2 PARTIAL: adaptación YOLO/entrenamiento/inferencia; no pesos ni baseline visual-only evaluado.
- B3 STUB: adaptador TruFor/base solo docstrings; calidad de imagen sí implementada y NO equivale a forense.
- B4 PARTIAL: features de concatenación existen; clasificador es docstring (LogisticRegression prevista), MLP ausente.
- B5-B8 NOT IMPLEMENTED. Calibración, métricas y stress slices solo docstrings.
- Demo y generador de variantes existen; NO constituyen benchmark C0-C10 completo.
- No CI, notebooks, GNN/GAT/GATv2, graph builder, gate o agente implementados.
- reliability solo campo opcional ForensicResult, no propagación.
- Python local .venv 3.11.9; PYTHONPATH externo ROS2 Python 3.10. Tests NLI cargan modelo real.
- .gitignore excluye raw/pesos/venv/caches; faltan reglas explícitas .env/secrets.
- Artefactos demo locales ignorados preservados; no incluirlos en commits.

## Mapping por archivo

| PATH | STATUS | KEEP / MOVE / MODIFY / REMOVE / UNKNOWN | DESTINATION | JUSTIFICATION |
|---|---|---|---|---|
| `.gitignore` | EXISTS; inspeccionado; ejecución pendiente | MODIFY | `vehicle-claim-verification-baselines/.gitignore` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `README.md` | EXISTS; inspeccionado; ejecución pendiente | MODIFY | `vehicle-claim-verification-baselines/README.md` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `artifacts/.gitkeep` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/artifacts/.gitkeep` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `configs/baseline.yaml` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/configs/baseline.yaml` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `configs/labels.yaml` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/configs/labels.yaml` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `data/README.md` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/data/README.md` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `data/manifests/.gitkeep` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/data/manifests/.gitkeep` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `data/processed/.gitkeep` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/data/processed/.gitkeep` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `data/raw/.gitkeep` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/data/raw/.gitkeep` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `demo/app.py` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/demo/app.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `demo/cases/assets/.gitkeep` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/demo/cases/assets/.gitkeep` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `demo/cases/cases.yaml` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/demo/cases/cases.yaml` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `demo/cases_loader.py` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/demo/cases_loader.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `demo/run_logger.py` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/demo/run_logger.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `pyproject.toml` | EXISTS; inspeccionado; ejecución pendiente | MODIFY | `vehicle-claim-verification-baselines/pyproject.toml` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `requirements.txt` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/requirements.txt` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `scripts/.gitkeep` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/scripts/.gitkeep` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `scripts/create_demo_variants.py` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/scripts/create_demo_variants.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `src/__init__.py` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/src/__init__.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `src/calibration/__init__.py` | STUB (solo docstring o vacío) | KEEP | `vehicle-claim-verification-baselines/src/calibration/__init__.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `src/calibration/calibrate.py` | STUB (solo docstring o vacío) | KEEP | `vehicle-claim-verification-baselines/src/calibration/calibrate.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `src/damage/__init__.py` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/src/damage/__init__.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `src/damage/inference.py` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/src/damage/inference.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `src/damage/train.py` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/src/damage/train.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `src/data/__init__.py` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/src/data/__init__.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `src/data/hitl_adapter.py` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/src/data/hitl_adapter.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `src/data/manifest.py` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/src/data/manifest.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `src/data/split.py` | EXISTS; inspeccionado; ejecución pendiente | MODIFY | `vehicle-claim-verification-baselines/src/data/split.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `src/evaluation/__init__.py` | STUB (solo docstring o vacío) | KEEP | `vehicle-claim-verification-baselines/src/evaluation/__init__.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `src/evaluation/metrics.py` | STUB (solo docstring o vacío) | KEEP | `vehicle-claim-verification-baselines/src/evaluation/metrics.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `src/evaluation/stress_slices.py` | STUB (solo docstring o vacío) | KEEP | `vehicle-claim-verification-baselines/src/evaluation/stress_slices.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `src/forensic/__init__.py` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/src/forensic/__init__.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `src/forensic/base.py` | STUB (solo docstring o vacío) | KEEP | `vehicle-claim-verification-baselines/src/forensic/base.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `src/forensic/image_quality.py` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/src/forensic/image_quality.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `src/forensic/trufor_adapter.py` | STUB (solo docstring o vacío) | KEEP | `vehicle-claim-verification-baselines/src/forensic/trufor_adapter.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `src/fusion/__init__.py` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/src/fusion/__init__.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `src/fusion/features.py` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/src/fusion/features.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `src/fusion/inference.py` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/src/fusion/inference.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `src/fusion/rules.py` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/src/fusion/rules.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `src/fusion/train_classifier.py` | STUB (solo docstring o vacío) | KEEP | `vehicle-claim-verification-baselines/src/fusion/train_classifier.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `src/narrative/__init__.py` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/src/narrative/__init__.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `src/narrative/nli_extractor.py` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/src/narrative/nli_extractor.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `src/schemas/__init__.py` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/src/schemas/__init__.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `src/schemas/claim.py` | EXISTS; inspeccionado; ejecución pendiente | MODIFY | `vehicle-claim-verification-baselines/src/schemas/claim.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `src/schemas/evidence.py` | EXISTS; inspeccionado; ejecución pendiente | MODIFY | `vehicle-claim-verification-baselines/src/schemas/evidence.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `tests/__init__.py` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/tests/__init__.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `tests/test_cases.py` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/tests/test_cases.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `tests/test_damage.py` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/tests/test_damage.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `tests/test_demo.py` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/tests/test_demo.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `tests/test_fusion.py` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/tests/test_fusion.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `tests/test_image_quality.py` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/tests/test_image_quality.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `tests/test_manifest.py` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/tests/test_manifest.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `tests/test_narrative.py` | EXISTS; inspeccionado; ejecución pendiente | MODIFY | `vehicle-claim-verification-baselines/tests/test_narrative.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `tests/test_schemas.py` | EXISTS; inspeccionado; ejecución pendiente | KEEP | `vehicle-claim-verification-baselines/tests/test_schemas.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |
| `tests/test_split.py` | EXISTS; inspeccionado; ejecución pendiente | MODIFY | `vehicle-claim-verification-baselines/tests/test_split.py` | Conservar implementación/fixture/configuración existente; no pertenece a P1/P2. |

## Árbol original versionable real

```text
.gitignore
README.md
artifacts/.gitkeep
configs/baseline.yaml
configs/labels.yaml
data/README.md
data/manifests/.gitkeep
data/processed/.gitkeep
data/raw/.gitkeep
demo/app.py
demo/cases/assets/.gitkeep
demo/cases/cases.yaml
demo/cases_loader.py
demo/run_logger.py
pyproject.toml
requirements.txt
scripts/.gitkeep
scripts/create_demo_variants.py
src/__init__.py
src/calibration/__init__.py
src/calibration/calibrate.py
src/damage/__init__.py
src/damage/inference.py
src/damage/train.py
src/data/__init__.py
src/data/hitl_adapter.py
src/data/manifest.py
src/data/split.py
src/evaluation/__init__.py
src/evaluation/metrics.py
src/evaluation/stress_slices.py
src/forensic/__init__.py
src/forensic/base.py
src/forensic/image_quality.py
src/forensic/trufor_adapter.py
src/fusion/__init__.py
src/fusion/features.py
src/fusion/inference.py
src/fusion/rules.py
src/fusion/train_classifier.py
src/narrative/__init__.py
src/narrative/nli_extractor.py
src/schemas/__init__.py
src/schemas/claim.py
src/schemas/evidence.py
tests/__init__.py
tests/test_cases.py
tests/test_damage.py
tests/test_demo.py
tests/test_fusion.py
tests/test_image_quality.py
tests/test_manifest.py
tests/test_narrative.py
tests/test_schemas.py
tests/test_split.py
```

## Baseline ejecutado antes de cambios

Python 3.11.9 existente. Primer intento: error de arranque por plugin ROS2/lark, sin colección. Ejecución aislada `env -u PYTHONPATH HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 .venv/bin/python -m pytest -q`: **64 passed, 0 failed, 0 skipped, 0 errors**, 1 FutureWarning, 40.90s. Modelo NLI ya en caché; no se descargaron modelos. Logs completos en snapshot externo.
