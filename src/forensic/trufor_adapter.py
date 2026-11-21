"""Adaptador del especialista forense: TruFor (Guillaro et al., CVPR 2023), solo inferencia.

Pesos: ``trufor.pth.tar`` del zip oficial
https://www.grip.unina.it/download/prog/TruFor/TruFor_weights.zip
(SHA-256 registrado en artifacts/forensic/trufor/weights/SHA256SUMS).
Licencia (GRIP-UNINA, LICENSE.txt del repositorio oficial): uso, reproducción y
modificación gratuitos SOLO con fines informativos y sin fines de lucro; prohibido
el uso industrial o comercial; hay que conservar los avisos de copyright y citar
a los autores al publicar resultados. El código y los pesos NO se redistribuyen
en este repositorio (viven en artifacts/, fuera de git).

Comando exacto para reconstruir el entorno:
    cd artifacts/forensic/trufor
    curl -sL https://codeload.github.com/grip-unina/TruFor/tar.gz/refs/heads/main | tar xz
    curl -sLO https://www.grip.unina.it/download/prog/TruFor/TruFor_weights.zip && unzip TruFor_weights.zip
    pip install yacs timm

Salida por imagen: puntaje global de integridad (``det``), mapa de localización
(probabilidad de manipulación por píxel) y mapa de confiabilidad de esa
localización. Los mapas se guardan reducidos para construir regiones (ℓ) e IoU.
Si el código o los pesos faltan, ``is_available`` es False y no se fabrica nada.

Escala reducida (CPU, 2026-11-13): la imagen se reescala para que su lado mayor
sea como mucho ``max_side`` px antes de la inferencia; queda registrado en la
procedencia de cada paquete.
"""
from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
TRUFOR_DIR = ROOT / "artifacts/forensic/trufor/TruFor-main/TruFor_train_test"
WEIGHTS = ROOT / "artifacts/forensic/trufor/weights/trufor.pth.tar"
METHOD = "TruFor (Guillaro et al., CVPR 2023), pretrained trufor_ph3, inference only"


@contextmanager
def _cwd(path: Path):
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


class TruForSpecialist:
    def __init__(self, max_side: int = 512, map_side: int = 64, threads: int | None = None):
        self.max_side = max_side
        self.map_side = map_side
        self.threads = threads
        self._model = None

    @property
    def is_available(self) -> bool:
        return TRUFOR_DIR.exists() and WEIGHTS.exists()

    def _load(self):
        if self._model is not None:
            return self._model
        if not self.is_available:
            raise FileNotFoundError("TruFor code/weights missing; forensic stays null (see module docstring)")
        import torch
        if self.threads:
            torch.set_num_threads(self.threads)
        if str(TRUFOR_DIR) not in sys.path:
            sys.path.insert(0, str(TRUFOR_DIR))
        with _cwd(TRUFOR_DIR):
            from lib.config import config  # type: ignore
            from lib.utils import get_model  # type: ignore
            config.defrost()
            config.merge_from_file("lib/config/trufor_ph3.yaml")
            config.merge_from_list(["TEST.MODEL_FILE", str(WEIGHTS)])
            config.freeze()
            # weights_only=True: tensors only, no arbitrary pickle code. The checkpoint stores
            # numpy scalars (e.g. best metric), which are explicitly allow-listed.
            scalar = np._core.multiarray.scalar
            safe = [(scalar, "numpy.core.multiarray.scalar"), scalar, np.dtype,
                    type(np.dtype("float64")), type(np.dtype("float32"))]
            with torch.serialization.safe_globals(safe):
                checkpoint = torch.load(str(WEIGHTS), map_location="cpu", weights_only=True)
            model = get_model(config)
            model.load_state_dict(checkpoint["state_dict"])
        model.eval()
        self._model = model
        return model

    def predict(self, image_path: str | Path) -> dict:
        import torch
        from PIL import Image
        from torch.nn import functional as F

        model = self._load()
        with Image.open(image_path) as im:
            im = im.convert("RGB")  # RGBA/RGB mode is a generation fingerprint: always normalize
            w, h = im.size
            scale = min(1.0, self.max_side / max(w, h))
            if scale < 1.0:
                im = im.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.BICUBIC)
            rgb = np.asarray(im, dtype=np.float32)
        tensor = torch.from_numpy(rgb.transpose(2, 0, 1)).unsqueeze(0) / 256.0
        with torch.no_grad():
            pred, conf, det, _ = model(tensor, save_np=False)
        loc = F.softmax(pred, dim=1)[:, 1:2]
        conf = torch.sigmoid(conf)
        side = (self.map_side, max(1, round(self.map_side * tensor.shape[3] / tensor.shape[2])))
        loc_small = F.interpolate(loc, size=side, mode="area")[0, 0].numpy()
        conf_small = F.interpolate(conf, size=side, mode="area")[0, 0].numpy()
        return {
            "score": float(torch.sigmoid(det).item()),
            "localization": loc_small.astype(np.float16),
            "confidence": conf_small.astype(np.float16),
            "inference_size": [int(tensor.shape[3]), int(tensor.shape[2])],
            "original_size": [w, h],
        }
