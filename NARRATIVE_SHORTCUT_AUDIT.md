# Narrative shortcut audit — v2 original

Descriptive document-frequency unigram/bigram associations; min support 3, precision>=0.8 OR lift>=2; no fitting, no inferential p-values; dependent variants

No vacías: 202; únicas: 33; duplicados: 83.663%; ausentes: 24.
Duplicados = (filas no vacías - textos distintos)/filas no vacías. Ausencia reportada por separado.
Longitudes de cada condición incluyen ausencia como cero. Desviación poblacional.

| condition | claims | unique_nonempty | missing | mean_tokens | std_tokens_population | mean_chars | std_chars_population | template_ids | punctuation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C0 | 24 | 20 | 0 | 12.125 | 2.3329612798615695 | 89.625 | 18.63869742408698 | {'objective-0': 5, 'objective-1': 7, 'objective-2': 12} | {',': 41, '.': 24} |
| C1 | 24 | 13 | 0 | 6.25 | 0.8779711460710615 | 38.125 | 6.022959543834465 | {'objective-0': 5, 'objective-1': 7, 'objective-2': 12} | {'.': 24} |
| C10 | 3 | 3 | 0 | 13 | 0.816496580927726 | 98.66666666666667 | 9.809292646374773 | {'objective-1': 1, 'objective-2': 2} | {',': 6, '.': 3} |
| C2 | 24 | 20 | 0 | 12.125 | 2.3329612798615695 | 89.625 | 18.63869742408698 | {'objective-0': 5, 'objective-1': 7, 'objective-2': 12} | {',': 41, '.': 24} |
| C3 | 24 | 20 | 0 | 12.125 | 2.3329612798615695 | 89.625 | 18.63869742408698 | {'objective-0': 5, 'objective-1': 7, 'objective-2': 12} | {',': 41, '.': 24} |
| C4 | 24 | 20 | 0 | 12.125 | 2.3329612798615695 | 89.625 | 18.63869742408698 | {'objective-0': 5, 'objective-1': 7, 'objective-2': 12} | {',': 41, '.': 24} |
| C5 | 24 | 13 | 0 | 6.25 | 0.8779711460710615 | 38.125 | 6.022959543834465 | {'objective-0': 5, 'objective-1': 7, 'objective-2': 12} | {'.': 24} |
| C6 | 24 | 0 | 24 | 0 | 0.0 | 0 | 0.0 | {'objective-0': 5, 'objective-1': 7, 'objective-2': 12} | {} |
| C7 | 24 | 20 | 0 | 12.125 | 2.3329612798615695 | 89.625 | 18.63869742408698 | {'objective-0': 5, 'objective-1': 7, 'objective-2': 12} | {',': 41, '.': 24} |
| C8 | 24 | 20 | 0 | 12.125 | 2.3329612798615695 | 89.625 | 18.63869742408698 | {'objective-0': 5, 'objective-1': 7, 'objective-2': 12} | {',': 41, '.': 24} |
| C9 | 7 | 6 | 0 | 13 | 1.511857892036909 | 95.14285714285714 | 13.324827218698307 | {'objective-0': 1, 'objective-1': 2, 'objective-2': 4} | {',': 14, '.': 7} |

## Longitud por etiqueta

| label | claims | missing | mean_tokens | std_tokens_population |
| --- | --- | --- | --- | --- |
| INSUFFICIENT | 55 | 24 | 6.945454545454545 | 6.331503287869124 |
| OOD | 3 | 0 | 13 | 0.816496580927726 |
| SUPPORTED | 48 | 0 | 12.125 | 2.3329612798615695 |
| SUSPICIOUS | 120 | 0 | 9.775 | 3.4435023353169565 |

## Puntuación por documento

| character | conditions | labels | exclusive_label | exclusive_condition |
| --- | --- | --- | --- | --- |
| , | {'C0': 21, 'C10': 3, 'C2': 21, 'C3': 21, 'C4': 21, 'C7': 21, 'C8': 21, 'C9': 6} | {'INSUFFICIENT': 27, 'OOD': 3, 'SUPPORTED': 42, 'SUSPICIOUS': 63} | False | False |
| . | {'C0': 24, 'C1': 24, 'C10': 3, 'C2': 24, 'C3': 24, 'C4': 24, 'C5': 24, 'C7': 24, 'C8': 24, 'C9': 7} | {'INSUFFICIENT': 31, 'OOD': 3, 'SUPPORTED': 48, 'SUSPICIOUS': 120} | False | False |

Menciones explícitas de condition/label/indicadores prefijados: [].

## Asociaciones con condition

| term | target | documents | target_documents | precision | lift | exclusive |
| --- | --- | --- | --- | --- | --- | --- |
| está | C1 | 24 | 12 | 0.5 | 4.208333333333334 | False |
| está | C5 | 24 | 12 | 0.5 | 4.208333333333334 | False |
| está libre | C1 | 24 | 12 | 0.5 | 4.208333333333334 | False |
| está libre | C5 | 24 | 12 | 0.5 | 4.208333333333334 | False |
| libre | C1 | 24 | 12 | 0.5 | 4.208333333333334 | False |
| libre | C5 | 24 | 12 | 0.5 | 4.208333333333334 | False |
| libre de | C1 | 24 | 12 | 0.5 | 4.208333333333334 | False |
| libre de | C5 | 24 | 12 | 0.5 | 4.208333333333334 | False |
| no | C1 | 24 | 12 | 0.5 | 4.208333333333334 | False |
| no | C5 | 24 | 12 | 0.5 | 4.208333333333334 | False |
| vehículo está | C1 | 24 | 12 | 0.5 | 4.208333333333334 | False |
| vehículo está | C5 | 24 | 12 | 0.5 | 4.208333333333334 | False |
| vehículo no | C1 | 24 | 12 | 0.5 | 4.208333333333334 | False |
| vehículo no | C5 | 24 | 12 | 0.5 | 4.208333333333334 | False |
| en | C1 | 14 | 7 | 0.5 | 4.208333333333334 | False |
| en | C5 | 14 | 7 | 0.5 | 4.208333333333334 | False |
| en el | C1 | 14 | 7 | 0.5 | 4.208333333333334 | False |
| en el | C5 | 14 | 7 | 0.5 | 4.208333333333334 | False |
| hay | C1 | 14 | 7 | 0.5 | 4.208333333333334 | False |
| hay | C5 | 14 | 7 | 0.5 | 4.208333333333334 | False |
| no hay | C1 | 14 | 7 | 0.5 | 4.208333333333334 | False |
| no hay | C5 | 14 | 7 | 0.5 | 4.208333333333334 | False |
| de abolladuras | C1 | 10 | 5 | 0.5 | 4.208333333333334 | False |
| de abolladuras | C5 | 10 | 5 | 0.5 | 4.208333333333334 | False |
| no presenta | C1 | 10 | 5 | 0.5 | 4.208333333333334 | False |
| no presenta | C5 | 10 | 5 | 0.5 | 4.208333333333334 | False |
| de rayones | C1 | 6 | 3 | 0.5 | 4.208333333333334 | False |
| de rayones | C5 | 6 | 3 | 0.5 | 4.208333333333334 | False |
| hay abolladuras | C1 | 6 | 3 | 0.5 | 4.208333333333334 | False |
| hay abolladuras | C5 | 6 | 3 | 0.5 | 4.208333333333334 | False |
| de piezas | C1 | 4 | 2 | 0.5 | 4.208333333333334 | False |
| de piezas | C5 | 4 | 2 | 0.5 | 4.208333333333334 | False |
| hay piezas | C1 | 4 | 2 | 0.5 | 4.208333333333334 | False |
| hay piezas | C5 | 4 | 2 | 0.5 | 4.208333333333334 | False |
| presenta abolladuras | C1 | 4 | 2 | 0.5 | 4.208333333333334 | False |
| presenta abolladuras | C5 | 4 | 2 | 0.5 | 4.208333333333334 | False |
| el | C1 | 79 | 24 | 0.3037974683544304 | 2.556962025316456 | False |
| el | C5 | 79 | 24 | 0.3037974683544304 | 2.556962025316456 | False |
| el vehículo | C1 | 79 | 24 | 0.3037974683544304 | 2.556962025316456 | False |
| el vehículo | C5 | 79 | 24 | 0.3037974683544304 | 2.556962025316456 | False |
| corrosión abolladuras | C10 | 7 | 1 | 0.14285714285714285 | 9.619047619047619 | False |
| muestra corrosión | C10 | 7 | 1 | 0.14285714285714285 | 9.619047619047619 | False |
| pintura piezas | C10 | 7 | 1 | 0.14285714285714285 | 9.619047619047619 | False |
| rotas pequeños | C9 | 7 | 1 | 0.14285714285714285 | 4.122448979591836 | False |
| corrosión | C10 | 9 | 1 | 0.1111111111111111 | 7.481481481481482 | False |
| grietas abolladuras | C9 | 33 | 3 | 0.09090909090909091 | 2.623376623376623 | False |
| rotas grietas | C9 | 33 | 3 | 0.09090909090909091 | 2.623376623376623 | False |
| grietas | C9 | 35 | 3 | 0.08571428571428572 | 2.473469387755102 | False |
| desconchados | C9 | 49 | 4 | 0.08163265306122448 | 2.355685131195335 | False |
| desconchados de | C9 | 49 | 4 | 0.08163265306122448 | 2.355685131195335 | False |
| pequeños | C9 | 49 | 4 | 0.08163265306122448 | 2.355685131195335 | False |
| pequeños desconchados | C9 | 49 | 4 | 0.08163265306122448 | 2.355685131195335 | False |
| faltantes pequeños | C9 | 13 | 1 | 0.07692307692307693 | 2.21978021978022 | False |
| abolladuras pequeños | C9 | 27 | 2 | 0.07407407407407407 | 2.1375661375661372 | False |
| muestra abolladuras | C10 | 14 | 1 | 0.07142857142857142 | 4.809523809523809 | False |
| muestra abolladuras | C9 | 14 | 1 | 0.07142857142857142 | 2.061224489795918 | False |
| y rayones | C9 | 100 | 7 | 0.07 | 2.02 | False |
| abolladuras desprendimientos | C10 | 19 | 1 | 0.05263157894736842 | 3.543859649122807 | False |
| faltantes y | C10 | 47 | 2 | 0.0425531914893617 | 2.8652482269503547 | False |
| abolladuras pequeños | C10 | 27 | 1 | 0.037037037037037035 | 2.493827160493827 | False |
| desprendimientos | C10 | 27 | 1 | 0.037037037037037035 | 2.493827160493827 | False |
| desprendimientos de | C10 | 27 | 1 | 0.037037037037037035 | 2.493827160493827 | False |
| y rayones | C10 | 100 | 3 | 0.03 | 2.02 | False |

## Asociaciones con expected_label

| term | target | documents | target_documents | precision | lift | exclusive |
| --- | --- | --- | --- | --- | --- | --- |
| está | SUSPICIOUS | 24 | 24 | 1.0 | 1.6833333333333333 | True |
| está libre | SUSPICIOUS | 24 | 24 | 1.0 | 1.6833333333333333 | True |
| libre | SUSPICIOUS | 24 | 24 | 1.0 | 1.6833333333333333 | True |
| libre de | SUSPICIOUS | 24 | 24 | 1.0 | 1.6833333333333333 | True |
| no | SUSPICIOUS | 24 | 24 | 1.0 | 1.6833333333333333 | True |
| vehículo está | SUSPICIOUS | 24 | 24 | 1.0 | 1.6833333333333333 | True |
| vehículo no | SUSPICIOUS | 24 | 24 | 1.0 | 1.6833333333333333 | True |
| en | SUSPICIOUS | 14 | 14 | 1.0 | 1.6833333333333333 | True |
| en el | SUSPICIOUS | 14 | 14 | 1.0 | 1.6833333333333333 | True |
| hay | SUSPICIOUS | 14 | 14 | 1.0 | 1.6833333333333333 | True |
| no hay | SUSPICIOUS | 14 | 14 | 1.0 | 1.6833333333333333 | True |
| de abolladuras | SUSPICIOUS | 10 | 10 | 1.0 | 1.6833333333333333 | True |
| no presenta | SUSPICIOUS | 10 | 10 | 1.0 | 1.6833333333333333 | True |
| de rayones | SUSPICIOUS | 6 | 6 | 1.0 | 1.6833333333333333 | True |
| hay abolladuras | SUSPICIOUS | 6 | 6 | 1.0 | 1.6833333333333333 | True |
| de piezas | SUSPICIOUS | 4 | 4 | 1.0 | 1.6833333333333333 | True |
| hay piezas | SUSPICIOUS | 4 | 4 | 1.0 | 1.6833333333333333 | True |
| presenta abolladuras | SUSPICIOUS | 4 | 4 | 1.0 | 1.6833333333333333 | True |
| corrosión abolladuras | OOD | 7 | 1 | 0.14285714285714285 | 9.619047619047619 | False |
| muestra corrosión | OOD | 7 | 1 | 0.14285714285714285 | 9.619047619047619 | False |
| pintura piezas | OOD | 7 | 1 | 0.14285714285714285 | 9.619047619047619 | False |
| corrosión | OOD | 9 | 1 | 0.1111111111111111 | 7.481481481481482 | False |
| muestra abolladuras | OOD | 14 | 1 | 0.07142857142857142 | 4.809523809523809 | False |
| abolladuras desprendimientos | OOD | 19 | 1 | 0.05263157894736842 | 3.543859649122807 | False |
| faltantes y | OOD | 47 | 2 | 0.0425531914893617 | 2.8652482269503547 | False |
| abolladuras pequeños | OOD | 27 | 1 | 0.037037037037037035 | 2.493827160493827 | False |
| desprendimientos | OOD | 27 | 1 | 0.037037037037037035 | 2.493827160493827 | False |
| desprendimientos de | OOD | 27 | 1 | 0.037037037037037035 | 2.493827160493827 | False |
| y rayones | OOD | 100 | 3 | 0.03 | 2.02 | False |

Las asociaciones son descriptivas, no p-valores ni observaciones independientes. No se ajustó un clasificador.
Los metadatos de condición/label están excluidos del texto y nunca deben entrar como features.

## Corrección versionada v3

Se preservó v2. v3 usa el mismo target de daño para C0/C1/C5 y cuatro formas emparejadas: afirmación, litotes, afirmación modal y doble negación, combinadas con ocho prefijos y cuatro cierres neutrales elegidos por hash/seed independientemente de la etiqueta. Así, negaciones aparecen también en controles SUPPORTED y no solo en SUSPICIOUS. No se usa test para ajustar frecuencias o seleccionar plantillas.

V3: 8468 narrativas no vacías; 960 distintas; 88.663% de duplicados. Ver NARRATIVE_SHORTCUT_AUDIT_V3.md para todas las asociaciones.

La repetición de controles sobre la misma fuente es intencional; las plantillas entre fuentes y asociaciones residuales siguen siendo limitaciones. No se afirma eliminar todos los shortcuts. El vocabulario disponible de ocho clases y la gramática controlada limita la diversidad; hacen falta narrativas adjudicadas y controles más naturales. Además, C1/C5 siguen negando daños presentes: falta un control de ausencia semántica compatible adjudicado. Balancear la palabra no no elimina ese atajo semántico; ausencia de anotación no autoriza inventar ausencia de daño.
