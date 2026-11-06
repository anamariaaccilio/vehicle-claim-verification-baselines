# Guía técnica operativa

[Mapa del repositorio y scripts](../README.md) · [Preparar entrenamiento](../../uafeg/docs/TRAINING.md)

## Comprobar sin regenerar datos

Desde la raíz de este repositorio:

```bash
env -u PYTHONPATH OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python -m pytest -q
env -u PYTHONPATH .venv/bin/python scripts/build_benchmark_v3.py --check --verify-images
```

El segundo comando requiere imágenes locales. No descarga datos ni resuelve ambigüedades científicas. No cambiar `READY_FOR_MODELS` por el mero hecho de superar verificaciones estructurales.

## Estado de componentes

| Componente | Estado |
|---|---|
| B0 reglas | Implementado; depende de evidencia disponible. |
| B1 texto | Extractor NLI implementado; evaluación independiente pendiente. |
| B2 visual | Preparación/train/inferencia implementados; sin pesos locales entrenados. |
| B3 forense | Pendiente; archivos vacíos retirados durante limpieza. |
| B4 fusión aprendida | Características disponibles; clasificador pendiente. |
| B5, B7, B8 | Pendientes. |
| B6, P1, P2 | Implementados en Repo B; no entrenados sobre el benchmark. |
| Métricas/calibración/abstención | Código disponible; evaluación científica pendiente. |

## Versiones y auditorías

V1/v2 son versiones históricas congeladas. V2 es la versión que referencia el lock del Repo B. V3 es el candidato de escala completa y sigue pendiente de QA científica.

Consultar [informe de QA](qa/FINAL_BENCHMARK_QA_REPORT.md), [escala](../DATASET_SCALE_AUDIT.md), [sustitución C2](../C2_SEMANTIC_AUDIT_V3.md), [manipulación C3](../C3_FORENSIC_AUDIT_V3.md), [C4](../C4_INPAINT_AUDIT_V3.md), [C5](../C5_COMBINED_AUDIT_V3.md) y [atajos narrativos](../NARRATIVE_SHORTCUT_AUDIT_V3.md).

Los scripts de auditoría escriben reportes en la raíz por compatibilidad con sus rutas actuales. Esos archivos constituyen evidencia; los README y la guía de entrenamiento contienen las instrucciones operativas.
