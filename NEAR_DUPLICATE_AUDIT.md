# NEAR DUPLICATE AUDIT — benchmark v1

## Método y umbral fijados antes del análisis

Se calcula dHash128 determinista: escala de grises y LANCZOS a 9×8 para 64 comparaciones horizontales, y a 8×9 para 64 comparaciones verticales. Bits de comparación `pixel_actual > pixel_siguiente`, concatenados. Distancia de Hamming <= **6 de 128 bits** marca candidatos. Umbral fijo en configs/benchmark_v1.yaml; no se ajustó con validation/test. No modelos, embeddings ni estadísticas aprendidas.

Además se comparan SHA256 de archivos y de `(dimensiones, píxeles RGB decodificados)` para detectar imágenes iguales con distinta codificación. Se evaluaron los 276 pares de las 24 fuentes.

## Pares sospechosos y decisión

No se detectaron pares exactos ni candidatos bajo el criterio declarado. No se eliminó ninguna imagen.

Política implementada y probada: unir por componentes conexas todos los pares exactos o candidatos, incluso si el par podría ser un falso positivo. Todos los miembros quedan en un split. No eliminación automática. El ID del grupo es el menor source_image_id lexicográfico; se aplica después el hash canónico seed=42 + ID del grupo, con ratios 0.70/0.15/0.15. Las variantes se generan al final y heredan ese split. No se reorganizaron splits para mejorar el balance observado.

## Grupos finales utilizados

| Group ID | Miembros | Split |
|---|---|---|
| `hitl:Car damages 1074` | hitl:Car damages 1074 | train |
| `hitl:Car damages 1172` | hitl:Car damages 1172 | train |
| `hitl:Car damages 1220` | hitl:Car damages 1220 | train |
| `hitl:Car damages 159` | hitl:Car damages 159 | train |
| `hitl:Car damages 163` | hitl:Car damages 163 | test |
| `hitl:Car damages 210` | hitl:Car damages 210 | train |
| `hitl:Car damages 250` | hitl:Car damages 250 | train |
| `hitl:Car damages 256` | hitl:Car damages 256 | test |
| `hitl:Car damages 259` | hitl:Car damages 259 | train |
| `hitl:Car damages 296` | hitl:Car damages 296 | train |
| `hitl:Car damages 463` | hitl:Car damages 463 | train |
| `hitl:Car damages 482` | hitl:Car damages 482 | train |
| `hitl:Car damages 495` | hitl:Car damages 495 | train |
| `hitl:Car damages 498` | hitl:Car damages 498 | train |
| `hitl:Car damages 619` | hitl:Car damages 619 | train |
| `hitl:Car damages 645` | hitl:Car damages 645 | train |
| `hitl:Car damages 698` | hitl:Car damages 698 | validation |
| `hitl:Car damages 708` | hitl:Car damages 708 | validation |
| `hitl:Car damages 867` | hitl:Car damages 867 | validation |
| `hitl:Car damages 899` | hitl:Car damages 899 | train |
| `hitl:Car damages 915` | hitl:Car damages 915 | validation |
| `hitl:Car damages 916` | hitl:Car damages 916 | train |
| `hitl:Car damages 986` | hitl:Car damages 986 | train |
| `hitl:Car damages 999` | hitl:Car damages 999 | test |

## Alcance y reproducción

`dataset_audit.json` registra fingerprints, pares y componentes; `splits.json` congela la asignación. `python scripts/build_claim_benchmark.py --check --verify-images` recalcula desde los archivos reales, verifica agrupaciones, recrea las variantes y comprueba hashes del manifest; requiere raw local. `--check` sin esa opción valida los artefactos versionados sin raw (CI).

No detectar candidatos **no prueba ausencia universal de leakage**. dHash no garantiza detectar recortes, grandes rotaciones, otras vistas del mismo vehículo ni ediciones localizadas. El umbral conserva similitud global muy fuerte; los controles requieren revisión humana y auditoría adicional al ampliar el dataset. La ausencia de IDs de vehículo/incidente limita la independencia comprobable. La aprobación de leakage en esta fase está acotada al método y a los 24 archivos auditados.
