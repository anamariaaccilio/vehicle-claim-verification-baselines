"""Tests de PASO 5/8: schema de demo/cases/cases.yaml.

Verifica que los 6 casos preparados esten bien formados y que
expected_condition sea puramente informativo (nunca se pasa a analyze(),
ver tests/test_fusion.py::test_feature_vector_signature_never_takes_a_label_argument).
"""
from demo.cases_loader import DemoCase, load_cases
from src.schemas.evidence import DecisionLabel


def test_load_cases_returns_six_cases():
    cases = load_cases()
    assert len(cases) == 6
    assert {c.case_id for c in cases} == {f"CASE{i:02d}" for i in range(1, 7)}


def test_every_case_has_valid_expected_condition():
    valid = {d.value for d in DecisionLabel}
    for c in load_cases():
        assert c.expected_condition in valid


def test_every_case_has_narrative_or_image_or_both():
    for c in load_cases():
        assert c.narrative_text is not None or c.image_path is not None


def test_case04_requires_no_image_and_is_runnable_today():
    cases = {c.case_id: c for c in load_cases()}
    case04 = cases["CASE04"]
    assert case04.image_path is None
    assert case04.narrative_text is not None
    assert case04.is_runnable is True  # no depende de ningun asset externo


def test_cases_requiring_real_images_are_marked_unavailable_without_dataset():
    # Refleja el estado REAL de este repositorio: data/raw/hitl/ vacio =>
    # demo/cases/assets/ tambien vacio => estos casos no son ejecutables
    # todavia. Si este test empieza a fallar es porque ya se agregaron
    # imagenes reales -- hay que actualizarlo, no el codigo.
    cases = {c.case_id: c for c in load_cases()}
    for case_id in ("CASE01", "CASE02", "CASE03", "CASE05", "CASE06"):
        assert cases[case_id].image_path is not None
        assert cases[case_id].is_runnable is False


def test_demo_case_dataclass_has_no_label_style_field_fed_to_pipeline():
    # DemoCase puede EXPONER expected_condition (para mostrarlo en la UI),
    # pero build_feature_vector/evaluate no lo aceptan como argumento (ver
    # test_fusion.py). Aqui solo confirmamos que el campo existe y esta
    # claramente separado del resto de los datos de entrada.
    fields = DemoCase.__dataclass_fields__.keys()
    assert "expected_condition" in fields
    assert "narrative_text" in fields
    assert "image_path" in fields
