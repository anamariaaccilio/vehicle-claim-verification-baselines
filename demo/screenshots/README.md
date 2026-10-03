# Capturas de la demo

Capturas locales PNG excluidas de Git: contienen imágenes reales del dataset.

1. **01_overview.png** — alcance, pipeline y estado BENCHMARK VALIDATION.
2. **02_condition_example.png** — C3 original / transformada / metadata; máscara debajo del primer viewport.
3. **03_evidencepacket_graph.png** — JSON canónico y grafo real de un nodo, sin evidencia especialista.
4. **04_leakage_audit.png** — fuentes por split e intersecciones.
5. **05_test_reproducibility.png** — hashes reales de tres regeneraciones.
6. **06_test_dashboard.png** — complemento recomendado: ejecución pytest y propósito de los tests.

Regenerar con la demo ya iniciada en el puerto 8765:

```bash
.venv/bin/python demo/benchmark/capture_demo.py
```

El script opcional usa Chrome/Chromium y el paquete `websockets` ya disponibles localmente. No instala ni descarga un navegador. Inicia un perfil temporal aislado, comprueba páginas/filtros/recorrido y captura a 1600×1000. Puerto de depuración local 9226. La demo en sí solo necesita las dependencias existentes del proyecto y la biblioteca estándar HTTP de Python.

Alternativa manual: abrir las páginas indicadas a 1600×1000 y utilizar la captura del navegador. Verificar que el panel de tests diga SOURCE SNAPSHOT CURRENT antes de enviar capturas.
