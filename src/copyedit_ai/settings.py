"""copyedit_ai Settings."""

from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings for copyedit_ai."""

    model_config = SettingsConfigDict(
        env_prefix="COPYEDIT_AI_",
        env_file=".env-copyedit_ai",
    )
    debug: bool = False
    default_model: str | None = None  # Uses llm's default if None
    use_isolated_llm_config: bool = True  # Use isolated LLM configuration
    llm_config_path: Path | None = None  # Override path for LLM config

    @model_validator(mode="after")
    def setup_llm_config(self) -> "Settings":
        """Set up LLM configuration path if isolated config is enabled."""
        if self.use_isolated_llm_config:
            # Import here to avoid circular imports
            from .user_dir import set_llm_user_path

            set_llm_user_path()
        return self
