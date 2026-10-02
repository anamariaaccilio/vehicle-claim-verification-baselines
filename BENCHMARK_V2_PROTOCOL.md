# Benchmark v0.2.0: cobertura operativa completa C0–C10

## Alcance y fuente

Continuación del piloto HITL auditado: 24 imágenes, 256 anotaciones, ocho clases.
`DATASET_AUDIT.md` y `NEAR_DUPLICATE_AUDIT.md` conservan la auditoría de fuentes.
La versión nueva no amplía ni representa el dataset completo. No hay información
personal inventada, outputs de especialistas, entrenamientos ni resultados de modelos.
La tabla proporcionada y autorizada por el usuario sigue siendo canónica.

## Protocolo y reproducibilidad

`configs/benchmark_v2.yaml` fija seed42, parámetros, condiciones y ratios antes de
generar variantes. No hay ajuste aprendido ni selección de parámetros con test.
Los componentes de duplicados exactos/visuales se agrupan antes del split y se
comprueba igualdad exacta con `benchmark_v1/splits.json`. C2 elige determinísticamente
una fuente de otro componente del mismo split. No hay donantes entre splits.

C3 copia una ventana 24×24 centrada en un píxel del polígono anotado de menor área
rasterizada hacia una ventana que no intersecta ningún daño anotado original.
La fuente y destino están registrados; se verifica que ningún píxel exterior a
la máscara destino cambie. No se afirma que la ventana contenga un daño completo
ni que la composición tenga realismo de fraude. No requiere donante externo.
C5 añade una negación de una clase realmente anotada: se conservan todos los
píxeles de los daños originales, por lo que la manipulación no destruye la
base de la contradicción.

C4 aplica inpainting Telea, radio3, dentro del menor polígono de daño rasterizado.
Se verifica cambio efectivo y ausencia de cambios fuera de la máscara. El método
reconstruye regiones usando su vecindad; es un algoritmo existente, no novedad UAFEG:
[OpenCV inpainting](https://docs.opencv.org/4.5.1/d7/d8b/group__photo__inpaint.html).
No se certifica reparación plausible ni eliminación semántica del daño.
El campo `damage_removal_verified=false` evita confundir ejecución con validación humana.

C10 invierte RGB únicamente dentro del polígono anotado seleccionado. Esta familia
no aparece en train ni validation; hay un registro para cada una de las tres fuentes
de test. Es una reserva procedimental OOD, no un resultado de generalización.
La etiqueta OOD es un objetivo de evaluación de estrés; no amplía `DecisionLabel`
ni debe mezclarse con accuracy/F1 de las tres clases ordinarias.

C8 usa la alternativa JPEG de la taxonomía disyuntiva, manteniendo SUPPORTED.
C9 no fuerza 24 etiquetas: conserva exactamente siete casos que superan el criterio
fijo y registra los 17 rechazos. No se reducen umbrales para completar la tabla.

## Artefactos

`data/manifests/benchmark_v2/` contiene manifest, EvidencePackets, fuentes auditadas,
splits, validación, exclusiones y metadata con hashes y versiones del runtime.
Los especialistas del EvidencePacket siguen ausentes/null. El manifest registra
parent C0, fuente, donante cuando corresponde, anotación, parámetros, seed y hashes.
Imágenes/máscaras locales se conservan en `data/processed/` ignorado; no se versionan.
El generador reutiliza la ruta de derivados básicos de v1 con IDs nuevos dependientes
de la configuración; no sobrescribe las imágenes/artefactos congelados de v1.

## Límites científicos y siguiente paso

Cobertura de once condiciones no equivale a benchmark validado externamente.
Solo hay tres fuentes de test y no se conocen identidades de vehículo/incidente.
El dHash global puede omitir otras vistas/crops. C1/C5 comparten negaciones, un
shortcut textual; missing modalities y blur extremo también identifican condiciones.
C2 puede conservar semántica visual compatible aun siendo una sustitución conocida:
reportar esta no-identificabilidad, no venderla como evidencia de fraude detectable.
Las anotaciones describen la fuente original, no predicciones ni anotaciones
actualizadas de todos los daños de las composiciones. No deben usarse como features.

Antes de interpretar rendimiento: revisión humana de narrativas, composiciones y
etiquetas, ampliación de fuentes independientes y diseño de controles lingüísticos
balanceados en una versión nueva. No modificar silenciosamente estos splits.
P1/P2 y entrenamiento permanecen fuera de esta fase.
