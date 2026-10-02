import os
import pytest

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"


def pytest_addoption(parser):
    parser.addoption("--run-model-tests", action="store_true", default=False,
                     help="Run existing integration tests using already cached NLI weights")


def pytest_configure(config):
    config.addinivalue_line("markers", "model: requires existing local model weights")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-model-tests"):
        return
    for item in items:
        if "model" in item.keywords:
            item.add_marker(pytest.mark.skip(reason="requires --run-model-tests and local NLI cache"))
