"""User directory management for copyedit_ai.

This module provides XDG-compliant directory management for copyedit_ai's
configuration, including isolated LLM configuration to prevent conflicts
with system-wide llm installations.
"""

import os
from pathlib import Path

import platformdirs
from loguru import logger

# Application identifier using reverse domain notation
APP_IDENTIFIER = "dev.pirateninja.copyedit_ai"


def get_xdg_config_home() -> Path:
    """Get XDG_CONFIG_HOME or fallback to ~/.config.

    Returns:
        Path to XDG config home directory

    """
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config)
    return Path.home() / ".config"


def get_app_config_dir() -> Path:
    """Get dev.pirateninja.copyedit_ai config directory.

    Returns:
        Path to application config directory

    """
    if os.environ.get("XDG_CONFIG_HOME"):
        return get_xdg_config_home() / APP_IDENTIFIER

    return Path(platformdirs.user_data_dir(APP_IDENTIFIER, "copyedit_ai"))


def get_llm_config_dir() -> Path:
    """Get llm_config subdirectory.

    Returns:
        Path to LLM configuration directory

    """
    return get_app_config_dir() / "llm_config"


def is_initialized() -> bool:
    """Check if directory structure exists.

    Returns:
        True if the directory structure has been initialized

    """
    llm_config_dir = get_llm_config_dir()
    return llm_config_dir.exists() and llm_config_dir.is_dir()


def initialize(*, force: bool = False) -> None:
    """Create directory structure.

    Args:
        force: If True, recreate directories even if they exist

    Raises:
        OSError: If directory creation fails

    """
    app_config_dir = get_app_config_dir()
    llm_config_dir = get_llm_config_dir()

    if is_initialized() and not force:
        logger.debug(f"Directory already initialized at {app_config_dir}")
        return

    try:
        # Create directories with appropriate permissions (0700 - user only)
        app_config_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        llm_config_dir.mkdir(parents=True, exist_ok=True, mode=0o700)

        # Create templates subdirectory
        templates_dir = llm_config_dir / "templates"
        templates_dir.mkdir(exist_ok=True, mode=0o700)

        logger.info(f"Initialized configuration at {app_config_dir}")
        logger.debug(f"LLM config directory: {llm_config_dir}")

    except OSError as e:
        logger.error(f"Failed to initialize directories: {e}")
        raise


def set_llm_user_path() -> None:
    """Set LLM_USER_PATH environment variable to our config dir.

    This function sets the LLM_USER_PATH environment variable to point to
    our isolated llm_config directory, ensuring that all llm package
    operations use copyedit_ai's isolated configuration.

    The function respects explicit user overrides - if LLM_USER_PATH is
    already set, it will not be changed.

    Note:
        This should be called before any llm package functions that access
        configuration, templates, or aliases.

    """
    # Respect explicit user overrides
    if os.environ.get("LLM_USER_PATH"):
        logger.debug("LLM_USER_PATH already set, using user override")
        return

    llm_config = get_llm_config_dir()
    os.environ["LLM_USER_PATH"] = str(llm_config)
    logger.debug(f"Set LLM_USER_PATH={llm_config}")
