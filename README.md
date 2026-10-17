# UAFEG

## ¿Qué intenta resolver?

¿La evidencia realmente respalda lo que dice un reclamo vehicular?
La tesis estudia cómo relacionar texto, imagen e integridad visual,
considerando contradicciones, información faltante y evidencia poco confiable.

## Cómo funciona

**Diseño propuesto; todavía no es un sistema predictivo completo.**

```text
Narrativa + imagen
↓ analizar evidencia
↓ organizar evidencia
↓ relacionarla
↓ decidir o abstenerse
```

La salida futura contempla Supported / Suspicious / Insufficient y revisión humana.
Las etiquetas actuales son experimentales, no predicciones.

## Estado actual

- Banco de pruebas (benchmark): construido y en validación científica.
- 807 imágenes reales aceptadas, 9.275 escenarios controlados y 11 tipos de prueba.
- EvidenceGraph: implementado en el repo hermano `uafeg`, con relaciones narrativa-visual.
- B0: reglas implementadas; otros baselines parciales o pendientes (ver [guía técnica](docs/TECHNICAL_GUIDE.md)).
- B6/P1/P2 (DeepSets / grafo sin compuerta / grafo con reliability gate): implementados y
  testeados en `uafeg`, pero **sin entrenar** sobre el benchmark real (`IMPLEMENTED_CODE_NOT_TRAINED`).
- Resultados predictivos finales: todavía no disponibles. **READY_FOR_MODELS = NO**.

## Estructura del proyecto

- **Repo A — vehicle-claim-verification-baselines:** datos, banco de pruebas, auditorías y métodos de referencia.
- **Repo B — uafeg:** propuesta UAFEG y prototipo del grafo.

## Abrir la demo

Ejecutar `./run_demo.sh` y abrir http://127.0.0.1:8765/.

## Profundizar

- [Guía técnica: reproducción, sistemas y antecedentes](docs/TECHNICAL_GUIDE.md)
- [Protocolo experimental](EXPERIMENTAL_PROTOCOL.md)
- [Protocolo estadístico](STATISTICAL_EVALUATION_PROTOCOL.md)
- [Auditoría del conjunto de datos](DATASET_SCALE_AUDIT.md)
- [Uso de la demo](demo/benchmark/README.md)

Las fotografías son reales; los escenarios de reclamo son controlados.
No son expedientes reales de una aseguradora.
