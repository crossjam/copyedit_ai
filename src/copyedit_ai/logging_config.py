"""Centralized logging configuration for the Copyedit application.

This module provides a thin wrapper around Loguru so that logging can be
configured in one place and used consistently across the codebase.

Usage
-----

1. Call :func:`setup_logging` once at application startup, passing the
   application directory and any CLI flags that affect verbosity:

   >>> from pathlib import Path
   >>> from copyedit_ai.logging_config import setup_logging, get_logger
   >>> setup_logging(Path(app_dir), verbose=True)
   >>> log = get_logger("my_component")
   >>> log.info("Ready")

2. In modules that need logging, obtain a logger via :func:`get_logger`:

   * ``get_logger()`` returns the shared Loguru logger as-is.
   * ``get_logger("name")`` returns a logger with ``extra["logger_name"]``
     bound to the given name so it appears in the log output.

Configuration precedence
-------------------------

When :func:`setup_logging` is called, logging configuration is resolved with
the following precedence (highest to lowest):

1. The path specified by the ``COPYEDIT_LOG_CONFIG`` environment variable,
   if it points to a valid configuration file understood by
   :class:`loguru_config.LoguruConfig`.
2. A ``logging.json`` file (see :data:`DEFAULT_CONFIG_FILENAME`) located in
   the provided ``app_dir``.
3. The built-in default configuration created by :func:`_default_loguru_config`,
   using the computed log level and optional file sink.

If either external configuration source (1) or (2) is successfully loaded,
the default configuration is not applied.

Logger naming pattern
---------------------

Log records are formatted via :func:`_format_record`, which ensures that
``extra["logger_name"]`` is present. If a logger name has been bound via
:func:`get_logger("name")`, that value is used; otherwise the underlying
Loguru record ``name`` is used as a fallback. The ``logger_name`` field is
then rendered in the log line according to :data:`LOG_FORMAT`.
"""

from __future__ import annotations

import os
import sys
from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger as _logger
from loguru_config.loguru_config import LoguruConfig  # type: ignore[import-untyped]

DEFAULT_CONFIG_FILENAME = "logging.json"
LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{extra[logger_name]}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>\n{exception}"
)


if TYPE_CHECKING:
    import loguru
    from loguru import Record
else:  # pragma: no cover - runtime alias for typing compatibility
    Record = MutableMapping[str, object]


def _format_record(record: Record) -> str:
    """Build the log line using either the bound name or module name."""
    logger_name = record["extra"].get("logger_name", record["name"])
    record["extra"].setdefault("logger_name", logger_name)
    return LOG_FORMAT


def _default_loguru_config(level: str, log_file: Path | None) -> dict[str, Any]:
    """Build a default loguru configuration dictionary."""
    handlers = [
        {
            "sink": sys.stderr,
            "level": level,
            "format": _format_record,
            "colorize": True,
            "backtrace": False,
            "diagnose": False,
        }
    ]

    if log_file is not None:
        if not log_file.parent.exists():
            log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(
            {
                "sink": log_file,
                "level": level,
                "format": _format_record,
                "backtrace": False,
                "diagnose": False,
                "enqueue": False,
            }
        )

    return {
        "handlers": handlers,
        "extra": {"logger_name": "copyedit"},
    }


def _load_external_config(config_path: Path) -> bool:
    """Load configuration from a file if it exists."""
    if config_path.is_file():
        LoguruConfig.load(config_path)
        return True
    return False


def setup_logging(
    app_dir: Path,
    *,
    verbose: bool = False,
    quiet: bool = False,
    log_file: Path | None = None,
    enable_file_logging: bool | None = None,
) -> None:
    """Configure loguru logging for the application.

    External configuration can be supplied via the ``COPYEDIT_LOG_CONFIG``
    environment variable or by placing a ``logging.json`` file in the
    application directory.

    Args:
        app_dir: Directory to search for a ``logging.json`` configuration
            file when no explicit configuration file is provided via the
            ``COPYEDIT_LOG_CONFIG`` environment variable.
        verbose: If True and ``quiet`` is False, set the log level to
            ``DEBUG`` instead of the default ``INFO`` level.
        quiet: If True, set the log level to ``ERROR`` regardless of the
            value of ``verbose`` (takes precedence over ``verbose``).
        log_file: Optional path to a log file. When file logging is enabled,
            log messages will also be written to this file.
        enable_file_logging: Explicit control over file logging. When True,
            file logging is enabled (using ``log_file`` if provided). When
            False, file logging is disabled even if ``log_file`` is set. When
            None, file logging is enabled only if ``log_file`` is not None.

    """
    # Determine log level with precedence: quiet > verbose > default
    if quiet:
        level = "ERROR"
    elif verbose:
        level = "DEBUG"
    else:
        level = "INFO"

    _logger.remove()

    config_file = os.getenv("COPYEDIT_LOG_CONFIG")
    if config_file and _load_external_config(Path(config_file)):
        return

    if _load_external_config(app_dir / DEFAULT_CONFIG_FILENAME):
        return

    # Determine if file logging should be enabled:
    # - True if enable_file_logging is explicitly True
    # - True if enable_file_logging is None and log_file is provided
    # - False otherwise
    should_log_to_file = enable_file_logging is True or (
        enable_file_logging is None and log_file is not None
    )
    file_sink = log_file if should_log_to_file else None
    LoguruConfig.load(_default_loguru_config(level, file_sink), inplace=True)


def get_logger(name: str | None = None) -> loguru.Logger:
    """Return a logger instance bound to the provided name."""
    if name:
        return _logger.bind(logger_name=name)
    return _logger


__all__ = ["get_logger", "setup_logging"]
