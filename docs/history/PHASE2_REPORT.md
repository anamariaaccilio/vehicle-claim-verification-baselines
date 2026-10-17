# Fase 2 — búsqueda de datos y piloto real

Fecha: 2026-10-02. Alcance completado: selección de fuente, adquisición pequeña, validación de ingestión y auditoría de splits. No se inició entrenamiento.

## Fuentes y decisión

Ver [comparativa y fuentes primarias](vehicle-claim-verification-baselines/docs/DATASET_DISCOVERY.md).
Se eligió HITL versión 2 publicado por sus autores en Kaggle. CarDD requiere solicitud al laboratorio; no se enviaron mensajes. Otras opciones Kaggle se documentaron por tamaño/taxonomía/licencia. No se solicitó ni guardó ninguna credencial.

## Evidencia real

- Inventario público: 7.250 archivos, 3.311.753.461 bytes; no se descargó todo.
- Subconjunto de daños: 814 imágenes. El contenido de `Car parts dataset` corresponde a daños, verificado con meta.json; los nombres de carpetas están invertidos.
- JSON estilo Supervisely (`objects`, `points`, `size`), no COCO. El adapter original no se usó.
- Piloto: 24 imágenes + 24 JSON + 2 meta.json = 50 archivos, 15.896.440 bytes.
- Archivos verificados contra recibo SHA256; raw permanece ignorado.
- 24 registros y 256 anotaciones válidas; no se fabricaron salidas de modelos ni labels de reclamos.
- Split seed 42: train 17 / validation 4 / test 3. Cero overlaps por source_image_id, hash de archivo y hash de píxeles RGB.
- Near-duplicates y relación vehículo/incidente todavía no auditados.
- Manifest SHA256: 82d45a445a8c04481341ac6514871c75c8737a398c5c175966c1f29bdba63a37.

## Validación ejecutada

Antes: A 70 passed / 5 skipped; B 15 passed.
Después: A **82 passed / 5 skipped**, B **15 passed**.
Los cinco skipped son integración con modelo NLI, conservados; no se volvieron a ejecutar en esta fase de ingestión. Doce tests nuevos cubren geometría, taxonomía, tamaño, imagen ausente y rechazo de combinación ambigua de fuentes.

Se ejecutó el CLI de split sobre el manifest real del piloto. Se reconstruyeron/verificaron los artefactos dos veces con el mismo SHA256. El descargador comprobó los 50 archivos frente al recibo. `git diff --check` pasó; ambos working trees quedaron limpios.

Incidencia de adquisición: Kaggle devuelve algunas imágenes dentro de ZIP de un archivo; el intento inicial detectó tamaños distintos y se detuvo. Se añadió lectura segura de ese miembro y se verificó su SHA256; no se aceptaron descargas truncadas ni se sobrescribieron archivos distintos.

## Commits locales

- A: fa4914517c641bcfd51b3596b049b4440d958c7d — feat: validate real HITL pilot ingestion and source splits
- B: a4d18ad524f4a7583e646fece06e6ebf81d3be7e — chore: pin canonical contract after HITL pilot validation

UAFEG fija el nuevo commit y hashes canónicos, incluido lector/recibo. Los campos manifest/splits/packets del benchmark siguen null: este piloto de imágenes no es el benchmark de reclamos. No se redefinieron schemas, labels ni splits en B. No hubo push.

## Reproducción

Desde Repo A:

```bash
python3 scripts/fetch_hitl_pilot.py --receipt data/hitl_pilot_receipt.json --output data/raw/hitl_pilot_v2
env -u PYTHONPATH .venv/bin/python scripts/prepare_hitl_pilot.py --dataset-dir 'data/raw/hitl_pilot_v2/Car parts dataset' --manifest data/manifests/hitl_pilot_v2.jsonl --audit data/manifests/hitl_pilot_v2.audit.json
env -u PYTHONPATH .venv/bin/python scripts/check_splits.py --manifest data/manifests/hitl_pilot_v2.jsonl --group-key source_image_id --split-key split
env -u PYTHONPATH OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 .venv/bin/python -m pytest -q
```

Desde Repo B:

```bash
env -u PYTHONPATH .venv/bin/python -m pytest -q
```

## Pendiente para fase experimental

Ampliar adquisición al subconjunto completo de daños, revisar duplicados cercanos/procedencia, definir narrativas/condiciones y labels de verificación, implementar evaluación común y congelar inputs. No usar anotaciones ground truth como VisualEvidence de un modelo. No afirmar que daño visible equivale a fraude. B6 vs P1 sigue siendo el contraste científico inicial previsto, todavía no ejecutable sobre un benchmark validado.
