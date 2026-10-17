# BENCHMARK PHASE REPORT — UAFEG

Fecha: 2026-10-02. Fase completada: primera versión reproducible de **reclamos controlados sobre imágenes reales**. No se reestructuraron los repositorios, no se entrenó B0–B8 y no se implementó P1/P2. El benchmark/generador/contratos/splits viven exclusivamente en Repo A; Repo B consume los artefactos por lock.

**Alcance de la aprobación:** manifest real, splits congelados y auditoría PASS de las fuentes/grupos/duplicados medidos. No constituye aprobación universal de independencia por vehículo/incidente ni validación científica final de UAFEG. Hay condiciones pendientes y shortcuts lingüísticos documentados.

## A. Dataset real encontrado

HITL Car Parts and Car Damages, publicación de autores en Kaggle, versión 2; licencia CC0 1.0 declarada por los autores. [Fuente oficial](https://humansintheloop.org/resources/datasets/car-parts-and-car-damages-dataset/) y [Kaggle](https://www.kaggle.com/datasets/humansintheloop/car-parts-and-car-damages).

Ruta local inspeccionada: `vehicle-claim-verification-baselines/data/raw/hitl_pilot_v2/Car parts dataset`. Los nombres de las carpetas de la publicación están invertidos respecto a las clases; se usa el subconjunto confirmado por meta.json, no el nombre. Formato JSON por imagen estilo Supervisely, polígonos exteriores.

Auditoría completa: [DATASET_AUDIT.md](vehicle-claim-verification-baselines/DATASET_AUDIT.md). No se descargaron nuevas imágenes durante esta fase ni se copiaron raw a Git.

## B. Número de imágenes y anotaciones

**24 imágenes locales**, 24 JSON de anotación, **256 objetos**. No se asumió que las 814 imágenes publicadas estuvieran disponibles localmente. Cero imágenes sin archivo de anotación, cero imágenes sin objetos, cero errores de integridad detectados por los controles estructurales implementados. Anchos 496–886 px, altos 375–599 px. No es revisión experta de exactitud de las anotaciones.

## C. Clases

| Clase | Anotaciones |
|---|---:|
| broken_part | 42 |
| corrosion | 2 |
| crack | 5 |
| dent | 52 |
| flaking | 14 |
| missing_part | 23 |
| paint_chip | 48 |
| scratch | 70 |

## D. Claims generados

**127 ClaimRecord** y **127 EvidencePacket**, schema 0.2.0, sobre imágenes reales; las narrativas y situaciones son experimentales/sintéticas. No son expedientes de una aseguradora. Los IDs son estables por hash de fuente/config/condición; no se inventaron personas, matrículas, pólizas ni incidentes.

Cada registro conserva source_image_id, referencia de imagen, narrativa, expected_label, split, condition, annotation_reference, clases anotadas, parent claim C0, provenance, transformación, seed y hashes. Las anotaciones son ground truth de auditoría, no predicciones del especialista visual. No se copian polígonos ni JSON raw al manifest.

NLI/visual/calidad/forense en EvidencePacket son explícitamente null. Los datos reales disponibles son el texto controlado, referencia de imagen y anotaciones referenciadas. Las métricas de transformación no se presentan como outputs de modelos.

## E. C0 y variantes por condición

Fuente canónica: tabla de la usuaria, autorizada explícitamente tras comprobar que la ruta indicada de capitulo4.tex no existía. No se afirma cotejo con el .tex. El registro exacto se versiona en configs/benchmark_conditions.yaml; protocolo detallado en [BENCHMARK_PROTOCOL.md](vehicle-claim-verification-baselines/BENCHMARK_PROTOCOL.md).

| Condición | Descripción canónica | Label esperado | Claims | Estado |
|---|---|---|---:|---|
| C0 | Narrativa compatible + imagen original | SUPPORTED | 24 | IMPLEMENTED |
| C1 | Daño declarado incompatible con lo observado | SUSPICIOUS | 24 | IMPLEMENTED |
| C2 | Sustitución por imagen de otro expediente | SUSPICIOUS | 0 | NOT IMPLEMENTED |
| C3 | Copy-move o splice localizado | SUSPICIOUS | 0 | NOT IMPLEMENTED |
| C4 | Inpainting o eliminación de daño | SUSPICIOUS | 0 | NOT IMPLEMENTED |
| C5 | Contradicción narrativa + manipulación visual | SUSPICIOUS | 0 | NOT IMPLEMENTED |
| C6 | Narrativa ausente | INSUFFICIENT | 24 | IMPLEMENTED |
| C7 | Imagen ausente | INSUFFICIENT | 24 | IMPLEMENTED |
| C8 | JPEG, redimensionado o recorte benigno | SUPPORTED | 24 | PARTIAL |
| C9 | Desenfoque o calidad insuficiente | INSUFFICIENT | 7 | IMPLEMENTED |
| C10 | Manipulación no vista durante el entrenamiento | OOD | 0 | NOT IMPLEMENTED |

C8 solo implementa JPEG benigno, conserva SUPPORTED. C9 solo emite las 7 variantes que pasaron el criterio fijo; **17 variantes propuestas se excluyeron**, sin claim/label, con parámetros/medidas en exclusions.json. Las 24 fuentes conservan sus controles. No se ajustaron parámetros para aumentar cobertura tras examinar resultados.

## F. Tamaño train / validation / test

| Split | Claims | Labels |
|---|---:|---|
| train | 89 | {'SUPPORTED': 34, 'SUSPICIOUS': 17, 'INSUFFICIENT': 38} |
| validation | 22 | {'SUPPORTED': 8, 'SUSPICIOUS': 4, 'INSUFFICIENT': 10} |
| test | 16 | {'SUPPORTED': 6, 'SUSPICIOUS': 3, 'INSUFFICIENT': 7} |

El split se asignó antes de crear variantes, mediante hash canónico seed=42 + ID del grupo; proporciones objetivo 70/15/15, realizadas aproximadamente, sin rebalancear test.

## G. source_image_id por split

| Split | Fuentes | Grupos |
|---|---:|---:|
| train | 17 | 17 |
| validation | 4 | 4 |
| test | 3 | 3 |

24 grupos singleton en el dataset local. El código y los tests cubren también grupos de múltiples fuentes y uniones transitivas. Si una ampliación modifica componentes, debe publicarse una nueva versión del benchmark; no recalcular estos splits congelados en silencio.

## H. Duplicate audit

SHA256 de archivos y de píxeles RGB decodificados: **0 pares de fuentes exactas** y **0 cruces entre splits**. El auditor también comprueba hashes de imágenes usadas por variantes y vínculos parent-claim. C0/C1/C6 comparten imagen por diseño dentro del mismo split. No se eliminó ninguna imagen.

## I. Near-duplicate audit

Método: dHash128 (64 gradientes horizontales + 64 verticales), grayscale/LANCZOS. Umbral Hamming <=6 fijado antes del análisis, sin modelos ni fit. 276 pares examinados, **0 candidatos**. Política: agrupar conservadoramente todos los candidatos/exactos por componentes conexas, sin borrar imágenes ambiguas. Los grupos y la decisión están en [NEAR_DUPLICATE_AUDIT.md](vehicle-claim-verification-baselines/NEAR_DUPLICATE_AUDIT.md).

Limitaciones: no garantiza detectar grandes recortes/rotaciones, otras vistas del mismo vehículo o manipulaciones localizadas. No hay IDs reales de vehículo/incidente/póliza. No detectar candidatos no prueba independencia universal.

## J. Leakage audit

**PASS**, con las siguientes intersecciones vacías:

- train_sources ∩ validation_sources = ∅
- train_sources ∩ test_sources = ∅
- validation_sources ∩ test_sources = ∅

También PASS para grupos de similitud, parent C0, claim_id y hashes de imagen. No se generaron condiciones con donor; el generador v1 rechaza donors/C2/C3 en lugar de ignorar su split. No hay claim real multiimagen; todos los claims experimentales tienen una fuente y el vínculo de variante se verifica.

Se ejecutaron el CLI de splits y `build_claim_benchmark.py --check --verify-images`, que recalcula desde los archivos reales los hashes/dHash, grupos, variantes y manifiestos. `--check` valida schema/artefactos/semántica sin necesitar raw, para CI.

## K. Manifest path

[vehicle-claim-verification-baselines/data/manifests/benchmark_v1/manifest.jsonl](vehicle-claim-verification-baselines/data/manifests/benchmark_v1/manifest.jsonl)

Contiene 127 filas JSONL deterministas y versionadas. Imágenes raw/derivadas siguen ignoradas. Artefactos adicionales: splits.json, evidence_packets.jsonl, dataset_audit.json, validation.json, exclusions.json, metadata.json.

## L. Manifest SHA256 y otros hashes reales

- `manifest.jsonl`: `e29bb20693e3b725e64a2641dd2617a9c1c19b2f1b09779dbdda084423c48840`
- `splits.json`: `2b49d6a8428fc9e58e050bc1ec3b39692351bb32e50da8b1405e5b19cf609544`
- `evidence_packets.jsonl`: `96117d4be37a555df90d8d18ae7482f8346bb325e6568d234d2de9790c982aba`

Metadata registra también hashes de configs/condiciones/recibo de adquisición y versiones de las librerías utilizadas para transformar imágenes. No se inventaron hashes ni se completaron valores para eludir tests.

## M. Schema version / benchmark lock

**Schema 0.2.0**, benchmark 0.1.0. ClaimRecord sigue siendo alias de Claim. Se añadieron explícitamente campos tipados de condición/split/provenance/transformación/referencia a anotaciones. Las instancias mínimas previas siguen funcionando; los JSON con versión explícita 0.1.0 no se reinterpretan silenciosamente como 0.2.0. No había packets congelados antiguos.

El lock de UAFEG se generó ejecutando `scripts/pin_benchmark.py --write` sobre un Repo A limpio y commiteado; `--check` confirmó igualdad con artefactos reales. Commit canónico:

`7a6cb9705273b313e38ae0655a4f4c3c125b5347`

[benchmark.lock.json](uafeg/benchmark.lock.json) incluye identificadores y SHA256 reales de manifest/splits/packets. No se duplicaron schemas, generadores ni lógica de benchmark en UAFEG. El test consumidor construye el grafo mínimo desde todos los packets reales; solo nodo claim, sin outputs de especialistas ficticios.

## N. Tests y verificaciones

| Suite | Resultado |
|---|---|
| Repo A, `pytest -q` | 102 passed, 5 skipped |
| Repo A, `pytest -q --run-model-tests` | **107 passed**, 0 failed, 0 skipped, 0 errors; 1 FutureWarning preexistente de torch.jit.script |
| Repo B, `pytest -q` | **18 passed**, 0 failed, 0 skipped, 0 errors |
| Consumo explícito de packets reales en B | 1 passed |
| Manifest/schema/semántica/packets | PASS |
| Split/exact duplicate/near-duplicate audit desde raw | PASS bajo criterios declarados |
| Lock contra artefactos/commit real | PASS |
| git diff --check | PASS en ambos |

Los cinco skipped por defecto siguen siendo tests optativos con NLI; se ejecutaron y pasaron en la suite completa, usando caché previa y sin descargas. Esa inferencia de tests no se usó para fabricar evidencias del benchmark. Los nuevos tests de generación usan fixtures pequeñas; los de compatibilidad leen los artefactos textuales reales sin raw. No se ejecutó GitHub Actions ni entrenamiento.

Logs preservados en `.benchmark-phase-validation/`. Durante preparación se corrigió una frase de C0 antes del freeze; el escritor rechazó sobrescribir el borrador distinto. Se conservó el borrador no publicado en un directorio ignorado y se generó la versión final. No se sobrescribieron datos ni artefactos previos del usuario.

## O. Condiciones todavía pendientes

- C2: sustitución de expediente con protocolo de donantes y validación semántica; solo donors del mismo split.
- C3: copy-move/splice con máscara y procedencia validada; cualquier donor del mismo split.
- C4: eliminación/inpainting con verificación real de remoción de daño.
- C5: combinación de contradicción con manipulación visual ya validada.
- C8: resize/crop benignos; solo JPEG implementado actualmente.
- C10: familia verdaderamente reservada fuera de entrenamiento; OOD se conserva en la taxonomía, sin introducirlo prematuramente como cuarta clase de decisión normal.

## P. Limitaciones científicas

1. Muestra de 24 imágenes y tres fuentes de test; no generalizar resultados a producción ni a toda la tesis.
2. Datos de imágenes anotadas + escenarios controlados, no expedientes/veredictos de seguros ni fraude confirmado.
3. Labels son expectativas de escenario derivadas de anotaciones/protocolo; requieren revisión semántica humana independiente.
4. C1 niega una clase realmente anotada. Todos los SUSPICIOUS actuales son C1, con negaciones o “libre de”: existe un shortcut lingüístico evidente. No confundir buen desempeño con razonamiento multimodal.
5. C6/C7 y blur extremo son señales de condición por diseño; podrían facilitar shortcuts. No se entrenó un probe para medirlos.
6. PSNR y varianza Laplaciana son gates operativos fijados previamente, no prueba universal de preservación/inobservabilidad de cada daño. C9 tiene cobertura selectiva (7 fuentes); comparar condiciones requiere declarar ese soporte.
7. No hay auditoría de parentesco por vehículo/incidente; dHash global puede omitir otras vistas o recortes.
8. No existen todavía probabilidades de modelos, métricas implementadas de evaluación, resultados B0–B8 ni P1/P2.
9. No usar expected_label, clases anotadas, condición, IDs, source hashes, provenance o parámetros de transformación como features.
10. El .tex no estuvo disponible; la fuente canónica de condiciones de esta fase es la tabla autorizada por la usuaria.

## Q. Commits realizados

Repo A:

```text
e64d4c2217f70a82bae36f3d265c6dfcf8ded333 feat: freeze controlled claims benchmark v1 with audited source groups
7a6cb9705273b313e38ae0655a4f4c3c125b5347 docs: record dataset audits and controlled benchmark limitations
```

Repo B:

```text
6b172ef82345624d52f32b1952081f0bb2d8fda1 chore: pin real controlled benchmark artifacts and validate packet consumption
```

Todos locales, sin commits vacíos, sin reescritura de historial y sin push. Este reporte externo permite registrar ambos SHAs finales sin alterar el commit canónico ya fijado.

## R. Git status y seguridad

`git status --short` vacío en ambos. `git diff --check` sin errores. No remotos nuevos ni publicación.

Se inspeccionaron archivos candidatos/versionados y patrones comunes de credenciales: sin hallazgos. Raw, derivados, .env, weights, .venv y caches no tracked. Solo se permitió el subdirectorio textual `data/manifests/benchmark_v1` mediante reglas específicas de .gitignore. Ningún archivo de imagen se incluyó en commits. Las carpetas locales ignoradas permanecen preservadas.

## S. Siguiente fase recomendada y reproducción

Antes de entrenar: revisión de la validez semántica y de shortcuts de narrativas/labels, ampliación del corpus con auditoría de relaciones entre imágenes y completar condiciones prioritarias con trazabilidad. Implementar después evaluación común. La comparación B6 vs P1, P1 vs P2 y ablations debe consumir exactamente este contrato o una nueva versión explícitamente validada; no cambiar los splits congelados silenciosamente.

Comandos exactos ejecutables:

```bash
cd '/home/ana/Documentos/tesis 2/vehicle-claim-verification-baselines'
# Si faltan datos locales (esta fase reutilizó el piloto existente):
python3 scripts/fetch_hitl_pilot.py --receipt data/hitl_pilot_receipt.json --output data/raw/hitl_pilot_v2
env -u PYTHONPATH OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 .venv/bin/python scripts/build_claim_benchmark.py
env -u PYTHONPATH OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 .venv/bin/python scripts/build_claim_benchmark.py --check --verify-images
env -u PYTHONPATH .venv/bin/python scripts/check_splits.py --manifest data/manifests/benchmark_v1/manifest.jsonl --group-key source_image_id --split-key split
env -u PYTHONPATH OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 .venv/bin/python -m pytest -q
env -u PYTHONPATH OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 .venv/bin/python -m pytest -q --run-model-tests
git diff --check
git status --short

cd '/home/ana/Documentos/tesis 2/uafeg'
env -u PYTHONPATH .venv/bin/python scripts/pin_benchmark.py --check
env -u PYTHONPATH .venv/bin/python -m pytest -q
git diff --check
git status --short
```

La reproducción de imágenes debe usar las versiones registradas en metadata.json; diferencias de bytes se rechazan, no se ocultan. La lectura/validación del manifest y packets no requiere raw (`--check` sin `--verify-images`).

**Trabajo detenido al terminar esta fase. Sin entrenamiento B0–B8, sin P1/P2 y sin publicación remota.**
