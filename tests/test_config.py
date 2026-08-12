from pathlib import Path

from virusforge import config


def test_load_defaults():
    cfg = config.load_config()
    assert config.get(cfg, "general.threads") == 8


def test_user_override(tmp_path: Path):
    user = tmp_path / "user.yaml"
    user.write_text("general:\n  threads: 32\n")
    cfg = config.load_config(user)
    assert config.get(cfg, "general.threads") == 32
    # ezilmeyen default korunur
    assert config.get(cfg, "general.memory_gb") == 32


def test_dotted_get_missing_returns_default():
    cfg = config.load_config()
    assert config.get(cfg, "tools.nope.x", "fallback") == "fallback"
