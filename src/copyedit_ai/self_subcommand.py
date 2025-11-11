"""copyedit_ai Self Command-Line Interface.

This module provides a command-line interface to interact with
internals of the copyedit_ai CLI.
"""

import json
import shutil
from importlib.metadata import version
from pathlib import Path

import llm
import typer
import yaml
from loguru import logger

from .copyedit import SYSTEM_PROMPT
from .user_dir import (
    get_app_config_dir,
    get_llm_config_dir,
    initialize,
    is_initialized,
    set_llm_user_path,
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
        typer.echo("  - Install templates: copyedit_ai self install-template")
        typer.echo("  - Create aliases: copyedit_ai self install-alias <alias> <model>")

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
def check_command(
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
            import os

            llm_user_path = os.environ.get("LLM_USER_PATH")
            if llm_user_path:
                typer.echo(f"  Isolated config: Enabled (LLM_USER_PATH={llm_user_path})")
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
            raise typer.Exit(1)

    except typer.Exit:
        raise
    except Exception as error:
        logger.exception("Failed to check configuration")
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from None


@cli.command(name="install-template")
def install_template(
    name: str = typer.Argument("copyedit", help="Name for the template"),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing template if it exists",
    ),
) -> None:
    """Install a copyedit prompt template for use with llm.

    This creates a template that can be used with the llm CLI tool:

        llm -t copyedit "Your text here"

    The template includes the copyedit system prompt and is stored
    in the llm templates directory.
    """
    try:
        # Check if configuration is initialized
        if not is_initialized():
            logger.error("Configuration not initialized")
            typer.echo("Error: Configuration not initialized.", err=True)
            typer.echo("Run 'copyedit_ai self init' first.", err=True)
            raise typer.Exit(1)

        # Set LLM user path to use isolated config
        set_llm_user_path()

        # Get the templates directory from llm
        templates_dir = Path(llm.user_dir()) / "templates"
        templates_dir.mkdir(parents=True, exist_ok=True)

        template_path = templates_dir / f"{name}.yaml"

        # Check if template already exists
        if template_path.exists() and not force:
            logger.error(f"Template '{name}' already exists at {template_path}")
            typer.echo(
                f"Error: Template '{name}' already exists. Use --force to overwrite.",
                err=True,
            )
            raise typer.Exit(1)

        # Create the template
        template_content = {
            "system": SYSTEM_PROMPT.strip(),
            "prompt": "Copy edit the text that follows:\n\n$input",
        }

        # Write the template file
        with template_path.open("w") as f:
            yaml.dump(template_content, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Created template '{name}' at {template_path}")
        typer.secho(f"✓ Installed template '{name}'", fg=typer.colors.GREEN)
        typer.echo(f"  Location: {template_path}")
        typer.echo(f"\nUsage: llm -t {name} 'Your text here'")
        typer.echo(f"       llm -t {name} --param input 'Your text here'")
        typer.echo(f"       cat file.txt | llm -t {name} --param input -")

    except Exception as error:
        logger.exception("Failed to install template")
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from None


@cli.command(name="install-alias")
def install_alias(
    alias: str = typer.Argument(..., help="Alias name to create"),
    model_id: str = typer.Argument(..., help="Model ID to alias"),
) -> None:
    """Install a model alias for use with llm.

    This creates an alias that can be used as a shortcut for a model:

        copyedit_ai self install-alias fast gpt-4o-mini
        copyedit_ai -m fast "Your text"

    Examples:
        copyedit_ai self install-alias fast gpt-4o-mini
        copyedit_ai self install-alias smart claude-3-5-sonnet-20241022
        copyedit_ai self install-alias cheap gpt-3.5-turbo
    """
    try:
        # Check if configuration is initialized
        if not is_initialized():
            logger.error("Configuration not initialized")
            typer.echo("Error: Configuration not initialized.", err=True)
            typer.echo("Run 'copyedit_ai self init' first.", err=True)
            raise typer.Exit(1)

        # Set LLM user path to use isolated config
        set_llm_user_path()

        # Set the alias using llm's API
        llm.set_alias(alias, model_id)

        logger.info(f"Created alias '{alias}' -> '{model_id}'")
        typer.secho(f"✓ Installed alias '{alias}' -> '{model_id}'", fg=typer.colors.GREEN)
        typer.echo(f"\nUsage: copyedit_ai -m {alias} 'Your text here'")
        typer.echo(f"       llm -m {alias} 'Your prompt'")

    except Exception as error:
        logger.exception("Failed to install alias")
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from None
