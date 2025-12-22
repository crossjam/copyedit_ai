"""copyedit_ai Self Command-Line Interface.

This module provides a command-line interface to interact with
internals of the copyedit_ai CLI.
"""

import json
import os
import shutil
from importlib.metadata import version
from pathlib import Path

import typer
import yaml
from llm.cli import template_dir
from loguru import logger

from .copyedit import SYSTEM_PROMPT, templates_installed
from .user_dir import (
    get_app_config_dir,
    get_llm_config_dir,
    initialize,
    is_initialized,
)

cli = typer.Typer()


@cli.command(name="version")
def version_subcommand() -> None:
    """Retrieve the package version."""
    try:
        pkg_version = version("copyedit_ai")
        logger.info(f"Package version: {pkg_version}")
        typer.secho(pkg_version, fg=typer.colors.GREEN)
    except Exception as error:
        logger.error(f"Failed to retrieve package version: {error}")
        raise typer.Exit(code=1) from None


@cli.command(name="init")
def init_command(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Reinitialize even if already exists",
    ),
    import_system_config: bool = typer.Option(
        False,
        "--import-system-config",
        help="Import aliases and templates from system llm",
    ),
) -> None:
    """Initialize copyedit_ai configuration directory.

    Creates the XDG-compliant configuration directory structure for
    copyedit_ai's isolated LLM configuration. This prevents conflicts
    with system-wide llm installations.

    Examples:
        copyedit_ai self init
        copyedit_ai self init --import-system-config
        copyedit_ai self init --force

    """
    try:
        app_config_dir = get_app_config_dir()
        llm_config_dir = get_llm_config_dir()

        existing_templates = templates_installed()

        if not any(k for k in existing_templates if k.startswith("copyedit")):
            typer.secho(
                "No copyedit llm templates found. Installing default",
                fg=typer.colors.YELLOW,
            )
            default_template = {}
            default_template["system"] = SYSTEM_PROMPT
            template_path = template_dir() / "copyedit.yaml"
            typer.secho(
                f"Writing default template to: {template_path!s}",
                fg=typer.colors.YELLOW,
            )

            template_path.write_text(
                yaml.safe_dump(
                    default_template,
                    indent=4,
                    default_flow_style=False,
                    sort_keys=False,
                ),
                "utf-8",
            )

        # Check if already initialized
        if is_initialized() and not force:
            logger.warning("Configuration already initialized")
            typer.secho(
                "⚠ Configuration already initialized",
                fg=typer.colors.YELLOW,
            )
            typer.echo(f"  Location: {app_config_dir}")
            typer.echo(f"  LLM config: {llm_config_dir}")
            typer.echo("\nUse --force to reinitialize")
            return

        # Initialize directory structure
        initialize(force=force)

        # Import from system llm if requested
        if import_system_config:
            _import_system_llm_config(llm_config_dir)

        # Success message
        typer.secho("✓ Initialized copyedit_ai configuration", fg=typer.colors.GREEN)
        typer.echo(f"  Location: {app_config_dir}")
        typer.echo(f"  LLM config: {llm_config_dir}")
        typer.echo("\nConfiguration is ready. You can now:")
        typer.echo("  - Manage API keys: copyedit_ai self keys set <provider>")
        typer.echo("  - Create aliases: copyedit_ai self aliases set <alias> <model>")
        typer.echo("  - Edit templates: copyedit_ai self templates edit <name>")

    except Exception as error:
        logger.exception("Failed to initialize configuration")
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from None


def _import_system_llm_config(target_dir: Path) -> None:
    """Import templates and aliases from system llm configuration.

    Args:
        target_dir: Target directory for imported configuration

    """
    # Get system llm directory
    system_llm_dir = Path.home() / ".config" / "io.datasette.llm"

    if not system_llm_dir.exists():
        logger.info("No system llm configuration found to import")
        typer.echo("  No system llm configuration found to import")
        return

    imported = []

    # Import templates
    system_templates = system_llm_dir / "templates"
    if system_templates.exists() and system_templates.is_dir():
        target_templates = target_dir / "templates"
        for template_file in system_templates.glob("*.yaml"):
            target_file = target_templates / template_file.name
            shutil.copy2(template_file, target_file)
            imported.append(f"template: {template_file.name}")
            logger.debug(f"Imported template: {template_file.name}")

    # Import aliases
    system_aliases = system_llm_dir / "aliases.json"
    if system_aliases.exists():
        target_aliases = target_dir / "aliases.json"
        shutil.copy2(system_aliases, target_aliases)
        imported.append("aliases.json")
        logger.debug("Imported aliases.json")

    if imported:
        typer.echo(f"  Imported {len(imported)} item(s) from system llm:")
        for item in imported:
            typer.echo(f"    - {item}")
    else:
        typer.echo("  No templates or aliases found in system llm")


@cli.command(name="check")
def check_command(  # noqa: C901, PLR0912, PLR0915
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed information",
    ),
) -> None:
    """Check copyedit_ai configuration status.

    Displays the initialization status of the configuration directory,
    shows paths, and lists installed templates and aliases.

    Examples:
        copyedit_ai self check
        copyedit_ai self check --verbose

    """
    try:
        app_config_dir = get_app_config_dir()
        llm_config_dir = get_llm_config_dir()
        initialized = is_initialized()

        if initialized:
            typer.secho("✓ Configuration initialized", fg=typer.colors.GREEN)
            typer.echo(f"  Config directory: {app_config_dir}")
            typer.echo(f"  LLM config: {llm_config_dir}")

            # Show isolated config status
            llm_user_path = os.environ.get("LLM_USER_PATH")
            if llm_user_path:
                typer.echo(
                    f"  Isolated config: Enabled (LLM_USER_PATH={llm_user_path})"
                )
            else:
                typer.echo("  Isolated config: Disabled")

            # List templates
            templates_dir = llm_config_dir / "templates"
            if templates_dir.exists():
                templates = list(templates_dir.glob("*.yaml"))
                typer.echo(f"\nTemplates ({len(templates)}):")
                if templates:
                    for template in templates:
                        typer.echo(f"  - {template.stem}")
                else:
                    typer.echo("  (none)")

            # List aliases
            aliases_file = llm_config_dir / "aliases.json"
            if aliases_file.exists():
                try:
                    with aliases_file.open() as f:
                        aliases = json.load(f)
                    typer.echo(f"\nAliases ({len(aliases)}):")
                    if aliases:
                        for alias, model in aliases.items():
                            typer.echo(f"  - {alias} -> {model}")
                    else:
                        typer.echo("  (none)")
                except (json.JSONDecodeError, OSError) as e:
                    logger.debug(f"Error reading aliases: {e}")
                    typer.echo("\nAliases: (error reading file)")
            else:
                typer.echo("\nAliases (0):")
                typer.echo("  (none)")

            if verbose:
                # Show additional details
                typer.echo("\nDirectory contents:")
                for item in llm_config_dir.iterdir():
                    typer.echo(f"  - {item.name}")

        else:
            typer.secho("⚠ Configuration not initialized", fg=typer.colors.YELLOW)
            typer.echo(f"  Expected location: {app_config_dir}")
            typer.echo("\nRun 'copyedit_ai self init' to set up configuration.")
            raise typer.Exit(1)  # noqa: TRY301

    except typer.Exit:
        raise
    except Exception as error:
        logger.exception("Failed to check configuration")
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from None
