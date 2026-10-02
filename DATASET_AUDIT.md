# DATASET AUDIT — HITL local, 2026-10-02

## Source / license / local path

- Fuente: [Humans in the Loop](https://humansintheloop.org/resources/datasets/car-parts-and-car-damages-dataset/), publicación de autores [Kaggle v2](https://www.kaggle.com/datasets/humansintheloop/car-parts-and-car-damages).
- Licencia declarada por el autor: CC0 1.0. Procedencia y URLs/hashes de adquisición en `data/hitl_pilot_receipt.json`.
- Ruta relativa: `data/raw/hitl_pilot_v2/Car parts dataset`.
- Ruta absoluta inspeccionada: `/home/ana/Documentos/tesis 2/vehicle-claim-verification-baselines/data/raw/hitl_pilot_v2/Car parts dataset`.
- La carpeta llamada Car parts dataset contiene las clases de DAÑO; ambos meta.json reales se verificaron en la fase de adquisición. No se infiere taxonomía del nombre de carpeta.

## Counts reales locales

- Imágenes: **24**, JSON de anotación: **24**, objetos anotados: **256**.
- Sin archivo de anotación: 0; sin objetos anotados: 0.
- Archivos corruptos/dimensiones inconsistentes/anotaciones estructuralmente inválidas detectadas: 0/0. Todos los registros pasaron el lector estricto; no se descartaron imágenes ni objetos.
- Las 814 imágenes son el tamaño publicado del subconjunto remoto, **NO el número local**. Esta fase no amplió ni duplicó raw data.
- Resoluciones: ancho 496–886 px; alto 375–599 px.
- Formatos por extensión: {'.png': 23, '.jpg': 1}.

| Clase canónica | Anotaciones |
|---|---:|
| broken_part | 42 |
| corrosion | 2 |
| crack | 5 |
| dent | 52 |
| flaking | 14 |
| missing_part | 23 |
| paint_chip | 48 |
| scratch | 70 |

## Annotation format e integrity checks

JSON por imagen estilo Supervisely: `objects/classTitle/geometryType/points/size`, con polígonos `exterior` y posibles `interior`. El lector canónico valida las ocho clases, decodificación, dimensiones, coordenadas numéricas finitas, límites y área no nula. Rechaza huecos y geometrías no representables; todos los objetos locales resultaron aceptados. Esto no equivale a verificar topología completa de polígonos o exactitud de anotación mediante expertos.

SHA256 de bytes y de píxeles RGB, y dHash128 por imagen en `data/manifests/benchmark_v1/dataset_audit.json`. No se incluyen bytes de imagen ni copia de los JSON raw en Git. El manifest de reclamos referencia la anotación original y su hash, y solo incorpora la lista de clases anotadas como ground truth de auditoría, nunca como output visual predicho.

## Duplicados y limitaciones

Pares de bytes exactos: 0; pares de píxeles idénticos: 0; candidatos dHash<=6: 0. Ver NEAR_DUPLICATE_AUDIT.md.

Muestra pequeña elegida por hash de rutas antes de esta fase, no representativa del dominio. No hay IDs verificables de incidente/vehículo/póliza ni expedientes reales; no se inventaron. No hay narrativas/veredictos de aseguradora: los reclamos se generan de forma controlada sobre anotaciones. Nombres de clase no proporcionan localización anatómica/parte del vehículo: las narrativas no atribuyen puertas/parachoques sin evidencia. Falta adjudicación semántica humana independiente y revisión de fotos del mismo vehículo desde otros ángulos.
