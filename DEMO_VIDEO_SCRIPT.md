# Guion de demo — 85 segundos

Inicio: `./run_demo.sh`; abrir http://127.0.0.1:8765/demo a 1600×1000 o pantalla completa. Avanzar con → y retroceder con ←; Escape sale del modo. Los tiempos y controles del guion no aparecen en el video. No activar entrenamientos ni la demo Streamlit antigua.

| Tiempo | Pantalla / paso | Qué decir | Qué NO afirmar |
|---|---|---|---|
| 0–8 s | 1 Overview | «Este avance construye la infraestructura experimental de UAFEG: 814 imágenes descargadas, 807 aceptadas y 9.275 reclamos controlados.» | Que son reclamos reales de una aseguradora o resultados de un modelo. |
| 8–13 s | 2 Real source image | «Las imágenes son reales de HITL; las narrativas y escenarios se generan de forma controlada.» | Que se conocen propietarios, incidentes o fraude real. |
| 13–18 s | 3 C0 | «El control relaciona una narrativa con daño anotado en la imagen original.» | Que toda narrativa ha sido aprobada por una persona. |
| 18–23 s | 4 C1 | «Aquí cambia la afirmación sobre el daño; conservamos la fuente y la trazabilidad.» | Que un modelo detectó la contradicción. |
| 23–30 s | 5 C2 | «La auditoría detectó que cambiar de expediente no siempre produce contradicción visual. Estos casos requieren revisión antes de entrenar.» | Que likely contradiction significa contradicción confirmada. |
| 30–36 s | 6 C3 | «La transformación conserva semilla, parámetros y máscara. Algunas regiones son pequeñas y están pendientes de revisión.» | Que la manipulación es realista o perceptible por estar implementada. |
| 36–42 s | 7 EvidencePacket | «El contrato canónico serializa el reclamo y su procedencia. Los especialistas todavía están ausentes.» | Que existen salidas de NLI, visión o forense. |
| 42–48 s | 8 EvidenceGraph | «El MVP construye y valida la estructura. Con estos paquetes produce un nodo de reclamo, sin aristas ni razonamiento aprendido.» | Que P1, P2 o reliability gating están implementados. |
| 48–55 s | 9 Leakage audit | «Todas las variantes de una fuente permanecen en el mismo split; verificamos intersecciones nulas y donantes dentro del split.» | Que un hash perceptual prueba ausencia absoluta de toda similitud. |
| 55–62 s | 10 Reproducibility | «Regeneramos tres artefactos usando los operadores existentes y la semilla registrada. Sus hashes coinciden exactamente.» | Que comprobar tres casos prueba todo el benchmark o su realismo. |
| 62–69 s | 11 Test dashboard | «Las suites verifican schemas, splits, procedencia, serialización y el grafo. Los tests que requieren modelos quedan omitidos en este recorrido.» | Accuracy, precisión predictiva o resultados finales; leer los counts actuales de la pantalla. |
| 69–78 s | 12 Current limitations | «La auditoría también revela plantillas repetidas y asociaciones lingüísticas. La limpieza de v4 aún está pendiente.» | Que v4 está terminado o READY_FOR_MODELS = YES. |
| 78–85 s | 13 Next phase | «El siguiente paso es depurar y adjudicar el benchmark. Después vendrán los baselines, P1, P2 y las ablaciones.» | Que ya se entrenó, publicó o validó científicamente el método. |

Para explicar C2 con más tiempo, abrir “C2 semantic QA”: muestra v3 likely compatible y likely contradiction; el ejemplo ambiguous está claramente identificado como histórico v2. No existen contradicciones confirmadas por adjudicación humana en estos artefactos.
