# UAFEG Benchmark Demo

Desde Repo A:

```bash
./run_demo.sh
```

Abrir http://127.0.0.1:8765 o http://127.0.0.1:8765/demo. Navegación con botones; en presentación, flechas ←/→. Ctrl+C detiene el servidor.

Opciones:

```bash
./run_demo.sh --refresh-tests --check  # volver a ejecutar suites sin modelos
./run_demo.sh --check          # validar paths, conteos y tres regeneraciones; salir
./run_demo.sh --port 8767      # puerto alternativo
```

La primera ejecución obtiene resultados pytest si no existen. Ejecuciones posteriores los leen con fecha y fingerprint del código/HEAD: los cambios muestran STALE, no un éxito actual ficticio. Para una captura definitiva ejecutar `--refresh-tests` con Repo A limpio y el lock de B actualizado mediante el mecanismo original. El verificador existente de UAFEG rechaza un Repo A con cambios sin commit.

No dependencias web nuevas, CDNs, fuentes externas ni conexión requerida. Usa `.venv` de Repo A, schemas canónicos y `../uafeg/src` para el grafo. Ambas carpetas hermanas y las imágenes locales originales/derivadas deben seguir disponibles. El comando detecta imports o archivos faltantes, no los descarga. Solo sirve imágenes explícitamente referidas en manifests y los recursos estáticos de la demo; no expone el repositorio completo. Escucha en 127.0.0.1.

Artefactos derivados de presentación en `generated/` son locales e ignorados. No se modifican manifests, raw images ni operadores. La demo antigua `demo/app.py` se conserva.

Todos los claims aceptados se muestran como REVIEW REQUIRED para aprobación humana. SCHEMA VALIDATED es exclusivamente validación de software. EXCLUDED se reserva para exclusiones registradas (C9) mostradas en Conditions. No se adjudican nuevos labels.

Los paquetes de v3 tienen especialistas null: su grafo real tiene un nodo claim y cero aristas. source_image_id es metadato, no un nodo. support/contradiction/overlap/unknown se muestran como relaciones futuras, no existentes. B sigue fijado al manifest v2; el preview de v3 no lo promueve a aprobado.

## Grabación sin instrucciones en pantalla

En `/demo`, la barra de pasos, los tiempos y los botones de presentación están ocultos. Avanzar con →, retroceder con ← y salir del modo con Escape. La navegación lateral sigue disponible. Se conservan los estados QA y las limitaciones científicas. Si el servidor ya existe, `./run_demo.sh` imprime su URL y termina sin error. Tras cambios visuales, recargar con Ctrl+Shift+R.

## Lectura progresiva de la demo

La portada explica problema, flujo propuesto, un caso real y avance. La navegación visible se reduce a Inicio, Casos, Cómo funciona, Estado y Técnico. Auditorías, hashes, pruebas y JSON permanecen accesibles desde Técnico. La comparación B6/P1/P2 está plegada en Explorar detalles. Las etiquetas del ejemplo son experimentales, nunca predicciones.
