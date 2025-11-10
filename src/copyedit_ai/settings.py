"""copyedit_ai Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings for copyedit_ai."""

    model_config = SettingsConfigDict(
        env_prefix="COPYEDIT_AI",
        env_file=".env-copyedit_ai",
    )
    debug: bool = False
