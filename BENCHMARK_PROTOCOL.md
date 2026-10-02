> Protocolo histórico de v0.1.0, preservado para reproducir sus 127 registros.
> El protocolo vigente C0–C10 es [BENCHMARK_V2_PROTOCOL.md](BENCHMARK_V2_PROTOCOL.md).

# Benchmark v1: reclamos controlados sobre imágenes reales

## Unidad experimental y versión

**Real vehicle-damage imagery + controlled/synthetic claim scenarios.** Cada ClaimRecord representa una instancia de verificación, no un reclamo real de una aseguradora. Los 24 archivos HITL locales originan 127 escenarios. No se inventan personas, placas, fechas, direcciones, pólizas ni causalidad de accidentes.

ClaimRecord sigue siendo alias de Claim; se extendió explícitamente el contrato a **0.2.0**, compartido con EvidencePacket. La distribución Python conserva su nombre/layout. El schema ahora registra:

| Información | Campo canónico |
|---|---|
| Identidad experimental estable | claim_id (hash de fuente/config/condición; no dato personal) |
| Fuente real y split congelado | source_image_id, split |
| Entradas | image_path, narrative_text (opcionales para C6/C7) |
| Etiqueta esperada del escenario | expected_label |
| Condición | condition |
| Ground truth disponible, no predicción | annotated_damage_classes, annotation_reference |
| Derivación | parent_claim_id (C0), transformation.operation/parameters/seed/image_sha256 |
| Procedencia | provenance: dataset/version, source_group_id, source path/SHA, annotation SHA, generator version, seed, template |

No se copian polígonos/bytes raw al manifest: se referencia el archivo de anotación y su SHA256. Las clases anotadas son ground truth para auditoría. **No usar expected_label, annotated_damage_classes, condition, provenance, IDs o metadata de transformación como features de un modelo**. Los inputs de verificación son la narrativa y la imagen/evidencias derivadas legítimamente de ella.

Los Claim mínimos anteriores siguen siendo construibles con sus campos previos. Los registros con condition exigen provenance/split/label/parent completos. JSON marcado explícitamente como schema 0.1.0 no se acepta como 0.2.0 en silencio; el benchmark nuevo se regenera. No existían packets congelados en el lock previo.

## Taxonomía canónica C0–C10

Fuente: tabla proporcionada por la usuaria y autorizada como canónica el 2026-10-02. No existía la ruta indicada `UAFEG_Tesis_Asesora/secciones/capitulo4.tex`; se buscó también en Documentos y Descargas. No se afirma que se verificó contra el .tex. El PDF de migración contenía referencias parciales compatibles, no la tabla completa. Cotejo con la tesis pendiente cuando esté disponible.

| CONDITION | DESCRIPTION / EXPECTED SEMANTICS | INPUT MODIFICATION | LABEL | IMPLEMENTATION STATUS |
|---|---|---|---|---|
| C0 | Control: Narrativa compatible + imagen original | Ninguna; narrativa derivada de clases anotadas | SUPPORTED | IMPLEMENTED |
| C1 | Semántica: Daño declarado incompatible con lo observado | Negación explícita de una clase de daño realmente anotada | SUSPICIOUS | IMPLEMENTED |
| C2 | Semántica: Sustitución por imagen de otro expediente | Imagen donante del mismo split; pendiente protocolo de sustitución y validación semántica | SUSPICIOUS | NOT IMPLEMENTED |
| C3 | Forense: Copy-move o splice localizado | Pendiente composición localizada con máscara trazable; cualquier donor del mismo split | SUSPICIOUS | NOT IMPLEMENTED |
| C4 | Forense: Inpainting o eliminación de daño | Pendiente eliminación verificada de daño; no basta aplicar relleno arbitrario | SUSPICIOUS | NOT IMPLEMENTED |
| C5 | Combinada: Contradicción narrativa + manipulación visual | Depende de una manipulación C3/C4 validada y contradicción real | SUSPICIOUS | NOT IMPLEMENTED |
| C6 | Ausencia: Narrativa ausente | narrative_text=null; imagen original conservada | INSUFFICIENT | IMPLEMENTED |
| C7 | Ausencia: Imagen ausente | image_path=null; narrativa C0 conservada | INSUFFICIENT | IMPLEMENTED |
| C8 | Control: JPEG, redimensionado o recorte benigno | JPEG quality=95 sin resize/crop; solo se emite si PSNR>=35 dB. Resize/crop pendientes | SUPPORTED | PARTIAL |
| C9 | Degradación: Desenfoque o calidad insuficiente | Gaussian blur de radio 0.15*min(width,height); emisión solo con varianza Laplaciana<=1 | INSUFFICIENT | IMPLEMENTED |
| C10 | Estrés OOD: Manipulación no vista durante el entrenamiento | Pendiente reservar familia de manipulación fuera de train; OOD no es cuarta clase de decisión corriente | OOD | NOT IMPLEMENTED |

C2/C3: cualquier donor futuro deberá pertenecer al mismo split; la versión actual rechaza donors y no emite esas condiciones. C5 requiere una manipulación validada junto con contradicción, no basta renombrar una imagen. C10 exige una familia reservada fuera del entrenamiento; no hay C10 emitido ni una cuarta clase OOD añadida al enum de decisión. Su etiqueta canónica OOD se conserva en el registro de condiciones para la futura evaluación específica.

## Narrativas y semántica de labels

C0 enumera únicamente tipos de daño anotados. Se usan tres realizaciones breves, con clases específicas y selección estable por SHA256(seed, source ID); no se presupone la parte del auto ni el origen del accidente. C1 niega explícitamente una clase realmente anotada, evitando inferir que una clase no anotada está ausente. C6/C7 eliminan una modalidad: no se consideran fraude.

SUPPORTED/SUSPICIOUS/INSUFFICIENT son **labels esperados de escenarios controlados**, no resoluciones de seguros ni fraude confirmado. C8 usa JPEG quality=95, subsampling=0, sin recortar/redimensionar; se exige PSNR >=35 dB contra la imagen fuente. JPEG benigno conserva SUPPORTED. PSNR=100 es un límite inferior registrado para la eventual igualdad exacta (MSE=0), no infinito serializado.

C9 usa GaussianBlur(radius=0.15*min(width,height)) y exige varianza Laplaciana <=1.0 para registrar calidad insuficiente. Son umbrales operativos conservadores fijados antes de aplicar a todas las imágenes, **no una validación humana de observabilidad**. Solo 7 de 24 variantes pasaron; las otras 17 están en exclusions.json sin claim ni label. No se ajustaron parámetros para aceptar más casos tras observar resultados/test. No se eliminaron fuentes: cada una conserva su C0 y variantes restantes.

## Splits antes de variantes y prevención de leakage

Primero se auditan bytes, píxeles RGB y dHash128 de originales. Pares exactos o Hamming <=6 se unen transitivamente; el menor source_image_id identifica el grupo. Después se aplica el algoritmo existente de hash seed=42 + group ID (70/15/15). Por último se generan narrativas y transformaciones. No hay fit, normalización aprendida ni selección de parámetros sobre test.

Se congelaron 24 grupos: **17 train / 4 validation / 3 test**. Todos los claims de una fuente y sus padres C0 pertenecen al mismo split; 127 claims quedan **89 / 22 / 16**. La proporción es aproximada por hash, no estratificación. No se manipuló el split para balancear clases/condiciones. No hay claim_id de un expediente real multiimagen; cada claim experimental apunta a una fuente y se verifica además parent-claim/group leakage.

El audit no encontró duplicados exactos ni candidatos dHash; no prueba ausencia de otras vistas del mismo vehículo. Ver DATASET_AUDIT.md y NEAR_DUPLICATE_AUDIT.md para límites y grupos completos.

## Artefactos canónicos y reproducción

En `data/manifests/benchmark_v1/` se versionan **solo texto**: manifest.jsonl, splits.json, evidence_packets.jsonl, dataset_audit.json, validation.json, exclusions.json y metadata.json. Metadata contiene SHA256 reales de artefactos/config/registro/recibo y versiones de Pillow/numpy/OpenCV. Imágenes originales y derivadas permanecen ignoradas, no se suben a Git.

Desde Repo A:

```bash
# Solo si faltan los archivos originales: descarga pública de la muestra fijada.
python3 scripts/fetch_hitl_pilot.py --receipt data/hitl_pilot_receipt.json --output data/raw/hitl_pilot_v2
# Generación/verificación idempotente: rechaza sobrescribir artefactos distintos.
env -u PYTHONPATH OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 .venv/bin/python scripts/build_claim_benchmark.py
# Recalcular duplicados, near-duplicates, variantes, hashes y semántica desde raw:
env -u PYTHONPATH OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 .venv/bin/python scripts/build_claim_benchmark.py --check --verify-images
# Validación schema/manifest/packets/splits sin raw (CI):
env -u PYTHONPATH .venv/bin/python scripts/build_claim_benchmark.py --check
env -u PYTHONPATH .venv/bin/python scripts/check_splits.py --manifest data/manifests/benchmark_v1/manifest.jsonl --group-key source_image_id --split-key split
env -u PYTHONPATH OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 .venv/bin/python -m pytest -q
```

Los tests de generación usan imágenes sintéticas pequeñas en tmp_path; no descargan datos. La regeneración de JPEG/dHash/blur debe usar las versiones registradas: un cambio de biblioteca que altere bytes se detecta por hash, no se ignora. Ampliar fuentes o cambiar agrupación/plantillas/parámetros exige una nueva versión y nuevo lock, conservando los artefactos congelados. `--output` permite construir en otra carpeta para comparar sin sobrescribir.

## EvidencePacket y frontera de disponibilidad

Cada ClaimRecord se serializa como EvidencePacket 0.2.0. `narrative`, `visual`, `image_quality`, `forensic` están explícitamente null: no se ejecutó NLI ni ningún encoder/detector/forense para producir estos packets. Las métricas de la transformación son comprobaciones del generador, no salidas de especialistas. El packet conserva el texto/referencia de imagen en claim; el grafo actual puede representarlo como nodo claim sin fabricar evidencia.

## Limitaciones científicas y siguiente revisión

24 imágenes no bastan para conclusiones generalizables; solo tres fuentes de test. C2–C5/C10 pendientes; C8 parcial; C9 tiene cobertura selectiva por un criterio heurístico, no etiquetas de observabilidad adjudicadas por expertos. No hay daño/partes localizados en texto ni expedientes reales. El benchmark es una primera versión real y reproducible de escenarios controlados, no la validación final de la tesis.

Riesgo explícito de **shortcut lingüístico**: todos los C1 usan negaciones o “libre de”; todos los SUSPICIOUS actuales son C1. La ausencia de modalidades determina C6/C7 y un blur extremo caracteriza C9 por diseño. No presentar buen desempeño en esta versión como evidencia de razonamiento multimodal/reliability. Se necesita revisión semántica y diversificación controlada de narrativas/contradicciones antes de una comparación científica robusta. No se entrenó un clasificador para medir estos shortcuts.

Aprobación de leakage acotada: PASS para fuentes/grupos/duplicados medidos y padres de los 127 claims. No aprobación absoluta de independencia por vehículo/incidente. Esta fase se detiene en congelación y auditoría: no entrena B0–B8 ni implementa P1/P2.
