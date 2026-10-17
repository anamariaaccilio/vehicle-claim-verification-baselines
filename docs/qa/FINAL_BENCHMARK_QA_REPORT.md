# FINAL BENCHMARK QA REPORT

La generación y verificación de ingeniería terminaron. La preparación científica
para empezar modelos **no está aprobada**. No se entrenó B0–B8, no se implementó
P1/P2 y no se hizo push.

Este reporte de cierre se guarda en la carpeta padre para registrar los commits
finales de ambos repositorios sin alterar el commit canónico fijado por el lock.
El benchmark, generadores, galerías y auditorías científicas están exclusivamente
en vehicle-claim-verification-baselines. No se creó otro repositorio.

## A. Benchmark version revisada

V2: benchmark 0.2.0, schema 0.3.0, preservado. V3: candidato benchmark 0.3.0,
schema 0.3.0, generado tras QA y ampliación real. Taxonomía C0–C10: tabla autorizada
por el usuario; no se afirma haber cotejado el .tex ausente.

Manifest v2 SHA256: `3e45880e3a0d5d949bded72b278d80d8366a0ede963c58631affc3258619f9fe`.
Manifest v3 SHA256: `378e1cdd698cb417720637adcd7da2d85a060a884c73fa3f67755e066f465588`.
Splits v3 SHA256: `b15029098e71d4834d6ca0ea0360a34a43819593928f8728ef40efc7ef8873f8`.
EvidencePackets v3 SHA256: `4cf1338d8f68e3b2d9066ab5b8179038aa27c457fcbaf40f020f0970a50410b6`.

Manifest v3: `/home/ana/Documentos/tesis 2/vehicle-claim-verification-baselines/data/manifests/benchmark_v3/manifest.jsonl`.

## B. Número de imágenes fuente

V2: 24. Se verificó el índice ZIP de Kaggle versión 2: 814 imágenes del subconjunto
anotado con daño y 998 del subconjunto anotado con partes. La carpeta de daño se
identificó por meta.json, no por su nombre intercambiado. Se descargó el subconjunto
completo de daño: 814 imágenes+814 anotaciones+meta.json, 1.629 archivos, 554.040.448 bytes.

**807 fuentes aceptadas**, con 8.979 objetos anotados; **783 adicionales** al piloto.
Las 24 originales están presentes con los mismos hashes; las copias históricas del
piloto no se cuentan otra vez. Siete pares se excluyen bajo el contrato actual:
cuatro contienen huecos de polígonos no soportados —no se declaran erróneos— y tres
contienen polígonos degenerados. Todos los raw se conservan. Las 998 imágenes con
anotaciones de partes no se convierten automáticamente en ejemplos sin daño.

Fuente y licencia declarada CC0 1.0: [Humans in the Loop](https://humansintheloop.org/resources/datasets/car-parts-and-car-damages-dataset/).
Adquisición pública versionada, sin credenciales; CRC/longitud y SHA256 registrados.
Detalles y cada exclusión: [DATASET_SCALE_AUDIT.md](</home/ana/Documentos/tesis 2/vehicle-claim-verification-baselines/DATASET_SCALE_AUDIT.md>).

## C. Número de claims derivados

V2: 226. V3:**9275**. Cada uno tiene EvidencePacket canónico con
especialistas null, sin outputs ficticios. Son escenarios controlados/sintéticos
sobre imágenes reales, no reclamos reales de una aseguradora.

Las 226 variantes v2 NO son 226 observaciones independientes; proceden de 24 fuentes.
Tampoco las 9.275 variantes v3 son 9.275 observaciones independientes. La unidad es
source_image_id y, cuando corresponde, source_group_id/claim source group.

## D. Distribución C0–C10

| Condición | V2 | V3 |
|---|---:|---:|
| C0 | 24 | 807 |
| C1 | 24 | 807 |
| C2 | 24 | 807 |
| C3 | 24 | 807 |
| C4 | 24 | 807 |
| C5 | 24 | 807 |
| C6 | 24 | 807 |
| C7 | 24 | 807 |
| C8 | 24 | 2421 |
| C9 | 7 | 269 |
| C10 | 3 | 129 |

Las variantes preservan parent, source, group, split, seed y parámetros. Ninguna
etiqueta C2 se cambió automáticamente a raíz de la auditoría.

## E. Distribución de labels

| Label esperado | V2 | V3 |
|---|---:|---:|
| SUPPORTED | 48 | 3228 |
| SUSPICIOUS | 120 | 4035 |
| INSUFFICIENT | 55 | 1883 |
| OOD | 3 | 129 |

OOD corresponde únicamente a test/C10. DecisionLabel conserva las tres clases
ordinarias: OOD no es una cuarta clase de entrenamiento.

## F. Distribución por clase de daño

| Clase | Objetos v2 | Objetos v3 | Fuentes v3 que la contienen | Claims v3 con esa clase de fuente |
|---|---:|---:|---:|---:|
| broken_part | 42 | 1480 | 657 | 7524 |
| corrosion | 2 | 277 | 109 | 1266 |
| crack | 5 | 76 | 67 | 773 |
| dent | 52 | 1655 | 624 | 7171 |
| flaking | 14 | 337 | 108 | 1235 |
| missing_part | 23 | 624 | 430 | 4950 |
| paint_chip | 48 | 1340 | 277 | 3195 |
| scratch | 70 | 3190 | 513 | 5905 |

Son clases multilabel de la fuente original: las columnas de fuentes/claims no
son particiones ni observaciones independientes. No son predicciones de especialistas.
C2 referencia adicionalmente la anotación del donante; las composiciones no tienen
una nueva anotación exhaustiva de daño adjudicada. C8 conserva la transformación
geométrica necesaria para interpretar las anotaciones de la fuente.

## G. Train/validation/test por source_image_id

| Split | Fuentes v2 | Fuentes/grupos v3 | Claims v3 |
|---|---:|---:|---:|
| train | 17 | 568 | 6428 |
| validation | 4 | 110 | 1256 |
| test | 3 | 129 | 1591 |

Agrupación de duplicados antes de asignación por hash+seed 42; variantes después.
Las proporciones realizadas no se fuerzan al número exacto de los ratios teóricos.
La evaluación futura exige intervalos/bootstraps agrupados y comparaciones emparejadas.
C2 conecta fuente y donante: los componentes de dependencia resultantes son
{'test': 4, 'train': 3, 'validation': 1}. Es especialmente limitante que haya
solo cuatro componentes en test y uno en validation; 129 fotos no eliminan esa dependencia.
Ver [protocolo estadístico](</home/ana/Documentos/tesis 2/vehicle-claim-verification-baselines/STATISTICAL_EVALUATION_PROTOCOL.md>).
No se ejecutó un bootstrap ni se inventaron intervalos de rendimiento.

## H. Duplicate audit

Fuentes v2/v3: cero pares exactos de bytes o píxeles RGB detectados.
Los hashes de imágenes utilizadas por los claims no cruzan splits. Reutilizar una
imagen como donante o como C0/C1/C6 dentro del split es deliberado; no equivale a
independencia. No se eliminó raw automáticamente.

## I. Near-duplicate audit

dHash 128, distancia <= 6 prefijada. V3: 807 fuentes, 325.221 pares, 0 candidatos bajo
umbral y 807 grupos singleton. Menor distancia observada: 15. Los 20 pares más
cercanos fuera del umbral se documentan para revisión, sin declararlos duplicados.
No prueba independencia por vehículo/incidente: esos IDs no están disponibles.
[Auditoría completa](</home/ana/Documentos/tesis 2/vehicle-claim-verification-baselines/NEAR_DUPLICATE_FULL_AUDIT.md>).

## J. C2 semantic audit

V2: 5 likely compatible, 18 ambiguous, 1 likely contradiction.
V3: 510 likely compatible, 297 likely contradiction; no solapamiento parcial porque
v3 narra una sola clase objetivo. Estas son categorías de una **heurística de
anotaciones**, no contradicciones confirmadas visualmente por un humano.
Ausencia de una clase anotada no prueba su ausencia visible. Ubicación anatómica:
UNKNOWN, porque no está expresada en estas narrativas ni en la taxonomía de daño.
Se registra similitud dHash y cada donor/source, con donor del mismo split.

Una sustitución conocida por procedencia puede ser indistinguible de un reclamo
compatible usando solo narrativa+imagen. No se cambian labels para ocultarlo.
[Cada C2 de v2](</home/ana/Documentos/tesis 2/vehicle-claim-verification-baselines/C2_SEMANTIC_AUDIT.md>) · [Cada C2 de v3](</home/ana/Documentos/tesis 2/vehicle-claim-verification-baselines/C2_SEMANTIC_AUDIT_V3.md>).

## K. C3 forensic audit

V2: 24 casos; v3: 807 casos comprobados con los archivos reales. Máscaras no vacías,
bounds válidos, copia de la propia fuente válida, píxeles fuera de máscara conservados
y transformación reproducible. Todos los copy-move de v2/v3 están por debajo del
umbral descriptivo de 0,5% de área modificada. La ventana 24×24 puede ser poco visible
al reducir la imagen: se registra su tamaño a 360 px de visualización. No se certifica
que sea perceptible o realista; no se alteran labels ni se excluyen automáticamente.
[C3 v2](</home/ana/Documentos/tesis 2/vehicle-claim-verification-baselines/C3_FORENSIC_AUDIT.md>) · [C3 v3](</home/ana/Documentos/tesis 2/vehicle-claim-verification-baselines/C3_FORENSIC_AUDIT_V3.md>).

## L. C4 inpainting audit

V3: 807 máscaras comprobadas contra el polígono anotado seleccionado; cambios
reales y localizados, exterior conservado y regeneración exacta. 755 casos
modifican<0,5%; 1 superan 20%. Hay 0 alertas del criterio
heurístico de incremento del gradiente de borde>2×original. No son diagnósticos de
realismo ni su ausencia implica un buen inpainting. La operación Telea está
verificada; damage_removal_verified=false y revisión humana NOT PERFORMED.
[C4 v2](</home/ana/Documentos/tesis 2/vehicle-claim-verification-baselines/C4_INPAINT_AUDIT.md>) · [C4 v3](</home/ana/Documentos/tesis 2/vehicle-claim-verification-baselines/C4_INPAINT_AUDIT_V3.md>).

## M. C5 combined audit

Los 24 casos v2 y 807 v3 pasan dos comprobaciones separadas: (1) la narrativa niega
una clase realmente anotada, cuyos píxeles originales siguen intactos; (2) hay
copy-move efectivo y reproducible. Esto establece la combinación operacional bajo
las anotaciones, no adjudicación humana. Conserva el problema de tamaño pequeño.
[C5 v2](</home/ana/Documentos/tesis 2/vehicle-claim-verification-baselines/C5_COMBINED_AUDIT.md>) · [C5 v3](</home/ana/Documentos/tesis 2/vehicle-claim-verification-baselines/C5_COMBINED_AUDIT_V3.md>).

## N. C8 benign controls

V2 se conserva con 24 JPEG. V3 contiene 807 C8_JPEG, 807 C8_RESIZE y 807 C8_CROP,
todos SUPPORTED. Subtype se registra en transformation.parameters.subtype.
JPEG95 exige PSNR >= 35 dB. Resize 1,25× usa Lanczos y registra escala real por eje.
Crop recorta como máximo 5% por borde y conserva TODOS los píxeles de daño anotado;
registra crop_box, tamaño, conteo retenido y traslación de coordenadas. Si no
hubiera margen seguro se excluiría, nunca se forzaría; en estas 807 fuentes sí lo hubo.
[Controles C8](</home/ana/Documentos/tesis 2/vehicle-claim-verification-baselines/C8_BENIGN_CONTROLS_AUDIT.md>).

## O. C9 degradation audit

Se conserva radius=0,15×min(width,height) y aceptación por varianza Laplaciana <= 1,0.
V2 mantiene 7 aceptados/17 excluidos; se comprobó que esas 24 fuentes conservan su
resultado en v3. Total v3: 269 aceptados/538 excluidos. Cada valor y decisión está
registrado, sin forzar exclusiones a convertirse en claims. Es un criterio operacional,
no prueba universal de insuficiencia semántica.
[C9 v2](</home/ana/Documentos/tesis 2/vehicle-claim-verification-baselines/C9_DEGRADATION_AUDIT.md>) · [C9 v3](</home/ana/Documentos/tesis 2/vehicle-claim-verification-baselines/C9_DEGRADATION_AUDIT_V3.md>).

## P. C10 OOD audit

Familia exacta: inversión RGB localizada, 255-RGB dentro del menor polígono de daño
rasterizado. Tres casos v2 y 129 v3, exclusivamente test. La familia no aparece en
train ni validation. Esto es un holdout procedimental; no se entrenó un modelo ni
se asegura que un futuro encoder preentrenado nunca haya visto inversiones de color.
[Auditoría C10](</home/ana/Documentos/tesis 2/vehicle-claim-verification-baselines/C10_OOD_AUDIT.md>).

## Q. Narrative shortcut audit

V2: 202 narrativas no vacías, 33 distintas, 83,663% de duplicados. Se detectaron
negaciones exclusivas de narrativas sospechosas y diferencias de estructura/longitud.

V3 final: 8.468 no vacías, 960 distintas, 88,663% de duplicados; 807 narrativas ausentes
se cuentan por separado. El porcentaje incluye la repetición intencional de una
narrativa en varias condiciones del mismo source; no equivale a independencia textual.

Se corrigió el generador mediante target común C0/C1/C5, cuatro formas semánticas
emparejadas y ocho prefijos/cuatro cierres neutrales por seed/hash, compartidos entre
etiquetas. No añade hechos del vehículo ni datos personales. El borrador previo
con 64 textos se conservó como no publicado; los artefactos finales contienen 960.

La mitigación no elimina el atajo semántico: C1/C5 siguen negando daños presentes y
faltan controles de ausencia compatibles adjudicados. La naturalidad y los patrones
composicionales requieren revisión. Se calcularon media/desviación por condición y por
etiqueta, plantilla, puntuación y asociaciones unigram/bigram por frecuencia documental,
precision/lift. No se ajustó ningún clasificador ni se presentaron p-valores sobre
variantes dependientes. [V2 y corrección](</home/ana/Documentos/tesis 2/vehicle-claim-verification-baselines/NARRATIVE_SHORTCUT_AUDIT.md>) · [V3 detallado](</home/ana/Documentos/tesis 2/vehicle-claim-verification-baselines/NARRATIVE_SHORTCUT_AUDIT_V3.md>).

## R. QA visual generado

- [benchmark_v2_qa.html](</home/ana/Documentos/tesis 2/vehicle-claim-verification-baselines/benchmark_v2_qa.html>): 226 reclamos y 527 referencias de imagen.
- [benchmark_v3_qa.html](</home/ana/Documentos/tesis 2/vehicle-claim-verification-baselines/benchmark_v3_qa.html>): 9.275 reclamos y 21.100 referencias.
- [Muestra rápida v3](</home/ana/Documentos/tesis 2/vehicle-claim-verification-baselines/benchmark_v3_qa_sample.html>): 39 reclamos seleccionados determinísticamente.

Se incluyen IDs, condition, label, narrativa, original, imagen presentada, donor,
mask, parámetros y seed. Filtro por condición y búsqueda; imágenes a tamaño completo
al hacer clic. Revisión local exportable como JSON con hash del manifest/selección.
No cambia labels. Se verificaron todas las referencias, sintaxis JavaScript y
regeneración byte a byte de galerías/resúmenes. No se afirma revisión humana ni
prueba interactiva completa en un navegador.

## S. Limitaciones restantes

C2 puede ser no identificable con las modalidades disponibles; manipulación demasiado
pequeña y ausencia de revisión de realismo; semántica/estilo sintéticos y repetición;
fuertes dependencias fuente/donante; desconocimiento de vehículo/incidente real;
siete anotaciones no incorporadas bajo el contrato actual. Más imágenes no resuelven
estos problemas por sí mismas. Metadatos/labels/anotaciones son auditoría, no features.
La QA examinó también test para diseñar el benchmark: no presentarlo como un conjunto
confirmatorio completamente ciego. Antes de resultados finales hará falta un protocolo
confirmatorio independiente o una versión preregistrada y adjudicada.

La siguiente acción es revisión humana de C2 y composiciones, controles semánticos
compatibles y definición del diseño estadístico; no entrenamiento automático.

## T. Tests y validaciones

Repo A: pytest -q **127 passed, 5 skipped**, sin failed/errors. Con --run-model-tests:
**132 passed**, sin failed/skipped/errors; un FutureWarning ya existente de torch.jit.script.
Repo B:**18 passed**, sin failed/skipped/errors. Las pruebas opcionales usan el NLI
cacheado en modo offline, sin entrenamiento ni nuevos pesos descargados.

PASS: regeneración completa v3 desde raw, masks/hashes/semántica, auditoría de píxeles
C3/C4/C5, split audit v2/v3, checksums, schema/packets, reproducción byte a byte de
resúmenes/galerías, preservación byte a byte de manifest/splits/packets/configs v2,
git diff --check y escaneo de rutas/patrones comunes de secretos sin hallazgos.
El escaneo de patrones no es una prueba absoluta de ausencia de secretos.

UAFEG sigue consumiendo `data/manifests/benchmark_v2/manifest.jsonl`, benchmark 0.2.0;
se actualizó el commit canónico real a `417084d12a92d9081d6a1b66078ea3b39bb9dccc` para mantener el lock
verificable, sin promover automáticamente v3. pin_benchmark.py --check pasó.

Logs reales preservados: `/home/ana/Documentos/tesis 2/.benchmark-phase-validation/scientific_qa`.

```bash
cd '/home/ana/Documentos/tesis 2/vehicle-claim-verification-baselines'
env -u PYTHONPATH .venv/bin/python scripts/fetch_hitl_full.py
env -u PYTHONPATH .venv/bin/python scripts/build_benchmark_v3.py
env -u PYTHONPATH .venv/bin/python scripts/build_benchmark_v3.py --check --verify-images
env -u PYTHONPATH .venv/bin/python scripts/audit_benchmark_v2.py
env -u PYTHONPATH .venv/bin/python scripts/summarize_benchmark_qa.py
env -u PYTHONPATH .venv/bin/python scripts/audit_benchmark_v3_pixels.py
env -u PYTHONPATH .venv/bin/python scripts/check_splits.py --manifest data/manifests/benchmark_v3/manifest.jsonl --group-key source_image_id --split-key split
env -u PYTHONPATH OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/python -m pytest -q
env -u PYTHONPATH OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/python -m pytest -q --run-model-tests
git diff --check
git status --short
cd '/home/ana/Documentos/tesis 2/uafeg'
env -u PYTHONPATH .venv/bin/python scripts/pin_benchmark.py --check
env -u PYTHONPATH .venv/bin/python -m pytest -q
git diff --check
git status --short
```

En una instalación nueva, QA v2 requiere adquirir su piloto con fetch_hitl_pilot.py
--receipt data/hitl_pilot_receipt.json --output data/raw/hitl_pilot_v2 y regenerar
build_benchmark_v2.py. CI sin raw usa --check sin --verify-images; los tests no
requieren la descarga completa. Las versiones congeladas rechazan sobrescrituras diferentes.

## U. Commits realizados

Repo A:

```text
417084d12a92d9081d6a1b66078ea3b39bb9dccc docs: record scientific QA limitations and human review galleries
c8b177d87becd6138ea80547a91b10856b0d0f44 feat: generate full HITL v3 benchmark with reproducible scientific QA
```

Repo B:

```text
edfb92f1313de28e91d11f53a8ed5532c1256832 chore: refresh canonical revision while retaining frozen v2 benchmark
```

Solo commits locales. Historial preservado, sin push ni reestructuración de repositorios.

## V. Git status

Repo A: limpio,git status --short vacío. Repo B: limpio,git status --short vacío.
Raw, imágenes derivadas, máscaras, .env, weights, .venv y caches no están versionados.
El borrador de narrativas v3 se conserva ignorado y no es el manifest final ni está
fijado por UAFEG. Los datos y anotaciones originales no se eliminaron ni alteraron.

## Decisión final

1. C2 contiene numerosas sustituciones plausibles; la procedencia conocida no demuestra contradicción observable.
2. Falta adjudicación humana de composiciones/etiquetas; las manipulaciones son frecuentemente muy pequeñas.
3. Persisten atajos semánticos y lenguaje artificial pese a corregir longitud, negación y diversidad de estilo.
4. La dependencia fuente/donante y la exposición de test durante QA requieren un diseño confirmatorio antes de conclusiones científicas.

READY_FOR_MODELS = NO
