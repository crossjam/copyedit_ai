"""copyedit_ai Self Command-Line Interface.

This module provides a command-line interface to interact with
internals of the copyedit_ai CLI.
"""

from importlib.metadata import version
from pathlib import Path

import llm
import typer
import yaml
from loguru import logger

from .copyedit import SYSTEM_PROMPT

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
