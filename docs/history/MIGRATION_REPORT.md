# Reporte de migración local UAFEG — 2026-10-02

La separación local y el MVP de grafo están validados. **La seguridad del split del dataset real sigue pendiente porque no existe un manifest real.** No se declara terminado el benchmark científico ni se reportan resultados de modelos.

Repositorios hermanos:
- `vehicle-claim-verification-baselines/` (Repo A)
- `uafeg/` (Repo B)

No hay tercer repositorio. `.migration-snapshot-2026-10-02/` es una carpeta de respaldo/evidencia sin `.git`, no un proyecto benchmark. Este reporte también permanece fuera de ambos repos para no modificar el commit ya fijado por el lock.

## A. Estado inicial encontrado

Ruta original: `/home/ana/Documentos/tesis 2/uafeg-baseline`.
`git branch --show-current`: master. `git remote -v`: vacío.
`git log --oneline -10`: falló porque no existía ningún commit.
`git rev-parse --show-toplevel`: ruta original anterior.
Había archivos staged, modificaciones adicionales y archivos untracked.

Se inspeccionó el código antes de generar `MIGRATION_AUDIT.md`; no se tomó el README como evidencia de implementación. El PDF se trató como referencia documental, no como autorización para publicar o realizar acciones adicionales.

Se guardaron índice original, diffs binarios, estado, árbol y SHA256 fuera de los repos. Después de pasar los tests se creó el primer commit con los cambios originales completos. Solo cuando el árbol quedó limpio se creó el tag `pre-two-repo-split-2026-10-02`, y después la rama `migration/two-repositories`. No se podía etiquetar el estado inicial sin commit. Se verificaron los 55 archivos originales byte por byte contra ese checkpoint. El índice previo a la consolidación se conserva en el snapshot.

Python existente: 3.11.9, `.venv`; PYTHONPATH apuntaba a ROS2 Python 3.10. No se modificó el sistema.

Estado inicial exacto:

```text
A  .gitignore
A  README.md
A  artifacts/.gitkeep
AM configs/baseline.yaml
AM configs/labels.yaml
A  data/README.md
A  data/manifests/.gitkeep
A  data/processed/.gitkeep
A  data/raw/.gitkeep
AM demo/app.py
A  pyproject.toml
A  requirements.txt
A  scripts/.gitkeep
A  src/__init__.py
A  src/calibration/__init__.py
A  src/calibration/calibrate.py
A  src/damage/__init__.py
AM src/damage/inference.py
AM src/damage/train.py
A  src/data/__init__.py
A  src/data/hitl_adapter.py
A  src/data/manifest.py
A  src/data/split.py
A  src/evaluation/__init__.py
A  src/evaluation/metrics.py
A  src/evaluation/stress_slices.py
A  src/forensic/__init__.py
A  src/forensic/base.py
AM src/forensic/image_quality.py
A  src/forensic/trufor_adapter.py
A  src/fusion/__init__.py
AM src/fusion/features.py
AM src/fusion/inference.py
AM src/fusion/rules.py
A  src/fusion/train_classifier.py
A  src/narrative/__init__.py
AM src/narrative/nli_extractor.py
A  src/schemas/__init__.py
A  src/schemas/claim.py
A  src/schemas/evidence.py
A  tests/__init__.py
A  tests/test_manifest.py
A  tests/test_schemas.py
A  tests/test_split.py
?? demo/cases/
?? demo/cases_loader.py
?? demo/run_logger.py
?? scripts/create_demo_variants.py
?? tests/test_cases.py
?? tests/test_damage.py
?? tests/test_demo.py
?? tests/test_fusion.py
?? tests/test_image_quality.py
?? tests/test_narrative.py
```

## B. Árbol original real

Inventario de archivos fuente/configuración versionables antes de la migración; excluye `.git`, `.venv`, caches y metadata editable generada. No había raw datasets ni weights locales del proyecto. NLI estaba disponible en la caché externa, no se versionó ni descargó.

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

Existían además tres logs ignorados en `artifacts/demo_runs/` (20260918T161300555381Z.json, 20260918T161403417606Z.json, 20260918T161427270248Z.json), conservados. Nuevas ejecuciones de la demo pueden generar más logs ignorados. No son fixtures ni resultados científicos.

## C. Qué estaba realmente implementado

- `Claim`, `SourceImage`, `Split`, `DecisionLabel` y evidencias tipadas individuales. No existían ClaimRecord ni EvidencePacket.
- IO de manifest JSONL; adapter HITL/COCO con supuestos explícitos; split hash por fuente y tests de leakage.
- Extractor NLI real y tests con inferencia; módulos YOLO para dataset/train/inference, sin checkpoint de daño.
- Métricas de calidad de imagen, features multimodales, reglas R01–R05 y pipeline B0; demo Streamlit y variantes JPEG/blur.
- Forensic/base/TruFor, clasificador, calibración y métricas eran docstrings/stubs.
- No había GNN/GAT/GATv2, graph builder, reliability gate, P1/P2, agente, notebooks ni CI.

## D. Mapping SOURCE → DESTINATION

Se renombró el directorio real con `Path.rename`, preservando `.git` y archivos ignorados. No se copió el repositorio a otro `.git`. Todos los archivos originales permanecen en el mismo path relativo de Repo A:

| SOURCE (`uafeg-baseline/`) | DESTINATION (`vehicle-claim-verification-baselines/`) | Acción final |
|---|---|---|
| `.gitignore` | `.gitignore` | MODIFY |
| `README.md` | `README.md` | MODIFY |
| `artifacts/.gitkeep` | `artifacts/.gitkeep` | KEEP |
| `configs/baseline.yaml` | `configs/baseline.yaml` | KEEP |
| `configs/labels.yaml` | `configs/labels.yaml` | KEEP |
| `data/README.md` | `data/README.md` | KEEP |
| `data/manifests/.gitkeep` | `data/manifests/.gitkeep` | KEEP |
| `data/processed/.gitkeep` | `data/processed/.gitkeep` | KEEP |
| `data/raw/.gitkeep` | `data/raw/.gitkeep` | KEEP |
| `demo/app.py` | `demo/app.py` | KEEP |
| `demo/cases/assets/.gitkeep` | `demo/cases/assets/.gitkeep` | KEEP |
| `demo/cases/cases.yaml` | `demo/cases/cases.yaml` | KEEP |
| `demo/cases_loader.py` | `demo/cases_loader.py` | KEEP |
| `demo/run_logger.py` | `demo/run_logger.py` | KEEP |
| `pyproject.toml` | `pyproject.toml` | MODIFY |
| `requirements.txt` | `requirements.txt` | KEEP |
| `scripts/.gitkeep` | `scripts/.gitkeep` | KEEP |
| `scripts/create_demo_variants.py` | `scripts/create_demo_variants.py` | KEEP |
| `src/__init__.py` | `src/__init__.py` | KEEP |
| `src/calibration/__init__.py` | `src/calibration/__init__.py` | KEEP |
| `src/calibration/calibrate.py` | `src/calibration/calibrate.py` | KEEP |
| `src/damage/__init__.py` | `src/damage/__init__.py` | KEEP |
| `src/damage/inference.py` | `src/damage/inference.py` | KEEP |
| `src/damage/train.py` | `src/damage/train.py` | KEEP |
| `src/data/__init__.py` | `src/data/__init__.py` | KEEP |
| `src/data/hitl_adapter.py` | `src/data/hitl_adapter.py` | KEEP |
| `src/data/manifest.py` | `src/data/manifest.py` | KEEP |
| `src/data/split.py` | `src/data/split.py` | MODIFY |
| `src/evaluation/__init__.py` | `src/evaluation/__init__.py` | KEEP |
| `src/evaluation/metrics.py` | `src/evaluation/metrics.py` | KEEP |
| `src/evaluation/stress_slices.py` | `src/evaluation/stress_slices.py` | KEEP |
| `src/forensic/__init__.py` | `src/forensic/__init__.py` | KEEP |
| `src/forensic/base.py` | `src/forensic/base.py` | KEEP |
| `src/forensic/image_quality.py` | `src/forensic/image_quality.py` | KEEP |
| `src/forensic/trufor_adapter.py` | `src/forensic/trufor_adapter.py` | KEEP |
| `src/fusion/__init__.py` | `src/fusion/__init__.py` | KEEP |
| `src/fusion/features.py` | `src/fusion/features.py` | KEEP |
| `src/fusion/inference.py` | `src/fusion/inference.py` | KEEP |
| `src/fusion/rules.py` | `src/fusion/rules.py` | KEEP |
| `src/fusion/train_classifier.py` | `src/fusion/train_classifier.py` | KEEP |
| `src/narrative/__init__.py` | `src/narrative/__init__.py` | KEEP |
| `src/narrative/nli_extractor.py` | `src/narrative/nli_extractor.py` | KEEP |
| `src/schemas/__init__.py` | `src/schemas/__init__.py` | KEEP |
| `src/schemas/claim.py` | `src/schemas/claim.py` | MODIFY |
| `src/schemas/evidence.py` | `src/schemas/evidence.py` | MODIFY |
| `tests/__init__.py` | `tests/__init__.py` | KEEP |
| `tests/test_cases.py` | `tests/test_cases.py` | KEEP |
| `tests/test_damage.py` | `tests/test_damage.py` | KEEP |
| `tests/test_demo.py` | `tests/test_demo.py` | MODIFY |
| `tests/test_fusion.py` | `tests/test_fusion.py` | KEEP |
| `tests/test_image_quality.py` | `tests/test_image_quality.py` | KEEP |
| `tests/test_manifest.py` | `tests/test_manifest.py` | KEEP |
| `tests/test_narrative.py` | `tests/test_narrative.py` | MODIFY |
| `tests/test_schemas.py` | `tests/test_schemas.py` | KEEP |
| `tests/test_split.py` | `tests/test_split.py` | MODIFY |

`uafeg/` se creó desde cero; no se movió ningún código propuesto preexistente porque no existía.

## E. Archivos movidos

Todo el directorio `uafeg-baseline/` → `vehicle-claim-verification-baselines/`, incluyendo los 55 archivos de la tabla, `MIGRATION_AUDIT.md` creado antes del rename, `.git`, `.venv` y artefactos locales ignorados. Ningún archivo cambió de ubicación interna. Ningún archivo de A fue trasladado a B.

## F. Archivos modificados

Respecto al checkpoint:

- `vehicle-claim-verification-baselines/.gitignore`
- `vehicle-claim-verification-baselines/MIGRATION_AUDIT.md`
- `vehicle-claim-verification-baselines/README.md`
- `vehicle-claim-verification-baselines/pyproject.toml`
- `vehicle-claim-verification-baselines/src/data/split.py`
- `vehicle-claim-verification-baselines/src/schemas/claim.py`
- `vehicle-claim-verification-baselines/src/schemas/evidence.py`
- `vehicle-claim-verification-baselines/tests/test_demo.py`
- `vehicle-claim-verification-baselines/tests/test_narrative.py`
- `vehicle-claim-verification-baselines/tests/test_split.py`

El alias ClaimRecord conserva la clase Claim; las constantes de taxonomía ahora se leen de YAML; el checker de split rechaza IDs/splits ausentes. Los cinco tests dependientes del modelo siguen existiendo y se ejecutaron completos; pasan a ser optativos en CI sin pesos.

## G. Archivos creados

Repo A (`MIGRATION_AUDIT.md` se creó antes del checkpoint):

- `vehicle-claim-verification-baselines/MIGRATION_AUDIT.md`
- `vehicle-claim-verification-baselines/.github/workflows/ci.yml`
- `vehicle-claim-verification-baselines/EXPERIMENTAL_PROTOCOL.md`
- `vehicle-claim-verification-baselines/requirements-ci.txt`
- `vehicle-claim-verification-baselines/scripts/check_splits.py`
- `vehicle-claim-verification-baselines/src/data/split_audit.py`
- `vehicle-claim-verification-baselines/src/schemas/packet.py`
- `vehicle-claim-verification-baselines/tests/conftest.py`
- `vehicle-claim-verification-baselines/tests/fixtures/split_manifest.jsonl`
- `vehicle-claim-verification-baselines/tests/test_packet.py`

Repo B:

- `uafeg/.github/workflows/ci.yml`
- `uafeg/.gitignore`
- `uafeg/README.md`
- `uafeg/benchmark.lock.json`
- `uafeg/configs/ablations/README.md`
- `uafeg/configs/p1_graph.yaml`
- `uafeg/configs/p2_uafeg.yaml`
- `uafeg/experiments/README.md`
- `uafeg/pyproject.toml`
- `uafeg/requirements.txt`
- `uafeg/src/uafeg/__init__.py`
- `uafeg/src/uafeg/benchmark.py`
- `uafeg/src/uafeg/graph.py`
- `uafeg/tests/test_graph.py`

Fuera de ambos repos: este reporte y el snapshot de auditoría/pruebas. La `.venv` nueva de B es local e ignorada.

## H. Archivos deliberadamente NO movidos

Schemas, labels, manifest/split, especialistas, reglas, demo, scripts, tests y stubs históricos permanecen en A. No se duplicaron en B. No se crearon directorios vacíos de modelos ni implementaciones ficticias de P1/P2. `requirements.txt`, configs originales y código funcional se conservaron; el cambio de packaging se limita al nombre/dependencias mínimas y la instalación editable.

## I. Estado B0–B8

| SYSTEM | DESCRIPTION | STATUS |
|---|---|---|
| B0 | Rules: features, R01–R05 y pipeline ejecutables; no evaluación científica | IMPLEMENTED |
| B1 | NLI real; falta baseline text-only de decisión/evaluación | PARTIAL |
| B2 | Dataset YOLO/train/inference; faltan pesos y evaluación visual-only | PARTIAL |
| B3 | Forensic adapter/base solo docstrings; calidad no equivale a forense | STUB |
| B4 | Features existentes; MLP ausente, entrenamiento clasificador stub | PARTIAL |
| B5 | Calibrated late fusion | NOT IMPLEMENTED |
| B6 | DeepSets | NOT IMPLEMENTED |
| B7 | Discounted Belief Fusion | NOT IMPLEMENTED |
| B8 | Frozen multimodal LLM; condicionado a viabilidad | NOT IMPLEMENTED |

## J. Tests antes de migración

1. Intento con PYTHONPATH heredado: error de arranque `ModuleNotFoundError: lark`, plugin ROS2 `launch_testing`. No llegó a recolectar tests; no es un fallo de un test del proyecto.
2. Misma suite, con PYTHONPATH eliminado solo para el proceso y HF offline: **64 passed, 0 failed, 0 skipped, 0 errors**, 1 warning, 40.90s. Incluye inferencia NLI real con caché previa.

Logs: `.migration-snapshot-2026-10-02/tests-before-normal.txt` y `tests-before-isolated.txt`.

## K. Tests después de migración

| Ejecución | passed | failed | skipped | errors | Observación |
|---|---:|---:|---:|---:|---|
| A completa `--run-model-tests` | 75 | 0 | 0 | 0 | 40.63s; 1 FutureWarning de torch.jit.script |
| A final por defecto | 70 | 0 | 5 | 0 | 7.93s; 5 integración NLI optativas |
| B final, entorno nuevo | 15 | 0 | 0 | 0 | 0.20s |
| B compatibilidad específica | 1 | 0 | 0 | 0 | commit/schema/hashes canónicos |

Los cinco omitidos son cuatro tests de NarrativeExtractor y el test de análisis de demo que carga NLI. Se ejecutaron satisfactoriamente con la opción explícita. No se ocultaron fallos. `pip check` de B: `No broken requirements found.`

`git diff --check` pasó en ambos; estado final limpio. CI no fue ejecutado remotamente: A tiene workflow push/PR, B manual con repositorio canónico explícito hasta tener remotos reales. No se entrenó ni descargó ningún modelo.

## L. Resultado exacto de split/leakage audit

**Manifest de dataset real: NOT AVAILABLE YET.** `data/manifests/` contiene únicamente `.gitkeep`. No se puede afirmar ausencia de leakage en datos que aún no existen.

Auditoría ejecutada sobre fixture sintética persistida:

```json
{
  "manifest": "tests/fixtures/split_manifest.jsonl",
  "sha256": "162a20db23a2b75d3d6e64d616f01a243443a1b3145e23c01a27c6cb07ee06da",
  "audits": [
    {
      "group_key": "source_image_id",
      "split_key": "split",
      "rows": 6,
      "groups": {
        "train": 1,
        "validation": 1,
        "test": 1
      },
      "overlap": {
        "train/validation": [],
        "train/test": [],
        "validation/test": []
      },
      "result": "PASS"
    },
    {
      "group_key": "claim_id",
      "split_key": "split",
      "rows": 6,
      "groups": {
        "train": 1,
        "validation": 1,
        "test": 1
      },
      "overlap": {
        "train/validation": [],
        "train/test": [],
        "validation/test": []
      },
      "result": "PASS"
    }
  ]
}
```

Hay 6 filas: C0/C8 sintéticas para una fuente por train/validation/test. source_image_id y claim_id tienen 1/1/1 grupos, cero overlap en las tres intersecciones y PASS. La fixture no define ni implementa las condiciones completas del benchmark.

Pruebas negativas del CLI ejecutadas: misma fuente en train/test → FAIL, exit 1; split ausente → ERROR, exit 2; manifest vacío → ERROR, exit 2. El checker no puede dar PASS ignorando filas incompletas. `incident_id`, `vehicle_id`, `policy_id` no existen como campos del contrato actual y no se inventaron.

## M. Estado de ClaimRecord / EvidencePacket

- ClaimRecord es alias de la clase original Claim: `ClaimRecord is Claim` verificado.
- EvidencePacket es nuevo y canónico en A, versión explícita 0.1.0; agrega ClaimRecord + NarrativeEvidence/VisualEvidence/ImageQuality/ForensicResult opcionales.
- B importa las mismas clases desde la instalación editable de A y no define labels/splits propios.
- Ground truth se conserva en el packet para trazabilidad, pero se excluye del grafo; test comprueba invariancia al cambiar label/metadata.
- YAML es fuente de taxonomía/mapping; el enum DecisionLabel mantiene API y se comprueba contra YAML.
- `RuleTrace.as_dict` es la salida real de B0. Esquema probabilístico común y métricas aún pendientes; no se reportan probabilidades calibradas ficticias.

## N. benchmark.lock.json real

El commit fijado corresponde al HEAD final real de A. SHA256 calculados sobre bytes locales. Manifest/splits/packets congelados nulos; no se usó una fixture para simular un benchmark. Versión nueva introducida en código, no inferida de documentación histórica.

```json
{
  "benchmark_repository": "vehicle-claim-verification-baselines",
  "git_commit": "1d1f864a3eabe9d72b7bc6a5bc786c2d62c00d29",
  "manifest_identifier": null,
  "manifest_sha256": null,
  "splits_identifier": null,
  "splits_sha256": null,
  "schema_version": "0.1.0",
  "evidence_packets_identifier": null,
  "evidence_packets_sha256": null,
  "availability": {
    "manifest": "NOT AVAILABLE YET",
    "splits": "NOT AVAILABLE YET",
    "frozen_evidence_packets": "NOT AVAILABLE YET"
  },
  "contract_files_sha256": {
    "src/schemas/claim.py": "b96ed766b6de7625f93902e702e2e4abc2c8ea756718adfe4defb7a4e374f7a6",
    "src/schemas/evidence.py": "87e4e92c2c7372cb3c6abf71e9087a2c3e2dd823b2f564e9003b324a3af15602",
    "src/schemas/packet.py": "6d9a5525b0500777a1d06d267d47565ebe4d7300d728518e7ed2e557455e560f",
    "configs/labels.yaml": "cef27ed3931057d2f3a7dec7ec3f9e88c5adfdb72a6a646b8a48a6257e424496",
    "configs/baseline.yaml": "e762ca785bff18c2ffc9214a137d841f522718c4053f2fe58a01b7e81ed0959c",
    "src/data/manifest.py": "945bd10da94c241b32deb8a67f3e7b70217693b6aaf6e88fb9a7e2a8a92a02f4",
    "src/data/split.py": "5a92cb80920d8e01796edb3dd50af2d974e033d283b3454d044c736ba2540835",
    "src/data/split_audit.py": "a30f06ad489aeccc084f863b974b4b8542cd9bab6d8b21ac0772db289b8ea3e1",
    "src/evaluation/metrics.py": "ba59b5b6cde76bc6584e16b011ca4da36636566d664fbdbaea4d84d276bc98ec",
    "src/evaluation/stress_slices.py": "6201036accf2f16138c8ff67ea651e1c9c8c2d55565d8565afeaba3b23609a41",
    "src/fusion/rules.py": "a45bdccc51347fb3a719a082ef732053c6d4acfc18369dd66633d5b8168c1713",
    "EXPERIMENTAL_PROTOCOL.md": "1487003f410b439618e7c6c392563e433806f5293c7aa605ff6a5ac580d67a64"
  }
}
```

## O. Estado del MVP EvidenceGraph

Importa en Python 3.11.9 en un entorno nuevo sin torch/transformers. Convierte un EvidencePacket compatible a estrella con claim y modalidades disponibles; preserva IDs solo como metadata. Valida tipos de payload, nodo claim único, IDs únicos, modalidades únicas, aristas válidas/completas y ausencia de duplicados/dangling/self loops.

Evidencia ausente produce solo el nodo claim. Forense no disponible no genera nodo. Visual presente sin detecciones conserva nodo. Serialización/roundtrip y exclusión de labels probadas. P1/P2 solo documentados/configurados; no hay forward ni reliability gate que probar aún. No se afirma que este grafo mínimo sea toda la propuesta.

## P. Commits creados

Repo A (`migration/two-repositories`; `master` conserva checkpoint):

```text
5f55c320762a27b8701f790884dcc3f8944a9688 chore: checkpoint baseline repository before split
216b54abde86127ec544ee175e533c3f3b1b0293 refactor: establish canonical benchmark contracts and baseline scope
c45705d8619ff084aa9025b021ad96f5b2270783 test: enforce source-level split integrity
1d101fca1b7c83119fa4ef282cb3ead82a9a5b8f ci: add offline pytest workflow and opt-in model integration tests
1d1f864a3eabe9d72b7bc6a5bc786c2d62c00d29 docs: clarify original claim and demo identifiers
```

Tag `pre-two-repo-split-2026-10-02` → 5f55c320762a27b8701f790884dcc3f8944a9688.

Repo B (`main`):

```text
26f3e9024f6938d6e8e1e0d101a5e33e0a83783b feat: add minimal evidence graph with pinned canonical benchmark contract
```

Sin commits vacíos, sin reescritura de historial, sin push.

## Q. Git remotes y publicación

`git remote -v` vacío en ambos. `git status --short` vacío en ambos. GitHub CLI autenticado; cuenta activa `anamariaaccilio`, otra cuenta inactiva; no se extrajeron/guardaron tokens. No se crearon remotos ni repositorios GitHub.

Los archivos que se publicarían son exactamente los listados versionados de A/B en `final-security.json`; el checkpoint contiene también sus versiones originales. Se escanearon nombres y patrones de credenciales; no se detectaron secrets ni raw/weights/.venv/caches versionados. El `.gitkeep` de data/raw es solo un marcador vacío. `.venv` y caches locales se preservan/excluyen, no se confunde esto con inexistencia física.

Comandos manuales posteriores, **no ejecutados**, una vez revisado y autorizado publicar (crear primero dos repositorios vacíos en la cuenta/organización deseada; no añadir README/license/gitignore):

```bash
OWNER=TU_USUARIO_O_ORGANIZACION
cd '/home/ana/Documentos/tesis 2/vehicle-claim-verification-baselines'
git remote add origin "git@github.com:${OWNER}/vehicle-claim-verification-baselines.git"
git push -u origin migration/two-repositories
git push origin pre-two-repo-split-2026-10-02
cd '/home/ana/Documentos/tesis 2/uafeg'
git remote add origin "git@github.com:${OWNER}/uafeg.git"
git push -u origin main
```

Revisar remotos de nuevo antes de esos comandos: no sobrescribir uno si se configura entre tanto. Para CI B privado entre repositorios falta configurar acceso; el workflow actual no agrega secretos y solo se declara viable sin secretos adicionales con acceso público.

## R. Blockers y limitaciones

1. No manifest/dataset/splits reales ni EvidencePackets congelados: audit científico de leakage pendiente. **El criterio de DONE de A referido a datos reales no está satisfecho**, aunque la lógica, el contrato y el milestone de migración sí están validados.
2. Condiciones C0–C10, benchmark generation completo, métricas y esquema probabilístico común no implementados. Protocolo/documentación canónicos disponibles en A.
3. B1/B2 no son sistemas text-only/visual-only completos; B3/B4 incompletos, B5–B8 ausentes. No checkpoint visual ni TruFor.
4. Riesgo preexistente del adapter HITL: agrupa variantes y fusiona anotaciones conservando primer path; requiere validar correspondencia geométrica con exportación real. No se alteró sin datos para justificarlo.
5. No ejecución remota de CI, ni publicación. B workflow manual requiere repositorio canónico publicado. A no se probó en una segunda instalación limpia completa; sí en la .venv real preexistente. B sí se probó en entorno nuevo.
6. Repo A usa paquete heredado `src` y configs externas al package: instalación editable soportada; distribución wheel autocontenida no validada. Sin reestructuración masiva.
7. `.venv` A preservada: scripts de activación/shebang antiguos pueden conservar ruta previa; usar `.venv/bin/python` como se verificó. Nueva instalación editable actualizada al nombre/ruta actual. Metadata antigua de distribución puede seguir en ese entorno local, sin afectar los imports verificados.
8. Dependencias directas CI fijadas, no lock transitivo completo. No afirmar reproducibilidad de hardware/modelos entrenados inexistentes.

## S. Comandos exactos para reproducir tests locales

No requieren activar venv ni modificar variables del sistema:

```bash
cd '/home/ana/Documentos/tesis 2/vehicle-claim-verification-baselines'
env -u PYTHONPATH OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 .venv/bin/python -m pytest -q
env -u PYTHONPATH OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 .venv/bin/python -m pytest -q --run-model-tests
env -u PYTHONPATH .venv/bin/python scripts/check_splits.py --manifest tests/fixtures/split_manifest.jsonl --group-key source_image_id --split-key split
git diff --check
git status --short

cd '/home/ana/Documentos/tesis 2/uafeg'
env -u PYTHONPATH .venv/bin/python -m pytest -q
env -u PYTHONPATH .venv/bin/python -m pytest -q tests/test_graph.py::test_benchmark_contract_compatibility
env -u PYTHONPATH .venv/bin/python -m pip check
git diff --check
git status --short
```

NLI debe existir previamente en caché para `--run-model-tests`; offline está forzado por conftest. Para recrear B: `python3.11 -m venv .venv` en una ruta/entorno nuevo y `.venv/bin/python -m pip install -r requirements.txt`, con A en el commit del lock. Se conservan logs y `environment-before.txt` en el snapshot.

## T. Próximo experimento científico recomendado

Después de autorización: integrar una muestra real, validar IDs/anotaciones, generar manifest y splits agrupados, congelar EvidencePackets y métricas. El primer contraste científico debe ser **B6 (DeepSets) vs P1 (grafo sin gate)** con idénticos inputs/splits/métricas/test set. Solo después, P1 vs P2 para aislar el aporte de reliability-aware propagation y P2 vs ablations. No atribuir novedad a DeepSets/GATv2/NLI/forense/calibración/late fusion/DBF ni al grafo multimodal genérico.

La ejecución se detiene en el MVP local. No se inicia entrenamiento ni siguiente fase experimental.
