# Datos

## Estado verificado en la fase de datos (2026-10-02)

Se obtuvo un piloto real de 24 imágenes de HITL v2 con 256 anotaciones.
Ver [fuentes, hallazgos y reproducción](../docs/DATASET_DISCOVERY.md).
La exportación real consultada es estilo Supervisely, no COCO: usar
`src/data/hitl_supervisely.py`. Los nombres de las carpetas están invertidos;
el lector valida `meta.json` antes de aceptar clases de daño.
El manifest del piloto está en `data/manifests/hitl_pilot_v2.jsonl` y no
constituye todavía el benchmark experimental de reclamos.

La sección COCO siguiente describe el adapter preexistente y sus supuestos,
no el formato observado en Kaggle v2. Su fusión de variantes no está validada
para entrenamiento y no se utiliza en el piloto.

## Dataset principal: Humans in the Loop — "Car Parts and Car Damages Dataset"

Este proyecto **no descarga el dataset automaticamente**. Descargalo manualmente
desde la fuente oficial de Humans in the Loop y coloca el contenido descomprimido en:

```
data/raw/hitl/
```

El adapter (`src/data/hitl_adapter.py`) espera encontrar, en algun lugar bajo
`data/raw/hitl/`, uno o mas archivos de anotaciones en formato COCO
(`*.json` con las claves `images`, `annotations`, `categories`), junto a las
imagenes referenciadas por `file_name`. Si el dataset se descarga con otra
estructura (por ejemplo, dividido en `train/`, `valid/`, `test/` al estilo
Roboflow), el adapter la soporta: recorre todos los `.json` bajo la carpeta
y **recalcula el split desde cero** por `source_image_id` (ver
`src/data/split.py`), ignorando cualquier split que venga preasignado en el
export original, para garantizar que no haya leakage entre splits.

Usamos inicialmente el subconjunto de **danios** (no el de partes del
vehiculo). Las categorias relevantes y su mapeo a la taxonomia canonica
interna estan en `configs/labels.yaml`:

| Clase HITL     | Clase canonica |
|----------------|----------------|
| Dent           | dent           |
| Cracked        | crack          |
| Scratch        | scratch        |
| Flaking        | flaking        |
| Broken part    | broken_part    |
| Paint chip     | paint_chip     |
| Missing part   | missing_part   |
| Corrosion      | corrosion      |

Cualquier categoria del export que no aparezca en ese mapping se ignora por
defecto (`unmapped_class_policy="skip"` en `parse_hitl_dataset`).

## Manifest interno

`src/data/manifest.py` + `src/data/split.py` generan un manifest JSONL en
`data/manifests/` con un registro por `source_image_id`, incluyendo su path,
split asignado, anotaciones y clases de danio presentes. Este manifest (no
las imagenes crudas) es lo que consumen los especialistas de vision y los
scripts de benchmark.

## CarDD

CarDD (https://cardd-ustc.github.io/) **no se descarga automaticamente**: requiere
su propio proceso de solicitud de acceso/licencia. Queda documentado aqui como
fuente de datos adicional a integrar en una fase posterior, mediante un adapter
analogo a `hitl_adapter.py`, una vez el usuario obtenga acceso por su cuenta.

## Estructura de esta carpeta

```
data/
├── raw/          # datasets descargados manualmente (no versionado en git)
│   └── hitl/     # <-- coloca aqui el dataset de Humans in the Loop
├── processed/    # artefactos derivados (no versionado en git)
├── manifests/    # manifest.jsonl generado (no versionado en git)
└── README.md
```
