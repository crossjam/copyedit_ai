"""Tests for user_dir module."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from copyedit_ai import user_dir


def test_get_xdg_config_home_with_env_var(monkeypatch) -> None:
    """Test get_xdg_config_home when XDG_CONFIG_HOME is set."""
    test_path = "/custom/config/path"
    monkeypatch.setenv("XDG_CONFIG_HOME", test_path)

    result = user_dir.get_xdg_config_home()

    assert result == Path(test_path)


def test_get_xdg_config_home_without_env_var(monkeypatch) -> None:
    """Test get_xdg_config_home fallback to ~/.config."""
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)

    result = user_dir.get_xdg_config_home()

    assert result == Path.home() / ".config"


def test_get_app_config_dir(monkeypatch) -> None:
    """Test get_app_config_dir returns correct path."""
    test_path = "/custom/config"
    monkeypatch.setenv("XDG_CONFIG_HOME", test_path)

    result = user_dir.get_app_config_dir()

    expected = Path(test_path) / "dev.pirateninja.copyedit_ai"
    assert result == expected


def test_get_llm_config_dir(monkeypatch) -> None:
    """Test get_llm_config_dir returns correct path."""
    test_path = "/custom/config"
    monkeypatch.setenv("XDG_CONFIG_HOME", test_path)

    result = user_dir.get_llm_config_dir()

    expected = Path(test_path) / "dev.pirateninja.copyedit_ai" / "llm_config"
    assert result == expected


def test_is_initialized_false(tmp_path: Path, monkeypatch) -> None:
    """Test is_initialized returns False when directory doesn't exist."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    result = user_dir.is_initialized()

    assert result is False


def test_is_initialized_true(tmp_path: Path, monkeypatch) -> None:
    """Test is_initialized returns True when directory exists."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    # Create the directory structure
    llm_config_dir = tmp_path / "dev.pirateninja.copyedit_ai" / "llm_config"
    llm_config_dir.mkdir(parents=True)

    result = user_dir.is_initialized()

    assert result is True


def test_initialize_creates_directories(tmp_path: Path, monkeypatch) -> None:
    """Test initialize creates the directory structure."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    user_dir.initialize()

    app_config_dir = tmp_path / "dev.pirateninja.copyedit_ai"
    llm_config_dir = app_config_dir / "llm_config"
    templates_dir = llm_config_dir / "templates"

    assert app_config_dir.exists()
    assert app_config_dir.is_dir()
    assert llm_config_dir.exists()
    assert llm_config_dir.is_dir()
    assert templates_dir.exists()
    assert templates_dir.is_dir()


def test_initialize_already_initialized(tmp_path: Path, monkeypatch, caplog) -> None:
    """Test initialize when already initialized doesn't fail."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    # Initialize once
    user_dir.initialize()

    # Initialize again (should not raise)
    user_dir.initialize()

    # Directory should still exist
    llm_config_dir = tmp_path / "dev.pirateninja.copyedit_ai" / "llm_config"
    assert llm_config_dir.exists()


def test_initialize_with_force(tmp_path: Path, monkeypatch) -> None:
    """Test initialize with force=True recreates directories."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    # Initialize once
    user_dir.initialize()

    # Create a test file in the directory
    llm_config_dir = tmp_path / "dev.pirateninja.copyedit_ai" / "llm_config"
    test_file = llm_config_dir / "test.txt"
    test_file.write_text("test content")

    # Initialize with force
    user_dir.initialize(force=True)

    # Directory should still exist
    assert llm_config_dir.exists()
    # Test file should still exist (force doesn't delete contents)
    assert test_file.exists()


def test_set_llm_user_path_sets_env_var(tmp_path: Path, monkeypatch) -> None:
    """Test set_llm_user_path sets LLM_USER_PATH environment variable."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.delenv("LLM_USER_PATH", raising=False)

    user_dir.set_llm_user_path()

    expected = str(tmp_path / "dev.pirateninja.copyedit_ai" / "llm_config")
    assert os.environ.get("LLM_USER_PATH") == expected


def test_set_llm_user_path_respects_existing(tmp_path: Path, monkeypatch) -> None:
    """Test set_llm_user_path respects existing LLM_USER_PATH."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    existing_path = "/custom/llm/path"
    monkeypatch.setenv("LLM_USER_PATH", existing_path)

    user_dir.set_llm_user_path()

    # Should not change existing value
    assert os.environ.get("LLM_USER_PATH") == existing_path


def test_initialize_permission_error(tmp_path: Path, monkeypatch) -> None:
    """Test initialize handles permission errors gracefully."""
    import os

    # Skip test if running as root (permissions work differently)
    if os.getuid() == 0:
        pytest.skip("Test skipped when running as root")

    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    # Make the directory read-only
    app_config_dir = tmp_path / "dev.pirateninja.copyedit_ai"
    app_config_dir.mkdir(parents=True)
    app_config_dir.chmod(0o444)  # Read-only

    try:
        with pytest.raises(OSError):
            user_dir.initialize()
    finally:
        # Cleanup: restore permissions
        app_config_dir.chmod(0o755)
