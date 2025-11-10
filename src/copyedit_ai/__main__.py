"""copyedit_ai CLI implementation.

Copyedit text from the CLI using AI
"""

import sys
from pathlib import Path

import typer
import typer.main
from click_default_group import DefaultGroup
from loguru import logger

from .copyedit import copyedit
from .self_subcommand import cli as self_cli
from .settings import Settings

app = typer.Typer()

# Register subcommands
app.add_typer(
    self_cli,
    name="self",
    help="Manage the copyedit_ai command.",
)


def _perform_copyedit(
    settings: Settings,
    file_path: Path | None,
    model: str | None,
    stream: bool,
) -> None:
    """Perform copyediting operation.

    Helper function to handle the actual copyediting logic.
    """
    # Use default model from settings if not provided
    model_name = model or settings.default_model

    # Read input text
    if file_path:
        logger.info(f"Reading from file: {file_path}")
        text = file_path.read_text()
    else:
        logger.info("Reading from stdin")
        text = sys.stdin.read()

    if not text.strip():
        logger.error("No input text provided")
        typer.echo("Error: No input text provided", err=True)
        raise typer.Exit(1)

    # Perform copyediting
    try:
        response = copyedit(text, model_name=model_name, stream=stream)

        if stream:
            # Stream output
            for chunk in response:
                typer.echo(chunk, nl=False)
            typer.echo()  # Final newline
        else:
            # Output complete response
            typer.echo(response.text())
    except Exception as e:
        logger.exception("Error during copyediting")
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e


@app.callback()
def main_callback(
    ctx: typer.Context,
    debug: bool = typer.Option(
        False,
        "--debug",
        "-D",
        help="Enable debugging output.",
    ),
) -> None:
    """Copyedit text from the CLI using AI"""
    ctx.obj = Settings()
    debug = debug or ctx.obj.debug
    (logger.enable if debug else logger.disable)("copyedit_ai")
    logger.add("copyedit_ai.log")
    logger.info(f"{debug=}")


@app.command(name="edit")
def edit_command(
    ctx: typer.Context,
    file_path: Path | None = typer.Argument(
        None,
        help="File to copyedit. If not provided, reads from stdin.",
        exists=True,
        readable=True,
    ),
    model: str | None = typer.Option(
        None,
        "--model",
        "-m",
        help="LLM model to use for copyediting.",
    ),
    stream: bool = typer.Option(
        True,
        "--stream/--no-stream",
        help="Stream the response as it's generated.",
    ),
) -> None:
    """Copyedit text using AI.

    Reads text from a file or stdin and copyedits it using an LLM.
    The copyedited text and a summary of changes are output to stdout.

    Examples:
        copyedit_ai < draft.txt
        copyedit_ai draft.txt
        cat draft.txt | copyedit_ai -m claude-opus

    """
    settings: Settings = ctx.obj
    _perform_copyedit(settings, file_path, model, stream)


def cli() -> None:
    """CLI entry point with default command support."""
    click_group = typer.main.get_command(app)
    # Replace the group class with DefaultGroup
    click_group.__class__ = DefaultGroup
    click_group.default_cmd_name = "edit"
    click_group.default_if_no_args = True
    click_group()


if __name__ == "__main__":
    sys.exit(cli())
