"""Validate configuration precedence and LLM isolation across settings upgrades."""

import os
from pathlib import Path

import pytest

from copyedit_ai.settings import Settings


@pytest.fixture
def isolated_settings(tmp_path: Path, monkeypatch) -> Path:
    """Keep settings tests independent of the user's environment and config."""
    monkeypatch.chdir(tmp_path)
    for name in os.environ:
        if name.startswith("COPYEDIT_AI_"):
            monkeypatch.delenv(name)
    monkeypatch.delenv("LLM_USER_PATH", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    return tmp_path


def test_settings_defaults_isolate_llm(isolated_settings: Path) -> None:
    """Default settings select the application's isolated LLM directory."""
    settings = Settings()
    assert settings.debug is False
    assert settings.default_model is None
    assert settings.log_file is None
    assert os.environ["LLM_USER_PATH"] == str(
        isolated_settings / "dev.pirateninja.copyedit_ai" / "llm_config"
    )


def test_settings_source_precedence(isolated_settings: Path, monkeypatch) -> None:
    """Constructor values override environment, which overrides the dotenv file."""
    (isolated_settings / ".env-copyedit_ai").write_text(
        "COPYEDIT_AI_DEFAULT_MODEL=dotenv-model\nCOPYEDIT_AI_DEBUG=true\n",
        encoding="utf-8",
    )
    assert Settings().default_model == "dotenv-model"
    assert Settings().debug is True
    monkeypatch.setenv("COPYEDIT_AI_DEFAULT_MODEL", "environment-model")
    assert Settings().default_model == "environment-model"
    assert Settings(default_model="explicit-model").default_model == "explicit-model"


@pytest.mark.usefixtures("isolated_settings")
def test_settings_can_disable_isolation(monkeypatch) -> None:
    """Disabling isolated config leaves LLM's environment untouched."""
    monkeypatch.setenv("COPYEDIT_AI_USE_ISOLATED_LLM_CONFIG", "false")
    assert Settings().use_isolated_llm_config is False
    assert "LLM_USER_PATH" not in os.environ


def test_settings_preserve_llm_override(isolated_settings: Path, monkeypatch) -> None:
    """Explicit LLM_USER_PATH continues to take precedence over isolation."""
    override = str(isolated_settings / "custom-llm")
    monkeypatch.setenv("LLM_USER_PATH", override)
    Settings()
    assert os.environ["LLM_USER_PATH"] == override
