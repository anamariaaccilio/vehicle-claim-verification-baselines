# Fuentes de datos y piloto de integración — 2026-10-02

Se consultaron fuentes oficiales y metadatos públicos de Kaggle sin credenciales. No se descargaron modelos ni se inició entrenamiento.

| Dataset | Evidencia consultada | Decisión |
|---|---|---|
| HITL Car Parts and Car Damages | Publicación de los autores: 814 imágenes de daños, 998 de partes, polígonos, CC0; Kaggle versión 2 | Elegido para piloto por correspondencia con las ocho clases existentes |
| CarDD | Sitio oficial: 4.000 imágenes, seis categorías; requiere solicitud/licencia del laboratorio | Candidato posterior, sin descargar mirrors ni enviar solicitudes |
| LPLenka COCO Car Damage Detection | API Kaggle: 80 imágenes declaradas, una clase damage o cinco partes, CC0; 15.630.103 bytes | Útil como smoke test alternativo, pequeño y taxonomía distinta. Descripción de splits suma 78: verificar antes de usar |
| anujms/car-damage-detection | API Kaggle: licencia Unknown, 130.044.688 bytes, sin descripción | No seleccionado; procedencia/licencia y anotaciones insuficientemente documentadas |

Fuentes primarias consultadas:

- [HITL oficial](https://humansintheloop.org/resources/datasets/car-parts-and-car-damages-dataset/)
- [Publicación HITL en Kaggle](https://www.kaggle.com/datasets/humansintheloop/car-parts-and-car-damages)
- [Metadatos públicos HITL](https://www.kaggle.com/api/v1/datasets/view/humansintheloop/car-parts-and-car-damages)
- [CarDD oficial](https://cardd-ustc.github.io/) y [licencia](https://cardd-ustc.github.io/docs/CarDD_license.pdf)
- [LPLenka](https://www.kaggle.com/datasets/lplenka/coco-car-damage-detection-dataset) y [metadatos](https://www.kaggle.com/api/v1/datasets/view/lplenka/coco-car-damage-detection-dataset)
- [Anuj](https://www.kaggle.com/datasets/anujms/car-damage-detection) y [metadatos](https://www.kaggle.com/api/v1/datasets/view/anujms/car-damage-detection)

## Hallazgos verificados directamente en archivos HITL v2

La lista pública contiene 7.250 archivos y 3.311.753.461 bytes en total. No se descargó el paquete completo. Las anotaciones usan `objects/classTitle/geometryType/points/size` y carpetas `ann/img`, estilo Supervisely, **no COCO**.

Los nombres de carpetas están invertidos respecto al contenido:

- `Car parts dataset/meta.json`: ocho clases de daño; 814 imágenes/anotaciones en su inventario.
- `Car damages dataset/meta.json`: 21 clases de partes; 998 imágenes/anotaciones.

Se verificaron ambos meta.json reales; no se eligió el subconjunto solo por su nombre. Para daños, todas las imágenes suman 536.824.090 bytes y sus anotaciones 17.215.402 bytes; las máscaras no son necesarias para el lector de polígonos del piloto.

El adapter COCO preexistente presupone otra exportación y fusiona anotaciones bajo el primer path cuando se repite la fuente. Una prueba sintética confirmó ese comportamiento. No se usa para estos archivos. Se conserva para compatibilidad y queda pendiente corregirlo/verificarlo antes de usarlo en otra exportación.

## Piloto real obtenido

24 imágenes, 24 anotaciones y dos meta.json: **50 archivos, 15.896.440 bytes**, verificados por tamaño y SHA256. Selección determinista: ordenar imágenes por SHA256 de `hitl-v2-pilot-42:` + ruta y tomar las primeras 24; sin escoger por clase o split.

El recibo versionado `data/hitl_pilot_receipt.json` contiene URLs públicas fijadas a versión 2 y SHA256; no contiene imágenes ni anotaciones raw. El inventario completo y los metadatos de búsqueda se conservaron fuera del repo, en `../project-history/phase2-data-discovery/` (reubicado 2026-10-17 desde `../.phase2-data-discovery/` durante la limpieza final del workspace; mismo contenido, fuera de ambos repos como fue diseñado).

El lector `src/data/hitl_supervisely.py` valida taxonomía, existencia/decodificación de imágenes, dimensiones, polígonos y límites. No mezcla geometrías de archivos distintos; rechaza IDs ambiguos, clases desconocidas, huecos y geometrías no representables. No transforma ground truth en predicciones del especialista visual.

Resultado real: 24 registros y 256 anotaciones. Instancias: dent 52, scratch 70, broken_part 42, missing_part 23, paint_chip 48, flaking 14, crack 5, corrosion 2. Esta muestra no es representativa ni suficiente para medir modelos científicamente.

Con seed 42 y el split canónico: **train 17 / validation 4 / test 3**. Cero solapamientos por source_image_id, SHA256 de archivo y SHA256 de píxeles RGB decodificados. Falta auditoría de near-duplicates y procedencia por vehículo/incidente; no se afirma independencia completa de escenas relacionadas.

Manifest piloto: `data/manifests/hitl_pilot_v2.jsonl`.
SHA256: `82d45a445a8c04481341ac6514871c75c8737a398c5c175966c1f29bdba63a37`.
Audit: `data/manifests/hitl_pilot_v2.audit.json`.
Estos artefactos locales están ignorados; se reconstruyen con los comandos siguientes.

## Reproducción desde Repo A

```bash
python3 scripts/fetch_hitl_pilot.py --receipt data/hitl_pilot_receipt.json --output data/raw/hitl_pilot_v2
env -u PYTHONPATH .venv/bin/python scripts/prepare_hitl_pilot.py \
  --dataset-dir 'data/raw/hitl_pilot_v2/Car parts dataset' \
  --manifest data/manifests/hitl_pilot_v2.jsonl \
  --audit data/manifests/hitl_pilot_v2.audit.json
env -u PYTHONPATH .venv/bin/python scripts/check_splits.py \
  --manifest data/manifests/hitl_pilot_v2.jsonl --group-key source_image_id --split-key split
env -u PYTHONPATH OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 .venv/bin/python -m pytest -q
```

Los scripts verifican artefactos existentes y rechazan sobrescribir contenido diferente. El fetch comprueba archivos descargados y también ZIP de un solo miembro devueltos por Kaggle. La primera descarga exploratoria detectó este formato ZIP y falló por tamaño; se corrigió el manejo del transporte y se completó/verificó el piloto, sin aceptar archivos truncados.

## Alcance científico pendiente

Son imágenes con anotaciones de daños, no expedientes de seguros con narrativas y veredictos de fraude. No se asignaron labels SUPPORTED/SUSPICIOUS/INSUFFICIENT a partir de daño visible. Para construir el benchmark de reclamos faltan narrativas/control de condiciones, reglas de etiquetado validadas y auditoría de shortcuts.

`benchmark.lock.json` de UAFEG mantiene manifest/splits/packets del benchmark en null: el manifest de imágenes de este piloto no debe hacerse pasar por el benchmark compartido de reclamos. El commit canónico se actualiza para registrar el lector de ingestión. No hay nuevos resultados B0–B8/P1/P2.

Próxima acción experimental: ampliar a las 814 imágenes de daños con la misma procedencia/versionado, auditar duplicados y definir el benchmark de reclamos antes de congelar el test set. No mezclar mirrors de HITL o CarDD como si fueran datasets independientes.
