# HITL full-source scale audit

Fuente: [Humans in the Loop](https://humansintheloop.org/resources/datasets/car-parts-and-car-damages-dataset/) y [Kaggle versión 2](https://www.kaggle.com/datasets/humansintheloop/car-parts-and-car-damages). Licencia declarada CC0 1.0, consultada en esta fase.

El índice ZIP público contiene 7250 entradas y 3103430533 bytes comprimidos. Conteos de imágenes por raíz reales: {'Car damages dataset': 998, 'Car parts dataset': 814}.
Los nombres de carpetas están intercambiados respecto a su contenido: se eligió la raíz cuyo meta.json coincide exactamente con las ocho clases canónicas de daño.
Se adquirieron 1629 archivos (554040448 bytes): 814 imágenes, 814 anotaciones y meta.json. La selección incluye TODO el subconjunto de daño; excluye exportaciones raster redundantes y las 998 imágenes del subconjunto anotado solo con partes, que no establecen ausencia/presencia de daño.

Se usaron rangos HTTP del ZIP sin credenciales; CRC32 y longitud por entrada, SHA256 por archivo y lector estricto después de descarga. No se descargó el ZIP completo ni se guardaron redirecciones firmadas. Receipt: data/hitl_full_receipt.json.

Disponibles: 814; aceptadas por contrato actual: 807; anotaciones aceptadas: 8979. Hay 783 fuentes válidas adicionales respecto a las 24 de v2; las 24 originales están presentes y sus bytes coinciden.

Cuatro rechazos contienen polígonos con huecos no representables por el contrato actual (no se declaran erróneos); tres contienen polígonos degenerados. No se descartan silenciosamente objetos ni se alteran raw. Se excluye el par completo del benchmark.

| annotation_reference | reason |
| --- | --- |
| data/raw/hitl_full_v2/Car parts dataset/File1/ann/Car damages 1155.png.json | Only simple polygon exteriors are supported; geometry was not discarded |
| data/raw/hitl_full_v2/Car parts dataset/File1/ann/Car damages 1161.png.json | Only simple polygon exteriors are supported; geometry was not discarded |
| data/raw/hitl_full_v2/Car parts dataset/File1/ann/Car damages 1165.png.json | Only simple polygon exteriors are supported; geometry was not discarded |
| data/raw/hitl_full_v2/Car parts dataset/File1/ann/Car damages 1169.jpg.json | Only simple polygon exteriors are supported; geometry was not discarded |
| data/raw/hitl_full_v2/Car parts dataset/File1/ann/Car damages 214.png.json | Degenerate polygon |
| data/raw/hitl_full_v2/Car parts dataset/File1/ann/Car damages 992.jpg.json | Degenerate polygon |
| data/raw/hitl_full_v2/Car parts dataset/File1/ann/Car damages 998.png.json | Degenerate polygon |

Reproducción: `env -u PYTHONPATH .venv/bin/python scripts/fetch_hitl_full.py`, seguido por `scripts/build_benchmark_v3.py`. La descarga es reanudable y rechaza archivos existentes con CRC/longitud distintos. Las imágenes/anotaciones/máscaras permanecen ignoradas por Git.
