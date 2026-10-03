# Unidad estadística y evaluación futura

Las **226 variantes de v2 NO son 226 observaciones independientes**. Se derivan
de 24 fuentes. La misma regla aplica a todas las variantes y controles C8 de v3.
La unidad principal de agrupación es `source_image_id`; si hay duplicados o
near-duplicates, usar su componente `source_group_id` (claim source group) como
unidad indivisible. El split se asigna al grupo antes de generar reclamos.

C2 añade dependencia entre la fuente del reclamo y el donante. Para intervalos
que incluyan C2, formar además componentes de dependencia que conecten fuente y
donante dentro de cada split y remuestrear esos componentes enteros, o reportar C2
por separado con esta dependencia explícita. No cambiar splits para este cálculo.

Toda evaluación futura debe usar intervalos/bootstraps agrupados, nunca bootstrap
de filas individuales. Protocolo preregistrado propuesto: 2.000 réplicas, seed2026,
muestreo con reemplazo de grupos del test; incluir todas sus variantes en cada réplica;
comparaciones B6/P1/P2 emparejadas sobre los mismos grupos y réplicas. Reportar el
número de fuentes/grupos, prevalencia, métricas por condición y C8 subtype, e
intervalos percentiles 2.5/97.5. Las réplicas de una métrica indefinida (por ejemplo,
una clase ausente) deben contarse y declararse; no rellenar con cero.
Estos son parámetros de un protocolo futuro, no resultados ni bootstrap ya ejecutado.

Separar dos estimandos: (1) macro-promedio por fuente/grupo, dando el mismo peso
inicial a cada fuente; (2) rendimiento por condición/subtype. No aumentar el peso
de una fuente porque produzca más variantes C8. Para pérdida/métricas globales,
fijar y reportar previamente los pesos por condición. Reportar datos faltantes y
exclusiones, no imputar silenciosamente ejemplos C9/CROP no emitidos.

C10 pertenece únicamente a test y a evaluación OOD; no es cuarta clase de
entrenamiento. Reportar sus métricas separadamente de las tres clases ordinarias.
Temperaturas, normalización, calibración y selección de umbrales no usan test.
Si se revisa el test durante QA para diseñar narrativas/controles, el benchmark
resultante es un conjunto de desarrollo de benchmark: no declarar selección
completamente ciega al test. Antes de conclusiones finales de tesis se recomienda
un conjunto confirmatorio independiente o una nueva versión preregistrada.

Con tres fuentes test en v2, los intervalos serían extremadamente inestables.
Más variantes no corrigen ese problema. La ampliación v3 tampoco elimina los
sesgos de selección, identidad de vehículo desconocida o anotaciones no adjudicadas.
No se implementó ni ejecutó entrenamiento o evaluación de modelos en esta fase.
