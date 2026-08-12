import pytest

from virusforge import registry


def test_known_tools_present():
    assert "bitbucket.org/berkeleylab/checkv" in registry.tool("checkv")["repo"]
    assert "apcamargo/genomad" in registry.tool("genomad")["repo"]
    assert "gbouras13/pharokka" in registry.tool("pharokka")["repo"]


def test_unknown_tool_raises():
    with pytest.raises(KeyError):
        registry.tool("nonexistent_tool")


def test_detect_version_missing_returns_none(monkeypatch):
    def _raise(*a, **k):
        raise FileNotFoundError
    monkeypatch.setattr(registry.subprocess, "run", _raise)
    assert registry.detect_version("checkv") is None
