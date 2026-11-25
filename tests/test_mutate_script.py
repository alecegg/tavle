import importlib.util
import sys
from pathlib import Path


def load_script():
    path = Path(__file__).resolve().parents[1] / "scripts" / "mutate.py"
    spec = importlib.util.spec_from_file_location("mutate_script", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_config_selects_fast_tests():
    config = load_script().mutmut_config([])
    assert '"-m", "not slow and not matrix_full"' in config


def test_default_workers(monkeypatch):
    module = load_script()
    monkeypatch.setattr(sys, "argv", ["mutate.py"])
    monkeypatch.setattr(module, "run", lambda work, workers, patterns: workers)
    assert module.main() == 2
