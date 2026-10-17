# BENCHMARK PHASE REPORT — ampliación C0–C10, 2026-10-02

Resultado: generación y validación operativa de las once condiciones completadas.
La versión actual es benchmark **0.2.0**, contrato **0.3.0**. Esto no certifica
realismo ni validez externa del benchmark. No se entrenaron modelos ni se implementaron P1/P2.
Este reporte externo registra los SHAs finales sin modificar el commit fijado por UAFEG.
El reporte anterior BENCHMARK_PHASE_REPORT.md describe la versión histórica v1.

## A. Dataset real encontrado

HITL humansintheloop/car-parts-and-car-damages v2, piloto local ya adquirido.
Fuente/licencia declarada y adquisición: Repo A/DATASET_AUDIT.md y data/hitl_pilot_receipt.json.
No se descargaron nuevas imágenes/modelos; no se copiaron raw a rutas versionadas.
Ruta: `/home/ana/Documentos/tesis 2/vehicle-claim-verification-baselines/data/raw/hitl_pilot_v2/Car parts dataset`.
La tabla del usuario es la fuente canónica C0–C10; no se afirma haber cotejado el .tex ausente.

## B. Número de imágenes

24 imágenes reales, 24 archivos de anotación, 256 objetos.
No son 814 imágenes locales. Cero archivos de anotación faltantes, imágenes sin
objetos o fallos estructurales detectados. Formato Supervisely con polígonos;
resoluciones 496–886 px de ancho y 375–599 px de alto.

## C. Clases

| Clase | Objetos |
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

**226 reclamos sintéticos/controlados** sobre imágenes reales y el mismo número
de EvidencePackets canónicos con especialistas null. No son reclamos de aseguradora.
Todos tienen fuente, split, parent C0 cuando corresponde, seed, parámetros y hashes.
C2 incluye donante; C3/C4/C5/C10 incluyen máscara local y hash de máscara.

## E. Condiciones y cobertura

| Condición | Claims |
|---|---:|
| C0 | 24 |
| C1 | 24 |
| C10 | 3 |
| C2 | 24 |
| C3 | 24 |
| C4 | 24 |
| C5 | 24 |
| C6 | 24 |
| C7 | 24 |
| C8 | 24 |
| C9 | 7 |

C0 compatible; C1 negación de daño anotado; C2 sustitución del mismo split;
C3 copy-move localizado; C4 inpainting Telea de daño; C5 C3 más contradicción;
C6 sin narrativa; C7 sin imagen; C8 JPEG benigno; C9 desenfoque; C10 inversión RGB
localizada de familia reservada. Etiquetas exactamente según tabla autorizada.
Las once tienen registros y generador real. C8 no cambia a SUSPICIOUS.

## F. Tamaños train/validation/test

**157 / 38 / 31 claims**. El mayor test respecto a fuentes incorpora los tres C10.

## G. Fuentes por split

**17 / 4 / 3 source_image_id** y los mismos números de grupos.
`benchmark_v2/splits.json` es idéntico al de v1. Las variantes se crean después
del agrupamiento/asignación. IDs de reclamos son únicos y dependientes de la configuración.

## H. Duplicate audit

SHA256 de bytes y de píxeles RGB: cero pares exactos entre las 24 fuentes.
El auditor de las 226 filas también comprueba SHA de imágenes utilizadas:
ninguna aparece en más de un split. Reutilización intrapartición de donantes C2
es deliberada y trazable, no independencia estadística de cada claim.

## I. Near-duplicate audit

dHash128, distancia Hamming<=6 prefijada, 276 pares de fuentes, cero candidatos.
Se conservan 24 componentes singleton. No se elimina ninguna imagen.
La regeneración volvió a calcular fingerprints y grupos; coincidieron con los congelados.
Este método no excluye fotografías del mismo vehículo desde otros ángulos.

## J. Leakage audit

PASS: train/validation, train/test y validation/test sin intersecciones de fuentes/grupos.
Donantes C2 siempre de otro grupo en el mismo split. C3/C5 usan la propia fuente.
C5 conserva todos los píxeles de los daños anotados originales.
Familia `localized_rgb_inversion`: exclusivamente test, ausente de train/validation.
OOD significa reserva de familia en el protocolo, no una medición de generalización ya realizada.

## K. Manifest

`/home/ana/Documentos/tesis 2/vehicle-claim-verification-baselines/data/manifests/benchmark_v2/manifest.jsonl`

EvidencePackets: `/home/ana/Documentos/tesis 2/vehicle-claim-verification-baselines/data/manifests/benchmark_v2/evidence_packets.jsonl`.
Imágenes y máscaras derivadas: data/processed/ ignorado. No hay bytes de imágenes en Git.

## L. SHA256 reales

- Manifest: `3e45880e3a0d5d949bded72b278d80d8366a0ede963c58631affc3258619f9fe`
- Splits: `2b49d6a8428fc9e58e050bc1ec3b39692351bb32e50da8b1405e5b19cf609544`
- EvidencePackets: `5a030f28f1a21db0af9b23e5c160af0d07b4417e592d6e5da3fb449691883d43`

El resto se registra en metadata.json. El lock de UAFEG fue generado desde esos
archivos y el checkout canónico limpio; `pin_benchmark.py --check` pasó.

## M. Schema y lock

ClaimRecord/EvidencePacket 0.3.0, conservando lectura y regeneración de 0.2.0.
`DecisionLabel` sigue con tres clases; OOD se permite únicamente en C10/test bajo 0.3.0.
UAFEG no redefine contratos ni generación y consume los 226 packets en su prueba.
Commit canónico fijado: `58130d874a5adf9facce06e4a82da843cb5f8340`.
Lock real: `/home/ana/Documentos/tesis 2/uafeg/benchmark.lock.json`.

## N. Tests y verificaciones ejecutadas

- Repo A, pytest -q: **119 passed, 5 skipped**, cero fallos/errores.
- Repo A, pytest -q --run-model-tests: **124 passed**, cero fallos/skips/errores;
  un FutureWarning ya existente de torch.jit.script.
- Repo B, pytest -q: **18 passed**, cero fallos/skips/errores.
- Regeneración v2 con imágenes/máscaras/hashes: PASS.
- Regeneración v1: PASS, artefactos/configs congelados sin diferencias desde el commit anterior.
- Split audit source_image_id y claim_id: PASS.
- Validación manifest/packets y prueba de alteraciones maliciosas: PASS.
- git diff --check en ambos: PASS.
- Revisión de rutas tracked/candidatas: sin raw, .env, weights, .venv ni caches.
  Escaneo de patrones comunes de secretos: sin hallazgos; no equivale a prueba absoluta.
- Las pruebas opcionales solo usan el NLI cacheado en modo offline; no entrenan
  ni producen outputs de especialistas para el benchmark.

Logs preservados: `/home/ana/Documentos/tesis 2/.benchmark-phase-validation/v2`.

## O. Qué sigue pendiente

No quedan IDs C0–C10 sin generación en esta versión. No se implementaron todas
las alternativas: C3 usa copy-move, no splice; C8 usa JPEG, no resize/crop.
C9 registra 17 exclusiones por el umbral de calidad original, sin forzar etiquetas.
C10 corresponde solo a las tres fuentes test por diseño.
Pendiente revisión humana de realismo/semántica, ampliación de fuentes independientes
y controles lingüísticos equilibrados. Inpainting ejecutado no implica daño eliminado convincentemente.

## P. Limitaciones científicas

Muestra de 24 imágenes y tres fuentes test, no representativa. No hay IDs reales
verificables de vehículo/incidente/póliza. Narrativas C1/C5 con negaciones pueden
crear shortcuts; missing modality y blur extremo también son pistas directas.
C2 puede ser visualmente compatible aunque el donante pertenezca a otro expediente
experimental: no-identificabilidad explícita, sin afirmar detección posible.
Las composiciones no tienen adjudicación humana; C4 registra damage_removal_verified=false.
OOD es respecto a una sola familia artificial reservada. No implica cobertura
universal de ataques. Los annotations/labels/conditions/provenance no deben ser
features de modelos. Las anotaciones referenciadas son de la fuente original.

## Q. Commits locales realizados

```text
58130d874a5adf9facce06e4a82da843cb5f8340 docs: document complete benchmark coverage and scientific limits
13ec9e552e6b22948047e7e4581428cccadcefca feat: generate all controlled C0-C10 conditions with held-out OOD family
30689055e131291c7adcb457549021682ea7bece chore: pin complete C0-C10 benchmark and canonical schema 0.3.0
```

No hubo push, reescritura de historia, borrado de raw ni reestructuración de repositorios.
Los remotes actuales: Repo A `(sin remotes)`;
Repo B `(sin remotes)`.

## R. Git status final

Repo A: limpio (`git status --short` vacío).
Repo B: limpio (`git status --short` vacío).
Solo texto/código/configs/manifests/packets se incorporaron a Git.

## S. Reproducción y siguiente fase

```bash
cd '/home/ana/Documentos/tesis 2/vehicle-claim-verification-baselines'
env -u PYTHONPATH .venv/bin/python scripts/build_benchmark_v2.py
env -u PYTHONPATH .venv/bin/python scripts/build_benchmark_v2.py --check --verify-images
env -u PYTHONPATH .venv/bin/python scripts/check_splits.py --manifest data/manifests/benchmark_v2/manifest.jsonl --group-key source_image_id --split-key split
env -u PYTHONPATH HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/python -m pytest -q
env -u PYTHONPATH HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/python -m pytest -q --run-model-tests
git diff --check
git status --short
cd '/home/ana/Documentos/tesis 2/uafeg'
env -u PYTHONPATH .venv/bin/python scripts/pin_benchmark.py --check
env -u PYTHONPATH .venv/bin/python -m pytest -q
git diff --check
git status --short
```

Para CI sin raw, usar `--check` sin `--verify-images`. El generador rechaza
sobrescribir artefactos diferentes. Nuevos datos/criterios requieren otra versión.
Siguiente paso recomendado: adjudicación humana y auditoría de shortcuts antes
de entrenar/comparar sistemas. Esta ejecución termina aquí; no inicia modelos.
