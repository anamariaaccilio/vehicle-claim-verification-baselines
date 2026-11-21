# Datos externos

Registro de todo dato que no forma parte del benchmark v3 congelado. Ningún archivo externo se
guarda en este repositorio ni en el disco local: se usan dentro de kernels privados de Kaggle.

## CarDD (validación externa del especialista visual)

| Campo | Valor |
|---|---|
| Dataset original | CarDD — Wang, X., Li, W., Wu, Z. "CarDD: A New Dataset for Vision-Based Car Damage Detection", IEEE T-ITS 24(7), 2023. https://cardd-ustc.github.io/ |
| Fuente usada | Espejo de Kaggle `gabrielfcarvalho/cardd-with-yolo-annotations-images-labels` (imágenes CarDD + etiquetas YOLO de cajas convertidas desde las anotaciones COCO originales) |
| Licencia | CC BY-NC 4.0 (declarada en los metadatos del dataset en Kaggle; uso académico no comercial) |
| Fecha de uso | 2026-11-21 (UTC), kernel privado `anamaria203/uafeg-yolo-train` |
| Partición | `test` del espejo |
| Imágenes | 374 |
| Objetos | 785 cajas (todas las clases); 753 tras excluir `tire flat` |
| Hash | SHA-256 de la concatenación ordenada de los SHA-256 de las 374 imágenes: `a732d9fc13edf7d0c7934075ac1014593fe610fc8fbd65ccdd51225ef2250fe6` |
| Tipo de etiqueta | Solo cajas: el mAP de máscara externo es NOT_RUN |
| Mapeo de clases (fijado antes de evaluar) | dent→dent, scratch→scratch, crack→crack, glass shatter→broken_part, lamp broken→broken_part, tire flat→excluida |

Descartados: otros espejos de CarDD en Kaggle con máscaras (`issamjebnouni/cardd`, `taki2003/cardd-yolo`) declaran licencia "unknown"; no se usaron.

## HITL v2 (fuente del benchmark, no externo)

Las 807 imágenes originales se leen en Kaggle desde `humansintheloop/car-parts-and-car-damages`
(versión 2, CC0) y se verifica que cada una coincida con el SHA-256 congelado de v3 (807/807
coincidieron; ver `artifacts/damage/yolo_record.json`, campo `hitl_sha_mismatch = 0`).

## Modelos externos

| Modelo | Uso | Licencia | Cita |
|---|---|---|---|
| `yolov8n-seg.pt` (Ultralytics 8.4.155) | base del especialista visual | AGPL-3.0 | Jocher, G. et al., Ultralytics YOLOv8, 2023 |
| TruFor `trufor.pth.tar` (GRIP-UNINA) | especialista forense, solo inferencia | licencia de investigación sin fines de lucro | Guillaro, F. et al., "TruFor: Leveraging all-round clues for trustworthy image forgery detection and localization", CVPR 2023 |
| `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli` | especialista narrativo (NLI) | MIT | Laurer, M. et al., 2022; He, P. et al., DeBERTaV3, 2021 |
| `Qwen/Qwen2-VL-2B-Instruct` | B8 (MLLM congelado, zero-shot) | Apache-2.0 | Wang, P. et al., "Qwen2-VL", arXiv:2409.12191, 2024 |
