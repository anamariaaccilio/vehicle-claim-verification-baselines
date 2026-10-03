# DEMO BUILD REPORT

## A. Archivos creados

- `run_demo.sh`: inicio único, offline y local.
- `demo/benchmark/server.py`: carga de artifacts, lectura de imágenes permitidas, grafo real, regeneraciones en memoria y ejecución/lectura de pytest.
- `demo/benchmark/index.html`, `style.css`, `app.js`: interfaz sin framework ni dependencias externas.
- `demo/benchmark/capture_demo.py`: comprobación de navegador y capturas opcionales con herramientas ya instaladas.
- `demo/benchmark/README.md`, `demo/screenshots/README.md`, `DEMO_VIDEO_SCRIPT.md`, este reporte.
- `demo/benchmark/generated/`: resultados actuales XML/JSON/log de pytest y comprobación del navegador; ignorados por Git.
- `demo/screenshots/01_overview.png` a `06_test_dashboard.png`: capturas locales ignoradas.
- `.gitignore` actualizado solo para salidas locales de demo. Demo Streamlit preexistente preservada.

## B. Fuente real de cada dato

| Dato | Fuente |
|---|---|
| 814 descargadas, 807 aceptadas; clases/anotaciones | `data/manifests/benchmark_v3/dataset_audit.json` |
| 9.275 claims, condiciones, labels y filtros | `data/manifests/benchmark_v3/manifest.jsonl` |
| Imágenes / donantes / máscaras / seeds / parámetros | Referencias exactas del manifest; lectura de archivos locales, sin copias raw |
| Definiciones C0–C10 | `configs/benchmark_conditions_v2.yaml`; C8 ampliado según config y artefactos v3 |
| JSON canónico | Manifest, `evidence_packets.jsonl`, modelos `src.schemas` existentes |
| Grafo mostrado | Ejecución real de `uafeg.graph.build_graph` sobre un packet validado |
| Splits y donantes | Intersecciones recalculadas desde manifest; auditoría canónica existente adicional |
| Exact / pixel / near duplicates | Pares y motivos en `dataset_audit.json`, dHash128 umbral 6 |
| C2 v3 | Función original `benchmark_qa.c2_audit`; v2 ambiguous desde `qa_measurements.json` |
| C3/C4/C5 QA | `qa_v3_pixels.json` |
| C9 excluidos | `exclusions.json` y `qa_summary.json` |
| Narrative shortcuts | `qa_summary.json`: `v3_narrative`, conteos, asociaciones y dispersión |
| Tests | Ejecuciones actuales pytest → JUnit XML → JSON; timestamps y fingerprints verificables |
| Reproducibilidad | Operadores originales `localized_transform`, `benign_control`, `png_bytes`; bytes en memoria vs SHA manifest y archivo |
| Lock | `../uafeg/benchmark.lock.json`; continúa fijando el benchmark v2 |

Manifest v3: `378e1cdd698cb417720637adcd7da2d85a060a884c73fa3f67755e066f465588`.

## C. Ejemplos utilizados

Todo el manifest es navegable. La selección inicial sigue el orden real del manifest. La presentación recorre C0/C1/C2/C3 de la primera fuente disponible, sin seleccionar por resultado de un modelo.

Regeneraciones reales:

- C3 `clm_7802065aa85939835e81a22c`.
- C8_RESIZE `clm_737da5c81f0e5582990ebdf3`.
- C10 `clm_b6376b4249f5dd270198b733`.

Las tres comparaciones dieron MATCH entre SHA esperado, regenerado y archivo guardado. Seed 42; no escritura de transformaciones.

C2 muestra un likely contradiction y un likely compatible de v3, más un ambiguous histórico v2. No hay contradicciones humanas confirmadas; se muestra explícitamente cero. La anotación faltante no se considera prueba de ausencia.

## D. Validación

Las suites se ejecutan con PYTHONPATH externo retirado, un hilo OMP/MKL y Hugging Face offline. Repo A: suite por defecto, sin `--run-model-tests`; se omiten los cinco tests que requieren NLI local. No se entrenan ni ejecutan especialistas para la demo.

La primera ejecución obtuvo 127 passed / 5 skipped en A y 17 passed / 1 failed en B. El fallo fue el control existente que exige Repo A limpio y committed; no un fallo de grafo. Se conserva esta explicación y se resuelve registrando cambios locales y regenerando el lock mediante `scripts/pin_benchmark.py`, manteniendo v2. Resultados finales exactos y duración: `demo/benchmark/generated/tests.json`, visibles en Test dashboard.

Comprobaciones adicionales: navegador Chrome real, diez páginas, once condiciones, filtros, imágenes, recorrido de trece pasos, reproducción de hashes y `git diff --check`. Capturas y log de navegador en carpetas documentadas; no screenshots simulados.

## E. Inicio

```bash
cd '/home/ana/Documentos/tesis 2/vehicle-claim-verification-baselines'
./run_demo.sh
```

URL: http://127.0.0.1:8765/ · Presentación: http://127.0.0.1:8765/demo.

## F. Páginas

Overview; Sample explorer; Conditions; EvidencePacket & Graph; Leakage; Reproducibility; Tests; C2 QA; Narrative shortcuts; What has been built. Presentación de 13 pasos con flechas, sin autoavance que interrumpa la explicación.

## G. Limitaciones

- READY_FOR_MODELS = NO. La demo no resuelve C2, manipulaciones pequeñas ni shortcuts. V4 no está terminado.
- VALIDATED solo se usa para schema; todos los claims requieren aprobación humana de semántica/realismo. Exclusiones C9 separadas de los claims aceptados.
- El grafo real de estos packets tiene un nodo claim y cero aristas: especialistas null. No se inventan nodos forenses, visuales, source ni relaciones semánticas.
- Las variantes no son observaciones independientes. Inferencia futura agrupada por fuente; considerar dependencias de donantes.
- Regenerar tres ejemplos no acredita toda condición o realismo. Near-duplicate audit con dHash es limitado.
- Requiere imágenes locales y ambas carpetas hermanas. No es una aplicación desplegada ni un empaquetado de raw data.
- Los grupos de propósito del dashboard se derivan de nombres de tests y pueden solaparse; no son nuevas métricas de calidad predictiva.

## H–I. Capturas y video

Seis capturas locales en `demo/screenshots/`. Las cinco esenciales se detallan en su README. Guion de 85 segundos en `DEMO_VIDEO_SCRIPT.md`, con pantalla, texto, duración y afirmaciones que evitar.

## J. Git

Se registran commits exclusivamente locales de la demo y la actualización mecánica del lock. No se modifican imágenes, manifests, schemas, generadores, P1/P2 ni modelos. Los resultados/capturas son ignorados. `git status --short` y hashes de commits finales se entregan también al cerrar la tarea; no se hace push.
