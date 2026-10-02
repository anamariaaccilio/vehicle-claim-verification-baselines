"""Carga y valida demo/cases/cases.yaml (PASO 5).

No calcula ni fabrica ningun resultado: solo expone las entradas de los
casos preparados y si sus assets (imagenes) existen en disco AHORA MISMO.
Un caso sin imagen real disponible se marca is_runnable=False en vez de
simular una prediccion.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

CASES_DIR = Path(__file__).resolve().parent / "cases"
CASES_YAML_PATH = CASES_DIR / "cases.yaml"
REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class DemoCase:
    case_id: str
    title: str
    narrative_text: str | None
    image_path: str | None
    expected_condition: str
    notes: str

    @property
    def image_available(self) -> bool:
        if self.image_path is None:
            return True  # el caso no requiere imagen
        return (REPO_ROOT / self.image_path).exists()

    @property
    def is_runnable(self) -> bool:
        return self.image_available

    @property
    def absolute_image_path(self) -> Path | None:
        if self.image_path is None:
            return None
        return REPO_ROOT / self.image_path


def load_cases(path: Path = CASES_YAML_PATH) -> list[DemoCase]:
    with Path(path).open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    cases: list[DemoCase] = []
    for entry in raw["cases"]:
        cases.append(
            DemoCase(
                case_id=entry["case_id"],
                title=entry["title"],
                narrative_text=entry.get("narrative_text"),
                image_path=entry.get("image_path"),
                expected_condition=entry["expected_condition"],
                notes=(entry.get("notes") or "").strip(),
            )
        )
    return cases
