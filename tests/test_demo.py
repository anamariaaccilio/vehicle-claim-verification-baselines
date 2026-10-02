"""Tests de PASO 8: 'demo import'. Usa streamlit.testing.v1.AppTest para
correr demo/app.py de verdad (sin servidor, sin browser) y confirmar que no
lanza excepciones -- ni en el estado inicial ni al presionar ANALIZAR con
el caso R01 (narrativa y imagen ausentes, el camino mas rapido de probar
porque no requiere una imagen real)."""
from pathlib import Path
import pytest

from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).resolve().parents[1] / "demo" / "app.py")


def test_demo_app_loads_without_exceptions():
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=60)
    assert not at.exception


@pytest.mark.model
def test_demo_app_analyze_with_no_input_triggers_r01_without_exceptions():
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=60)
    assert not at.exception

    at.button[0].click().run(timeout=120)
    assert not at.exception
